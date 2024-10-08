from T2DMSimulator.actuator.pump import InsulinPump
from T2DMSimulator.sensor.cgm import CGMSensor
from T2DMSimulator.simulation.scenario import CustomScenario
from T2DMSimulator.utils.glucose_params_subtypes import get_mard_params
from ..patient.t2dpatient import Action, T2DPatient
from ..analysis.risk import risk_index
import pandas as pd
from datetime import timedelta
import logging
from collections import namedtuple
from ..simulation.rendering import Viewer
import numpy as np

try:
    from rllab.envs.base import Step
except ImportError:
    _Step = namedtuple("Step", ["observation", "reward", "done", "info"])

    def Step(observation, reward, done, **kwargs):
        """
        Convenience method creating a namedtuple with the results of the
        environment.step method.
        Put extra diagnostic info in the kwargs
        """
        return _Step(observation, reward, done, kwargs)


Observation = namedtuple("Observation", ["CGM"])
logger = logging.getLogger(__name__)

def add_tuples(t1, t2):
    return Action(*((a + b)  for a, b in zip(t1, t2)))

def divide_tuple(t, divisor):
    # Validate divisor to avoid division by zero
    if divisor == 0:
        raise ValueError("Divisor cannot be zero.")
    return Action(*(value / divisor for value in t))

def risk_diff(BG_last_hour):
    if len(BG_last_hour) < 2:
        return 0
    else:
        _, _, risk_current = risk_index([BG_last_hour[-1]], 1)
        _, _, risk_prev = risk_index([BG_last_hour[-2]], 1)
        return risk_prev - risk_current


def create_month_scenario():
    from datetime import timedelta
    from datetime import datetime
    now = datetime.now()
    start_time = datetime.combine(now.date(), datetime.min.time())
    scen = []
    for i in range(30):
        scen.extend([(7 + (i * 24), 30, "meal"), (12 + (i * 24), 50, "meal"),(14 + (i * 24),500,"metformin") ,(18 + (i * 24), 120, "meal")])
    scenario = CustomScenario(start_time=start_time, scenario=scen)
    return scenario

class T2DSimEnv(object):
    def __init__(self, patient=T2DPatient({},glucose_params=get_mard_params(), name="MARD"), sensor=CGMSensor.withName('Dexcom', seed=1), pump=InsulinPump.withName('Insulet'), scenario=create_month_scenario()):
        self.patient = patient
        self.sensor = sensor
        self.pump = pump
        self.scenario = scenario
        self._reset()

    @property
    def time(self):
        return self.scenario.start_time + timedelta(minutes=self.patient.t)

    def mini_step(self, action):
        # current action
        patient_action = self.scenario.get_action(self.time)
        basal = self.pump.basal(action.basal)
        bolus = self.pump.bolus(action.bolus)
        insulin = basal + bolus
        CHO = patient_action.meal
        metformin = patient_action.metformin
        insulin_fast = patient_action.insulin_fast
        patient_mdl_act = Action(insulin_fast=insulin_fast, CHO=CHO, insulin_long=patient_action.insulin_long, metformin=metformin, vildagliptin=0,physical=80., stress=patient_action.stress)
        # State update
        taken_action, heart_beat_observation = self.patient.step(patient_mdl_act, action)

        # next observation
        BG = self.patient.observation.Gsub
        CGM = self.sensor.measure(self.patient)

        return CHO, insulin, BG, CGM, taken_action, heart_beat_observation

    def step(self, action, reward_fun=risk_diff):
        """
        action is a namedtuple with keys: basal, bolus
        """
        CHO = 0.0
        insulin = 0.0
        BG = 0.0
        CGM = 0.0
        heart_beat = 0.0
        merged_taken_action = Action(CHO=0, insulin_fast=0, insulin_long=0, metformin=0, vildagliptin=0, stress=0, physical=0)
        for _ in range(int(self.sample_time)):
            # Compute moving average as the sample measurements
            tmp_CHO, tmp_insulin, tmp_BG, tmp_CGM, taken_action, heart_beat_observation = self.mini_step(action)
            
            merged_taken_action = add_tuples(merged_taken_action, taken_action)
            CHO += tmp_CHO / self.sample_time
            insulin += tmp_insulin / self.sample_time
            BG += tmp_BG / self.sample_time
            CGM += tmp_CGM / self.sample_time
            heart_beat += heart_beat_observation / self.sample_time
        #merged_taken_action = divide_tuple(merged_taken_action, self.sample_time)
        # Compute risk index
        horizon = 1
        LBGI, HBGI, risk = risk_index([BG], horizon)

        # Record current action
        self.CHO_hist.append(CHO)
        self.insulin_hist.append(insulin)

        # Record next observation
        self.time_hist.append(self.time)
        self.BG_hist.append(BG)
        self.CGM_hist.append(CGM)
        self.risk_hist.append(risk)
        self.LBGI_hist.append(LBGI)
        self.HBGI_hist.append(HBGI)
        self.BPM_hist.append(heart_beat)
        self.action_hist.append(np.array([merged_taken_action.CHO, merged_taken_action.insulin_fast, merged_taken_action.insulin_long, merged_taken_action.metformin, merged_taken_action.physical, merged_taken_action.stress, merged_taken_action.vildagliptin], dtype=np.float32))

        # Compute reward, and decide whether game is over
        window_size = int(60 / self.sample_time)
        BG_last_hour = self.CGM_hist[-window_size:]
        reward = reward_fun(BG_last_hour)
        done = BG < 10 or BG > 600
        obs = Observation(CGM=CGM)

        return Step(
            observation=obs,
            reward=reward,
            done=done,
            sample_time=self.sample_time,
            patient_name=self.patient.name,
            meal=CHO,
            patient_state=self.patient.state,
            time=self.time,
            bg=BG,
            lbgi=LBGI,
            hbgi=HBGI,
            risk=risk,
        )

    def _reset(self):
        self.sample_time = self.sensor.sample_time
        self.viewer = None

        BG = self.patient.observation.Gsub
        horizon = 1
        LBGI, HBGI, risk = risk_index([BG], horizon)
        CGM = self.sensor.measure(self.patient)
        self.time_hist = [self.scenario.start_time]
        self.BG_hist = [BG]
        self.CGM_hist = [CGM]
        self.risk_hist = [risk]
        self.LBGI_hist = [LBGI]
        self.HBGI_hist = [HBGI]
        self.BPM_hist = []
        self.CHO_hist = []
        self.insulin_hist = []
        self.action_hist = []

    def reset(self):
        self.patient.reset()
        self.sensor.reset()
        self.pump.reset()
        self.scenario.reset()
        self._reset()
        CGM = self.sensor.measure(self.patient)
        obs = Observation(CGM=CGM)
        return Step(
            observation=obs,
            reward=0,
            done=False,
            sample_time=self.sample_time,
            patient_name=self.patient.name,
            meal=0,
            patient_state=self.patient.state,
            time=self.time,
            bg=self.BG_hist[0],
            lbgi=self.LBGI_hist[0],
            hbgi=self.HBGI_hist[0],
            risk=self.risk_hist[0],
        )

    def render(self, close=False):
        if close:
            self._close_viewer()
            return

        if self.viewer is None:
            self.viewer = Viewer(self.scenario.start_time, self.patient.name)

        self.viewer.render(self.show_history())

    def _close_viewer(self):
        if self.viewer is not None:
            self.viewer.close()
            self.viewer = None

    def show_history(self):
        df = pd.DataFrame()
        df["Time"] = pd.Series(self.time_hist)
        df["BG"] = pd.Series(self.BG_hist)
        df["CGM"] = pd.Series(self.CGM_hist)
        df["CHO"] = pd.Series(self.CHO_hist)
        df["insulin"] = pd.Series(self.insulin_hist)
        df["LBGI"] = pd.Series(self.LBGI_hist)
        df["HBGI"] = pd.Series(self.HBGI_hist)
        df["BPM"] = pd.Series(self.BPM_hist)
        df["Risk"] = pd.Series(self.risk_hist)
        df["actions"] = pd.Series(self.action_hist)
        df = df.set_index("Time")
        return df