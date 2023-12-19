import numpy as np
from T2DMSimulator.glucose.GlucoseParameters import GlucoseParameters

class FodeSimulator:
    def __init__(self, t, x, Dg, stressv, HRv, T, glucoseParameters: GlucoseParameters, basal):
        self.t = t
        self.x = x
        self.Dg = Dg
        self.stressv = stressv
        self.HRv = HRv
        self.T = T
        self.stress = np.interp(self.t, self.T, self.stressv)
        self.glucoseParameters = glucoseParameters
        self.basal = basal
        self.dx = np.zeros_like(x)

    def compute(self):
        Ra, kempt = self.glucose_absorption_submodel()
        EGW,EL,EP = self.metformin_submodel()
        self.vildagliptin_submodel()
        self.physical_activity_submodel()
        rKGE, MIHGPinft, MIHGUinft, rHGU,rHGP, rPGU = self.glucose_submodel_rates(EGW, EL, EP)
        self.rates_dynamic_model(MIHGPinft, MIHGUinft)
        self.glucose_submodel(Ra, rKGE, rHGU,rHGP, rPGU)
        self.glucagon_submodel()
        self.glp1_submodel(kempt)
        S = self.pancreas_submodel()
        # insulin
        rPIR, rLIC, rKIC, rPIC = self.insulin_submodel_rates(S)
        self.long_acting_insulin_equations()
        self.fast_acting_insulin_equations()
        self.insulin_submodel(rPIR, rLIC, rKIC, rPIC)
        return self.dx
    
    def insulin_submodel(self, rPIR, rLIC, rKIC, rPIC):
        insulin = self.glucoseParameters.InsulinSubmodel
        fast_insulin = self.glucoseParameters.fastActingInsulinSubmodel
        long_insulin = self.glucoseParameters.longActingInsulinSubmodel
        VIB, VIH, QIB, QIL, QIK, QIP, QIH, QIG, VIG, VIL, QIA, VIK, VIPC, VIPF, TIP = insulin.VIB, insulin.VIH, insulin.QIB, insulin.QIL, insulin.QIK, insulin.QIP, insulin.QIH, insulin.QIG, insulin.VIG, insulin.VIL, insulin.QIA, insulin.VIK, insulin.VIPC, insulin.VIPF, insulin.TIP
        IB, IH, IG, IL, IK, IPC, IPF = self.x[25], self.x[26], self.x[27], self.x[28], self.x[29], self.x[30], self.x[31]
        dIB = (QIB / VIB) * (IH - IB)
        dIH = (1 / VIH) * (QIB * IB + QIL * IL + QIK * IK + QIP * IPF - QIH * IH)
        dIG = (QIG / VIG) * (IH - IG)
        dIL = (1 / VIL) * (QIA * IH + QIG * IG - QIL * IL + (1 - self.stress) * rPIR - rLIC)
        dIK = (1 / VIK) * (QIK * (IH - IK) - rKIC)
        dIPC = (1 / VIPC) * (QIP * (IH - IPC) - (VIPF / TIP) * (IPC - IPF)) + 10 * self.x[55] + 10 * self.x[54]
        dIPF = (1 / VIPF) * ((VIPF / TIP) * (IPC - IPF) - rPIC)
        self.dx[25] = dIB
        self.dx[26] = dIH
        self.dx[27] = dIG
        self.dx[28] = dIL
        self.dx[29] = dIK
        self.dx[30] = dIPC
        self.dx[31] = dIPF
        dXIC = rLIC + rKIC + rPIC
        dXIS = (1 - self.stress) * rPIR
        dXIinj = VIPF * long_insulin.rla * long_insulin.bla * self.x[54] / (1 + IPF) + VIPF * fast_insulin.rfa * fast_insulin.bfa * self.x[55] / (1 + IPF)
        self.dx[51] = dXIC
        self.dx[52] = dXIS
        self.dx[53] = dXIinj
    
    def fast_acting_insulin_equations(self):
        insulin = self.glucoseParameters.fastActingInsulinSubmodel
        Hfa, Dfa, Ifa = self.x[17], self.x[18], self.x[55]
        dHfa = -insulin.pfa * (Hfa - insulin.qfa * Dfa ** 3)
        dDfa = insulin.pfa * (Hfa - insulin.qfa * Dfa ** 3) - insulin.bfa * Dfa / (1 + Ifa)
        dIfa = insulin.rfa * insulin.bfa * Dfa / (1 + (Ifa)) - insulin.kclf * (Ifa)
        self.dx[17] = dHfa
        self.dx[18] = dDfa
        self.dx[55] = dIfa
    
    def long_acting_insulin_equations(self):
        insulin = self.glucoseParameters.longActingInsulinSubmodel
        Bla, Hla, Dla, Ila = self.x[19], self.x[20], self.x[21], self.x[54]
        dBla = -insulin.kla * Bla * (insulin.Cmax / (1 + Hla))
        dHla = -insulin.pla * (Hla - insulin.qla * Dla ** 3) + insulin.kla * Bla * (insulin.Cmax / (1 + Hla))
        dDla = insulin.pla * (Hla - insulin.qla * Dla ** 3) - insulin.bla * Dla / (1 + Ila)
        dIla = insulin.rla * insulin.bla * Dla / (1 + (Ila)) - insulin.kcll * (Ila)
        self.dx[19] = dBla
        self.dx[20] = dHla
        self.dx[21] = dDla
        self.dx[54] = dIla

    def insulin_submodel_rates(self, S):
        insulin = self.glucoseParameters.InsulinSubmodel
        rPIR = (S / self.basal['SB']) * self.basal['rPIR']
        rLIC = 0.4 * (insulin.QIA * self.x[26] + insulin.QIG * self.x[27] + rPIR)
        rKIC = 0.3 * insulin.QIK * self.x[29]
        rPIC = self.x[31] / ((0.85) / (0.15 * insulin.QIP) - 20 / insulin.VIPF)
        return rPIR, rLIC, rKIC, rPIC

    def pancreas_submodel(self):
        pancreas = self.glucoseParameters.pancreasModel
        PHI, mpan, P, R = self.x[42], self.x[22],self.x[23], self.x[24]
        XG = self.x[34] ** (3.27) / (1.32 ** 3.27 + 5.93 * self.x[34] ** 3.02)
        Pinft = XG ** (1.11) + pancreas.zeta1 * PHI
        Y = Pinft
        if XG > R:
            S = pancreas.Sfactor * mpan * (pancreas.N1 * Y + pancreas.N2 * (XG - R) + pancreas.zeta2 * PHI)
        else:
            S = pancreas.Sfactor * mpan * (pancreas.N1 * Y + pancreas.zeta2 * PHI)
        dmpan = (pancreas.ml0 * pancreas.Kl) - pancreas.Ks * mpan + pancreas.gammapan * P - S
        dP = pancreas.alphapan * (Pinft - P)
        dR = pancreas.betapan * (XG - R)
        self.dx[22] = dmpan
        self.dx[23] = dP
        self.dx[24] = dR
        return S
    
    def glp1_submodel(self, kempt):
        glp1 = self.glucoseParameters.gLP1Submodel
        vildagliptin = self.glucoseParameters.vildagliptinSubmodel
        dphi = glp1.zeta * kempt * self.x[1] - self.x[41] / glp1.tphi
        dPHI = (1 / glp1.VPHI) * (self.x[41] / glp1.tphi - (glp1.Kout + (vildagliptin.RmaxC - self.x[13]) * glp1.CF2) * self.x[42])
        self.dx[41] = dphi
        self.dx[42] = dPHI
    
    def glucagon_submodel(self):
        glucagon = self.glucoseParameters.glucagonSubmodel
        
        rBPGammaR = 9.1
        MGPGammaR = 1.31 - 0.61 * np.tanh(1.06 * ((self.x[34] / self.basal['GH']) - 0.47))
        MIPGammaR = 2.93 - 2.09 * np.tanh(4.18 * ((self.x[26] / self.basal['IH']) - 0.62))
        rPGammaR = MGPGammaR * MIPGammaR * rBPGammaR
        dGamma = (1 / glucagon.VGamma) * ((1 + self.stress) * rPGammaR - 9.1 * self.x[40])
        self.dx[40] = dGamma
    
    def glucose_submodel(self, Ra, rKGE,rHGU, rHGP, rPGU):
        glucose = self.glucoseParameters.glucoseSubmodel
        physical = self.glucoseParameters.physicalActivityParameters
        GBC, GBF, GH, GG, GL, GK, GPC, GPF = self.x[32], self.x[33], self.x[34], self.x[35], self.x[36], self.x[37], self.x[38], self.x[39]
        rBGU, rGGU,rRBCU = self.basal['rBGU'],self.basal['rGGU'],self.basal['rRBCU']
        E1,E2 = self.x[15],self.x[16]
        dGBC = (1 / glucose.VGBC) * (glucose.QGB * (GH - GBC) - (glucose.VGBF / glucose.TGB) * (GBC - GBF))
        dGBF = (1 / glucose.VGBF) * ((glucose.VGBF / glucose.TGB) * (GBC - GBF) - rBGU)
        dGH = (1 / glucose.VGH) * (glucose.QGB * GBC + glucose.QGL * GL + glucose.QGK * GK + glucose.QGP * GPC - glucose.QGH * GH - rRBCU)
        dGG = (1 / glucose.VGG) * (glucose.QGG * (GH - GG) - rGGU + Ra)
        dGL = (1 / glucose.VGL) * (glucose.QGA * GH + glucose.QGG * GG - glucose.QGL * GL + ((1 + self.stress) * (1 - physical.alphae * E2) * rHGP - (1 + physical.alphae * E2) * rHGU))
        dGK = (1 / glucose.VGK) * (glucose.QGK * (GH - GK) - rKGE)
        dGPC = (1 / glucose.VGPC) * (glucose.QGP * (GH - GPC) - (glucose.VGPF / glucose.TGP) * (GPC - GPF))
        dGPF = (1 / glucose.VGPF) * ((glucose.VGPF / glucose.TGP) * (GPC - (1 + physical.betae * E1) * GPF) - (1 + physical.alphae * E2) * rPGU)
        self.dx[32] = dGBC
        self.dx[33] = dGBF
        self.dx[34] = dGH
        self.dx[35] = dGG
        self.dx[36] = dGL
        self.dx[37] = dGK
        self.dx[38] = dGPC
        self.dx[39] = dGPF
        dXGC = (rBGU) + rRBCU + rGGU + (1 + physical.alphae * E2) * rHGU + rKGE + physical.betae * E1 * GPF * glucose.QGP + (1 + physical.alphae * E2) * rPGU
        dXGP = Ra + (1 + self.stress) * (1 - physical.alphae * E2) * rHGP
        dGHint = GH
        self.dx[49] = dXGC
        self.dx[50] = dXGP
        self.dx[56] = dGHint

    def glucose_absorption_submodel(self):
        absorption = self.glucoseParameters.glucoseAbsorptionSubmodel
        DNq = self.x[47]
        dDe = -absorption.kmin * self.x[46]
        dDNq = absorption.kmin * (self.Dg - DNq)
        qss = self.x[0]
        dqss = -absorption.k12 * qss
        QA1 = 5 / (2 * DNq * (1 - absorption.Kq1))
        QA2 = 5 / (2 * DNq * absorption.Kq2)
        qsl = self.x[1]
        kempt = absorption.kmin + ((absorption.kmax - absorption.kmin) / 2) * (np.tanh(QA1 * (qss + qsl - absorption.Kq1 * DNq)) - np.tanh(QA2 * (qss + qsl - absorption.Kq2 * DNq)) + 2)
        dqsl = -kempt * qsl + absorption.k12 * qss
        qint = self.x[2]
        dqint = -absorption.kabs * qint + kempt * qsl
        self.dx[0] = dqss
        self.dx[1] = dqsl
        self.dx[2] = dqint
        self.dx[46] = dDe
        self.dx[47] = dDNq
        return absorption.fg * absorption.kabs * qint / 70 #Ra
    
    def glucose_submodel_rates(self, EGW,EL,EP):
        rates = self.glucoseParameters.glucoseMetabolicRates
        cIPGU, cIHGPinft,cGHGP,cIHGUinft,cGHGU,dIPGU,dIHGPinft,dGHGP,dIHGUinft,dGHGU = rates.c1, rates.c2,rates.c3,rates.c4,rates.c5,rates.d1,rates.d2,rates.d3,rates.d4,rates.d5
        IL, IBL, GBL, GL, GK = self.x[28], self.basal['IL'], self.basal['GL'], self.x[36], self.x[37]
        MIPGU = (7.03 + rates.SPGU * 6.52 * np.tanh(cIPGU * (self.x[31] / self.basal['IPF'] - dIPGU))) / (7.03 + rates.SPGU * 6.52 * np.tanh(cIPGU * (1 - dIPGU)))
        MGPGU = self.x[39] / self.basal['GPF']
        rPGU = MIPGU * MGPGU * self.basal['rPGU']
        MIHGPinft = (1.21 - rates.SHGP * 1.14 * np.tanh(cIHGPinft * (IL / IBL - dIHGPinft))) / (1.21 - rates.SHGP * 1.14 * np.tanh(cIHGPinft * (1 - dIHGPinft)))
        MGHGP = (1.42 - 1.41 * np.tanh(cGHGP * (GL / GBL - dGHGP))) / (1.42 - 1.41 * np.tanh(cGHGP * (1 - dGHGP)))
        MgammaHGP = 2.7 * np.tanh(0.39 * self.x[40] / self.basal['Gamma']) - self.x[44]
        rHGP = self.x[43] * MGHGP * MgammaHGP * self.basal['rHGP']
        MIHGUinft = (np.tanh(cIHGUinft * (IL / IBL - dIHGUinft))) / (np.tanh(cIHGUinft * (1 - dIHGUinft)))
        MGHGU = (5.66 + 5.66 * np.tanh(cGHGU * (GL / GBL - dGHGU))) / (5.66 + 5.66 * np.tanh(cGHGU * (1 - dGHGU)))
        rHGU = self.x[45] * MGHGU * self.basal['rHGU']
        if GK >= 460:
            rKGE = 330 + 0.872 * GK
        else:
            rKGE = 71 + 71 * np.tanh(0.011 * (GK - 460))
        # Effect of Metformin:
        rHGP = rHGP * (1 - EL)
        rGGU = rGGU * (1 + EGW)
        rPGU = rPGU * (1 + EP)
        return rKGE, MIHGPinft, MIHGUinft, rHGU,rHGP, rPGU

    def rates_dynamic_model(self, MIHGPinft, MIHGUinft):
        dMIHGP = 0.04 * (MIHGPinft - self.x[43])
        dfr = 0.0154 * (0.5 * (2.7 * np.tanh(0.39 * self.x[40] / self.basal['Gamma']) - 1) - self.x[44])
        dMIHGU = 0.04 * (MIHGUinft - self.x[45])
        self.dx[43] = dMIHGP
        self.dx[44] = dfr
        self.dx[45] = dMIHGU
    
    def metformin_submodel(self):
        metformin = self.glucoseParameters.metforminSubmodel
        MO1,MO2,MGl,MGW,ML,MP = self.x[3],self.x[4],self.x[5],self.x[6],self.x[7],self.x[8]
        dMO1 = -metformin.alpham * MO1
        dMO2 = -metformin.betam * MO2
        dMGl = -(metformin.kgo + metformin.kgg) * MGl + metformin.rhoalpha * MO1 + metformin.rhobeta * MO2
        dMGW = MGl * metformin.kgg + MP * metformin.kpg - MGW * metformin.kgl
        dML = MGW * metformin.kgl + MP * metformin.kpl - ML * metformin.klp
        dMP = ML * metformin.klp - (metformin.kpl + metformin.kpg + metformin.kpo) * MP + MGl
        self.dx[3] = dMO1
        self.dx[4] = dMO2
        self.dx[5] = dMGl
        self.dx[6] = dMGW
        self.dx[7] = dML
        self.dx[8] = dMP
        EGW = (metformin.vGWmax * (MGW) ** (metformin.nGW)) / (metformin.phiGW50 ** (metformin.nGW) + (MGW) ** (metformin.nGW))
        EL = (metformin.vLmax * (ML) ** (metformin.nL)) / (metformin.phiL50 ** (metformin.nL) + (ML) ** (metformin.nL))
        EP = (metformin.vPmax * (MP) ** (metformin.nP)) / (metformin.phiP50 ** (metformin.nP) + (MP) ** (metformin.nP))
        return EGW,EL,EP
    
    def vildagliptin_submodel(self):
        vildagliptin = self.glucoseParameters.vildagliptinSubmodel
        AG1,AG2,Ac,Ap,DRc,DRp = self.x[9],self.x[10],self.x[11],self.x[12],self.x[13],self.x[14]
        dAG1 = -vildagliptin.ka1 * AG1
        dAG2 = vildagliptin.ka1 * AG1 - vildagliptin.ka2 * AG2
        dAc = vildagliptin.ka2 * AG2 - ((vildagliptin.CL + vildagliptin.CLic) / vildagliptin.Vc) * Ac + (vildagliptin.CLic / vildagliptin.Vp) * Ap - ((vildagliptin.RmaxC - DRc) * vildagliptin.k2v * (Ac / vildagliptin.Vc)) / (vildagliptin.kvd + Ac / vildagliptin.Vc) + vildagliptin.koff * DRc
        dAP = vildagliptin.CLic * (Ac / vildagliptin.Vc - Ap / vildagliptin.Vp) - ((vildagliptin.RmaxP - DRp) * vildagliptin.k2v * (Ap / vildagliptin.Vp)) / (vildagliptin.kvd + Ap / vildagliptin.Vp) + vildagliptin.koff * DRp
        dDRc = (vildagliptin.RmaxC - DRc) * vildagliptin.k2v * (Ac / vildagliptin.Vc) / (vildagliptin.kvd + Ac / vildagliptin.Vc) - (vildagliptin.koff - vildagliptin.kdeg) * DRc
        dDRp = (vildagliptin.RmaxP - DRp) * vildagliptin.k2v * (Ap / vildagliptin.Vp) / (vildagliptin.kvd + Ap / vildagliptin.Vp) - (vildagliptin.koff + vildagliptin.kdeg) * DRp
        self.dx[9] = dAG1
        self.dx[10] = dAG2
        self.dx[11] = dAc
        self.dx[12] = dAP
        self.dx[13] = dDRc
        self.dx[14] = dDRp
    
    def physical_activity_submodel(self):
        physical = self.glucoseParameters.physicalActivityParameters
        E1,E2,TE = self.x[15],self.x[16],self.x[48]
        HR = np.interp(self.t, self.T, self.HRv)
        dE1 = (1 / physical.tHR) * (HR - physical.HRb - E1)
        gE = (E1 / (physical.ae * physical.HRb)) ** physical.ne / (1 + (E1 / (physical.ae * physical.HRb)) ** physical.ne)
        dTE = (1 / physical.te) * (physical.ce1 * gE + physical.ce2 - TE)
        dE2 = -(gE + 1 / physical.te) * E2 + gE
        self.dx[15] = dE1
        self.dx[16] = dE2
        self.dx[48] = dTE

# Usage example
# fode_simulator = FodeSimulator(obj, t, x, Dg, stressv, HRv, T, param, basal)
# results = fode_simulator.compute()
