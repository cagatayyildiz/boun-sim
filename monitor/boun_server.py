''' 
This study is a Bogazici University - NETAS Nova V-Gate collaboration and funded by TEYDEB project "Realization of Anomaly Detection and Prevention with Learning System Architectures, Quality Improvement, High Rate Service Availability and Rich Services in a VoIP Firewall Product'', by the Scientific and Technological Research Council Of Turkey (TUBITAK).
'''

import argparse

from monitor.monitor import MonitorServer

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Network Traffic Monitor Server')
    parser.add_argument('-p', '--port', type=int, default=MonitorServer.DEFAULT_PORT,
                        help='Port for listening to client control messages')
    args = parser.parse_args()
    MonitorServer(port=args.port).listen()
