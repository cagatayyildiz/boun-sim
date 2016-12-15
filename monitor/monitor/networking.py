''' 
This study is a Bogazici University - NETAS Nova V-Gate collaboration and funded by TEYDEB project "Realization of Anomaly Detection and Prevention with Learning System Architectures, Quality Improvement, High Rate Service Availability and Rich Services in a VoIP Firewall Product'', by the Scientific and Technological Research Council Of Turkey (TUBITAK).
'''

import socket
import SocketServer
import struct
import pickle

__author__ = 'Baris Kurt'


class Message:
    def __init__(self, header=None, body={}):
        self.header = header
        self.body = body

    def insert(self, key, value):
        self.body[key] = value

    def __len__(self):
        return len(self.header) + len(self.body)

    def __str__(self):
        return 'header = %s\nbody = %s' % (self.header, self.body)

    def write(self):
        return pickle.dumps(self)

    @staticmethod
    def read_from(buf):
        return pickle.loads(buf)

    def sent_to(self, address, proto='TCP'):
        if proto == 'TCP':
            send_tcp_message(address, self)
        elif proto == 'UDP':
            send_udp_message(address, self)


class UDPServer(SocketServer.UDPServer):
    def __init__(self, address):
        SocketServer.UDPServer.__init__(self, address, None)
        self.running = False

    def listen(self):
        self.running = True
        self.timeout = 0.1
        try:
            while self.running:
                self.handle_request()
        except KeyboardInterrupt:
            self.running = False

    def stop(self):
        self.running = False

    def handle_message(self, message, address):
        pass

    def finish_request(self, request, client_address):
        message = Message.read_from(request[0])
        self.handle_message(message, client_address)


def send_udp_message(address, message):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(message.write(), address)
    except socket.error, (value, err_message):
        print "Cannot send UDP message: " + err_message


class TCPServer(SocketServer.TCPServer):
    def __init__(self, address):
        SocketServer.TCPServer.allow_reuse_address = True
        SocketServer.TCPServer.__init__(self, address, None)
        self.running = False
        print 'TCPServer: up'

    def __del__(self):
        self.close()

    def listen(self):
        self.running = True
        self.timeout = 0.1
        try:
            while self.running:
                self.handle_request()
        except KeyboardInterrupt:
            self.running = False

    def stop(self):
        self.running = False

    def close(self):
        self.server_close()
        print 'TCPServer: closed.'

    def finish_request(self, request, client_address):
        length, = struct.unpack('!I', request.recv(4))
        data = b''
        while length:
            part = request.recv(length)
            if not part:
                return None
            data += part
            length -= len(part)
        self.handle_message(Message.read_from(data), client_address)

    def handle_message(self, message, address):
        pass


def send_tcp_message(address, message):
    try:
        data = message.write()
        sock = socket.create_connection(address)
        sock.sendall(struct.pack('!I', len(data)))
        sock.sendall(data)
    except socket.error, (value, err_message):
        print "Cannot send TCP message: " + err_message
