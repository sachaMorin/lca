import numpy as np

from lca.emission.emission import Emission


class Bernoulli(Emission):
    """Bernoulli (binary) emission model."""

    def m_step(self, X, resp):
        pis = X.T @ resp
        pis /= resp.sum(axis=0, keepdims=True)
        pis = np.clip(pis, 1e-15, 1 - 1e-15)  # avoid probabilities 0 or 1
        self.parameters['pis'] = pis

    def log_likelihood(self, X):
        # compute log emission probabilities
        pis = np.clip(self.parameters['pis'], 1e-15, 1 - 1e-15)  # avoid probabilities 0 or 1
        log_eps = X @ np.log(pis) + (1 - X) @ np.log(1 - pis)
        return log_eps

    def sample(self, class_no, n_samples):
        feature_weights = self.parameters['pis'][:, class_no].reshape((1, -1))
        K = feature_weights.shape[1]  #number of features
        X = (self.random_state.uniform(size=(n_samples, K)) < feature_weights).astype(int)
        return X

class Multinoulli(Emission):
    """Multinoulli (categorical) emission model."""

    def m_step(self, X, resp):
        pis = X.T @ resp
        pis /= resp.sum(axis=0, keepdims=True)
        pis = np.clip(pis, 1e-15, 1 - 1e-15)  # avoid probabilities 0 or 1
        self.parameters['pis'] = pis

    def log_likelihood(self, X):
        # compute log emission probabilities
        #
        # n individuals, K features, L possible outcomes for each multinoulli. X[n,KL], pis[KL,C]
        # X[n,k*L+l]=1 if l is the observed outcome for the kth attribute of individual n
        # pis[k*L+l,c]=P[ X[n,k*L+l]=1 | n belongs to class c]
        #
        pis = np.clip(self.parameters['pis'], 1e-15, 1 - 1e-15)
        log_eps = X @ np.log(pis)
        return log_eps

    def sample(self, class_no, n_samples):
        pis = self.parameters['pis']
        KL, C = pis.shape
        L = 1 + np.where(np.isclose(np.cumsum(pis, axis=0)[:, 0], 1))[0][0]
        K = int(KL / L)
        feature_weights = pis[:, class_no].reshape(K,L)
        X = np.array([self.random_state.multinomial(1, feature_weights[k], size=n_samples) for k in range(K)])
        X = np.reshape(np.swapaxes(X, 0, 1), (n_samples, KL))
        return X