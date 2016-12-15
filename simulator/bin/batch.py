''' 
This study is a Bogazici University - NETAS Nova V-Gate collaboration and funded by TEYDEB project "Realization of Anomaly Detection and Prevention with Learning System Architectures, Quality Improvement, High Rate Service Availability and Rich Services in a VoIP Firewall Product'', by the Scientific and Technological Research Council Of Turkey (TUBITAK).
'''

__author__ = 'cagatay'

import heapq
import numpy as np
import time
from multiprocessing import Process
from time import sleep
from model import Model

import pjsua as pj

from user import User, UserAccountCallback


def log_cb(level, str, len):
    """Callback function for printing statements to the console, used by PJSIP
    Currently, it is configured to print nothing.
    """
    pass


class Batch(Process):
    """This class extends the built-in Process class.
    It contains a C{PJSUA} library that is used to generate SIP traffic.

    There should be no instance of this class but classes that are responsible for the realization of the simulation,
    such as L{TrafficGeneratingBatch} and L{AttackGeneratingBatch}, must extend this class.

    """
    def __init__(self, batch_id, uids, server_ip, num_users, num_users_per_batch, base_id=10000):
        """Default initializer

        @type batch_id:             int
        @param batch_id:            the id of this batch
        @type uids:                 list
        @param uids:                ids of the users to be registered to this batch
        @type server_ip:            str
        @param server_ip:           the IP address of the SIP server to which users are registered
        @type num_users:            int
        @param num_users:           number of users in the simulation
        @type num_users_per_batch:  int
        @param num_users_per_batch: number of users in a batch
        @type base_id:              int
        @param base_id:             the offset of user ids
        """
        super(Batch, self).__init__()
        self.id = batch_id
        self.uids = uids
        self.lib = None
        self.users = []
        self.SIP_SERVER_IP = server_ip
        self.PASSWORD = "tamtam"
        self.BASE_ID = base_id
        self.NUM_USERS = num_users
        self.NUM_USERS_PER_BATCH = num_users_per_batch

    def init_lib(self):
        """Initiates and start a PJSUA library
        """
        try:
            self.lib = pj.Lib()
            self.lib.init(log_cfg = pj.LogConfig(level=0, callback=log_cb))
            self.lib.set_null_snd_dev()
            self.lib.start()
            # for user in self.users: print "new user @ batch:",self.id, ", user_id:", user
        except pj.Error, e:
            print "Exception while initiating pj.Lib()", str(e)

    def reg_user(self,user):
        """ Registers a L{User} instance in this batch to the SIP server.
        At the beginning of the simulation, users stay unregistered for some amount of time
        and this function is called when the register event is triggered.

        Along with registration, a C{PJSUA.Account} instance is attached to the user and a
        L{UserAccountCallback} instance is set to the C{Account}.

        @type   user:   User
        @param  user:   the user instance to be registered
        """
        try:
            uname = user.id + self.BASE_ID
            trans = self.lib.create_transport(pj.TransportType.UDP,
                                              pj.TransportConfig(uname))
            conf = pj.AccountConfig(self.SIP_SERVER_IP,
                                    str(uname), self.PASSWORD)
            conf.reg_timeout = user.registration_period
            conf.ka_interval = 0
            conf.transport_id = trans._id
            acc = self.lib.create_account(conf)
            user.account = acc
            acc_cb = UserAccountCallback(user)
            acc.set_callback(acc_cb)
        except Exception, e:
            print "Exception while registering user:", str(e)

    def init_users(self):
        """Creates all the users in the batch
        """
        for uid in self.uids:
            self.users.append(User(uid,self))

    def run(self):
        """Must be overriden by child classes to that simulation starts
        """
        pass


class TrafficGeneratingBatch(Batch):
    """This class is responsible for the network traffic generation.
    It extends L{Batch} class and therefore, one C{PJSUA} library is inherently attached to this class.

    The traffic generation is event-driven. A global min-heap stores all events and their timestamp.
    When it is the time, the first event, or the earliest one, is popped from the heap and executed.
    After the execution, this batch sleeps until the occurrence time of the next event is reached.
    """

    def __init__(self, batch_id, uids, model, server_ip, num_users, num_users_per_batch, base_id=10000, sim_duration=1e6, verbose=False):
        """Constructor

        @type   batch_id:               int
        @param  batch_id:               the id of the batch
        @type   uids:                   list
        @param  uids:                   ids of the users to be registered to this batch
        @type   model:                  Model
        @param  model:                  the L{Model} instance containing functions for parameter generation
        @type   server_ip:              str
        @param  server_ip:              the IP address of the SIP server to which users are registered
        @type   num_users:              int
        @param  num_users:              number of users in the simulation
        @type   num_users_per_batch:    int
        @param  num_users_per_batch:    number of users in a batch
        @type   base_id:                int
        @param  base_id:                the offset of user ids
        @type   sim_duration:           int
        @param  sim_duration:           simulation durations in seconds
        @type   verbose:                bool
        @param  verbose:              enerating  simulation logs are printed if true
        """
        super(TrafficGeneratingBatch, self).__init__(batch_id, uids, server_ip, num_users, num_users_per_batch, base_id)
        self.model = model
        self.events = []                        # event heap
        self.t = 0                              # time spent since the beginning of the simulation
        self.verbose = verbose
        self.SIMULATION_DURATION = sim_duration # in secs
        self.EVENT_TYPE_DICT = {"Terminate":-1,"Register":0, "Call":1, "Hangup":2}
        self.TICK_DURATION = 1                  # in secs

    def set_user_params(self):
        """Generates user parameters
        """
        self.model.gen_user_params(self.users)

    def init_reg_events(self):
        """Inits events for the first registration of the users
        """
        for curr_user in self.users:
            wait_time = curr_user.initial_unregistered_duration
            event = [wait_time,self.EVENT_TYPE_DICT["Register"], curr_user.id]
            heapq.heappush(self.events,event)

    def init_terminating_event(self):
        """Inits an event that signals the termination of the simulation
        """
        heapq.heappush(self.events, [self.SIMULATION_DURATION,self.EVENT_TYPE_DICT["Terminate"]])

    def init_call_from_callcallback(self,user):
        """Inits a new call event from a callback, given a L{User} instance.
        The occurrence time of the event depends on the user parameters

        @type   user:   User
        @param  user:   the L{User} instance whose next call event is to be generated
        """
        self.init_call_event(user)

    def init_call_event(self,user):
        """Inits a new call event, given a L{User} instance.
        The occurrence time of the event depends on the user parameters

        @type   user:   User
        @param  user:   the L{User} instance whose next call event is to be generated
        """
        wait_time = user.wait_time
        time_to_call = self.model.gen_wait_time_with_rate(wait_time)
        event = [self.t+time_to_call,self.EVENT_TYPE_DICT["Call"], user.id]
        heapq.heappush(self.events,event)

    def init_hangup_event(self, call_duration, user_id, other_party_id):
        """Inits a hangup event for a conversation.

        @type   call_duration:  float
        @param  call_duration:  the amount of time caller(a L{User} instance) of this function plans to spend on the phone
        @type   user_id:        int
        @param  user_id:        the id of the caller of this function
        @type   other_party_id: int
        @param  other_party_id: the id of the other user who is involved in a conversation with the caller of this function
        """
        event = [self.t+call_duration, self.EVENT_TYPE_DICT["Hangup"], user_id,other_party_id]
        heapq.heappush(self.events,event)

    def run(self):
        """Sets up the library and the parameters, adds events to the heap, and runs the simulation.
        The simulation is executed until terminating event is handled.

        If the next event takes place within C{self.TICK_DURATION} seconds, process sleeps until the event time.
        Otherwise, it sleeps for C{self.TICK_DURATION} seconds, wakes up, checks the first event in the heap
        and sleeps again depending on the time of the next event.
        """

        self.init_lib()
        self.init_users()
        self.set_user_params()
        self.init_reg_events()
        self.init_terminating_event()


        # main simulation loop
        while self.events:
            current_event = heapq.heappop(self.events)
            current_event_time = current_event[0]
            event_type = current_event[1]
            t_jump = current_event_time - self.t

            # if event occurs in within TICK_DURATION seconds, sleep for TICK_DURATION secs
            if t_jump > self.TICK_DURATION:
                heapq.heappush(self.events,current_event)
                self.t += self.TICK_DURATION
                sleep(self.TICK_DURATION)
            # else, sleep until the event and then process the event
            else:
                self.t = current_event_time
                sleep(t_jump)

                if event_type == self.EVENT_TYPE_DICT["Terminate"]:
                    if self.verbose: print "Terminate message received. This batch will be killed. Good bye."
                    break

                elif event_type == self.EVENT_TYPE_DICT["Register"]:
                    user_id = int(current_event[2])
                    user_batch_id = np.mod(user_id, self.NUM_USERS_PER_BATCH)
                    user = self.users[user_batch_id]
                    self.reg_user(user)
                    if self.verbose:
                        print int(current_event[2]), "is registered"
                    self.init_call_event(user)

                elif event_type == self.EVENT_TYPE_DICT["Call"]:
                    caller_id = int(current_event[2])
                    caller_batch_id = np.mod(caller_id, self.NUM_USERS_PER_BATCH)
                    caller = self.users[caller_batch_id]
                    callee_id = self.model.pick_callee(caller)
                    callee_sip_uri = "sip:"+str(self.BASE_ID+callee_id)+"@"+self.SIP_SERVER_IP

                    # if the user is available, make the call and the number of calls s/he currently has is less than 4
                    # the second condition is because of PJSUA's implementation (PJSUA_MAX_CALLS = 4)
                    if caller.status == caller.STATUS_DICT["Available"] and len(caller.calls) < pj.UAConfig.max_calls:
                        caller.make_call(callee_sip_uri)
                    # otherwise, add a new call event
                    else:
                        self.init_call_event(caller)

                elif event_type == self.EVENT_TYPE_DICT["Hangup"]:
                    this_user_id = int(current_event[2])
                    this_user_batch_id = np.mod(this_user_id, self.NUM_USERS_PER_BATCH)
                    this_user = self.users[this_user_batch_id]
                    other_party_id = int(current_event[3])

                    # find the event in the call list and hangup
                    hangup_completed = False
                    for _call in this_user.calls:
                        _other_party_id = this_user.extract_other_party_id(_call)
                        if other_party_id == _other_party_id:
                            this_user.hangup(_call)
                            hangup_completed = True
                            break

        self.lib.destroy()
        if self.verbose: print 'batch with id %d quits' % self.id


class AttackGeneratingBatch(Batch):
    """This class is responsible for the attack generation. The implementation has just started.
    """

    def __init__(self, batch_id, uids, server_ip, num_users, num_users_per_batch, base_id=10000, _type=None, _rate=10):
        super(AttackGeneratingBatch, self).__init__(batch_id, uids, server_ip, num_users, num_users_per_batch, base_id)
        self.type = _type
        self.rate = _rate

    def reg_attack(self):
        trans = {}
        for user in self.users:
            uname = user.id + self.BASE_ID
            trans[user.id] = self.lib.create_transport(pj.TransportType.UDP, pj.TransportConfig(uname))
        while True:
            for user in self.users:
                try:
                    uname = user.id + self.BASE_ID
                    conf = pj.AccountConfig(self.SIP_SERVER_IP, str(uname), self.PASSWORD)
                    conf.transport_id = trans[user.id]._id
                    acc = self.lib.create_account(conf)
                    acc.delete()
                except Exception, e:
                    print "Exception while registering user:", str(e)

            time.sleep(3)

    def register_all(self):
        trans = {}
        accs = []
        for user in self.users:
            uname = user.id + self.BASE_ID
            trans[user.id] = self.lib.create_transport(pj.TransportType.UDP, pj.TransportConfig(uname))
            uname = user.id + self.BASE_ID
            conf = pj.AccountConfig(self.SIP_SERVER_IP, str(uname), self.PASSWORD)
            conf.reg_timeout = 1000000
            conf.ka_interval = 0
            conf.transport_id = trans[user.id]._id
            accs.append(self.lib.create_account(conf))
        return trans, accs

    def inv_attack(self):
        trans, accs = self.register_all()
        time.sleep(3)
        while True:
            for acc in accs:
                rnd_id = np.random.randint(low=20000, high=30000)
                sip_uri = "sip:"+str(rnd_id)+"@"+self.SIP_SERVER_IP  # sip:10178@79.123.176.85
                call = acc.make_call(sip_uri)
                if call: call.hangup()
            time.sleep(3)

    def subs_attack(self):
        trans, accs = self.register_all()
        time.sleep(3)
        while True:
            for acc in accs:
                rnd_id = np.random.randint(low=20000, high=30000)
                sip_uri = "sip:" + str(rnd_id) + "@" + self.SIP_SERVER_IP  # sip:10178@79.123.176.85
                buddy = acc.add_buddy(sip_uri)
                buddy.subscribe()
            time.sleep(3)

    def run(self):
        self.init_lib()
        self.init_users()

        if self.type == 'reg':
            self.reg_attack()
        elif self.type == 'inv':
            self.inv_attack()
        elif self.type == 'subs':
            self.subs_attack()

        self.lib.destroy()
        print 'batch with id %d quits' % self.id