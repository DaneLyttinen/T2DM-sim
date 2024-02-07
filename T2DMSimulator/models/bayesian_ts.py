from contextualbandits.online import _BasePolicyWithExploit
from contextualbandits.utils import _ZeroPredictor, _apply_sigmoid, _unexpected_err_msg
import pymc3 as pm, pandas as pd
import numpy as np

def _check_bay_inp(method, n_iter, n_samples):
    assert method in ['advi','nuts']
    if n_iter == 'auto':
        if method == 'nuts':
            n_iter = 100
        else:
            n_iter = 2000
    assert n_iter > 0
    if isinstance(n_iter, float):
        n_iter = int(n_iter)
    assert isinstance(n_iter, int)

    assert n_samples > 0
    if isinstance(n_samples, float):
        n_samples = int(n_samples)
    assert isinstance(n_samples, int)

    return n_iter, n_samples

class _BayesianLogisticRegression:
    def __init__(self, method='advi', niter=2000, nsamples=20, mode='ucb', perc=None):
        #TODO: reimplement with something faster than using PyMC3's black-box methods
        self.nsamples = nsamples
        self.niter = niter
        self.mode = mode
        self.perc = perc
        self.method = method

    def fit(self, X, y):
        with pm.Model():
            pm.glm.linear.GLM(X, y, family = 'binomial')
            pm.find_MAP()
            if self.method == 'advi':
                trace = pm.fit(progressbar = False, n = self.niter)
            if self.method == 'nuts':
                trace = pm.sample(progressbar = False, draws = self.niter)
        if self.method == 'advi':
            self.coefs = [i for i in trace.sample(self.nsamples)]
        elif self.method == 'nuts':
            samples_chosen = np.random.choice(np.arange( len(trace) ), size = self.nsamples, replace = False)
            samples_chosen = set(list(samples_chosen))
            self.coefs = [i for i in trace if i in samples_chosen]
        else:
            raise ValueError("'method' must be one of 'advi' or 'nuts'")
        self.coefs = pd.DataFrame.from_dict(self.coefs)
        self.coefs = self.coefs[ ['Intercept'] + ['x' + str(i) for i in range(X.shape[1])] ]
        self.intercept = self.coefs['Intercept'].values.reshape((-1, 1)).copy()
        del self.coefs['Intercept']
        self.coefs = self.coefs.values.T

    def _predict_all(self, X):
        pred_all = X.dot(self.coefs) + self.intercept
        _apply_sigmoid(pred_all)
        return pred_all

    def predict(self, X):
        pred = self._predict_all(X)
        if self.mode == 'ucb':
            pred = np.percentile(pred, self.perc, axis=1)
        elif self.mode == ' ts':
            pred = pred[:, np.random.randint(pred.shape[1])]
        else:
            raise ValueError(_unexpected_err_msg)
        return pred

    def exploit(self, X):
        pred = self._predict_all(X)
        return pred.mean(axis = 1)
# import numpy as np
class BayesianTS(_BasePolicyWithExploit):
    """
    Bayesian Thompson Sampling
    
    Performs Thompson Sampling by sampling a set of Logistic Regression coefficients
    from each class, then predicting the class with highest estimate.

    Note
    ----
    The implementation here uses PyMC3's GLM formula with default parameters and ADVI.
    This is a very, very slow implementation, and will probably take at least two
    orders or magnitude more to fit compared to other methods.
    
    Parameters
    ----------
    nchoices : int or list-like
        Number of arms/labels to choose from. Can also pass a list, array or series with arm names, in which case
        the outputs from predict will follow these names and arms can be dropped by name, and new ones added with a
        custom name.
    method : str, either 'advi' or 'nuts'
        Method used to sample coefficients (see PyMC3's documentation for mode details).
    n_samples : int
        Number of samples to take when making predictions.
    n_iter : int
        Number of iterations when using ADVI, or number of draws when using NUTS. Note that, when using NUTS,
        will still first draw a burn-out or tuning 500 samples before 'niter' more have been produced.
        If passing 'auto', will use 2000 for ADVI and 100 for NUTS, but this might me insufficient.
    beta_prior : str 'auto', None, or tuple ((a,b), n)
        If not None, when there are less than 'n' positive samples from a class
        (actions from that arm that resulted in a reward), it will predict the score
        for that class as a random number drawn from a beta distribution with the prior
        specified by 'a' and 'b'. If set to auto, will be calculated as:
        beta_prior = ((3/nchoices, 4), 2)
    smoothing : None or tuple (a,b)
        If not None, predictions will be smoothed as yhat_smooth = (yhat*n + a)/(n + b),
        where 'n' is the number of times each arm was chosen in the training data.
        This will not work well with non-probabilistic classifiers such as SVM, in which case you might
        want to define a class that embeds it with some recalibration built-in.
        Recommended to use only one of 'beta_prior' or 'smoothing'.
    assume_unique_reward : bool
        Whether to assume that only one arm has a reward per observation. If set to False,
        whenever an arm receives a reward, the classifiers for all other arms will be
        fit to that observation too, having negative label.
    njobs : int or None
        Number of parallel jobs to run. If passing None will set it to 1. If passing -1 will
        set it to the number of CPU cores. Be aware that the algorithm will use BLAS function calls,
        and if these have multi-threading enabled, it might result in a slow-down
        as both functions compete for available threads.
    """
    def __init__(self, nchoices, method='advi', n_samples=20, n_iter='auto',
                 beta_prior='auto', smoothing=None, assume_unique_reward=False, njobs=1):

        ## NOTE: this is a really slow and poorly thought implementation
        ## TODO: rewrite using some faster framework such as Edward,
        ##       or with a hard-coded coordinate ascent procedure instead. 
        self._add_common_params(_ZeroPredictor(), beta_prior, smoothing, njobs, nchoices,
                                False, assume_unique_reward, assign_algo=False)
        self.nchoices = nchoices
        self.n_iter, self.n_samples = _check_bay_inp(method, n_iter, n_samples)
        self.method = method
        self.base_algorithm = _BayesianLogisticRegression(
                    method = self.method, niter = self.n_iter,
                    nsamples = self.n_samples, mode = 'ts')
        self.batch_train = False