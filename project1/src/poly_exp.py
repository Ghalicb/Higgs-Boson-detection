### This is to experiment with the dataset, the degree of the polynomial expansion, the regularisation parameter, and the learning rate.

from helpers import *

seed = 1
DATA_TRAIN_PATH = '../data/train.csv'
y_train, tX_train, ids_train = load_csv_data(DATA_TRAIN_PATH, sub_sample=False)

## First make a dataset where the NaNs are replaced by the mean
tX_train_replace_invalid = tX_train.copy()

# Make the -999 into NaNs
tX_train_replace_invalid[tX_train_replace_invalid == -999.] = np.nan
# Replace NaNs by the column average
for i in range(tX_train.shape[1]):
  a = tX_train_replace_invalid[:, i]
  mean = np.average(a[ ~np.isnan(a) ])
  a[ np.isnan(a) ] = mean
# Now, tX_train_replace_invalid is the way we need it.

## Now make a dataset where the columns with NaNs are dropped
tX_train_drop_invalid = tX_train.copy()
tX_train_drop_invalid = tX_train_drop_invalid[:, ~np.any(tX_train_drop_invalid == -999., axis=0)]
# Now, tX_train_drop_invalid is the way we need it.

tX_dict = {
  "NO_NANS" : tX_train_drop_invalid,
  "REPLACE_NANS" : tX_train_replace_invalid,
}


def partition(y, tx, seed, fraction = 0.8):
  """
  Partition data.
  """
  indices = np.random.permutation(len(y))
  cutoff = int(fraction * len(y))

  y_train = y[:cutoff]
  tx_train = tx[:cutoff]
  y_test = y[cutoff:]
  tx_test = tx[cutoff:]
  return y_train, tx_train, y_test, tx_test


def lambda_gamma_degree_sgd_cv(data_set, algorithm, lambdas, gammas, degrees, K, max_iters, batch_size):
  """Do K-fold cross-validation for each value in lambdas and gammas and each degree of polynomial expansion, at every iteration.
  
  Inputs:
  ========
  data_set : string
    Which dataset to work with
    Can take any value in { "NO_NANS", "REPLACE_NANS" }
  algorithm : string
    The algorithm to use for training
    Can take any value in { "LEAST_SQUARE" , "LOGISTIC_REGRESSION", "REGULARIZED_LOGISTIC_REGRESSION"}
  lambdas : iterable
    Regularisation parameters for cost function
  gammas : iterable
    Learning rates for SGD
  degrees : iterable
    Highest polynomial degree
  K : int
    Number of folds
  max_iters : int
    Maxium number of iterations for SGD
  batch_size : int
    Size of mini-batches
  seed : int
    Seed for pseudo-random number generation
  
  Outputs:
  w_best : np array
    (D, len(lambdas), len(lambdas))
    Trained weights that produced the smallest validation error
    over all folds, for each lambda and gamma
  training_errors : np array
    (K, len(lambdas), len(lambdas))
    Training loss for each fold, for each degree, for each lambda and gamma
  validation_errors : np array
    (K, len(lambdas), len(lambdas))
    Validation loss for each fold, for each degree, for each lambda and gamma
  """
  y, tx = prepare_dimensions(y_train, tX_dict[data_set])

  N = len(y)
  len_lambdas = len(degrees)
  len_lambdas = len(lambdas)
  len_gammas = len(gammas)

  initial_w = np.ones((tx.shape[1], 1))
  w_best = np.zeros((tx.shape[1], len_degrees, len_lambdas, len_gammas))

  training_errors = np.zeros((K, len_degrees, len_lambdas, len_gammas))
  validation_errors = np.zeros((K, len_degrees, len_lambdas, len_gammas))
  min_error = np.inf * np.ones((len_degrees, len_lambdas, len_gammas))

  k_indices = build_k_indices(y, K, seed)

  for d, degree in enumerate(degrees):
    print("Degree = {}".format(degree))
    tx_poly = build_poly(tx, degree)
    tx_poly, *_ = standardise(tx_poly)

    for k in range(K):
      print("  Fold = {}".format(k+1))
      # Take all but the k-th row of tx and y
      tx_train, y_train = map(lambda a: a[np.delete(k_indices, k).flatten()], (tx_poly, y))
      # Take the k-th row of tx and y
      tx_test, y_test = map(lambda a: a[k_indices[k]], (tx_poly, y))

      for i, lambda_ in enumerate(lambdas):
        for j, gamma in enumerate(gammas):
          # Train
          w, loss_tr = SGD(y_train, tx_train, initial_w, max_iters, gamma, algorithm, batch_size, lambda_)
          # Test
          loss_te = compute_mse_loss(y_test, tx_test, w)
          
          training_errors[k, d, i, j] = loss_tr
          validation_errors[k, d, i, j] = loss_te

          # Keep the weights that give the lowest loss_te
          if loss_te < min_error[d, i, j]:
            min_error[d, i, j] = loss_te
            w_best[:, d, i, j] = w.ravel()

  return w_best, training_errors, validation_errors



# Now let's run it
lambdas = np.logspace(-8, -1, 5)
gammas = np.logspace(-2, 1, 3)
algorithm = "REGULARIZED_LOGISTIC_REGRESSION"
data_set = "REPLACE_NANS"
degrees = range(1, 4)
K = 4
max_iters = 1000
batch_size = 1

w_best, training_errors, validation_errors = lambda_gamma_degree_sgd_cv(
  data_set,
  algorithm,
  lambdas,
  gammas,
  degrees,
  K,
  max_iters,
  batch_size)
