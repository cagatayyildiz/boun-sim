''' 
This study is a Bogazici University - NETAS Nova V-Gate collaboration and funded by TEYDEB project "Realization of Anomaly Detection and Prevention with Learning System Architectures, Quality Improvement, High Rate Service Availability and Rich Services in a VoIP Firewall Product'', by the Scientific and Technological Research Council Of Turkey (TUBITAK).
'''

import numpy as np
import scipy.special as sp
import os


def find_or_create(dirname):
    if not os.path.isdir(dirname):
        try:
            os.makedirs(dirname)
        except:
            print("Cannot create directory : " + dirname)
            return False
    return True


def load_txt(filename):
    if os.path.isfile(filename):
        x = np.loadtxt(filename)
        ndim = int(x[0])
        shape = np.asarray(x[1:ndim+1], dtype=int)
        x = np.reshape(x[ndim+1:], shape, order='F')
        return x
    else:
        print("utils.load_txt error: file not found: " + filename)
        return np.ndarray([])


def save_txt(filename, x, fmt='%.8f'):
    y = np.asarray(x)
    data = np.concatenate(([y.ndim], y.shape, y.reshape(np.product(y.shape), order='F')))
    with open(filename, 'wb') as f:
        np.savetxt(f, data, fmt=fmt)


def save_txt2(filename, x, fmt='%.8f'):
    y = np.asarray(x)
    data = np.concatenate(([y.ndim], y.shape, y.reshape(np.product(y.shape))))
    with open(filename, 'wb') as f:
        np.savetxt(f, data, fmt=fmt)


def normalize(x):
    sum_x = np.sum(x)
    return np.asarray(x) / sum_x


def normalize_exp(x):
    return normalize(np.exp(x - np.max(x)))


def log_sum_exp(x):
    max_x = np.max(x)
    return max_x + np.log(np.sum(np.exp(x-max_x)))


def psi(x):
    return sp.digamma(x)


def inv_psi(y):
    x = (np.exp(y) + 0.5) * (y > -2.22) + (-1 / (y + 0.577215)) * (y <= -2.22)
    for i in range(5):
        x = x - ((sp.digamma(x) - y) / sp.polygamma(1, x))
    return x


def gammaln(x):
    return sp.gammaln(x)
