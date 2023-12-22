from T2DMSimulator.glucose.GlucoseParameters import GlucoseParameters
# from T2DMSimulator.patient.t2dpatient import T2DPatient
import numpy as np
    # Glucose Dynamics Parameters:
    # | Parameter            | Index Range |
    # |----------------------|-------------|
    # | Glucose absorption   | 0 - 4       |
    # | Metformin            | 5 - 10      |
    # | Vildagliptin         | 11 - 16     |
    # | Physical activity    | 17 - 18     |
    # | Fast acting insulin  | 19 - 20     |
    # | Long acting insulin  | 21 - 23     |

class GlucoseInitializer():
    def __init__(self, glucose_parameters: GlucoseParameters, patient):
        self.glucose_parameters = glucose_parameters
        self.brates = patient.brates
        self.patient = patient
        self.x = np.zeros(57)

    def calculate_values(self):
        rHGP = self.__calculate_basal_values()
        rPIR = self.__calculate_insulin_values()
        S = self.__calculate_pancreas_values()
        self.__set_basal_rates()
        rates = [rPIR, self.brates['rBGU'], self.brates['rRBCU'], self.brates['rGGU'], self.brates['rPGU'], rHGP, self.brates['rHGU']]
        return self.x, rates, S
    
    def __calculate_basal_values(self):
        GPC = self.patient.GBPC0
        glucose = self.glucose_parameters.glucoseSubmodel
        GPF = GPC - glucose.TGP * self.brates['rPGU'] / glucose.VGPF
        GH = GPC + (glucose.VGPF / (glucose.QGP * glucose.TGP)) * (GPC - GPF)
        GK = GH
        GG = GH - self.brates['rGGU'] / glucose.QGG
        GBC = GH - (1 / glucose.QGB) * self.brates['rBGU']
        GBF = GBC - (glucose.TGB / glucose.VGBF) *self.brates['rBGU'] 
        GL = (1 / glucose.QGL) * (glucose.QGH * GH + self.brates['rRBCU'] - glucose.QGB * GBC - glucose.QGK * GK - glucose.QGP * GPC)
        rHGP = glucose.QGL * GL - glucose.QGA * GH - glucose.QGG * GG + self.brates['rHGU']
        self.x[32] = GBC
        self.x[33] = GBF
        self.x[34] = GH
        self.x[35] = GG
        self.x[36] = GL
        self.x[37] = GK
        self.x[38] = GPC
        self.x[39] = GPF
        return rHGP
    
    def __extract_insulin_submodel_params(self):
        insulin = self.glucose_parameters.InsulinSubmodel
        return insulin.QIB, insulin.QIL, insulin.QIK, insulin.QIP, insulin.QIH, \
               insulin.QIG, insulin.QIA, insulin.VIPF, insulin.TIP
    
    def __calculate_insulin_values(self):
        QIB, QIL, QIK, QIP, QIH, QIG, QIA, VIPF, TIP = self.__extract_insulin_submodel_params()
        IPF = self.patient.IBPF0
        t2 = QIP ** 2
        t3 = QIP * 6.0e+1
        t4 = VIPF * 1.7e+1
        t5 = IPF * QIP * TIP * 3.0
        t8 = IPF * VIPF * 2.0e+1
        t9 = IPF * QIP * -6.0e+1
        t6 = -t4
        t7 = IPF * t3
        t12 = t5 + t8 + t9
        t10 = t3 + t6
        t11 = 1.0 / t10
        t13 = t11 * t12
        t14 = -t13
        outI = [t14, t14, t14, (t11 * (IPF * t2 * -7.8e+2 - IPF * QIB * QIP * 7.8e+2 + IPF * QIH * QIP * 7.8e+2 - IPF * QIK * QIP * 6.0e+2 + IPF * QIB * VIPF * 2.6e+2 - IPF * QIH * VIPF * 2.6e+2 + IPF * QIK * VIPF * 2.0e+2 + IPF * QIP * VIPF * 2.21e+2 + IPF * QIB * QIP * TIP * 3.9e+1 - IPF * QIH * QIP * TIP * 3.9e+1 + IPF * QIK * QIP * TIP * 3.0e+1)) / (QIL * 1.3e+1), t13 * (-1.0e+1 / 1.3e+1), -t11 * (t5 + t9 + IPF * t4), (t11 * (IPF * t2 * -3.9e+3 - IPF * QIA * QIP * 2.34e+3 - IPF * QIB * QIP * 3.9e+3 - IPF * QIG * QIP * 2.34e+3 + IPF * QIH * QIP * 3.9e+3 - IPF * QIK * QIP * 3.0e+3 + IPF * QIA * VIPF * 7.8e+2 + IPF * QIB * VIPF * 1.3e+3 + IPF * QIG * VIPF * 7.8e+2 - IPF * QIH * VIPF * 1.3e+3 + IPF * QIK * VIPF * 1.0e+3 + IPF * QIP * VIPF * 1.105e+3 + IPF * QIA * QIP * TIP * 1.17e+2 + IPF * QIB * QIP * TIP * 1.95e+2 + IPF * QIG * QIP * TIP * 1.17e+2 - IPF * QIH * QIP * TIP * 1.95e+2 + IPF * QIK * QIP * TIP * 1.5e+2)) / 3.9e+1]
        self.x[25] = outI[0]
        self.x[26] = outI[1]
        self.x[27] = outI[2]
        self.x[28] = outI[3]
        self.x[29] = outI[4]
        self.x[30] = outI[5]
        self.x[31] = IPF
        rPIR = outI[6]
        return rPIR
    
    def __set_basal_rates(self):
        self.x[43] = 1
        self.x[44] = 0.0027
        self.x[45] = 1
        
    def __calculate_pancreas_values(self):
        pancreas = self.glucose_parameters.pancreasModel
        XG = self.x[34] ** 3.27 / (1.32 ** 3.27 + 5.93 * self.x[34] ** 3.02)
        Pinft = XG ** 1.11
        Y = Pinft
        kdmdpan = pancreas.ml0 * pancreas.Kl
        mpan = (kdmdpan + pancreas.gammapan * Pinft) / (pancreas.Ks + pancreas.N1 * Y)
        S = pancreas.N1 * Y * mpan
        self.x[22] = mpan
        self.x[23] = Pinft
        self.x[24] = XG
        # Glucagon:
        self.x[40] = 1
        return S