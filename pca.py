import pprint
import numpy as np


INPUT = [[7, 4, 3],
         [4, 1, 8],
         [6, 3, 5],
         [8, 6, 1],
         [8, 5, 7],
         [7, 2, 9],
         [5, 3, 3],
         [9, 5, 8],
         [7, 4, 5],
         [8, 2, 2]]


def reduce_dimensionality(input, n):
    """
    Reduce input matrix dimensionality using PCA
    :param input: Input matrix as 2D array
    :return: Output with reduced dimensionality
    """
    x_original = np.array(input)
    x_mean = np.mean(input, 0)

    # 1. cov_matrix * v = w * v
    cov_matrix = np.cov(x_original.T)

    # 2. eigen decomposition
    # eigenvectors in v are orthogonal to each other
    w, v = np.linalg.eig(cov_matrix)

    # 3. Construct the transformation matrix using eigenvectors of top n eigenvalues
    a = np.fliplr(v[:, -n:]).T

    # 4. Transform original dimension input to reduced dimension
    x_reduced = np.matmul(a, (x_original - x_mean).T).T

    return x_reduced


if __name__ == '__main__':
    x = reduce_dimensionality(INPUT, 2)
    pprint.pprint(x)
