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

    ## MARD parameters
    glucoseParams.pancreasModel.ml0 = glucoseParams.pancreasModel.ml0 * 2
    glucoseParams.pancreasModel.Ks = glucoseParams.pancreasModel.Ks - glucoseParams.pancreasModel.Ks/4
    glucoseParams.glucoseMetabolicRates.c1 = glucoseParams.glucoseMetabolicRates.c1 + 10*glucoseParams.glucoseMetabolicRates.c1
    glucoseParams.glucoseMetabolicRates.c2 = glucoseParams.glucoseMetabolicRates.c2 + 20*glucoseParams.glucoseMetabolicRates.c2
    glucoseParams.glucoseMetabolicRates.c4 = glucoseParams.glucoseMetabolicRates.c4 + 20*glucoseParams.glucoseMetabolicRates.c2

    # glucoseParams.InsulinSubmodel.QIB = glucoseParams.InsulinSubmodel.QIB  * (1 - 40 / 100)
    # glucoseParams.InsulinSubmodel.QIL = glucoseParams.InsulinSubmodel.QIL  * (1 - 40 / 100)
    # glucoseParams.InsulinSubmodel.QIK = glucoseParams.InsulinSubmodel.QIK  * (1 - 40 / 100)
    # glucoseParams.InsulinSubmodel.QIP = glucoseParams.InsulinSubmodel.QIP  * (1 - 40 / 100)
    # glucoseParams.InsulinSubmodel.QIH = glucoseParams.InsulinSubmodel.QIH  * (1 - 40 / 100)
    # #glucoseParams.InsulinSubmodel.mpan0 = glucoseParams.InsulinSubmodel.mpan0 - 80*glucoseParams.InsulinSubmodel.mpan0
    # glucoseParams.pancreasModel.ml0 -= 80*glucoseParams.pancreasModel.ml0
    # glucoseParams.pancreasModel.Ks = glucoseParams.pancreasModel.Ks / 10
    #glucoseParams.metforminSubmodel.vGWmax = glucoseParams.metforminSubmodel.vGWmax  / 4
    #glucoseParams.metforminSubmodel.vPmax = glucoseParams.metforminSubmodel.vPmax / 4
    #glucoseParams.metforminSubmodel.vLmax  = glucoseParams.metforminSubmodel.vLmax  / 4
    #glucoseParams.InsulinSubmodel.mpan0 += 50 * glucoseParams.InsulinSubmodel.mpan0
    patient = T2DPatient({},glucose_params=glucoseParams, name="MARD")
    sensor = CGMSensor.withName('Dexcom', seed=1)
    pump = InsulinPump.withName('Insulet')
    # custom scenario is a list of tuples (time, meal_size)
    scen = []
    for i in range(1):
        scen.extend([(7 + (i * 24), 30, "meal"), (12 + (i * 24), 50, "meal"),(14 + (i * 24),500,"metformin") ,(18 + (i * 24), 120, "meal")])
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

def modify_glucose_parameters(glucose_params):
    # Insulin Submodel Parameters Reduction
    insulin_reduction_percentage = 10
    for param in ['c1', 'c2', 'QIK', 'QIP', 'QIH']:
        current_value = getattr(glucose_params.InsulinSubmodel, param)
        setattr(glucose_params.InsulinSubmodel, param, current_value * (1 - insulin_reduction_percentage / 100))

    # Glucose Submodel Basal Rates Reduction
    glucose_basal_reduction_percentage = 20
    for param in ['QGB', 'QGH', 'QGA', 'QGL', 'QGG', 'QGK', 'QGP']:
        current_value = getattr(glucose_params.glucoseSubmodel, param)
        setattr(glucose_params.glucoseSubmodel, param, current_value * (1 - glucose_basal_reduction_percentage / 100))

    # Pancreas Submodel Parameters Reduction
    pancreas_reduction_percentage = 30
    for param in ['N1', 'N2']:
        current_value = getattr(glucose_params.pancreasModel, param)
        setattr(glucose_params.pancreasModel, param, current_value * (1 - pancreas_reduction_percentage / 100))

    # Metformin and Physical Activity Parameters Reduction
    metformin_physical_reduction_percentage = 30
    for param in ['vGWmax', 'vLmax', 'vPmax']:
        current_value = getattr(glucose_params.metforminSubmodel, param)
        setattr(glucose_params.metforminSubmodel, param, current_value * (1 - metformin_physical_reduction_percentage / 100))

    physical_activity_increase_percentage = 15
    for param in ['alphae', 'betae']:
        current_value = getattr(glucose_params.physicalActivityParameters, param)
        setattr(glucose_params.physicalActivityParameters, param, current_value * (1 + physical_activity_increase_percentage / 100))


if __name__ == '__main__':
    main()