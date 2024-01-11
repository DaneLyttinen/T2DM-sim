import sys

# Assuming your script is in the 'examples' directory
sys.path.append('C:\\Users\\Dane\\Desktop\\Masters\\T2DM-sim\\T2DMSimulator')

from T2DMSimulator.glucose.GlucoseParameters import GlucoseParameters
from T2DMSimulator.simulation.env import T2DSimEnv
from T2DMSimulator.controller.basal_bolus_ctrller import BBController
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

    # Create a simulation environment
    patient = T2DPatient.withName('adolescent#001')
    sensor = CGMSensor.withName('Dexcom', seed=1)
    pump = InsulinPump.withName('Insulet')
    scenario = RandomScenario(start_time=start_time, seed=1)
    env = T2DSimEnv(patient, sensor, pump, scenario)

    # Create a controller
    controller = BBController()

    # Put them together to create a simulation object
    # s1 = SimObj(env, controller, timedelta(days=1), animate=True, path=path)
    # results1 = sim(s1)
    # print(results1)

    # --------- Create Custom Scenario --------------
    # Create a simulation environment
    
    
    #Lower the parameters for the effect of insulin on the hepatic glucose
    #uptake and production rates (See paper): 
    glucoseParams = GlucoseParameters()
    glucoseParams.glucoseMetabolicRates.c4 = glucoseParams.glucoseMetabolicRates.c4 - 50*glucoseParams.glucoseMetabolicRates.c4
    glucoseParams.glucoseMetabolicRates.c2 = glucoseParams.glucoseMetabolicRates.c2 - 20*glucoseParams.glucoseMetabolicRates.c2
    #The same for the peripheral uptake rate:
    glucoseParams.glucoseMetabolicRates.c1 = glucoseParams.glucoseMetabolicRates.c1 - 50*glucoseParams.glucoseMetabolicRates.c1
    #glucoseParams.InsulinSubmodel.mpan0 += 50 * glucoseParams.InsulinSubmodel.mpan0
    patient = T2DPatient({},glucose_params=glucoseParams)
    sensor = CGMSensor.withName('Dexcom', seed=1)
    pump = InsulinPump.withName('Insulet')
    # custom scenario is a list of tuples (time, meal_size)
    scen = [(7, 45, "meal"), (12, 70, "meal"), (16, 15, "meal"),(17,500,"insulin_long") ,(18, 80, "meal"), (21,15,"meal")]
    scenario = CustomScenario(start_time=start_time, scenario=scen)
    env = T2DSimEnv(patient, sensor, pump, scenario)

    # Create a controller
    controller = BBController()

    # Put them together to create a simulation object
    s2 = SimObj(env, controller, timedelta(days=1), animate=False, path=path)
    results2 = sim(s2)
    s2.save_results()
    print(results2)


    # --------- batch simulation --------------
    # Re-initialize simulation objects
   # s1.reset()
    s2.reset()

    # create a list of SimObj, and call batch_sim
    # s = [s1, s2]
    # results = batch_sim(s, parallel=True)
    # print(results)

if __name__ == '__main__':
    main()