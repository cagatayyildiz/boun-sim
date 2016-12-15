''' 
This study is a Bogazici University - NETAS Nova V-Gate collaboration and funded by TEYDEB project "Realization of Anomaly Detection and Prevention with Learning System Architectures, Quality Improvement, High Rate Service Availability and Rich Services in a VoIP Firewall Product'', by the Scientific and Technological Research Council Of Turkey (TUBITAK).
'''

import matplotlib.pyplot as plt
import numpy as np

from monitor.monitor import MessageHandler
from monitor.sip import SIPNetwork


class CallGraph(MessageHandler):

    NUM_MAX_USERS = 50

    class Layout:
        def __init__(self):
            self.num_nodes = 0
            self.R = 0.45

        def get_next_pos(self):
            phi = np.random.rand() * 2 * np.pi
            pos = self.pol2cart(self.R, phi)
            pos += 0.5
            return pos

        @staticmethod
        def pol2cart(rho, phi):
            x = rho * np.cos(phi)
            y = rho * np.sin(phi)
            return np.asarray((x, y))

    class Graph:
        def __init__(self):
            self.users = {}  # dictionary: keys=user_id, values=position
            self.layout = CallGraph.Layout()

        def draw(self, ax, network):
            ax.clear()
            self.update_users(network)

            for call in network.active_calls.values():
                if call.caller_id in self.users and call.callee_id in self.users:
                    caller_pos = self.users[call.caller_id]
                    callee_pos = self.users[call.callee_id]
                    if call.state == 'SETUP':
                        color_code = 'r'
                    else:
                        color_code = 'g'
                    ax.add_artist(plt.Line2D((caller_pos[0], callee_pos[0]),
                                             (caller_pos[1], callee_pos[1]), color=color_code))

            for pos in self.users.values():
                ax.add_artist(plt.Circle(pos, 0.01, color='b'))

        def update_users(self, network):
            # remove unauthorized users
            for user_id in self.users.keys():
                if user_id not in network.active_users:
                    del self.users[user_id]

            # add newly authorized users
            for user_id in network.active_users:
                if user_id not in self.users:
                    pos = self.layout.get_next_pos()
                    self.users[user_id] = pos

    def __init__(self, width=600, height=600, dpi=96):
        super(CallGraph, self).__init__('CallGraph', ['SIPMessages'])
        plt.ion()
        self.fig = None
        self.ax = None
        self.G = None
        self.node_pos = None
        self.dpi = dpi
        self.width = float(width)/self.dpi
        self.height = float(height)/self.dpi
        self.graph = CallGraph.Graph()
        self.network = SIPNetwork()
        # Initialize graph:
        self.fig = plt.figure(figsize=(self.width, self.height), dpi=self.dpi, frameon=False)
        self.ax = self.fig.gca()
        self.ax.hold(False)

    def handle_message(self, message):
        if 'SIPMessages' in message.body.keys():
            self.update(message.body['SIPMessages'])

    def update(self, sip_messages):
        self.network.add_messages(sip_messages)
        self.graph.draw(self.ax, self.network)
        self.ax.set_title('Call Graph')
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.fig.canvas.draw()
