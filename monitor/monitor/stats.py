''' 
This study is a Bogazici University - NETAS Nova V-Gate collaboration and funded by TEYDEB project "Realization of Anomaly Detection and Prevention with Learning System Architectures, Quality Improvement, High Rate Service Availability and Rich Services in a VoIP Firewall Product'', by the Scientific and Technological Research Council Of Turkey (TUBITAK).
'''

import collections
import psutil
import sys, os, string, re

from sip import SIPMessage


class Stats(object):
    ''' This class contains the statistics for PacketHistogram, ResourceUsage, ResourceHistogram
    	and CallStats.
    '''
    STATS_LIST = ['ResourceUsage', 'PacketHistogram', 'SIPMessages', 'AsteriskLogHistogram']

    def __init__(self, name=None):
        self.name = name
        print 'Collecting feature: %s ' % self.name

    def add_packet(self, message):
        pass

    def finalize(self):
        pass

    def clear(self):
        pass

    def get_stats(self):
        pass

    @staticmethod
    def create_by_name(name):
        if name in Stats.STATS_LIST:
            if name == 'ResourceUsage':
                return ResourceUsage()
            elif name == 'PacketHistogram':
                return PacketHistogram()
            elif name == 'SIPMessages':
                return SIPMessages()
            elif name == 'AsteriskLogHistogram':
                return AsteriskLogHistogram()

        print 'No such Stats found: %s' % name
        return None


class PacketHistogram(Stats):
    HEADERS = SIPMessage.HEADERS

    def __init__(self):
        super(PacketHistogram, self).__init__('PacketHistogram')
        self.histogram = None
        self.clear()

    def clear(self):
        self.histogram = collections.OrderedDict.fromkeys(self.HEADERS, 0)

    def add_packet(self, pkt):
        if pkt.sip_message and pkt.sip_message.type in self.histogram:
            self.histogram[pkt.sip_message.type] += 1

    def get_stats(self):
        return self.histogram


class SIPMessages(Stats):
    def __init__(self):
        super(SIPMessages, self).__init__('SIPMessages')
        self.messages = []

    def clear(self):
        self.messages = []

    def add_packet(self, pkt):
        if pkt.sip_message:
            self.messages.append(pkt.sip_message)

    def get_stats(self):
        return self.messages


class AsteriskStats:

    HEADERS = ('FH', 'THREADS', 'TCP_CONN', 'UDP_CONN', 'IO_READ',
                    'IO_WRITE', 'IO_BYTES_READ', 'IO_BYTES_WRITE')

    def __init__(self, process=None):
        self.cpu_percent = 0
        self.memory_percent = 0
        self.num_file_handlers = 0
        self.num_threads = 0
        self.num_tcp_connections = 0
        self.num_udp_connections = 0
        self.io_counters = [0]*4
        if process:
            self.update(process)

    def to_list(self):
        return [self.num_file_handlers, self.num_threads,
                self.num_tcp_connections, self.num_udp_connections] + self.io_counters

    def update(self, process):
        self.cpu_percent = process.cpu_percent()
        self.memory_percent = process.memory_percent()
        self.num_file_handlers = process.num_fds()
        self.num_threads = process.num_threads()
        self.num_tcp_connections = len(process.connections(kind="tcp"))
        self.num_udp_connections = len(process.connections(kind="udp"))
        self.io_counters = list(process.io_counters())


class ResourceUsage(Stats):
    ''' This class contains the statistics for Resource Usage (percentage).
    total_cpu_percent: total cpu usage percentage of server
    trixbox_cpu_percent: total cpu usage percentage of asterisk
    total_used_memory_percent: total memory usage percentage of server
    trixbox_used_memory_percent: total memory usage percentage of asterisk
    '''

    # check except part in the finalize function as IF YOU UPDATE HEADERS
    HEADERS = ('TOT_CPU','TOT_MEM', 'CPU','MEM', 'FH', 'THREADS', 'TCP_CONN', 'UDP_CONN',
               'IO_READ', 'IO_WRITE', 'IO_BYTES_READ', 'IO_BYTES_WRITE')

    def __init__(self):
        super(ResourceUsage, self).__init__('ResourceUsage')

        self.histogram = None
        self.clear()

        for process in psutil.process_iter():
            if process.name() == 'asterisk':
                self.asterisk_pid = process.pid
                break

    # Serializes a dictionary containing resource usage stats
    def finalize(self):
        # Collect Overall Stats
        self.histogram['TOT_CPU'] = psutil.cpu_percent()
        self.histogram['TOT_MEM'] = psutil.virtual_memory().percent

        # Collect Asterisk Stats
        if self.asterisk_pid:
            # Can reach Asterisk ?
            try:
                process = psutil.Process(self.asterisk_pid)
                self.histogram['CPU'] = process.cpu_percent()
                self.histogram['MEM'] = process.memory_percent()
                self.histogram['FH'] = process.num_fds()
                self.histogram['THREADS'] = process.num_threads()
                self.histogram['TCP_CONN'] = len(process.connections(kind="tcp"))
                self.histogram['UDP_CONN'] = len(process.connections(kind="udp"))
                ioc = list(process.io_counters())
                self.histogram['IO_READ'] = ioc[0]
                self.histogram['IO_WRITE'] = ioc[1]
                self.histogram['IO_BYTES_READ'] = ioc[2]
                self.histogram['IO_BYTES_WRITE'] = ioc[3]
                self.io_counters = list(process.io_counters())

            except psutil.NoSuchProcess:
                print 'Warning: Asterisk dead.'
                hdr_list = list(self.HEADERS)
                for i in range(2, len(hdr_list)): # asterisk related stats start from the second item in the header list
                    self.histogram[hdr_list[i]]= 0
                self.asterisk_pid = None

    def clear(self):
        self.histogram = collections.OrderedDict.fromkeys(self.HEADERS, 0)

    def get_stats(self):
        return self.histogram


class AsteriskLogHistogram(Stats):
    LOG_LEVELS = ['WARNING', 'NOTICE', 'VERBOSE', 'ERROR', 'DEBUG']
    OLD_HEADERS = ('BYTES_CHANGE', 'LINE_CHANGE', 'NUM_DIST_PID', 'NUM_DIST_LOGGER',
                    'WARNING', 'NOTICE', 'VERBOSE', 'ERROR', 'DEBUG')
    HEADERS = ('WARNING', 'NOTICE', 'VERBOSE', 'ERROR', 'DEBUG')

    def __init__(self,log_file="/var/log/asterisk/full",blksize=4096):
        super(AsteriskLogHistogram, self).__init__('AsteriskLogHistogram')
        self.histogram = None
        if os.path.isfile(log_file):
            self.file = log_file
            self.size = int(os.stat(self.file)[6])# get the file size
            self.blksize = blksize # how big of a block to read from the file...
            self.blkcount = 1 # how many blocks we've read
            self.f = open(self.file, 'r')
            self.data = self.readContent()
            self.current_line = self.readLine(False) # reads last line without removing it
            # self.num_bytes = 0 # initial size of the log file
        self.clear()

    def get_stats(self):
        return self.histogram

    def clear(self):
        self.histogram = collections.OrderedDict.fromkeys(self.HEADERS, 0)

    def finalize(self):
        # file size related stuff
        newFileSize = int(os.stat(self.file)[6])
        # self.histogram['BYTES_CHANGE'] = (newFileSize - self.size)/100
        self.size  = newFileSize

        # line related stuff
        linesAdded = self.readAddedLines()
        # print "linesAdded:",linesAdded
        # self.histogram['LINE_CHANGE'] = len(linesAdded)
        self.countLogLevels(linesAdded)

    def readContent(self):
        self.blkcount = 1
        # if the file is smaller than the blocksize, read a block,
        # otherwise, read the whole thing...
        if self.size > self.blksize:
            self.f.seek(-self.blksize * self.blkcount, 2) # read from end of file
        data = string.split(self.f.read(self.blksize), '\n')
        # strip the last item if it's empty...  a byproduct of the last line having
        # a newline at the end of it
        if not data[-1]:
            data = data[:-1]
        return data

    def getLineCount(self):
        f_gen = self._make_gen(self.f.read)
        return sum( buf.count(b'\n') for buf in f_gen )
    def _make_gen(self,reader):
        b = reader(1024 * 1024)
        while b:
            yield b
            b = reader(1024*1024)

    def readAddedLines(self):
        self.data = self.readContent()
        linesbr = []
        line = self.readLine()
        lastLine = line
        while line != self.current_line and line!="" :
            if line != "":
                linesbr.append(line)
            line = self.readLine()
        self.current_line = lastLine
        return linesbr

    def countLogLevels(self, lines):
        for line in lines:
            for level in self.LOG_LEVELS:
                if level in line:
                    self.histogram[level] += 1
                    # print "level %s found!" % level

    def readLine(self, remove_last_line=True):
        while len(self.data) == 1 and ((self.blkcount * self.blksize) < self.size) and remove_last_line:
            self.blkcount = self.blkcount + 1
            line = self.data[0]
            try:
                self.f.seek(-self.blksize * self.blkcount, 2) # read from end of file
                self.data = string.split(self.f.read(self.blksize) + line, '\n')
            except IOError:  # can't seek before the beginning of the file
                self.f.seek(0)
                # self.data = string.split(self.f.read(self.size - (self.blksize * (self.blkcount-1))) + line, '\n')

        if len(self.data) == 0:
             return ""

        line = self.data[-1]
        if remove_last_line:
            self.data = self.data[:-1]
        return line + '\n'

