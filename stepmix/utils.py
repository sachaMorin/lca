import numbers
import numpy as np

from sklearn.utils.validation import check_is_fitted


# Check parameters utils copied from the PHATE library
def check_positive(**params):
    """Check that parameters are positive as expected
    Raises
    ------
    ValueError : unacceptable choice of parameters
    """
    for p in params:
        if not isinstance(params[p], numbers.Number) or params[p] <= 0:
            raise ValueError("Expected {} > 0, got {}".format(p, params[p]))


def check_nonneg(**params):
    """Check that parameters are non-negative as expected
    Raises
    ------
    ValueError : unacceptable choice of parameters
    """
    for p in params:
        if not isinstance(params[p], numbers.Number) or params[p] < 0:
            raise ValueError("Expected {} >= 0, got {}".format(p, params[p]))


def check_int(**params):
    """Check that parameters are integers as expected
    Raises
    ------
    ValueError : unacceptable choice of parameters
    """
    for p in params:
        if not isinstance(params[p], numbers.Integral):
            raise ValueError("Expected {} integer, got {}".format(p, params[p]))


def check_if_not(x, *checks, **params):
    """Run checks only if parameters are not equal to a specified value
    Parameters
    ----------
    x : excepted value
        Checks not run if parameters equal x
    checks : function
        Unnamed arguments, check functions to be run
    params : object
        Named arguments, parameters to be checked
    Raises
    ------
    ValueError : unacceptable choice of parameters
    """
    for p in params:
        if params[p] is not x and params[p] != x:
            [check(**{p: params[p]}) for check in checks]


def check_in(choices, **params):
    """Checks parameters are in a list of allowed parameters
    Parameters
    ----------
    choices : array-like, accepted values
    params : object
        Named arguments, parameters to be checked
    Raises
    ------
    ValueError : unacceptable choice of parameters
    """
    for p in params:
        if params[p] not in choices:
            raise ValueError(
                "{} value {} not recognized. Choose from {}".format(
                    p, params[p], choices
                )
            )


def check_type(type, **params):
    """Checks parameters are of a given type.
    Parameters
    ----------
    choices : array-like, accepted values
    params : object
        Named arguments, parameters to be checked
    Raises
    ------
    ValueError : unacceptable choice of parameters
    """
    for p in params:
        if not isinstance(params[p], type):
            raise ValueError(
                "{} value {} not recognized. Choose from {}".format(
                    p, params[p], p
                )
            )


def check_between(v_min, v_max, **params):
    """Checks parameters are in a specified range
    Parameters
    ----------
    v_min : float, minimum allowed value (inclusive)
    v_max : float, maximum allowed value (inclusive)
    params : object
        Named arguments, parameters to be checked
    Raises
    ------
    ValueError : unacceptable choice of parameters
    """
    for p in params:
        if params[p] < v_min or params[p] > v_max:
            raise ValueError(
                "Expected {} between {} and {}, "
                "got {}".format(p, v_min, v_max, params[p])
            )


def check_emission_param(descriptor, keys):
    """Check if the emission descriptor is valid.

    A string describes a homogeneous model (e.g., all binary, all gaussian).

    A dict will trigger a nested model. Please refer to stepmix.emission.nested.Nested for details.

    Parameters
    ----------
    descriptor: str or list, parameter description.
    keys: list, list of valid emission strings.

    Returns
    -------
    is_valid: bool, indicating a valid parameter description.

    """
    if isinstance(descriptor, str):
        check_in(keys, emission=descriptor)
    elif isinstance(descriptor, dict):
        for key, item in descriptor.items():
            if isinstance(item, dict):
                if 'model' not in item or 'n_features' not in item:
                    raise ValueError(f'Nested dict descriptors should include at least a model key and an n_features '
                                     f'key.')

                # Check that n_features is a positive int
                check_in(keys, emission=item['model'])
            else:
                raise ValueError(f'Items in a nested model description should be dicts.')

    else:
        raise ValueError(f'Emission descriptor should be either a string or a dict.')


def identify_coef(coef):
    """Find a reference configuration of the coefficients.

    Pick whichever coefficient is closest to 0 in the first row of coef. Subtract the associated
    column from all coefficients. This will give us a reference class with 0 coefficients everywhere.


    Parameters
    ----------
    coef: np.ndarray, Current coefficient estimates.

    Returns
    -------
    coef: np.ndarray, Corrected coefficient estimates with a null reference class.

    """
    closest_id = np.argsort(coef[0])[1]
    coef -= coef[:, closest_id].reshape((-1, 1))
    return coef


def modal(resp, clip=False):
    """Takes in class probabilities and performs modal assignment.

    Will return a one-hot encoding. The clip argument can also be used to clip the results to the (1e-15, 1-1e-15)
    range.
    
    Parameters
    ----------
    resp : array-like of shape (n_samples, n_components)
        Class probabilities.
    clip : bool, default=False
        Clip the probabilities to the range (1e-15, 1-1e-15).

    Returns
    -------
    modal_resp : array, shape (n_samples, n_components)
        Modal class assignment.

    """
    preds = resp.argmax(axis=1)
    modal_resp = np.zeros(resp.shape)
    modal_resp[np.arange(resp.shape[0]), preds] = 1

    if clip:
        modal_resp = np.clip(modal_resp, 1e-15, 1 - 1e-15)

    return modal_resp


def print_report(model, X, Y=None):
    """Print detailed output for the model.

    Parameters
    ----------
    model: stepmix.StepMix
        Fitted StepMix instance.
    X : array-like of shape (n_samples, n_features)
        List of n_features-dimensional data points. Each row
        corresponds to a single data point of the measurement model.
    Y : array-like of shape (n_samples, n_structural), default = None
        List of n_structural-dimensional data points. Each row
        corresponds to a single data point of the structural model.
    """
    check_is_fitted(model)
    n_classes = model.n_components
    n_samples = X.shape[0]
    n_parameters = model.n_parameters
    ll = model.score(X, Y)
    bic = model.bic(X, Y)
    aic = model.aic(X, Y)

    print("=" * 80)
    print("MODEL REPORT")
    print("=" * 80)
    print("    " + "=" * 76)
    print(f"    Measurement model parameters")
    print("    " + "=" * 76)
    model._mm.print_parameters(indent=2)

    if hasattr(model, '_sm'):
        print("    " + "=" * 76)
        print(f"    Structural model parameters")
        print("    " + "=" * 76)
        model._sm.print_parameters(indent=2)

    print("    " + "=" * 76)
    print(f"    Class weights")
    print("    " + "=" * 76)
    for i, w in enumerate(model.weights_):
        print(f"        Class {i + 1} : {w:.2f}")


    print("    " + "=" * 76)
    print(f"    Fit for {n_classes} latent classes")
    print("    " + "=" * 76)
    print(f"    Estimation method             : {model.n_steps}-step")
    if model.n_steps == 3:
        print(f"    Correction method             : {model.correction}")
        print(f"    Assignment method             : {model.assignment}")
    print(f"    Number of observations        : {n_samples}")
    print(f"    Number of latent classes      : {n_classes}")
    print(f"    Number of estimated parameters: {n_parameters}")
    print(f"    Average log-likelihood        : {ll:.4f}")
    print(f"    AIC                           : {aic:.2f}")
    print(f"    BIC                           : {bic:.2f}")


def print_parameters(params, model_name, indent=1, np_precision=2, n_outcomes=1, intercept=False, print_mean=False,
                     covariances=None, tied=False):
    """Print model parameters with nice formatting.

    Parameters
    ----------
    params: np.ndarray
        Array of parameters to print. The first axis should correspond to latent classes.
    model_name: str
        Model name.
    indent: int
        Indent of the print.
    np_precision: int
        Float precision for numpy prints.
    n_outcomes: int
        Number of possible categorical outcomes. Only used for multinoulli model
    intercept: bool, default=False
        One parameter is an intercept. Only used for covariate model.
    print_mean: bool, default=False
        Add a 'means' header before printing the first parameters. Used for gaussian models.
    covariances: np.ndarray, default=None
        If provided, also print covariances. Used for gaussian models.
    tied: bool, default=False
        Only print the covariance once and not by class. Used for gaussian model with tied covariance..
    """
    np.set_printoptions(precision=np_precision)
    indent_str = "    " * indent
    n_classes, n_features = params.shape

    if intercept:
        n_features -= 1

    if (n_outcomes >= 2):
        n_features = int(n_features/n_outcomes)

    # Title
    print(indent_str + '-' * (80 - indent * 4))
    print(indent_str + f"{model_name} model with {n_features} feature" + ("s" if n_features > 1 else "") +
          (f", each with {n_outcomes} possible outcomes" if n_outcomes >= 2 else "") +
          (" and intercept" if intercept else "")
          )
    print(indent_str + '-' * (80 - indent * 4))

    # Clarification message for multinoulli model
    if (n_outcomes >= 2 and n_features >= 2):
        print(indent_str + "Columns 1 to", n_outcomes,"are associated with the first feature,")
        print(indent_str + "columns",n_outcomes+1,"to", 2*n_outcomes, "are associated with the second feature, etc.\n")

    # Clarification message for covariate model
    if intercept:
        print(indent_str + "Intercept coefficients are in the first column.")

    # Specify that the following parameters are means
    if print_mean:
        print(indent_str + "Means")
        print(indent_str + "-----")

    # Print parameters
    for i, p in enumerate(params):
        print(indent_str + f"Class {i + 1} : {p}")

    # Print covariances if provided
    if covariances is not None:
        print()
        print(indent_str + "Covariance"  + ("s" if not tied else ""))
        print(indent_str + "-----------")
        if tied:
            for c in covariances:
                print(indent_str + f"{c}")
        else:
            for i, p in enumerate(covariances):
                if isinstance(p, np.ndarray) and len(p.shape) == 2:
                    print(indent_str + f"Class {i + 1} :")
                    for c in p:
                        print(indent_str + f"{c}")
                    print()
                elif isinstance(p, np.ndarray):
                    print(indent_str + f"Class {i + 1} : {p}")
                else:
                    print(indent_str + f"Class {i + 1} : {p:.2f}")
