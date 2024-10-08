from .base import Patient
import numpy as np
from scipy.integrate import ode
import pandas as pd
from collections import namedtuple
import logging
import pkg_resources
from T2DMSimulator.glucose.GlucoseDynamics import GlucoseDynamics
from T2DMSimulator.glucose.GlucoseParameters import GlucoseParameters
from T2DMSimulator.glucose.glucose_initializer import GlucoseInitializer
from T2DMSimulator.utils.TimerQueue import TimerQueue
from T2DMSimulator.utils.TrapezoidFunc import TrapezoidFunc
import random
import queue

logger = logging.getLogger(__name__)

Action = namedtuple("patient_action", ['CHO', 'insulin_fast', 'insulin_long', 'metformin', 'vildagliptin', 'stress', 'physical'])
Observation = namedtuple("observation", ['Gsub'])

PATIENT_PARA_FILE = pkg_resources.resource_filename(
    'T2DMSimulator', 'params/vpatient_params.csv')


class T2DPatient(Patient):
    SAMPLE_TIME = 1  # min
    EAT_RATE = 5  # g/min CHO

    def __init__(self,
                 params,
                 init_state=None,
                 random_init_bg=False,
                 seed=None,
                 t0=0,
                 GBPC0=None, 
                 IBPF0=None, 
                 brates=None,
                 glucose_params=None,
                 name="testing",
                 prob_of_actioning=1,
                 constraints=[]):
        '''
        T2DPatient constructor.
        Inputs:
            - params: a pandas sequence
            - init_state: customized initial state.
              If not specified, load the default initial state in
              params.iloc[2:15]
            - t0: simulation start time, it is 0 by default
        '''
        self._params = params
        self.name = name
        self.param = GlucoseParameters() if glucose_params == None else glucose_params
        self.GBPC0 = 7/0.0555 if GBPC0 is None else GBPC0
        self.IBPF0 = 1 if IBPF0 is None else IBPF0
        self.brates = {'rBGU': 70, 'rRBCU': 10, 'rGGU': 20, 'rPGU': 35, 'rHGU': 20} if brates is None else brates
        self._init_state = init_state
        self.random_init_bg = random_init_bg
        self._seed = seed
        self.t0 = t0
        self.prob = prob_of_actioning
        self.reccomended_actions = TimerQueue()
        self.physical_activity_queue = []
        self.heart_rates_running = [55,56,55]
        self.constraints = constraints
        self.X0v, self.rates, self.SB = GlucoseInitializer(self.param, self).calculate_values()
        self.reset()

    @property
    def basal(self):
        basal0 = {
            'GPF': self.X0v[39],
            'IPF': self.IBPF0,
            'IL': self.X0v[28],
            'GL': self.X0v[36],
            'Gamma': self.X0v[40],
            'SB': self.SB,
            'GH': self.X0v[34],
            'IH': self.X0v[26],
            'rPIR': self.rates[0],
            'rBGU': self.rates[1],
            'rRBCU': self.rates[2],
            'rGGU': self.rates[3],
            'rPGU': self.rates[4],
            'rHGP': self.rates[5],
            'rHGU': self.rates[6]
        }
        return basal0

    @classmethod
    def withID(cls, patient_id, **kwargs):
        '''
        Construct patient by patient_id
        id are integers
        '''
        patient_params = pd.read_csv(PATIENT_PARA_FILE)
        params = patient_params.iloc[patient_id - 1, :]
        return cls(params, **kwargs)

    @classmethod
    def withName(cls, name, **kwargs):
        '''
        Construct patient by name.
        Names can be
            adolescent#001 - adolescent#010
            adult#001 - adult#001
            child#001 - child#010
        '''
        patient_params = pd.read_csv(PATIENT_PARA_FILE)
        params = patient_params.loc[patient_params.Name == name].squeeze()
        return cls(params, **kwargs)

    @property
    def state(self):
        return self._odesolver.y

    @property
    def t(self):
        return self._odesolver.t

    @property
    def sample_time(self):
        return self.SAMPLE_TIME
    
    def add_reccomended_action(self, reccomended_action):
        if not all(getattr(reccomended_action, field) == 0 for field in reccomended_action._fields if field != 'time'):
            random.seed(self.seed)
            # random chance for action to be carried out later or earlier by 10-20 minutes
            if random.random() < 0.4:
                noise = random.randint(10,20)
                # may be added or negated to the original time
                newTime = reccomended_action.time + noise if random.random() > 0.5 else reccomended_action.time - noise
                self.reccomended_actions.put(reccomended_action, newTime)
            else:
                self.reccomended_actions.put(reccomended_action, reccomended_action.time)

    def simulate_running_heart_rate(self):
        std_deviation = 5
        coefficients = [0.5, 0.3, 0.2]
        lower_bound = 50
        upper_bound = 85
        
        next_value = sum(coeff * self.heart_rates_running[-lag] for lag, coeff in enumerate(coefficients, start=1)) \
                    + np.random.normal(0, std_deviation)
        
        # Ensure the next value stays within the specified bounds
        next_value = min(max(next_value, lower_bound), upper_bound)
        self.heart_rates_running.append(next_value)
        self.heart_rates_running.pop()
        return next_value

    def step(self, action, reccomended_action):
        curr_recc_action = self.reccomended_actions.get()
        
        self.add_reccomended_action(reccomended_action)
        # Convert announcing meal to the meal amount to eat at the moment
        to_eat = self._announce_meal(action.CHO)
        action = action._replace(CHO=to_eat)

        heart_rate = self.simulate_running_heart_rate()
        action = action._replace(physical=heart_rate)

        if curr_recc_action != None:
            random.seed(self.seed)
            # random chance to not carry out action
            if random.random() < self.prob:
                if curr_recc_action.meal != 0:
                    print(f"eating {curr_recc_action.meal}")
                    to_eat = self._announce_meal(curr_recc_action.meal)
                    action = action._replace(CHO=to_eat)
                elif curr_recc_action.physical != 0:
                    print("exercising")
                    heartbeat = TrapezoidFunc(curr_recc_action.physical, 
                                              curr_recc_action.times[0], 
                                              curr_recc_action.times[1], 
                                              curr_recc_action.times[2], 
                                              curr_recc_action.times[3])
                    action = action._replace(physical=heartbeat.pop(0) + action.physical)
                    self.physical_activity_queue.extend(heartbeat)
                if curr_recc_action.metformin != 0:
                    action = action._replace(metformin=curr_recc_action.metformin)
        physical_activity_heart_beat = 0
        original_heart_beat = action.physical
        if len(self.physical_activity_queue) != 0:
            physical_activity_heart_beat = self.physical_activity_queue.pop(0)
            action = action._replace(physical=physical_activity_heart_beat + action.physical)

        # Detect eating or not and update last digestion amount
        if action.CHO > 0 and self._last_action.CHO <= 0:
            print('t = {}, patient starts eating ...'.format(self.t))
            #self._last_Qsto = self.state[0] + self.state[1]  # unit: mg
            self._last_foodtaken = 0  # unit: g
            self.is_eating = True

        if to_eat > 0:
           print(f"{self._odesolver.t} + {self.sample_time}")
           print('t = {}, patient eats {} g'.format(
                self.t, action.CHO))

        if self.is_eating:
            self._last_foodtaken += action.CHO  # g

        # Detect eating ended
        if action.CHO <= 0 and self._last_action.CHO > 0:
            logger.info('t = {}, Patient finishes eating!'.format(self.t))
            self.is_eating = False

        if self._last_action.metformin != 0:
            action = action._replace(metformin=0)

        # Update last input
        self._last_action = action

        # ODE solver
        self._odesolver.set_f_params(action, self.basal, self.param, self)
        if self._odesolver.successful():
            self._odesolver.integrate(self._odesolver.t + self.sample_time)
        else:
            logger.error('ODE solver failed!!')
            raise
        # return new named tuple with the rise in heartbeat due to Physical Activity
        return action._replace(physical=physical_activity_heart_beat), original_heart_beat

    @staticmethod
    def model(t, x, action, basal, glucose_parameters, self):
        t = round(t)
        action = self._last_action
        Dg = action.CHO * 1e3
        long_insulin = action.insulin_long * 1e2
        fast_insulin = action.insulin_fast * 1e2
        # Doesn't seem to have an effect?
        if long_insulin != 0 or fast_insulin != 0:
            action = action._replace(insulin_long = 0)
            action = action._replace(insulin_fast = 0)

        metformin = action.metformin * 1e3
        if metformin != 0:
            action = action._replace(metformin = 0)

        vildagliptin = action.vildagliptin * (1 / (303.406) * 10 ** 6)
        physical = action.physical
        stress = action.stress
        if t == 0.0 and Dg == 0:
            DM = 1.0
        elif (Dg != 0):
            DM = x[46] + Dg - x[47]
        else:
            DM = 0
        indices = [0, 46, 47, 3, 4, 9, 17, 19]
        values = [Dg, Dg, DM, metformin, metformin, vildagliptin, fast_insulin / 6.76, long_insulin / 6.76]

        for index, value in zip(indices, values):
            x[index] = value + x[index]
        glucose_dynamics = GlucoseDynamics(t,x,Dg,stress,physical,basal,glucose_parameters)
        dxdt = glucose_dynamics.compute()
        self._last_action = action
        return dxdt

    @property
    def observation(self):
        '''
        return the observation from patient
        for now, only the plasma glucose level is returned
        TODO: add heart rate as an observation
        '''
        GM = self.state[34]  # subcutaneous glucose (mg/kg) #Might be different, matlab code uses Plasma Glucose
       # Gsub = GM / self._params.Vg
        observation = Observation(Gsub=GM)
        return observation

    def _announce_meal(self, meal):
        '''
        patient announces meal.
        The announced meal will be added to self.planned_meal
        The meal is consumed in self.EAT_RATE
        The function will return the amount to eat at current time
        '''
        self.planned_meal += meal
        if self.planned_meal > 0:
            to_eat = min(self.EAT_RATE, self.planned_meal)
            self.planned_meal -= to_eat
            self.planned_meal = max(0, self.planned_meal)
        else:
            to_eat = 0
        return to_eat

    @property
    def seed(self):
        return self._seed

    @seed.setter
    def seed(self, seed):
        self._seed = seed
        self.reset()

    def reset(self):
        '''
        Reset the patient state to default intial state
        '''
        # if self._init_state is None:
        #     self.init_state = self._params.iloc[2:15]
        # else:
        #     self.init_state = self._init_state

        self.random_state = np.random.RandomState(self.seed)
        # if self.random_init_bg:
        #     # Only randomize glucose related states, x4, x5, and x13
        #     mean = [
        #         1.0 * self.init_state[3], 1.0 * self.init_state[4],
        #         1.0 * self.init_state[12]
        #     ]
        #     cov = np.diag([
        #         0.1 * self.init_state[3], 0.1 * self.init_state[4],
        #         0.1 * self.init_state[12]
        #     ])
        #     bg_init = self.random_state.multivariate_normal(mean, cov)
        #     self.init_state[3] = 1.0 * bg_init[0]
        #     self.init_state[4] = 1.0 * bg_init[1]
        #     self.init_state[12] = 1.0 * bg_init[2]

        #self._last_Qsto = self.init_state[0] + self.init_state[1]
        self._last_foodtaken = 0
       # self.name = self._params.Name

        ## should be fine but order is 4 (5) while other tested is order 5(4)
        self._odesolver = ode(self.model).set_integrator('dopri5')
        self._odesolver.set_initial_value(self.X0v, self.t0)

        self._last_action = Action(CHO=0, insulin_fast=0, insulin_long=0, metformin=0, vildagliptin=0, stress=0, physical=0)
        self.is_eating = False
        self.planned_meal = 0
