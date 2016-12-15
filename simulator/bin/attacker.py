''' 
This study is a Bogazici University - NETAS Nova V-Gate collaboration and funded by TEYDEB project "Realization of Anomaly Detection and Prevention with Learning System Architectures, Quality Improvement, High Rate Service Availability and Rich Services in a VoIP Firewall Product'', by the Scientific and Technological Research Council Of Turkey (TUBITAK).
'''

__author__ = 'cagatay'

import argparse

from batch import *
from model import CallGraph,Model

# ---- ! DO NOT CHANGE ! ----
__NUM_USERS__ = int(10)
__MAX_NUM_USERS__ = int(1000)

__BASE_ID__ = int(10000)

__NUM_USERS_PER_BATCH__ = int(1)
__MAX_NUM_USERS_PER_BATCH__ = int(2)

__SIP_SERVER_IP_ADDRESS__ = "79.123.176.59"

__DEFAULT_TRAFFIC_INT__ = "low"

__SIM_DUR__ = int(1000) # in seconds

__ATTACK_TYPES__ = ['reg','inv', 'subs']
__ATTACK_RATE__ = 10


def create_user_batches(args):
    '''
    given the parameters, forks a number of child processes and start simulation
    :param num_users: number of users in the simulation
    :param num_users_per_batch: number of users in each batch. this cannot be greater than 8.
    :return: batches(processes created)
    '''
    batches = []

    # divide user ids into batches
    uid = range(0, args.num_users, args.num_users_per_batch)
    if uid[-1] != args.num_users:
        uid.append(args.num_users)
    # start batches
    for i in range(len(uid)-1):
        batches.append(AttackGeneratingBatch(i, range(uid[i], uid[i+1]), args.server_ip, args.num_users, args.num_users_per_batch, args.base_id, args.attack_type, args.attack_rate))
    for i in range(len(batches)):
        time.sleep(3.0/len(batches))
        batches[i].start()

def main():

    # Parse Command Line
    parser = argparse.ArgumentParser(description='Network Traffic Generator')
    parser.add_argument('-n', '--num_users', type=int, help='Number of SIP users.', default = __NUM_USERS__)
    parser.add_argument('-b', '--num_users_per_batch', type=int, help='Number of users per process.', default = __NUM_USERS_PER_BATCH__)
    parser.add_argument('-a', '--server_ip', type=str, help='SIP server IP.', default = __SIP_SERVER_IP_ADDRESS__)
    parser.add_argument('-id', '--base_id', type=int, help='Min ID in users created', default = __BASE_ID__)
    parser.add_argument('-dur', '--sim_duration', type=int, help='Duration of the simulation', default = __SIM_DUR__)
    parser.add_argument('-atype', '--attack_type', type=str, help='Attack type: invite, register.', default = __ATTACK_TYPES__[0])
    parser.add_argument('-r', '--attack_rate', type=int, help='Attack rate', default = __ATTACK_RATE__)

    args = parser.parse_args()

    # Security Checks
    if args.num_users > __MAX_NUM_USERS__:
        print 'Error: Number of users cannot exceed %d' % __MAX_NUM_USERS__
        return

    if args.num_users_per_batch > __NUM_USERS_PER_BATCH__:
        print 'Error: Number of users per batch cannot exceed %d' % __NUM_USERS_PER_BATCH__
        return

    if args.num_users + args.base_id >= __BASE_ID__ + __MAX_NUM_USERS__:
        print 'Error: User ids cannot exceed %d' % (__BASE_ID__ + __MAX_NUM_USERS__)
        return

    if args.base_id < __BASE_ID__:
        print 'Error: Base id must be greater than', __BASE_ID__
        return

    if args.attack_type not in __ATTACK_TYPES__:
        print 'Error: Attack type must be one of', __ATTACK_TYPES__
        return

    # Create User Processes
    create_user_batches(args)

if __name__ == "__main__":
    main()