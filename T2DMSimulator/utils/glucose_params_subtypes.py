from T2DMSimulator.glucose.GlucoseParameters import GlucoseParameters


def get_mard_params():
        ## MARD parameters
    glucoseParams = GlucoseParameters()
    glucoseParams.pancreasModel.ml0 = glucoseParams.pancreasModel.ml0 * 2
    glucoseParams.pancreasModel.Ks = glucoseParams.pancreasModel.Ks - glucoseParams.pancreasModel.Ks/4
    glucoseParams.glucoseMetabolicRates.c1 = glucoseParams.glucoseMetabolicRates.c1 + 10*glucoseParams.glucoseMetabolicRates.c1
    glucoseParams.glucoseMetabolicRates.c2 = glucoseParams.glucoseMetabolicRates.c2 + 20*glucoseParams.glucoseMetabolicRates.c2
    glucoseParams.glucoseMetabolicRates.c4 = glucoseParams.glucoseMetabolicRates.c4 + 20*glucoseParams.glucoseMetabolicRates.c2
    return glucoseParams