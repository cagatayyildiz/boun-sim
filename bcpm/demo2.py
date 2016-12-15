''' 
This study is a Bogazici University - NETAS Nova V-Gate collaboration and funded by TEYDEB project "Realization of Anomaly Detection and Prevention with Learning System Architectures, Quality Improvement, High Rate Service Availability and Rich Services in a VoIP Firewall Product'', by the Scientific and Technological Research Council Of Turkey (TUBITAK).
'''

import sys

from model import Data, Model


def experiment(data_dir):
    data = Data.load(data_dir)
    data.v = data.v[:, sum(data.v > 0) > 0]

    model = Model.default_model(1e-5, data.v.shape[1], 0)

    print('filtering...')
    result = model.filter(data.v)
    result.evaluate(data.s)
    print('\tF-score : ' + str(result.score))

    print('smoothing...')
    result = model.smooth(data.v)
    result.evaluate(data.s)
    print('\tF-score : ' + str(result.score))

    print('online smoothing...')
    result = model.online_smooth(data.v, lag=10)
    result.evaluate(data.s)
    print('\tF-score : ' + str(result.score))


if __name__ == '__main__':
    experiment(sys.argv[1])

