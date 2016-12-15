''' 
This study is a Bogazici University - NETAS Nova V-Gate collaboration and funded by TEYDEB project "Realization of Anomaly Detection and Prevention with Learning System Architectures, Quality Improvement, High Rate Service Availability and Rich Services in a VoIP Firewall Product'', by the Scientific and Technological Research Council Of Turkey (TUBITAK).
'''

__author__ = 'cagatay'

import numpy as np
import sklearn.preprocessing as pre

from xml.dom import minidom


class CallGraph:
    '''This class generates a the call probabilities between users based on
    the stochastic block model.
    '''

    def __init__(self, num_users, num_groups):
        '''initializes a model

        @type   num_users:  int
        @param  num_users:  number of users registered to SIP server
        @type   num_groups:  int
        @param  num_groups: number of blocks in the stochastic block model
        '''
        self.num_users = num_users
        self.num_groups = num_groups

        # group probabilities
        self.pi = np.random.dirichlet(np.ones(self.num_groups))

        # group assignments
        self.G = np.zeros((self.num_users, self.num_groups), dtype=int)
        self.G[range(self.num_users), np.random.choice(self.num_groups, p=self.pi, size=self.num_users)] = 1

        # Inter-group call probabilities
        a, b = 2, 0.4
        self.B = np.random.beta(b, a, size=(self.num_groups, self.num_groups))
        np.fill_diagonal(self.B, np.random.beta(a, b, size=self.num_groups))

        # Phone Book
        self.PB = self.G.dot(self.B).dot(self.G.transpose())
        np.fill_diagonal(self.PB, 0)
        self.PB = pre.normalize(self.PB, norm='l1', axis=1)


class Model:
    '''This class generates simulation parameters, which is done by filling in fields L{User} instances.
    '''

    def __init__(self, call_graph, seed, traffic_intensity, filename, intensity_list, param_list):
        """Initializes a model
        @type call_graph:           L{CallGraph}
        @param call_graph:          the connectivity layout of SIP users, including phone-books.
        @type seed:                 int
        @param seed:                seed to generate random numbers, which is the same for all L{User} instances
        @type traffic_intensity:    str
        @param traffic_intensity:   a traffic intensity level
        @type filename:             str
        @param filename:            the path to the configuration file
        @type intensity_list:       list
        @param intensity_list:      different traffic intensity levels that can be simulated by the
        @type param_list:           list
        @param param_list:          L{User} parameters to be set by this module
        """

        self.call_graph = call_graph
        self.intensity_list = intensity_list
        self.param_list = param_list
        self.num_users = call_graph.num_users
        self.seed = seed
        self.filename = filename
        self.all_params = self.read_attributes(self.param_list, self.filename, "params", "intensity")
        self.params = self.all_params[traffic_intensity]

    def gen_user_params(self, users):
        '''A wrapper function that calls all functions that set model parameters

        @type   users:  list
        @param  users:  L{User} instances whose fields are to be set
        '''
        np.random.seed(seed=self.seed)
        self.gen_wait_time(users)
        self.gen_average_conv_duration(users)
        self.gen_answering_prob(users)
        self.gen_reg_times(users)
        self.gen_unregistered_duration(users)
        self.gen_phone_book(users)


    def gen_response_to_call(self, user, caller_id):
        """Generates a response to an incoming call depending on user's status.

        @type   user:       L{User} instance
        @param  user:       the user whose response to a call is to be decided
        @type   caller_id:  int
        @param  caller_id:  id of the caller

        @rtype:             int
        @return:            response to the call, must be one of the values in User.STATUS_DICT
        """
        if user.status == user.STATUS_DICT["Available"]:
            if np.random.rand() < user.answering_prob:
                return user.CALL_RESPONSE_DICT["ACCEPT"]
            else:
                return user.CALL_RESPONSE_DICT["REJECT"]
        else:
            return user.CALL_RESPONSE_DICT["BUSY"]

    def gen_wait_time(self, users):
        """Generates parameters for the waiting times between calls

        @type   users:  list
        @param  users:  L{User} instances whose fields are to be set
        """
        shape = self.params['wait_time_shape']
        scale = self.params['wait_time_scale']
        tmp = np.random.gamma(shape, scale, len(users))
        for i in range(len(users)):
            users[i].wait_time = tmp[i]

    def gen_average_conv_duration(self, users):
        '''Generates parameters for the average conversation duration

        @type   users:  list
        @param  users:  L{User} instances whose fields are to be set
        '''
        lower_lim = self.params['aver_conv_dur_lower']
        upper_lim = self.params['aver_conv_dur_upper']
        tmp = lower_lim + np.random.randint(lower_lim, upper_lim, (len(users), 1))
        for i in range(len(users)):
            users[i].average_conv_duration = tmp[i]

    def gen_answering_prob(self, users):
        """Generates parameters for the probability of answering/rejecting a call.

        @type   users:  list
        @param  users:  L{User} instances whose fields are to be set
        """
        tmp = np.random.uniform(self.params['ans_prob_lower'], self.params['ans_prob_upper'], len(users))
        for i in range(len(users)):
            users[i].answering_prob = tmp[i]


    def gen_reg_times(self, users):
        """Generates the durations in which registrations of users will be valid.

        @type   users:  list
        @param  users:  L{User} instances whose fields are to be set
        """
        reg_time_shape, reg_time_scale = self.params['reg_period_shape'], self.params['reg_period_scale']
        tmp = np.round(np.random.gamma(reg_time_shape, reg_time_scale, len(users)))
        for i in range(len(users)):
            users[i].registration_period = tmp[i]

    def gen_unregistered_duration(self, users):
        """Generates parameter that controls how long a user stay unregistered at the beginning of simulation

        @type   users:  list
        @param  users:  L{User} instances whose fields are to be set
        """
        shape, scale = self.params['unreg_dur_shape'], self.params['unreg_dur_scale']  # mean and dispersion
        tmp = np.random.gamma(shape, scale, len(users))
        for i in range(len(users)):
            users[i].initial_unregistered_duration = tmp[i]

    def gen_phone_book(self, users):
        """Generates phone books of users, which controls how likely a user to call some other.
        @type   users:  list
        @param  users:  L{User} instances whose fields are to be set
        """
        for user in users:
            user.phone_book = self.call_graph.PB[user.id, :]

    @staticmethod
    def gen_wait_time_with_rate(wait_time):
        """Given the parameter controlling the amount of time spent between two consecutive calls, generates when the next call will be made.

        @type       wait_time:  float
        @param      wait_time:  the parameter controlling the amount of time spent between two consecutive calls

        @rtype:                 float
        @return:                when the next call will be made
        """
        tmp = 1 + np.random.exponential(wait_time)
        return tmp

    @staticmethod
    def pick_callee(caller):
        """Given a user, picks who to call depending on the missed calls of phone book of this user.

        @type   caller: L{User} instance
        @param  caller: the user whose partner in the upcoming conversation is to be determined

        @rtype:         int
        @return:        the id of the user to be called
        """
        return np.random.choice(len(caller.phone_book), p=caller.phone_book)

    @staticmethod
    def gen_call_duration(lam):
        """Given the parameter controlling how long one likes to talk on the phone, generates the duration of the upcoming conversation.

        @type   lam:    float
        @param  lam:    the parameter controlling the length of a conversation

        @rtype:         float
        @return:        the id of the user to be called
        """
        return 1 + np.random.exponential(lam)


    @staticmethod
    def read_attributes(param_list, filename, xml_element_tag_name="params", xml_attribute="intensity"):
        '''Parses the configuration file and extract model parameters.
        Returns the a dictionary where keys are the attributes, such as low or high,
        and values are the corresponding simulation parameters, which is another dictionary.

        @type   param_list:             list
        @param  param_list:             parameters to be read
        @type   filename:               string
        @param  filename:               path to the configuration file
        @type   xml_element_tag_name:   string
        @param  xml_element_tag_name:   tag names in the xml file
        @type   xml_attribute:          string
        @param  xml_attribute:          an attribute in the xml file

        @rtype:                         dictionary of dictionaries
        @return:                        a dictionary of xml attributes and corresponding data, which is another dictionary.
        '''
        doc = minidom.parse(filename)
        param_sets = doc.getElementsByTagName(xml_element_tag_name)
        dicts = {}
        for params in param_sets:
            dict = {}
            intensity = str(params.getAttribute(xml_attribute))
            dict[xml_attribute] = intensity
            for param in param_list:
                try:
                    data = params.getElementsByTagName(param)[0].firstChild.data
                    dict[param] = float(data)
                except:
                    print param, "is missing in the configuration file."
                    return None
            dicts[intensity] = dict
        return dicts