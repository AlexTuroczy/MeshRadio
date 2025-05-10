import numpy as np
import scipy

input = np.array([[1, 2], [0, 0]])
sigma_x = 1
sigma_y = 1
scale = 100
sigma = np.array([[sigma_x ** 2, 0], [0, sigma_y ** 2]])  # Covariance matrix
bound = 5


def eval(x, y):
    sum = 0
    for center in input:
        rv = scipy.stats.multivariate_normal(mean=center, cov=sigma)
        altitude = rv.pdf(np.array([x, y])) * scale
        sum += altitude
    return sum


for x in range(bound):
    alt = []
    for y in range(bound):
        alt.append(eval(x, y))
    print(alt)

