class GlucoseParameters:
    def __init__(self):
        self.glucoseSubmodel = GlucoseSubmodel()
        self.InsulinSubmodel = InsulinSubmodel()
        self.glucagonSubmodel = GlucagonSubmodel()
        self.glucoseAbsorptionSubmodel = GlucoseAbsorptionParameters()
        self.glucoseMetabolicRates = GlucoseMetabolicRates()
        self.pancreasModel = PancreasModel()
        self.gLP1Submodel = GLP1Submodel()
        self.vildagliptinSubmodel = VildagliptinSubmodel()
        self.metforminSubmodel = MetforminSubmodel()
        self.longActingInsulinSubmodel = LongActingInsulinSubmodel()
        self.fastActingInsulinSubmodel = FastActingInsulinSubmodel()
        self.physicalActivityParameters = PhysicalActivityParameters()
        self.sMBGSigmaSubmodel = SMBGSigmaSubmodel()

class GlucoseSubmodel():
    def __init__(self):
        self.VGBC = 3.5
        self.VGBF = 4.5
        self.VGH = 13.8
        self.VGL = 25.1
        self.VGG = 11.2
        self.VGK = 6.6
        self.VGPC = 10.4
        self.VGPF = 67.4
        self.QGB = 5.9
        self.QGH = 43.7
        self.QGA = 2.5
        self.QGL = 12.6
        self.QGG = 10.1
        self.QGK = 10.1
        self.QGP = 15.1
        self.TGB = 2.1
        self.TGP = 5.0

class InsulinSubmodel():
    def __init__(self):
        self.VIB = 0.26
        self.VIH = 0.99
        self.VIG = 0.94
        self.VIL = 1.14
        self.VIK = 0.51
        self.VIPF = 6.74
        self.QIB = 0.45
        self.QIH = 3.12
        self.QIA = 0.18
        self.QIK = 0.72
        self.QIP = 1.05
        self.QIG = 0.72
        self.TIP = 20.0
        self.mpan0 = 6.33
        self.QIL = 0.9
        self.VIPC = 0.74

class GlucagonSubmodel():
    def __init__(self):
        self.VGamma = 6.74

class GlucoseAbsorptionParameters():
    def __init__(self):
        self.fg = 0.9
        self.Kq1 = 0.68
        self.Kq2 = 0.00236
        self.k12 = 0.08
        self.kmin = 0.005
        self.kmax = 0.05
        self.kabs = 0.08

class GlucoseMetabolicRates():
    def __init__(self):
        self.c1 = 0.067  # cIPGU
        # Changed below as 1.59 * 121
        self.c2 = 192.39  # cIHGPinft
        self.c3 = 0.62  # cGHGP
        self.c4 = 1.72  # cIHGUinft
        self.c5 = 2.03  # cGHGU
        self.d1 = 1.126  # dIPGU
        self.d2 = 0.683  # dIHGPinft
        self.d3 = 0.14  # dGHGP
        self.d4 = 0.023  # dIHGUinft
        self.d5 = 1.59  # dGHGU
        self.SHGU = 1
        self.SHGP = 1
        self.SPGU = 1

class PancreasModel():
    def __init__(self):
        self.zeta1 = 0.0026
        self.zeta2 = 0.000099
        self.ml0 = 6.33
        self.Kl = 0.0572
        self.Ks = 0.0572  # Kpan
        self.gammapan = 2.366
        self.alphapan = 0.615
        self.betapan = 0.931
        self.N1 = 0.0499
        self.N2 = 0.00015
        self.KILLPAN = 0
        self.Sfactor = 1

class GLP1Submodel():
    def __init__(self):
        self.VPHI = 11.31
        self.Kout = 68.30411374407583
        self.CF2 = 21.151177251184837
        self.tphi = 35.1
        self.zeta = 8.248
        

class VildagliptinSubmodel():
    def __init__(self):
        self.Fv = 0.772
        self.ka1 = 1.26 / 60
        self.ka2 = 1.05 / 60
        self.CL = 36.4 / 60
        self.CLic = 40.1 / 60
        self.Vp = 97.3
        self.Vc = 22.2
        self.kvd = 71.9  # kdvil
        self.k2v = 23.4 / 60  # k2vil
        self.koff = 0.612 / 60
        self.RmaxP = 13
        self.kdeg = 0.110 / 60
        self.RmaxC = 5

class MetforminSubmodel():
    def __init__(self):
        self.kgo = 1.88e-03
        self.kgg = 1.85e-03
        self.kpg = 4.13
        self.kgl = 0.46
        self.kpl = 1.01e-02
        self.klp = 0.91
        self.kpo = 0.51
        self.vGWmax = 0.9720
        # modified, divided by 4
        self.vLmax = 0.189
        self.vPmax = 0.2960
        self.nGW = 2
        self.nL = 5
        self.nP = 5
        self.phiGW50 = 431
        self.phiL50 = 521
        self.phiP50 = 1024
        self.rhoalpha = 2.70e+04 / 500000
        self.rhobeta = 2.70e+04 / 500000
        self.alpham = 0.06
        self.betam = 0.1

class LongActingInsulinSubmodel():
    def __init__(self):
        self.pla = 0.014023809879501
        self.rla = 0.005642135109700
        self.qla = 0.007287049037943
        self.bla = 0.088371175275079
        self.Cmax = 15
        self.kla = 0.033904763958221
        self.kcll = 0.005347967285141

class FastActingInsulinSubmodel():
    def __init__(self):
        self.pfa = 0.033304427073854
        self.rfa = 0.192838157600319
        self.qfa = -0.000000009999983
        self.bfa = 0.350073112766538
        self.kclf = 0.031321989850181

class PhysicalActivityParameters():
    def __init__(self):
        self.tHR = 5
        self.ne = 4
        self.ae = 5
        self.te = 600
        self.alphae = 0.8
        self.betae = 3.39e-4
        self.HRb = 65
        self.ce1 = 500
        self.ce2 = 100

class SMBGSigmaSubmodel():
    def __init__(self):
        self.sigsmbg = 0.1
