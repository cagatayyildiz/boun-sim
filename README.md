# BOUN-SIM
Session Initiation Protocol (SIP) is one of the most popular open standard signaling protocols designed for Voice Over Internet Protocol (VoIP). Yet, difficulties of access to a real SIP data set prevent researchers from studying on SIP-related tasks. The motivation of this work is to present a tool that eliminates the real data set obstacle. We developed a python library named BOUN-SIM that generates real-time SIP traffic by simulating behaviors of a number of users. Our system is also capable of recording the data and re-running the simulation.

Please refer to **boun-sim-documentation.pdf** for the software architecture, implementation details, installation manual, dependencies and how to run.

## Folder Content
Below are the brief description of each folder in this repository:

#### bcpm
An implementation of of Bayesian multiple change point model. You can see `bcpm/demo.py` and `bcpm/demo2.py` for experiments with synthetic and real-data, respectively.

#### monitor
Monitor is the unit that runs in a SIP server, collects the features of interest and delivers to some other machine via the Internet. See `monitor/boun_client.py` and `monitor/boun_server.py` for example implementations.

#### sample_data
This folder contains 4 different data sets, each of which containing 40 DDoS attacks along with SIP network traffic. SIP traffic is generated using our *Simulator* and a commercial vulnerability scanning tool named [Nova V-Spy](http://www.netas.com.tr/en/innovation-productization/nova-cyber-security-products/)

#### simulator
Simulator is a stand-alone program that generates the network traffic by exchanging SIP packets with a SIP server and runs independent of the rest of the modules. To produce SIP packets, we make use of [pjsip](http://www.pjsip.org/), an open source library implementing SIP and many other protocols.

#### Virtual Machine
Our simulation system together with all dependencies has been installed in [this virtual machine] (https://dl.dropboxusercontent.com/u/5464866/BOUN-VM.ova). You can download and open with [VirtualBox](https://www.virtualbox.org) and immediately run the simulator.

## About the Work
This study is a Bogazici University - NETAS Nova V-Gate collaboration and funded by TEYDEB project, "Realization of Anomaly Detection and Prevention with Learning System Architectures, Quality Improvement, High Rate Service Availability and Rich Services in a VoIP Firewall Product'', by the Scientific and Technological Research Council Of Turkey (TUBITAK).
