import numpy as np
import pkg_resources
from datetime import datetime
from gymnasium import spaces, utils as gymnasium_utils
from T2DMSimulator.simulation.env import T2DSimEnv as _T2DSimEnv
from T2DMSimulator.patient.t2dpatient import T2DPatient
from T2DMSimulator.sensor.cgm import CGMSensor
from T2DMSimulator.actuator.pump import InsulinPump
from T2DMSimulator.simulation.scenario_gen import RandomScenario
from T2DMSimulator.controller.base import Action
from gymnasium.utils import seeding
from gymnasium import Env
import gym
from gym import spaces
from gym.utils import seeding
# PATIENT_PARA_FILE = pkg_resources.resource_filename(
#     "simglucose", "params/vpatient_params.csv"
# )

class T2DSimEnv(gym.Env):
    metadata = {"render_modes": ["human"]}
    SENSOR_HARDWARE = "Dexcom"
    INSULIN_PUMP_HARDWARE = "Insulet"

    def __init__(self, patient_name=None, custom_scenario=None, reward_fun=None, seed=None, render_mode=None):
        super().__init__()
        self.render_mode = render_mode
        self.reward_fun = reward_fun
        self.np_random, _ = seeding.np_random(seed=seed)
        self.patient_name = patient_name if patient_name is not None else ["adolescent#001"]
        self.custom_scenario = custom_scenario
        self.env, _, _, _ = self._create_env()

    def _step(self, action):
        act = Action(basal=action, bolus=0)
        if self.reward_fun is None:
            return self.env.step(act)
        return self.env.step(act, reward_fun=self.reward_fun)

    def _raw_reset(self):
        return self.env.reset()

    def _reset(self):
        self.env, _, _, _ = self._create_env()
        obs, _, _, _ = self.env.reset()
        return obs

    def _seed(self, seed=None):
        self.np_random, seed1 = seeding.np_random(seed=seed)
        self.env, seed2, seed3, seed4 = self._create_env()
        return [seed1, seed2, seed3, seed4]
    
    def _create_env(self):
        # Derive a random seed. This gets passed as a uint, but gets
        # checked as an int elsewhere, so we need to keep it below
        # 2**31.
        seed2 = seeding.hash_seed(self.np_random.randint(0, 1000)) % 2**31
        seed3 = seeding.hash_seed(seed2 + 1) % 2**31
        seed4 = seeding.hash_seed(seed3 + 1) % 2**31

        hour = self.np_random.randint(low=0.0, high=24.0)
        start_time = datetime(2018, 1, 1, hour, 0, 0)

        if isinstance(self.patient_name, list):
            patient_name = self.np_random.choice(self.patient_name)
            patient = T2DPatient.withName(patient_name, random_init_bg=True, seed=seed4)
        else:
            patient = T2DPatient.withName(
                self.patient_name, random_init_bg=True, seed=seed4
            )

        if isinstance(self.custom_scenario, list):
            scenario = self.np_random.choice(self.custom_scenario)
        else:
            scenario = (
                RandomScenario(start_time=start_time, seed=seed3)
                if self.custom_scenario is None
                else self.custom_scenario
            )

        sensor = CGMSensor.withName(self.SENSOR_HARDWARE, seed=seed2)
        pump = InsulinPump.withName(self.INSULIN_PUMP_HARDWARE)
        env = _T2DSimEnv(patient, sensor, pump, scenario)
        return env, seed2, seed3, seed4

    def _render(self, mode="human", close=False):
        self.env.render(close=close)

    def _close(self):
        super()._close()
        self.env._close_viewer()

    @property
    def action_space(self):
        ub = self.env.pump._params["max_basal"]
        return spaces.Box(low=0, high=ub, shape=(7,))

    @property
    def observation_space(self):
        return spaces.Box(low=0, high=1000, shape=(1,))

    @property
    def max_basal(self):
        return self.env.pump._params["max_basal"]
    
class T2DSimGymnasiumEnv(Env):
    metadata = {"render_modes": ["human"]}
    MAX_BG = 1000
    SENSOR_HARDWARE = "Dexcom"
    INSULIN_PUMP_HARDWARE = "Insulet"

    def __init__(self, patient_name=None, custom_scenario=None, reward_fun=None, seed=None, render_mode=None):
        super().__init__()
        self.render_mode = render_mode
        self.reward_fun = reward_fun
        self.np_random, _ = gymnasium_utils.np_random(seed=seed)
        self.patient_name = patient_name if patient_name is not None else ["adolescent#001"]
        self.custom_scenario = custom_scenario
        self.env, _, _, _ = self._create_env()
        self.observation_space = spaces.Box(low=0, high=self.MAX_BG, shape=(1,), dtype=np.float32)
        self.action_space = spaces.Box(low=0, high=self.env.pump._params["max_basal"], shape=(1,), dtype=np.float32)

    def step(self, action):
        act = Action(basal=action, bolus=0)
        obs, reward, done, info = self.env.step(act, reward_fun=self.reward_fun)
        truncated = False  # Controlled by TimeLimit wrapper when registering the env
        return np.array([obs.CGM], dtype=np.float32), reward, done, truncated, info

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.env, _, _, _ = self._create_env()
        obs, _, _, _ = self.env.reset()
        return np.array([obs.CGM], dtype=np.float32)

    def render(self):
        if self.render_mode == "human":
            self.env.render()

    def close(self):
        self.env._close_viewer()

    def _create_env(self):
        # Derive a random seed. This gets passed as a uint, but gets
        # checked as an int elsewhere, so we need to keep it below
        # 2**31.
        seed2 = seeding.hash_seed(self.np_random.randint(0, 1000)) % 2**31
        seed3 = seeding.hash_seed(seed2 + 1) % 2**31
        seed4 = seeding.hash_seed(seed3 + 1) % 2**31

        hour = self.np_random.randint(low=0.0, high=24.0)
        start_time = datetime(2018, 1, 1, hour, 0, 0)

        if isinstance(self.patient_name, list):
            patient_name = self.np_random.choice(self.patient_name)
            patient = T2DPatient.withName(patient_name, random_init_bg=True, seed=seed4)
        else:
            patient = T2DPatient.withName(
                self.patient_name, random_init_bg=True, seed=seed4
            )

        if isinstance(self.custom_scenario, list):
            scenario = self.np_random.choice(self.custom_scenario)
        else:
            scenario = (
                RandomScenario(start_time=start_time, seed=seed3)
                if self.custom_scenario is None
                else self.custom_scenario
            )

        sensor = CGMSensor.withName(self.SENSOR_HARDWARE, seed=seed2)
        pump = InsulinPump.withName(self.INSULIN_PUMP_HARDWARE)
        env = _T2DSimEnv(patient, sensor, pump, scenario)
        return env, seed2, seed3, seed4