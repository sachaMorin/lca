import numpy as np
from lca.datasets import data_bakk_covariate
from lca.lca import LCA
from lca.emission import Covariate
from sklearn.metrics import adjusted_rand_score, accuracy_score
from lca.utils import identify_coef

n = 1000
sep_level = .9

X, Y, c = data_bakk_covariate(sample_size=n, sep_level=sep_level, random_state=42)

# First a sanity check to see if the covariate model learns
# on modal ground truth latent classes
target = np.zeros((n, 3))
target[np.arange(n), c] = 1
m = Covariate(n_components=3, iter=1000, lr=1, random_state=42)
m.initialize(X, target)
m.m_step(X, target)
pred = m.predict(X)
print(f'Trained on GT Accuracy : {accuracy_score(c, pred):.3f}\n')


# Then we train the full LCA models
# Helper function to quickly print experiment results
def print_results(log_likelihoods, rand_scores, means, intercepts):
    print("Log-likelihoods")
    print("_________________________")
    for i, ll in enumerate(log_likelihoods):
        print(f'{i + 1}-step log-likelihood : {ll:.3f}')

    print("\nRand Scores")
    print("_________________________")
    for i, rs in enumerate(rand_scores):
        print(f'{i + 1}-step Rand score : {rs:.3f}')

    print("\nParameters")
    print("_________________________")
    for i, mean in enumerate(means):
        order = np.argsort(mean.flatten())
        print(f'{i + 1}-step coefficients : {mean[order].flatten()}')
        print(f'{i + 1}-step intercepts   : {intercepts[i][order].flatten()}')
        print("\n")


print('Bakk covariate experiment...')

ll_list = []
rand_score = []
means_list = []
intercepts_list = []

# Run experiment for 1-step, 2-step and 3-step
for n_steps in [1, 2, 3]:
    m = LCA(n_steps=n_steps, n_components=3, measurement='bernoulli', structural='covariate', n_init=10,
            random_state=42, max_iter=1000, tol=1e-5, structural_params=dict(lr=5e-3,
                                                                             iter=1 if n_steps < 3 else 1000))
    m.fit(X, Y)

    # Model estimates all K coefficients. Apply translation to have a a null reference category
    coef = identify_coef(m.get_parameters()['structural']['coef'].copy())

    # Likelihood and paramters
    ll_list.append(m.score(X, Y))
    means_list.append(coef[0])
    intercepts_list.append(coef[1])

    # Compare clustering quality vs. ground truth
    pred = m.predict(X, Y)
    rand_score.append(adjusted_rand_score(c, pred))

# Report ll, rand score and parameters
print_results(ll_list, rand_score, means_list, intercepts_list)
