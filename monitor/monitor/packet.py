''' 
This study is a Bogazici University - NETAS Nova V-Gate collaboration and funded by TEYDEB project "Realization of Anomaly Detection and Prevention with Learning System Architectures, Quality Improvement, High Rate Service Availability and Rich Services in a VoIP Firewall Product'', by the Scientific and Technological Research Council Of Turkey (TUBITAK).
'''

import dpkt
import socket

from sip import SIPMessage

__author__ = 'Baris Kurt'


class Packet:

    def __init__(self, timestamp, buf):
        self.timestamp = timestamp
        self.error = None
        self.src_mac = None
        self.dst_mac = None
        self.src_ip = None
        self.src_port = None
        self.dst_ip = None
        self.dst_port = None
        self.len = None
        self.proto = None
        self.sip_message = None
        self.parse_buffer(buf)

    def parse_buffer(self, buf):

        # 1) Parse Ethernet
        eth = dpkt.ethernet.Ethernet(buf)
        self.src_mac = ':'.join('%02x' % ord(b) for b in eth.src)
        self.dst_mac = ':'.join('%02x' % ord(b) for b in eth.dst)

        # 2) Parse IP
        ip = eth.data
        if eth.type != dpkt.ethernet.ETH_TYPE_IP:
            self.error = 'Not IPv4'
            return

        more_fragments = bool(ip.off & dpkt.ip.IP_MF)
        fragment_offset = ip.off & dpkt.ip.IP_OFFMASK
        if more_fragments or fragment_offset > 0:
            self.error = 'Fragmented Packet'
            return

        self.src_ip = socket.inet_ntop(socket.AF_INET, ip.src)
        self.dst_ip = socket.inet_ntop(socket.AF_INET, ip.dst)
        self.len = ip.len
        self.proto = ip.p

        # 3) Parse UDP
        if ip.p != dpkt.ip.IP_PROTO_UDP:
            self.error = 'Not UDP'
            return
        udp = ip.data
        self.src_port = udp.sport
        self.dst_port = udp.dport

        # Remaining Payload:
        self.sip_message = SIPMessage.parse_from_text(udp.data, self.timestamp)

    def is_udp(self):
        return self.proto == dpkt.ip.IP_PROTO_UDP
