import sys

# Assuming your script is in the 'examples' directory
sys.path.append('C:\\Users\\Dane\\Desktop\\Masters\\T2DM-sim\\T2DMSimulator')

from T2DMSimulator.glucose.GlucoseParameters import GlucoseParameters
from T2DMSimulator.simulation.env import T2DSimEnv
from T2DMSimulator.controller.baseline_controller import BaselineController
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
   # modify_glucose_parameters(glucoseParams)
    
    ## SIDD PARAMETERS
    #Lower the parameters for the effect of insulin on the hepatic glucose
    #uptake and production rates (See paper): 
    #glucoseParams.glucoseMetabolicRates.c4 = glucoseParams.glucoseMetabolicRates.c4 - 120*glucoseParams.glucoseMetabolicRates.c4
    # #The same for the peripheral uptake rate:
    #glucoseParams.glucoseMetabolicRates.c1 = glucoseParams.glucoseMetabolicRates.c1 - 120*glucoseParams.glucoseMetabolicRates.c1
    # increas franction of glucose absorped (fg)
    #glucoseParams.glucoseAbsorptionSubmodel.fg = glucoseParams.glucoseAbsorptionSubmodel.fg * 2
    # decrease Insulin Secretion rate
    #glucoseParams.pancreasModel.Ks  = glucoseParams.pancreasModel.Ks/2
    ## END OF SIDD PARAMETERS

    ## SIRD parameters
    #glucoseParams.InsulinSubmodel.QIH = glucoseParams.InsulinSubmodel.QIH  - glucoseParams.InsulinSubmodel.QIH/ 5
    #glucoseParams.InsulinSubmodel.QIP = glucoseParams.InsulinSubmodel.QIP / 2
    #brates = {'rBGU': 70, 'rRBCU': 10, 'rGGU': 20, 'rPGU': 17.5, 'rHGU': 10}
    ## END SIRD parameters

    ## MOD parameters
    #glucoseParams.glucoseMetabolicRates.c5 = glucoseParams.glucoseMetabolicRates.c5 * 2
    #glucoseParams.glucoseMetabolicRates.c2 = glucoseParams.glucoseMetabolicRates.c2 * 2
    #glucoseParams.physicalActivityParameters.ae = glucoseParams.physicalActivityParameters.ae / 20
    #glucoseParams.physicalActivityParameters.tHR = glucoseParams.physicalActivityParameters.tHR / 20

    patient = T2DPatient({},glucose_params=glucoseParams, name="MARD_baseline")
    sensor = CGMSensor.withName('Dexcom', seed=1)
    pump = InsulinPump.withName('Insulet')
    # custom scenario is a list of tuples (time, meal_size)
    scen = []
    #for i in range(1):
    #    scen.extend([(7 + (i * 24), 30, "meal"), (12 + (i * 24), 50, "meal"),(14 + (i * 24),500,"metformin") ,(18 + (i * 24), 120, "meal")])
    scenario = CustomScenario(start_time=start_time, scenario=scen)
    env = T2DSimEnv(patient, sensor, pump, scenario)

    # Create a controller
    controller = BaselineController()

    # Put them together to create a simulation object
    s2 = SimObj(env, controller, timedelta(days=2), animate=True, path=path)
    results2 = sim(s2)
    s2.save_results()
    print(results2)

if __name__ == '__main__':
    main()