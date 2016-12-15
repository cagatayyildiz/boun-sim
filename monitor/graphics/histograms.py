''' 
This study is a Bogazici University - NETAS Nova V-Gate collaboration and funded by TEYDEB project "Realization of Anomaly Detection and Prevention with Learning System Architectures, Quality Improvement, High Rate Service Availability and Rich Services in a VoIP Firewall Product'', by the Scientific and Technological Research Council Of Turkey (TUBITAK).
'''

import matplotlib.pyplot as plt
import numpy as np

from monitor.monitor import MessageHandler
from monitor.stats import *#PacketHistogram, ResourceUsage, AsteriskLogHistogram
from monitor.sip import SIPMessage


# Author : Baris
class SlidingWindow(MessageHandler):
    WINDOW_LENGTH = int(40)
    X_TICK_STEP = int(5)

    def __init__(self, name, stats_names, width, height, dpi=96):        
        super(SlidingWindow, self).__init__(name, stats_names)
        plt.ion()
        # Figure and axis
        self.fig = None
        self.ax = None
        # Dimensions
        self.dpi = dpi
        self.width = float(width)/self.dpi
        self.height = float(height)/self.dpi
        # Decorations
        self.title = None
        self.x_label = None
        self.y_label = None
        self.x_tick_labels = np.arange(self.X_TICK_STEP - self.WINDOW_LENGTH, 1, self.X_TICK_STEP)
        self.x_tick_pos = np.arange(self.X_TICK_STEP-1, self.WINDOW_LENGTH, self.X_TICK_STEP) + 0.5
        self.y_tick_labels = None
        self.y_tick_pos = None
        self.legend = None
        self.legend_loc = 0
        # Time
        self.epoch = 0

    def create(self):
        self.fig = plt.figure(figsize=(self.width, self.height), dpi=self.dpi, frameon=False)
        self.ax = self.fig.gca()
        self.ax.hold(False)

    def slide_x_ticks(self):
        if self.epoch % self.X_TICK_STEP == 0:
            self.x_tick_pos += self.X_TICK_STEP - 1
            self.x_tick_labels += self.X_TICK_STEP
        else:
            self.x_tick_pos -= 1

    def draw(self, slide_x_ticks=True):
        # update time
        self.epoch += 1
        # x ticks
        if slide_x_ticks: self.slide_x_ticks()
        self.ax.set_xticks(self.x_tick_pos, minor=False)
        self.ax.set_xticklabels(self.x_tick_labels)
        # y-ticks
        if self.y_tick_labels is not None:
            if self.y_tick_pos is not None:
                self.ax.set_yticks(self.y_tick_pos, minor=False)
            self.ax.set_yticklabels(self.y_tick_labels)
        # labels and titles
        self.ax.set_title(self.title)
        self.ax.set_xlabel(self.x_label)
        self.ax.set_ylabel(self.y_label)
        if self.legend:
            self.ax.legend(self.legend, loc=self.legend_loc)
        # draw
        self.fig.canvas.draw()
        plt.pause(0.0001)



# Author : Baris
class PacketHistogramGraph(SlidingWindow):

    NUM_HEADERS = len(PacketHistogram.HEADERS)

    def __init__(self, width=800, height=500, dpi=96, headers=None):
        if headers is None:
            self.headers = SIPMessage.HEADERS
        else:
            self.headers = headers
            self.NUM_HEADERS = len(self.headers)
            height = 200 + 10*self.NUM_HEADERS
        super(PacketHistogramGraph, self).__init__('PacketHistogramGraph', ['PacketHistogram'], width, height, dpi)
        plt.ion()
        # titles, labels:
        self.title = 'Number of Packets'
        self.x_label = 'Time Frame (sec.)'
        self.y_label = 'Packet Type'
        # x - y axis labels
        self.y, self.x = np.mgrid[slice(0, self.NUM_HEADERS + 1, 1),
                                  slice(0, self.WINDOW_LENGTH + 1, 1)]
        self.histogram = np.zeros((self.NUM_HEADERS, self.WINDOW_LENGTH))
        # y-ticks
        self.y_tick_pos = np.arange(self.NUM_HEADERS) + 0.5
        self.y_tick_labels = self.headers
        # Initialize graph:
        super(PacketHistogramGraph, self).create()
        self.update(PacketHistogram().histogram)

    def handle_message(self, message):
        if 'PacketHistogram' in message.body.keys():
            self.update(message.body['PacketHistogram'])

    def update(self, _packet_histogram):

        h = PacketHistogram.HEADERS
        header_d = dict( zip( h, range(len(h))))
        v = _packet_histogram.values()
        v_sampled = [v[header_d[i]] for i in self.headers]
        print v_sampled
        # shift window and append new data
        self.histogram[:, :-1] = self.histogram[:, 1:]
        self.histogram[:, -1] = v_sampled

        # plot histogram
        self.ax.pcolormesh(self.x, self.y, self.histogram, cmap=plt.cm.Greys, vmin=0, vmax=50)
        super(PacketHistogramGraph, self).draw()


class AsteriskLogHistogramGraph(SlidingWindow):

    NUM_HEADERS = len(AsteriskLogHistogram.HEADERS)

    def __init__(self, width=800, height=500, dpi=96, _headers=None):
        if _headers is None:
            self.headers = AsteriskLogHistogram.HEADERS
        else:
            self.headers = _headers
            self.NUM_HEADERS = len(self.headers)
            height = 200 + 10*self.NUM_HEADERS
        super(AsteriskLogHistogramGraph, self).__init__('AsteriskLogHistogramGraph', ['AsteriskLogHistogram'], width, height, dpi, _headers=self.headers)
        plt.ion()
        # titles, labels:
        self.title = 'Number of Log Features'
        self.x_label = 'Time Frame (sec.)'
        self.y_label = 'Log Type'
        # x - y axis labels
        self.y, self.x = np.mgrid[slice(0, self.NUM_HEADERS + 1, 1),
                                  slice(0, self.WINDOW_LENGTH + 1, 1)]
        self.histogram = np.zeros((self.NUM_HEADERS, self.WINDOW_LENGTH))
        # y-ticks
        self.y_tick_pos = np.arange(self.NUM_HEADERS) + 0.5
        self.y_tick_labels = self.headers
        # Initialize graph:
        super(AsteriskLogHistogramGraph, self).create()
        self.update(AsteriskLogHistogram(active=False).histogram)

    def handle_message(self, message):
        if 'AsteriskLogHistogram' in message.body.keys():
            self.update(message.body['AsteriskLogHistogram'])

    def update(self, _log_histogram):
        h = AsteriskLogHistogram.HEADERS
        header_d = dict( zip( h, range(len(h))))
        v = _log_histogram.values()
        v_sampled = [v[header_d[i]] for i in self.headers]

        # shift window and append new data
        self.histogram[:, :-1] = self.histogram[:, 1:]
        self.histogram[:, -1] = v_sampled
        # plot histogram
        self.ax.pcolormesh(self.x, self.y, self.histogram, cmap=plt.cm.Greys, vmin=0, vmax=50)
        super(AsteriskLogHistogramGraph, self).draw()


class HistogramWindow(SlidingWindow):
    STATS =['PacketHistogram']
    HEADERS = [('REGISTER', 'INVITE', 'OPTIONS', 'ACK', 'BYE', 'CANCEL', '100',
            '180', '183', '200', '401', '481', '486', '487', '500', '603')]
    STATS_INDICES = dict( zip(STATS, range(len(STATS))))

    def __init__(self, headers, stats, K, width=800, height=None, dpi=96, title='Histogram', y_label='', nmf=None):
        # headers is an array of tuples
        self.stats = stats
        self.headers = headers
        self.nmf = nmf
        self.DIM = K
        if height is None:
            height = 200 + 10*self.DIM
        super(HistogramWindow, self).__init__(title, self.stats, width, height, dpi)

        # titles, labels:
        self.title = title
        self.x_label = 'Time Frame (sec.)'
        self.y_label = y_label

        # x - y axis labels
        self.y, self.x = np.mgrid[slice(0, self.DIM + 1, 1),
                                  slice(0, self.WINDOW_LENGTH + 1, 1)]
        # y-ticks
        self.y_tick_labels = ()
        if self.nmf:
            for i in np.arange(1, self.DIM+1):
                self.y_tick_labels = self.y_tick_labels + ('Basis'+str(i))
        else:
            for h in self.headers:
                self.y_tick_labels = self.y_tick_labels + h

        self.y_tick_pos = np.arange(self.DIM) + 0.5

        self.histogram = np.zeros((self.DIM, self.WINDOW_LENGTH))
        self.posterior = np.zeros(self.WINDOW_LENGTH)
        self.ground_truth = np.zeros(self.WINDOW_LENGTH)
        super(HistogramWindow, self).create()

    def handle_message(self, message):
        packet_histogram = np.array([])
        for stat in self.STATS:
            if stat is not 'SIPMessages':
                stat_i = self.STATS_INDICES[stat]
                h = Stats.create_by_name(stat).HEADERS
                header_d = dict( zip( h, range(len(h))))
                v = message.body[stat].values()
                if type(self.HEADERS[stat_i]) is str:
                    i = self.HEADERS[stat_i]
                    v_sampled = [v[header_d['%s'%i]]]
                else:
                    v_sampled = [v[header_d[i]] for i in self.HEADERS[stat_i]]
                packet_histogram = np.hstack((packet_histogram, v_sampled ))

        # if self.title in message.body.keys():
        #     dt = np.array(message.body[self.title].values())
        dt = packet_histogram
        self.update(1.0*dt/dt.sum())

    def update(self, data_hist, cpp=None, attack_time=None):
        self.attack_time = attack_time
        # data_hist and cpp may not be of the same length !!!!!
        if data_hist.ndim == 1:
            np.ndarray.resize(data_hist, (len(data_hist), 1))
        # shift
        self.histogram[:, :-1] = self.histogram[:, 1:]
        self.posterior[:-1] = self.posterior[1:]
        self.ground_truth[:-1] = self.ground_truth[1:]
        self.ground_truth[-1] = 0
        if cpp is None: # just visualization of the histogram
            self.histogram[:,-1] = data_hist.reshape(len(data_hist))
        else:
            # update smoothed intensity
            smt_int_lag = data_hist.shape[1]
            self.histogram[:,-smt_int_lag:] = data_hist
            # update cpp
            cpp_lag = len(cpp)
            self.posterior[-cpp_lag:] = cpp
        # draw
        self.ax.pcolormesh(self.x, self.y, self.histogram, cmap=plt.cm.Greys, vmin=0, vmax=1)

        self.ax.hold(True)
        x_val = np.arange(0, self.WINDOW_LENGTH)
        if self.attack_time is not None:
            self.ground_truth[-1] = 1
        self.ax.vlines(x_val, [0], self.ground_truth*self.DIM, colors='g',linewidth=2, linestyles='dashed')
        self.ax.hold(False)

        self.ax.hold(True)
        x_val = np.arange(0, self.WINDOW_LENGTH)
        self.ax.vlines(x_val, [0], self.posterior*self.DIM, colors='r',linewidth=2, linestyles='solid')
        self.ax.hold(False)

        super(HistogramWindow, self).draw()
        # super(CPPosteriorWindow, self).draw(slide_x_ticks=False)

class HistogramGraph():
    NUM_HEADERS = len(PacketHistogram.HEADERS)

    def __init__(self, width=800, height=500, dpi=96, _headers=None):
        if _headers is None:
            self.headers = AsteriskLogHistogram.HEADERS
        else:
            self.headers = _headers
            self.NUM_HEADERS = len(self.headers)
            height = 200 + 10*self.NUM_HEADERS
        super(AsteriskLogHistogramGraph, self).__init__('AsteriskLogHistogramGraph', ['AsteriskLogHistogram'], width, height, dpi, _headers=self.headers)
        plt.ion()
        # titles, labels:
        self.title = 'Number of Log Features'
        self.x_label = 'Time Frame (sec.)'
        self.y_label = 'Log Type'
        # x - y axis labels
        self.y, self.x = np.mgrid[slice(0, self.NUM_HEADERS + 1, 1),
                                  slice(0, self.WINDOW_LENGTH + 1, 1)]
        self.histogram = np.zeros((self.NUM_HEADERS, self.WINDOW_LENGTH))
        # y-ticks
        self.y_tick_pos = np.arange(self.NUM_HEADERS) + 0.5
        self.y_tick_labels = self.headers
        # Initialize graph:
        super(AsteriskLogHistogramGraph, self).create()
        self.update(AsteriskLogHistogram(active=False).histogram)

    def handle_message(self, message):
        if 'AsteriskLogHistogram' in message.body.keys():
            self.update(message.body['AsteriskLogHistogram'])

    def update(self, _log_histogram):
        h = AsteriskLogHistogram.HEADERS
        header_d = dict( zip( h, range(len(h))))
        v = _log_histogram.values()
        v_sampled = [v[header_d[i]] for i in self.headers]

        # shift window and append new data
        self.histogram[:, :-1] = self.histogram[:, 1:]
        self.histogram[:, -1] = v_sampled
        # plot histogram
        self.ax.pcolormesh(self.x, self.y, self.histogram, cmap=plt.cm.Greys, vmin=0, vmax=50)
        super(AsteriskLogHistogramGraph, self).draw()


# Author : Baris
class CpuMemPercentageGraph(SlidingWindow):

    def __init__(self, width=800, height=250, dpi=96):
        super(CpuMemPercentageGraph, self).__init__('CpuMemPercentageGraph', ['ResourceUsage'], width, height, dpi)
        # titles, labels:
        self.title = 'CPU and Memory Percentages'
        self.x_label = 'Time Frame (sec.)'
        self.y_label = 'Percentage'
        self.legend = ['Total CPU', 'Trixbox CPU', 'Total Used Memory', 'Trixbox Used Memory']
        self.legend_loc = 2  # upper left
        # y_ticks
        self.y_tick_pos = np.arange(0, 101, 10)
        self.y_tick_labels = np.arange(0, 101, 10)
        # data:
        self.total_cpu = np.zeros(self.WINDOW_LENGTH)
        self.total_memory = np.zeros(self.WINDOW_LENGTH)
        self.asterisk_cpu = np.zeros(self.WINDOW_LENGTH)
        self.asterisk_memory = np.zeros(self.WINDOW_LENGTH)
        # Initialize graph:
        super(CpuMemPercentageGraph, self).create()
        self.draw()

    def handle_message(self, message):
        if 'ResourceUsage' in message.body.keys():
            self.update(message.body['ResourceUsage'])

    def update(self, resource_usage):
        # update data
        self.total_cpu[:-1] = self.total_cpu[1:]
        self.total_cpu[-1] = resource_usage['TOT_CPU']

        self.total_memory[:-1] = self.total_memory[1:]
        self.total_memory[-1] = resource_usage['TOT_MEM']

        self.asterisk_cpu[:-1] = self.asterisk_cpu[1:]
        self.asterisk_cpu[-1] = resource_usage['CPU']

        self.asterisk_memory[:-1] = self.asterisk_memory[1:]
        self.asterisk_memory[-1] = resource_usage['MEM']
        # draw
        x_val = np.arange(0, 40)
        self.ax.plot(x_val, self.total_cpu, '-b', x_val, self.asterisk_cpu, '-r', x_val,
                     self.total_memory, '-g', x_val, self.asterisk_memory, '-k')
        super(CpuMemPercentageGraph, self).draw()


class OsStatsCountsGraph(SlidingWindow):

    def __init__(self, width=800, height=500, dpi=96):
        super(OsStatsCountsGraph, self).__init__('OsStatsCountsGraph', ['ResourceUsage'], width, height, dpi)
        # titles, labels:
        self.title = 'Operating System Statistics'
        self.x_label = 'Time Frame (sec.)'
        self.y_label = 'Counts'
        self.legend = ['File Handlers', 'Threads', 'TCP Connections', 'UDP Connections','IO_READ(MB)', 'IO_WRITE(MB)']
        self.legend_loc = 2  # upper left
        # y_ticks
        self.y_tick_pos = np.arange(0, 251, 50)
        self.y_tick_labels = np.arange(0, 251, 50)
        # data:
        self.file_handler = np.zeros(self.WINDOW_LENGTH)
        self.thread = np.zeros(self.WINDOW_LENGTH)
        self.tcp_connection = np.zeros(self.WINDOW_LENGTH)
        self.udp_connection = np.zeros(self.WINDOW_LENGTH)
        self.io_read = np.zeros(self.WINDOW_LENGTH)
        self.io_write = np.zeros(self.WINDOW_LENGTH)
        # Initialize graph:
        super(OsStatsCountsGraph, self).create()
        self.draw()

    def handle_message(self, message):
        if 'ResourceUsage' in message.body.keys():
            self.update(message.body['ResourceUsage'])

    def update(self, resource_usage):
        print resource_usage
        # update data
        self.file_handler[:-1] = self.file_handler[1:]
        self.file_handler[-1] = resource_usage['FH']

        self.thread[:-1] = self.thread[1:]
        self.thread[-1] = resource_usage['THREADS']

        self.tcp_connection[:-1] = self.tcp_connection[1:]
        self.tcp_connection[-1] = resource_usage['TCP_CONN']

        self.udp_connection[:-1] = self.udp_connection[1:]
        self.udp_connection[-1] = resource_usage['UDP_CONN']

        self.io_read[:-1] = self.io_read[1:]
        self.io_read[-1] = resource_usage['IO_BYTES_READ']/1024/1024

        self.io_write[:-1] = self.io_write[1:]
        self.io_write[-1] = resource_usage['IO_BYTES_WRITE']/1024/1024
        # draw
        x_val = np.arange(0, 40)
        self.ax.plot(x_val, self.file_handler, '-b', x_val, self.tcp_connection, '-r',
                     x_val, self.thread, '-g', x_val, self.udp_connection, '-k',
                     x_val, self.io_read, '--c', x_val, self.io_write, '.-m')
        super(OsStatsCountsGraph, self).draw()

'''
class IOHistogramGraph(SlidingWindow):

    def __init__(self, width=1000, height=300, dpi=96):
        super(IOHistogramGraph, self).__init__('IOHistogramGraph', ['ResourceUsage'], width, height, dpi)
        plt.ion()
        # titles, labels:
        self.HEADERS = ('IO_READ', 'IO_WRITE', 'IO_BYTES_READ', 'IO_BYTES_WRITE')
        self.NUM_HEADERS = len(self.HEADERS)
        self.histogram = collections.OrderedDict.fromkeys(self.HEADERS, 0)
        self.title = 'I/O Histogram (Normalized)'
        self.x_label = 'Time Frame (sec.)'
        self.y_label = 'Operation Type'
        # x - y axis labels
        self.y, self.x = np.mgrid[slice(0, self.NUM_HEADERS + 1, 1),
                                  slice(0, self.WINDOW_LENGTH + 1, 1)]
        self.histogram = np.zeros((self.NUM_HEADERS, self.WINDOW_LENGTH))
        # y-ticks
        self.y_tick_pos = np.arange(self.NUM_HEADERS) + 0.5
        self.y_tick_labels = self.HEADERS
        # Initialize graph:
        super(IOHistogramGraph, self).create()
        # self.update(IOHistogramGraph().histogram)

    def handle_message(self, message):
        if 'ResourceUsage' in message.body.keys():
            self.update(message.body['ResourceUsage'])

    def update(self, packet_histogram):
        # shift window and append new data
        self.histogram[:, :-1] = self.histogram[:, 1:]
        stats = np.array([packet_histogram[x] for x in self.HEADERS])
        print stats
        self.histogram[:, -1] = 1.0*stats/stats.sum()
        # plot histogram
        self.ax.pcolormesh(self.x, self.y, self.histogram, cmap=plt.cm.Greys, vmin=0, vmax=1)
        super(IOHistogramGraph, self).draw()
'''
