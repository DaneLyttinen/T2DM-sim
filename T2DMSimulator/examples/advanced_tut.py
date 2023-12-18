import sys

# Assuming your script is in the 'examples' directory
sys.path.append('C:\\Users\\Dane\\Desktop\\Masters\\T2DM-sim\\T2DMSimulator')


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
    s1 = SimObj(env, controller, timedelta(days=1), animate=True, path=path)
    #results1 = sim(s1)
    #print(results1)

    # --------- Create Custom Scenario --------------
    # Create a simulation environment
    patient = T2DPatient.withName('adolescent#001')
    sensor = CGMSensor.withName('Dexcom', seed=1)
    pump = InsulinPump.withName('Insulet')
    # custom scenario is a list of tuples (time, meal_size)
    scen = [(7, 45), (12, 70), (16, 15), (18, 80), (23, 10)]
    scenario = CustomScenario(start_time=start_time, scenario=scen)
    env = T2DSimEnv(patient, sensor, pump, scenario)

    # Create a controller
    controller = BBController()

    # Put them together to create a simulation object
    s2 = SimObj(env, controller, timedelta(days=1), animate=True, path=path)
    #results2 = sim(s2)
    #print(results2)


    # --------- batch simulation --------------
    # Re-initialize simulation objects
    s1.reset()
    s2.reset()

    # create a list of SimObj, and call batch_sim
    s = [s1, s2]
    results = batch_sim(s, parallel=True)
    print(results)

if __name__ == '__main__':
    main()