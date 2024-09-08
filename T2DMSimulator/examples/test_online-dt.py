import sys
from T2DMSimulator.glucose.GlucoseParameters import GlucoseParameters
from T2DMSimulator.simulation.env import T2DSimEnv
from T2DMSimulator.controller.online_dt_controller import OnlineDTController
from T2DMSimulator.sensor.cgm import CGMSensor
from T2DMSimulator.actuator.pump import InsulinPump
from T2DMSimulator.patient.t2dpatient import T2DPatient
from T2DMSimulator.simulation.scenario_gen import RandomScenario
from T2DMSimulator.simulation.scenario import CustomScenario
from T2DMSimulator.simulation.sim_engine import SimObj, sim, batch_sim
from datetime import timedelta
from datetime import datetime

# specify start_time as the beginning of today
def main():
    now = datetime.now()
    start_time = datetime.combine(now.date(), datetime.min.time())

    # --------- Create Random Scenario --------------
    # Specify results saving path
    path = './results'
    
    glucoseParams = GlucoseParameters()
    
    patient = T2DPatient({},glucose_params=glucoseParams, name="MARD_baseline")
    sensor = CGMSensor.withName('Dexcom', seed=1)
    pump = InsulinPump.withName('Insulet')
    scen = []
    for i in range(1):
        scen.extend([(7 + (i * 24), 30, "meal"), (12 + (i * 24), 50, "meal"),(14 + (i * 24),500,"metformin") ,(18 + (i * 24), 120, "meal")])
    scenario = CustomScenario(start_time=start_time, scenario=scen)
    env = T2DSimEnv(patient, sensor, pump, scenario)
        # Create a controller
    controller = OnlineDTController()

    # Put them together to create a simulation object
    s2 = SimObj(env, controller, timedelta(days=1), animate=False, path=path)
    results2 = sim(s2)
    s2.save_results()
    print(results2)