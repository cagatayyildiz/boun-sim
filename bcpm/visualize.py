''' 
This study is a Bogazici University - NETAS Nova V-Gate collaboration and funded by TEYDEB project "Realization of Anomaly Detection and Prevention with Learning System Architectures, Quality Improvement, High Rate Service Availability and Rich Services in a VoIP Firewall Product'', by the Scientific and Technological Research Council Of Turkey (TUBITAK).
'''

import matplotlib.pyplot as plt
from matplotlib import gridspec
import numpy as np
import sys

from model import Data


def visualize_data(dirname, m, n):
    data = Data.load(dirname)
    v = data.v.transpose()
    t = v.shape[1]
    print(t)
    if m > 0:
        fig = plt.figure(figsize=(12, 4))
        ax = fig.gca()
        ax.pcolormesh(v[0:m, :], cmap=plt.cm.Greys)
        ax.vlines(np.arange(0, t), 0, data.s * m, colors='r', linestyles='-', linewidth=2)
        ax.legend(['change points'])
    if n > 0:
        fig = plt.figure(figsize=(12, 4))
        gs = gridspec.GridSpec(n, 1, height_ratios=np.ones(n))
        for i in range(n):
            ax = plt.subplot(gs[i])
            y = v[m + i, :]
            y_lim_max = np.max(y) * 1.1
            ax.plot(range(t), y, 'b-')
            ax.vlines(np.arange(0, t), 0, data.s * y_lim_max, colors='r', linestyles='-', linewidth=2)
            ax.set_ylim([0, y_lim_max])
    plt.show()

if __name__ == '__main__':
    visualize_data(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
