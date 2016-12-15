''' 
This study is a Bogazici University - NETAS Nova V-Gate collaboration and funded by TEYDEB project "Realization of Anomaly Detection and Prevention with Learning System Architectures, Quality Improvement, High Rate Service Availability and Rich Services in a VoIP Firewall Product'', by the Scientific and Technological Research Council Of Turkey (TUBITAK).
'''

import copy
import numpy as np
import utils
import heapq


class Potential:
    def __init__(self, alpha=(), a=(), b=(), log_c=0):
        self.alpha = np.asarray(alpha, dtype=float)
        self.a = np.asarray(a, dtype=float)
        self.b = np.asarray(b, dtype=float)
        self.log_c = log_c

    def __lt__(self, other):
        return self.log_c < other.log_c

    def __gt__(self, other):
        return self.log_c > other.log_c

    def __mul__(self, other):
        p = copy.deepcopy(self)
        p.log_c += other.log_c
        # Multiply Dirichlet component
        if len(self.alpha) > 0:
            p.alpha = self.alpha + other.alpha - 1
            p.log_c += utils.gammaln(np.sum(self.alpha)) - np.sum(utils.gammaln(self.alpha))
            p.log_c += utils.gammaln(np.sum(other.alpha)) - np.sum(utils.gammaln(other.alpha))
            p.log_c += np.sum(utils.gammaln(p.alpha)) - utils.gammaln(np.sum(p.alpha))
        # Multiply Gamma components
        if len(self.a) > 0:
            p.a = self.a + other.a - 1
            p.b = (self.b * other.b) / (self.b + other.b)
            p.log_c += np.sum(utils.gammaln(p.a) + p.a * np.log(p.b))
            p.log_c -= np.sum(utils.gammaln(self.a) + self.a * np.log(self.b))
            p.log_c -= np.sum(utils.gammaln(other.a) + other.a * np.log(other.b))
        return p

    def __str__(self):
        np.set_printoptions(precision=3)
        buffer = np.concatenate((self.alpha, self.a, self.b, [self.log_c]))
        return str(buffer)

    @classmethod
    def default(cls, m, n):
        return cls(np.ones(m), np.ones(n) * 10, np.ones(n), 0)

    @classmethod
    def from_observation(cls, obs, m, n):
        p = cls()
        if m > 0:
            sum_obs = np.sum(obs[0:m])
            p.log_c = utils.gammaln(sum_obs+1) - utils.gammaln(sum_obs+m)
            p.alpha = np.asarray(obs[0:m]) + 1
        if n > 0:
            p.a = np.asarray(obs[m:]) +1
            p.b = np.ones(n)
        return p

    def size(self):
        return self.alpha.size + self.a.size

    def copy(self):
        return copy.deepcopy(self)

    def rand(self):
        x = np.ndarray(0)
        if len(self.alpha) > 0:
            x = np.random.dirichlet(self.alpha)
        if len(self.a) > 0:
            x = np.concatenate((x, np.random.gamma(self.a, self.b, self.a.shape)))
        return x

    def mean(self):
        m = np.ndarray(0)
        if len(self.alpha) > 0:
            m = utils.normalize(self.alpha)
        if len(self.a) > 0:
            m = np.concatenate((m, self.a * self.b))
        return m

    def get_ss(self):
        ss = np.ndarray(0)
        if len(self.alpha) > 0:
            ss = utils.psi(self.alpha) - utils.psi(np.sum(self.alpha))
        if len(self.a) > 0:
            ss = np.concatenate((ss, self.a * self.b, utils.psi(self.a) + np.log(self.b)))
        return ss

    def fit(self, ss):
        m = len(self.alpha)
        n = len(self.a)
        if m > 0:
            self.alpha = utils.fit_dirichlet_from_ss(ss[0:m])
        for i in range(n):
            [self.a[i], self.b[i]] = utils.fit_gamma_from_ss([ss[m+i], ss[m+i+n]])


class Message:

    def __init__(self, max_k=100):
        self.potentials = []  # potentials
        self.h = []           # heap for fast pruning
        self.max_k = max_k    # max capacity

    def __mul__(self, other):
        message = Message()
        for p1 in self.potentials:
            for p2 in other.potentials:
                message.potentials.append(p1 * p2)
        return message

    def __len__(self):
        return len(self.potentials)

    def add_potential(self, p):
        k = len(self.potentials)
        if k == self.max_k:
            k = heapq.heappop(self.h)[1]
            self.potentials[k] = p
        else:
            self.potentials.append(p)
        if k > 0:
            # push no-change message to heap
            heapq.heappush(self.h, (p.log_c, k))

    # p(potential)
    def pp(self):
        return utils.normalize_exp(self.log_c())

    # first k potentials belong to change probabilities
    def cpp(self, k=1):
        return np.sum(self.pp()[:k])

    def log_likelihood(self):
        return utils.log_sum_exp(self.log_c())

    def log_c(self):
        return np.asarray([p.log_c for p in self.potentials])

    def mean(self):
        m = np.asarray([p.mean() for p in self.potentials])
        return np.dot(m.transpose(), self.pp())

    def get_ss(self):
        ss = np.asarray([p.get_ss() for p in self.potentials])
        return np.dot(ss.transpose(), self.pp())
