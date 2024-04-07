import numpy as np

def bump_score(cgm):
    if 90 < cgm < 180:
        return np.exp(-1 * ((1 - ((cgm - 90) / 45)) ** 2))
    else:
        return 0