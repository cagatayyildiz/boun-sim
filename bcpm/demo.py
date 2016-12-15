''' 
This study is a Bogazici University - NETAS Nova V-Gate collaboration and funded by TEYDEB project "Realization of Anomaly Detection and Prevention with Learning System Architectures, Quality Improvement, High Rate Service Availability and Rich Services in a VoIP Firewall Product'', by the Scientific and Technological Research Council Of Turkey (TUBITAK).
'''

from utils import find_or_create
from model import Data, Model
from visualize import visualize_data

work_dir = '/tmp/demo'


def experiment():

    # Generate Model
    t = 200
    p1 = 0.01
    m = 4
    n = 3
    model = Model.default_model(p1, m, n)
    model.save(work_dir + '/model.txt')

    # Generate Data
    data = model.generate_data(t)
    data.save(work_dir + '/data')

    # Change Point Estimations
    print('filtering...')
    result = model.filter(data.v)
    result.evaluate(data.s)
    result.save(work_dir + '/filtering')
    print('\tF-score : ' + str(result.score))

    print('smoothing...')
    result = model.smooth(data.v)
    result.evaluate(data.s)
    result.save(work_dir + '/smoothing')
    print('\tF-score : ' + str(result.score))

    print('online smoothing...')
    result = model.online_smooth(data.v, lag=10)
    result.evaluate(data.s)
    result.save(work_dir + '/online_smoothing')
    print('\tF-score : ' + str(result.score))

    # Visualization
    visualize_data(work_dir + '/data', m, n)

    print('done.')


if __name__ == '__main__':
    find_or_create(work_dir)
    experiment()

