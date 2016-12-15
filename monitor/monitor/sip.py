''' 
This study is a Bogazici University - NETAS Nova V-Gate collaboration and funded by TEYDEB project "Realization of Anomaly Detection and Prevention with Learning System Architectures, Quality Improvement, High Rate Service Availability and Rich Services in a VoIP Firewall Product'', by the Scientific and Technological Research Council Of Turkey (TUBITAK).
'''

import re


class SIPMessage:

    HEADERS = ('REGISTER', 'INVITE', 'SUBSCRIBE', 'NOTIFY', 'OPTIONS', 'ACK', 'BYE', 'CANCEL',
               'PRACK', 'PUBLISH', 'INFO', 'REFER', 'MESSAGE', 'UPDATE',
               '100', '180', '183', '200', '400', '401', '403', '404', '405', '481', '486', '487', '500', '603')

    def __init__(self, lines, timestamp=None):
        self.timestamp = timestamp
        self.type = None
        self.frm = None
        self.to = None
        self.call_id = None
        self.via_count = 0
        # Initialize
        self.parse(lines)

    def __str__(self):
        return '%.6f : %s -> %s : %s, %d' % (self.timestamp, self.frm, self.to, self.type, self.via_count)

    def parse(self, headers):
        # Mandatory fields: To, From, CSeq, Call-ID, Max-Forwards,and Via
        # These header fields are in addition to the mandatory request line,
        # which contains the method, Request-URI, and SIP version.

        # Part 1: Parse Status Line
        status = headers[0].split()
        if status[0].startswith('SIP'):
            self.type = status[1]
        else:
            self.type = status[0]
        # Part 2: Parse from, to, call_id fields
        fields_to_parse = 3
        for header in headers[1:]:
            temp_results = re.match('^(.+?):(.+?)$', header)
            if temp_results :
                [hdr_name, hdr_data] = temp_results .groups()
                hdr_name = hdr_name.lower()
            if hdr_name == 'from' or hdr_name == 'f':
                temp_results = re.search('sip:(.+?)(>|;|:|$)', hdr_data)
                if temp_results:
                    self.frm = temp_results.group(1).strip()
                    if self.frm.endswith('\r'):
                        print header
                fields_to_parse -= 1
            elif hdr_name == 'to' or hdr_name == 't':
                temp_results = re.search('sip:(.+?)(>|;|:|$)', hdr_data)
                if temp_results:
                    self.to = temp_results.group(1).strip()
                    if self.to.endswith('\r'):
                        print header
                fields_to_parse -= 1
            elif hdr_name == 'call-id' or hdr_name == 'i':
                temp_results = re.search('^(.+?)(@|>|;|:|$)', hdr_data)
                if temp_results:
                    self.call_id = temp_results.group(1).strip()
                fields_to_parse -= 1
            elif hdr_name == 'via' or hdr_name == 'v':
                self.via_count += 1
            if fields_to_parse == 0:
                break

    @staticmethod
    def parse_from_text(payload, timestamp):
        lines = payload.split('\n')
        if 'SIP' not in lines[0]:
            return None
        return SIPMessage(lines, timestamp)


class SIPCall:
    '''Call class contains the information of a call between users.
    It has user ids, call ids and state of the call.
    '''

    # Call States:
    # NULL            -- no packet received yet
    # ERROR           -- something is not right# ERROR           -- something is not right
    # IGNORED         -- Ignore message
    # SETUP           -- INVITE is sent
    # TALKING         -- ACK is received
    # TERMINATED      -- Callee rejected call or call ended peacefully
    # ON_HOLD         -- Callee or Callee put the call on hold
    # REGISTERING     -- Trying to register
    # AUTHORIZED      -- Register Success

    def __init__(self):
        self.state = 'NULL'
        self.caller_id = None
        self.callee_id = None
        self.caller_call_id = None
        self.callee_call_id = None
        self.call_start_time = None
        self.call_end_time = None

    def update(self, sip_message):
        '''updates call state according to message
        :param sip_message: a sip message with body and header
        '''
        if self.state == 'NULL':
            # First SIP packet in this call
            self.caller_id = sip_message.frm
            self.callee_id = sip_message.to
            self.caller_call_id = sip_message.call_id
            self.call_start_time = sip_message.timestamp
            if sip_message.type == 'INVITE':
                self.state = 'SETUP'
            elif sip_message.type == 'REGISTER':
                self.state = 'REGISTERING'
            else:
                self.state = 'IGNORED'
            self.call_end_time = sip_message.timestamp

        elif self.state == 'REGISTERING':
            # REGISTER gets AUTHORIZED
            if sip_message.type == '200':
                self.state = 'AUTHORIZED'
            self.call_end_time = sip_message.timestamp

        elif self.state == 'SETUP':
            # SETUP either gets CONFIRMED or TERMINATED:
            if sip_message.type == 'ACK':
                self.state = 'CONFIRMED'
            elif self.__terminated__(sip_message):
                self.state = 'TERMINATED'
            self.call_end_time = sip_message.timestamp

        elif self.state == 'CONFIRMED':
            # CONFIRMED gets TERMINATED:
            if self.__terminated__(sip_message):
                self.state = 'TERMINATED'
            self.call_end_time = sip_message.timestamp

    @staticmethod
    def __terminated__(sip_message):
        return sip_message.type in ['486', '503', '603', 'BYE']


class SIPNetwork:
    '''
    SIPNetwork records the active users and calls.
    '''
    def __init__(self):
        self.active_users = set()
        self.active_calls = {}

    def add_messages(self, sip_messages):
        '''If multiple new calls are detected, it adds them to the active calls.
        It calls add_message for each call.
        '''
        for message in sip_messages:
            self.add_message(message)

    def add_message(self, sip_message):
        '''If a new call is detected, it adds it to the active calls.
        When a packet of a existing call arrives, it updates the ongoing call.
        '''
        # We ignore OPTIONS in calls
        if sip_message.type == 'OPTIONS':
            return

        # Ignore, Add or Update
        sip_key = SIPNetwork.key(sip_message)
        if sip_key not in self.active_calls:
            # new packet does not belong to a call:
            call = SIPNetwork.start_call(sip_message)
            if call:
                self.active_calls[sip_key] = call
        else:
            # new packet belongs to an existing call:
            call = self.active_calls[sip_key]
            call.update(sip_message)

        if call:
            # update users
            if call.state == 'AUTHORIZED':
                self.active_users.add(sip_message.frm)
            # update calls
            if call.state in ['ERROR', 'TERMINATED', 'IGNORED', 'AUTHORIZED']:
                del self.active_calls[sip_key]

    @staticmethod
    def start_call(sip_message):
        '''When an INVITE or a REGISTER packet arrives, it creates a new call object.
        :param sip_message: a sip message
        :return: call: a call object created from the sip message
        '''
        if sip_message.type == 'INVITE' or sip_message.type == 'REGISTER':
            # Initialize a new call object:
            call = SIPCall()
            call.update(sip_message)
            return call
        else:
            return None

    @staticmethod
    def key(sip_message):
        '''It generates a hash key to record an unique call.
        :param sip_message: a sip message
        :return: key: a hash key that is generated by 'to' and 'from' of a sip message
        '''
        if sip_message.frm < sip_message.to:
            return sip_message.frm + '#' + sip_message.to
        return sip_message.to + '#' + sip_message.frm
