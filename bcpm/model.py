''' 
This study is a Bogazici University - NETAS Nova V-Gate collaboration and funded by TEYDEB project "Realization of Anomaly Detection and Prevention with Learning System Architectures, Quality Improvement, High Rate Service Availability and Rich Services in a VoIP Firewall Product'', by the Scientific and Technological Research Council Of Turkey (TUBITAK).
'''

import numpy as np
import json
import utils
import os

from message import Potential, Message


class Data:
    def __init__(self, s=(), h=(), v=()):
        self.s = np.asarray(s)
        self.h = np.asarray(h)
        self.v = np.asarray(v)

    def save(self, dirname):
        utils.find_or_create(dirname)
        if self.s.size > 0:
            np.savetxt(dirname + '/cps.txt', self.s, fmt='%d')
        if self.h.size > 0:
            np.savetxt(dirname + '/states.txt', self.h, fmt='%.6f')
        if self.v.size > 0:
            np.savetxt(dirname + '/obs.txt', self.v, fmt='%.6f')

    @classmethod
    def load(cls, dirname):
        data = cls()
        filename = dirname + '/cps.txt'
        if os.path.isfile(filename):
            data.s = np.loadtxt(filename)
        filename = dirname + '/states.txt'
        if os.path.isfile(filename):
            data.h = np.loadtxt(filename)
        filename = dirname + '/obs.txt'
        if os.path.isfile(filename):
            data.v = np.loadtxt(filename)
        return data


class Result:
    def __init__(self):
        self.cpp = []
        self.mean = []
        self.ll = []
        self.score = []

    def save(self, dirname):
        utils.find_or_create(dirname)
        if len(self.mean) > 0:
            np.savetxt(dirname + '/mean.txt', self.mean, fmt='%.6f')
        if len(self.cpp) > 0:
            np.savetxt(dirname + '/cpp.txt', self.cpp, fmt='%.6f')
        if len(self.ll) > 0:
            np.savetxt(dirname + '/ll.txt', self.ll, fmt='%.6f')
        if len(self.score) > 0:
            np.savetxt(dirname + '/score.txt', self.score, fmt='%.6f')

    def evaluate(self, cps, threshold=0.99, window=10):

        x = np.where(cps == 1)[0]
        y = np.where(np.asarray(self.cpp) > threshold)[0]
        true_points = np.zeros(len(x))
        pred_points = np.zeros(len(y))
        for i in range(len(x)):
            for j in range(len(y)):
                if x[i] - y[j] in range(-1, window):
                    true_points[i] = 1
                    pred_points[j] = 1

        true_positives = np.sum(true_points)
        false_positives = len(pred_points) - np.sum(pred_points)
        false_negatives = len(true_points) - np.sum(true_positives)
        self.score = [0]
        if true_positives > 0:
            precision = true_positives / (true_positives + false_positives)
            recall = true_positives / (true_positives + false_negatives)
            self.score = [2 * (precision * recall) / (precision + recall)]


class Model:
    def __init__(self, p1, alpha, a, b):
        self.p1 = None      # prob. of change
        self.log_p1 = None  # log prob. of change
        self.log_p0 = None  # log prob. no change
        self.set_p1(p1)
        self.prior = Potential(alpha, a, b)
        self.m = len(alpha)
        self.n = len(a)

    def set_p1(self, p1):
        self.p1 = p1
        self.log_p1 = np.log(p1)
        self.log_p0 = np.log(1-p1)

    @classmethod
    def load(cls, filename):
        buffer = utils.load_txt(filename)
        p1 = buffer[0]
        m = int(buffer[1])
        n = int(buffer[2])
        alpha = buffer[3:m+3]
        a = buffer[3+m:3+m+n]
        b = buffer[3+m+n:3+m+n+n]
        return cls(p1, alpha, a, b)

    @classmethod
    def default_model(cls, p1, m, n):
        alpha = np.ones(m)
        a = np.ones(n) * 10
        b = np.ones(n)
        return cls(p1, alpha, a, b)

    def save(self, filename):
        buffer = np.concatenate(([self.p1, self.m, self.n], self.prior.alpha, self.prior.a, self.prior.b))
        utils.save_txt(filename, buffer)

    def generate_data(self, t):
        s = np.random.binomial(1, self.p1, t)               # change points
        h = np.zeros((t, self.m + self.n))    # hidden states
        v = np.zeros((t, self.m + self.n))    # observations
        for i in range(t):
            if i == 0 or s[i] == 1:
                # generate random state:
                h[i, :] = self.prior.rand()
            else:
                # copy previous state
                h[i, :] = h[i-1, :]
            # generate observation
            v[i, :] = self.rand_obs(h[i, :])
        return Data(s, h, v)

    def rand_obs(self, state):
        obs = np.asarray([])
        if self.m > 0:
            obs = np.random.multinomial(100, state[0:self.m])
        if self.n > 0:
            obs = np.concatenate((obs, np.random.poisson(state[self.m:])))
        return obs

    def predict(self, alpha):
        m = Message()
        # add change component
        m.add_potential(Potential(self.prior.alpha, self.prior.a, self.prior.b, self.log_p1 + alpha.log_likelihood()))
        # add no-change components
        for p in alpha.potentials:
            m.add_potential(Potential(p.alpha, p.a, p.b, p.log_c + self.log_p0))
        return m

    def update(self, predict, obs):
        m = Message()
        p_obs = Potential.from_observation(obs, self.m, self.n)
        for p in predict.potentials:
            m.add_potential(p * p_obs)
        return m

    def forward(self, obs):
        alpha = []
        alpha_predict = []
        for i in range(obs.shape[0]):
            if i == 0:
                m = Message()
                m.add_potential(Potential(self.prior.alpha, self.prior.a, self.prior.b, self.log_p1))
                m.add_potential(Potential(self.prior.alpha, self.prior.a, self.prior.b, self.log_p0))
                alpha_predict.append(m)
            else:
                alpha_predict.append(self.predict(alpha[-1]))
            alpha.append(self.update(alpha_predict[-1], obs[i, :]))
        return [alpha_predict, alpha]

    def backward(self, obs, start=0, length=0):
        if length == 0:
            length = obs.shape[0]
            start = length-1
        beta = []
        for i in range(start, start - length, -1):
            message = Message()
            # change
            p_obs = Potential.from_observation(obs[i, :], self.m, self.n)
            pot_change = p_obs.copy()
            if len(beta) > 0:
                temp = Message()
                for p in beta[-1].potentials:
                    temp.add_potential(p * self.prior)
                pot_change.log_c += self.log_p1 + temp.log_likelihood()
            message.add_potential(pot_change)
            # no change
            if len(beta) > 0:
                for p in beta[-1].potentials:
                    p2 = p * p_obs
                    p2.log_c += self.log_p0
                    message.add_potential(p2)
            beta.append(message)
        beta.reverse()
        return beta

    def filter(self, obs):
        alpha = self.forward(obs)[1]
        # compile result
        result = Result()
        result.cpp = [message.cpp() for message in alpha]
        result.mean = [message.mean() for message in alpha]
        result.ll = [alpha[-1].log_likelihood()]
        return result

    def smooth(self, obs):
        [alpha_predict, alpha] = self.forward(obs)
        beta = self.backward(obs)
        # compile result
        result = Result()
        for i in range(len(alpha)):
            gamma = alpha_predict[i] * beta[i]
            result.cpp.append(gamma.cpp(len(beta[i].potentials)))
            result.mean.append(gamma.mean())
        result.ll = [alpha[-1].log_likelihood()]
        return result

    def online_smooth(self, obs, lag):
        if lag == 0:
            return self.filter(obs)

        t = obs.shape[0]
        if lag >= t:
            return self.smooth(obs)

        result = Result()
        [alpha_predict, alpha] = self.forward(obs)
        beta = []

        # Run Fixed-Lag for alpha[0:T - lag]
        for i in range(t - lag + 1):
            beta = self.backward(obs, i + lag - 1, lag)
            gamma = alpha_predict[i] * beta[0]
            result.cpp.append(gamma.cpp(len(beta[0])))
            result.mean.append(gamma.mean())

        # Smooth alpha[T-lag+1:T] with last beta.
        for i in range(1, lag):
            gamma = alpha_predict[t - lag + i] * beta[i]
            result.cpp.append(gamma.cpp(len(beta[i])))
            result.mean.append(gamma.mean())

        result.ll = [alpha[-1].log_likelihood()]
        return result


