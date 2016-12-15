''' 
This study is a Bogazici University - NETAS Nova V-Gate collaboration and funded by TEYDEB project "Realization of Anomaly Detection and Prevention with Learning System Architectures, Quality Improvement, High Rate Service Availability and Rich Services in a VoIP Firewall Product'', by the Scientific and Technological Research Council Of Turkey (TUBITAK).
'''

import argparse

from batch import *
from model import CallGraph, Model
import socket

# ---- ! DEFAULT MODEL PARAMETERS ! ----
__NUM_USERS__ = int(8)
'''Number of users in the simulation'''

__MAX_NUM_USERS__ = int(5000)
'''The upper limit for the number of users, which is most probably equal to the number of accounts registered to the SIP server used'''

__NUM_GROUPS__ = int(4)
'''Number of groups in the simulation'''

__BASE_ID__ = int(10000)
'''id of user i is equal to __BASE_ID__ + i, i being a non-negative integer'''

__SIP_SERVER_IP_ADDRESS__ = "192.168.1.9"
'''Default IP address of the SIP server used in the simulation'''

__SIMULATION_CONFIG_FILE__ = "../etc/simulation_params.xml"
'''Default path to the simulation configuration file'''

__TRAFFIC_INT__ = "low"
'''Default traffic intensity'''

__SIMULATION_DUR__ = int(1000)
'''Default simulation duration (in seconds)'''

PARAM_LIST = ["wait_time_shape", "wait_time_scale",
              "aver_conv_dur_lower", "aver_conv_dur_upper",
              "ans_prob_lower", "ans_prob_upper",
              "reg_period_shape", "reg_period_scale",
              "unreg_dur_shape", "unreg_dur_scale"]
'''The list of parameters that simulation configuration file must define'''

__INTENSITY_LIST__ = ["low", "high"]
'''Intensity levels at which simulator can generate traffic'''

# ---- ! DEFAULT MODEL PARAMETERS ! ----


def create_user_batches(args):
    """Given the arguments from the user, this function forks a number of child processes and start simulation.

    C{PJSUA} library is designed in such a way that only a single instance of C{PJSUA} library is allowed to be
    initialized in a process and at most 8 users can be created from a C{PJSUA} library.
    Therefore, larger simulations can be realized by initiating multiple processes, or batches,
    each containing one C{PJSUA} library (and hence up to 8 users).

    @type   args:   namespace
    @param  args:   Arguments given by the user
    """
    call_graph = CallGraph(args.num_users, args.num_groups)
    seed_ = np.random.randint(low=0, high=int(1e5))
    model = Model(call_graph, seed_, args.traf_int, args.sim_config_file, __INTENSITY_LIST__, PARAM_LIST)
    uids = range(0, args.num_users)

    batch = TrafficGeneratingBatch(0, uids, model, args.server_ip, args.num_users,
                           args.num_users, args.base_id, args.sim_duration, args.verbose)
    batch.start()


def main():
    """Gets user parameters and checks whether they are valid or not.
    If they are, C{create_user_batches} method is executed and simulation starts.
    Otherwise, erroneous option is printed and execution is terminated.
    """
    # Parse Command Line
    parser = argparse.ArgumentParser(description='Network Traffic Generator')
    parser.add_argument('-n', '--num_users', type=int, help='Number of SIP users.', default=__NUM_USERS__)
    parser.add_argument('-k', '--num_groups', type=int, help='Number of SIP user groups.', default=__NUM_GROUPS__)
    parser.add_argument('-a', '--server_ip', type=str, help='SIP server IP.', default=__SIP_SERVER_IP_ADDRESS__)
    parser.add_argument('-i', '--traf_int', type=str, help='Default traffic intensity.', default=__TRAFFIC_INT__)
    parser.add_argument('-f', '--sim_config_file', type=str, help='Simulation configuration file.', default=__SIMULATION_CONFIG_FILE__)
    parser.add_argument('-id', '--base_id', type=int, help='Min ID in users created.', default=__BASE_ID__)
    parser.add_argument('-t', '--sim_duration', type=int, help='Simulation duration.', default=__SIMULATION_DUR__)
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help="Print simulation logs or not")

    args = parser.parse_args()

    if args.num_users > __MAX_NUM_USERS__:
        print 'Error: Number of users cannot exceed %d' % __MAX_NUM_USERS__
        return

    if args.num_groups > args.num_users:
        print 'Error: Number of groups cannot exceed number of users'
        return

    try:
        socket.inet_aton(args.server_ip)
    except socket.error:
        print "Please enter a valid IP address"
        return

    if args.num_users + args.base_id >= __BASE_ID__ + __MAX_NUM_USERS__:
        print 'Error: User ids cannot exceed %d' % (__BASE_ID__ + __MAX_NUM_USERS__)
        return

    if args.traf_int not in __INTENSITY_LIST__:
        print 'Error: Invalid traffic intensity. Pick one of', __INTENSITY_LIST__
        return

    try:
        params = Model.read_attributes(PARAM_LIST,args.sim_config_file)
        assert params is not None
    except:
        print "Error: Check your configuration file"
        return

    try:
        base_id = int(args.base_id)
        if base_id < 0:
            print 'Error: Base id must be an integer greater than', __BASE_ID__
            return
    except:
        print 'Error: Base id must be an integer greater than', __BASE_ID__
        return

    try:
        sim_dur = int(args.sim_duration)
        if sim_dur < 0:
            print 'Error: Simulation duration must be a nonnegative integer'
            return
    except:
        print 'Error: Simulation duration must be a nonnegative integer'
        return

    # if all checks are passed,then batch instances are initialized
    create_user_batches(args)


if __name__ == "__main__":
    main()
