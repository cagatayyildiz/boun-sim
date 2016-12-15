''' 
This study is a Bogazici University - NETAS Nova V-Gate collaboration and funded by TEYDEB project "Realization of Anomaly Detection and Prevention with Learning System Architectures, Quality Improvement, High Rate Service Availability and Rich Services in a VoIP Firewall Product'', by the Scientific and Technological Research Council Of Turkey (TUBITAK).
'''

import re
import threading
import time
import multiprocessing

import pjsua as pj


class User:
    """This class implements the behaviors of a user in real life.
    User parameters are set by L{Model} and user states change in real-time based on actions performed.

    Many of the methods are just wrappers for simplifying the calls made to functions in L{Batch}.

    """

    def __init__(self, id, process):
        self.id = id                                # this user's id
        self.wait_time = 0                          # the parameter that controls the wait time bw calls
        self.average_conv_duration = 0              # average conversation duration
        self.answering_prob = 0                     # answering vs rejecting
        self.registration_period = 300              # the duration (in secs) spent between two registration requests
        self.initial_unregistered_duration = 0      # the time spent bw the start of the simulation and first reg. request
        self.phone_book = []                        # this user's phone book
        self.account = None                         # this user's account
        self.calls = []                             # list of active and held calls
        self.batch = process                      # the process in which this instance is created
        self.STATUS_DICT = {"Available": 1, "Connecting": 2, "Busy": 3}
        self.CALL_RESPONSE_DICT = {"ACCEPT": 1, "REJECT": 2, "BUSY": 3}
        self.status = self.STATUS_DICT["Available"]
        self.sem = multiprocessing.Semaphore(1)

    def __str__(self):
        return 'id: %d' % (self.id)

    def __repr__(self):
        return self.__str__()

    def extract_other_party_id_from_call_uri(self, remote_uri):
        '''Extracts the id of the other party in a call

        @type   remote_uri: str
        @param  remote_uri: the uri that belongs to other party of a call

        @rtype:             int
        @return:            id of the other party of a call
        '''
        pattern = '^.*:(.*)@.*$'
        match = re.search(pattern, remote_uri)
        caller_id = int(match.group(1)) - self.batch.BASE_ID
        return caller_id

    def extract_other_party_id(self, call):
        '''Extracts the id of the other party in a call

        @type   call: pjsua.Call instance
        @param  call: the call instance whose second party is aimed to extracted

        @rtype:             int
        @return:            id of the other party of a call; None, if the call is invalid or None
        '''
        '''
        if call and call.is_valid() and isinstance(call, pj.Call):
            return self.extract_other_party_id_from_call_uri(call.info().remote_uri)
        else:
            return None
        '''
        return self.extract_other_party_id_from_call_uri(call.info().remote_uri)

    def make_call(self, uri):
        '''Makes a call to the user whose SIP uri is given as the parameter

        @type   uri:    str
        @param  uri:    the uri of the callee

        @rtype:         Call instance or None
        @return:        Call instance of the call that is just initiated or None (in case of a thrown exception from
                        C{PJSUA} library
        '''
        self.sem.acquire(block=True, timeout=None)
        call = None
        try:
            assert(self.status == self.STATUS_DICT["Available"])
            other_id = self.extract_other_party_id_from_call_uri(uri)
            if self.batch.verbose: print self.id, "called", other_id
            call = self.account.make_call(uri, cb=UserCallCallback(self))
        except pj.Error, e:
            print "Exception in User.make_call(): " + str(e)
        finally:
            self.sem.release()
        return call

    def hangup(self, call):
        '''Hangs up a call and prints the error in case of an exception

        @type   call:   C{PJSUA.Call} instance
        @param  call:   the call instance to be hung up
        '''
        self.sem.acquire(block=True, timeout=None)
        try:
            call.hangup()
        except pj.Error, e:
            print "Exception while", self.id, "hanging up:", str(e)
        finally:
            self.sem.release()

    def answer(self, call, code, reason=""):
        '''Hangs up a call and prints the error in case of an exception

        @type   call:   C{PJSUA.Call} instance
        @param  call:   the call instance to be hung up
        @type   code:   int
        @param  code:   code of the reply to the call (e.g. 180, 200)
        @type   reason: str
        @param  reason: message to be attached to the answer
        '''
        self.sem.acquire(block=True, timeout=None)
        try:
            call.answer(code=code, reason=reason)
        except pj.Error, e:
            print "Error while", self.id,  "answering a call with the code", code,":", str(e)
        finally:
            self.sem.release()

    def gen_response_to_a_call(self, caller_id):
        '''Generates a response to a call depending on the user's features and the caller id

        @type   caller_id:  int
        @param  caller_id:  id of the caller

        @rtype:             int
        @return:            the response to the call (a value in C{CALL_RESPONSE_DICT})
        '''
        return self.batch.model.gen_response_to_call(self, caller_id)

    def gen_call_duration(self, rate):
        '''Generates the amount of time this user wants to spend on the phone.
        The exact value depends on the implementation in the L{Model}.
        Note that the duration of the call is the minimum of the call durations generated by both parties of the conversation.

        @type   rate:   float
        @param  rate:   the rate of the distribution

        @rtype:         float
        @return:        the amount of time this user wants to spend on the phone
        '''
        return self.batch.model.gen_call_duration(rate)

    def init_hangup_event(self, call_duration, other_party_id):
        '''Inits a hangup event and adds it to the event heap.

        @type   call_duration:  float
        @param  call_duration:  this user's call duration preference
        @type   other_party_id: int
        @param  other_party_id: id of the other party in the call
        '''
        self.batch.init_hangup_event(call_duration, self.id, other_party_id)

    def init_call_from_callcallback(self):
        '''Inits a call and adds it to the event heap. This function is called only from the L{UserCallCallback}.
        '''
        self.batch.init_call_from_callcallback(self)


class UserAccountCallback(pj.AccountCallback):
    '''This class is responsible for receiving and responding the changes in the account status.

    C{PJSUA}'s implementation requires setting an C{AccountCallback} instance to each C{Account}.
    See that there is a circular reference between this class, C{Account} and L{User}:
    Each L{User} instance C{U} has an C{Account} field C{A}, to which an instance of C{AccountCallback}, say C{AC},
    is attached. What brings circular reference is that C{AC} has a pointer to C{U}.
    '''
    sem = None

    def __init__(self, user):
        '''Constructor

        @type   user:   L{User}
        @param  user:   the user whose account is attached by this L{UserAccountCallback} instance
        '''
        pj.AccountCallback.__init__(self, user.account)
        self.user = user

    def wait(self):
        '''Waits until acquiring semaphore
        '''
        self.sem = threading.Semaphore(0)
        self.sem.acquire()

    def on_reg_state(self):
        '''The callback function called whenever registration status changes
        '''
        if self.sem:
            if self.account.info().reg_status >= 200:
                self.sem.release()

    def on_incoming_call(self, call):
        '''Receives a notification on incoming call.
        Response to the call is decided by the model but the action (network packet generation) takes place here.

        @type   call:   C{PJSUA.Call} instance
        @param  call:   the call instance that has been received

        @rtype:         int
        @return:        the response to the call (a value in L{User}.C{CALL_RESPONSE_DICT})
        '''
        try:
            # call.info().remote_uri returns a string like this: "user10000" <sip:10000@79.123.177.226>
            # to extract caller_id info, use the following pattern
            caller_id = self.user.extract_other_party_id_from_call_uri(call.info().remote_uri)
            call_cb = UserCallCallback(self.user, call)
            call.set_callback(call_cb)

            try:
                # as PJSUA_MAX_CALLS = 4 by default, a user cannot have more than 3 calls (1 reserved for calls to be rejected)
                if len(self.user.calls) >= pj.UAConfig.max_calls-1:
                    response = self.user.CALL_RESPONSE_DICT["REJECT"]
                    self.user.hangup(call)
                    # if self.user.batch.verbose: print self.user.id, "rejected", caller_id, "at", time.time()
                    return response

                response = self.user.gen_response_to_a_call(caller_id)
                # call transferring has not been tested yet
                '''
                transfer_uri = "sip:"+str(BASE_ID+who_to_transfer)+"@"+TRIXBOX_IP_ADDRESS
                print "forwarded to ", transfer_uri
                call.transfer(transfer_uri)
                '''
                if response == self.user.CALL_RESPONSE_DICT["ACCEPT"]:
                    assert(self.user.status == self.user.STATUS_DICT["Available"])
                    self.user.answer(call, 180)
                    self.user.answer(call, 200)
                    if self.user.batch.verbose: print self.user.id, "accepted", caller_id

                elif response == self.user.CALL_RESPONSE_DICT["REJECT"]:
                    self.user.hangup(call)
                    if self.user.batch.verbose: print self.user.id, "rejected", caller_id

                elif response == self.user.CALL_RESPONSE_DICT["BUSY"]:
                    assert(self.user.status != self.user.STATUS_DICT["Available"])
                    self.user.answer(call, 486, "Busy")
                    if self.user.batch.verbose: print self.user.id, "busied", caller_id

                return response

            finally:
                pass

        except pj.Error, e:
            print "Exception during parsing call.info().remote_uri: " + str(e)




class UserCallCallback(pj.CallCallback):
    """Changes in a call trigger functions in this class. Depending on the change, user status or fields are updated.
    """

    def __init__(self, user, call=None):
        '''Constructor
        @type   user:   L{User}
        @param  user:   one party of the call
        @type   call:   C{PJSUA.Call} instance
        @param  call:   the call instance to which this callcallaback instance is attached
        '''
        pj.CallCallback.__init__(self, call)
        self.user = user

    def on_state(self):
        """
        Notification when call state has changed

        Note:
        NULL            -- call is not initialized.
        CALLING         -- initial INVITE is sent.
        INCOMING        -- initial INVITE is received.
        EARLY           -- provisional response has been sent or received.
        CONNECTING      -- 200/OK response has been sent or received.
        CONFIRMED       -- ACK has been sent or received.
        DISCONNECTED    -- call is disconnected.
        """

        if self.call.info().state == pj.CallState.CONNECTING:
            self.user.status = self.user.STATUS_DICT["Connecting"]

        if self.call.info().state == pj.CallState.CONFIRMED:
            other_party_id = self.user.extract_other_party_id(self.call)
            self.user.status = self.user.STATUS_DICT["Busy"]
            if self.user.batch.verbose: print self.user.id, "-", other_party_id, "confirmed"
            self.user.calls.append(self.call)
            rate = self.user.average_conv_duration
            call_duration = self.user.gen_call_duration(rate)
            self.user.init_hangup_event(call_duration, other_party_id)

        elif self.call.info().state == pj.CallState.DISCONNECTED:
            # self.call belongs to a call where this user once accepted
            caller_id = self.user.extract_other_party_id(self.call)
            if self.user.batch.verbose:
                print self.user.id, "-", caller_id, "disconnected", "with code", self.call.info().last_code, "and call duration is", self.call.info().call_time, "seconds"

            if self.call in self.user.calls:
                # get rid of calls that are terminated
                confirmed_calls = [_call for _call in self.user.calls if isinstance(_call, pj.Call) and _call.is_valid() and _call.info().state == pj.CallState.CONFIRMED]
                self.user.calls = confirmed_calls
                self.user.status = self.user.STATUS_DICT["Available"]
                self.user.init_call_from_callcallback()

            # the user either rejected or busied this call WITHOUT connection is established
            else:
                print "self.user.status:", self.user.status
                pass




    def on_media_state(self):
        '''Notification when call's media state has changed. Currently empty
        '''
        # print self.user.id,", media_state:", self.call.info().media_state
        pass
