''' 
This study is a Bogazici University - NETAS Nova V-Gate collaboration and funded by TEYDEB project "Realization of Anomaly Detection and Prevention with Learning System Architectures, Quality Improvement, High Rate Service Availability and Rich Services in a VoIP Firewall Product'', by the Scientific and Technological Research Council Of Turkey (TUBITAK).
'''

'''
This is the default client of the BOUN SIP Network Monitoring System.

Please Do NOT Modify this client.

In order to experiment your algorithms, you can generate your own client easily.
'''

import argparse

try:
    from monitor.monitor import MonitorClient, MonitorServer, Logger
    from graphics.histograms import *
    from graphics.call_graph import CallGraph
except ImportError:
    print '\nUsage: python -m detectors.boun_client [OPTIONS]\n'
    print '(Caution: you have to run this command from the project root directory.)\n'
    exit(-1)

# Defaults:
DEFAULT_INTERFACE = 'eth0'
DEFAULT_PORT = MonitorServer.DEFAULT_PORT
DEFAULT_SERVER_IP = 'localhost'
DEFAULT_VERBOSITY = False


def main(address, interface, logfile_name, verbose):
    '''
    Initializes a BounClient which is inherited from MonitorClient
        :param address:   IP of the MonitorServer
        :param interface: interface of the BounClient
        :param visualize: registers to a MessageHandler to visualize
        :param verbose:   a boolean indicating whether logging is enabled or not
    '''
    mc = MonitorClient(address, interface, port=MonitorClient.DEFAULT_PORT, verbose=verbose)
    mc.register(PacketHistogramGraph())
    # mc.register(CallGraph())
    # mc.register(CpuMemPercentageGraph())
    # mc.register(OsStatsCountsGraph())

    if logfile_name:
        mc.register(Logger(logfile_name))

    mc.run_forever()

def print_help():
    print '\nUsage: python -m detectors.boun_client [OPTIONS]\n'
    print '\t-i (--interface) INTERFACE : input source           (default : eth0)'
    print '\t-o (--filename)  FILENAME  : output log name        (default : None)'
    print '\t-a (--ip)        IP        : boun_server ip address (default : 192.168.1.2)'
    print '\t-p (--port)      PORT      : boun_server ip port    (default : 5010)'
    print '\t-v (--verbose)             : verbosity              (default : False)\n'
    print 'Possible input sources are:'
    print '\t-network interfaces'
    print '\t-pcap files'
    print '\t-previous monitor outputs saved as pickle files\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Network Traffic Monitor', add_help=False)
    parser.add_argument('-i', '--interface', type=str, default=DEFAULT_INTERFACE)
    parser.add_argument('-o', '--logfile',   type=str, default=None)
    parser.add_argument('-a', '--ip',        type=str, default=DEFAULT_SERVER_IP)
    parser.add_argument('-p', '--port',      type=int, default = DEFAULT_PORT)
    parser.add_argument('-v', '--verbose',   action='store_true', default=DEFAULT_VERBOSITY)
    parser.add_argument('-h', '--help',      action='store_true', default=False)
    args = parser.parse_args()

    if args.help:
        print_help()
        exit(0)

    main(address=(args.ip, args.port), interface=args.interface, logfile_name=args.logfile, verbose=args.verbose)
