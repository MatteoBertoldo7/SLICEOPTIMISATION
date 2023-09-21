#!/usr/bin/env python3

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.link import TCLink
from ipaddress import IPv4Network
import socket

class CustomTopology(Topo):
    def __init__(self):
        # Inizializzazione
        Topo.__init__(self)

        # Aggiungi gli switch per le cinque slice
        wifi_switch = self.addSwitch('s1')
        iot_switch = self.addSwitch('s2')
        traffic_switch = self.addSwitch('s3')
        safety_switch = self.addSwitch('s4')
        communication_switch = self.addSwitch('s5')

        # Aggiungi gli host per le cinque slice (quinta non ha host)
        wifi_host1 = self.addHost('h11')
        wifi_host2 = self.addHost('h12')
        iot_host1 = self.addHost('h21')
        iot_host2 = self.addHost('h22')
        traffic_host1 = self.addHost('h31')
        traffic_host2 = self.addHost('h32')
        safety_host1 = self.addHost('h41')
        safety_host2 = self.addHost('h42')

        # Collegamenti tra switch delle slice
        self.addLink(wifi_switch, communication_switch, bw=500, delay='10ms', loss=0, use_htb=True)
        self.addLink(iot_switch, communication_switch, bw=20, delay='25ms', loss=0, use_htb=True)
        self.addLink(traffic_switch, communication_switch, bw=100, delay='2ms', loss=0, use_htb=True)
        self.addLink(safety_switch, communication_switch, bw=50, delay='8ms', loss=0, use_htb=True)

        # Collegamenti tra switch e host delle slice
        self.addLink(wifi_host1, wifi_switch)
        self.addLink(wifi_host2, wifi_switch)
        self.addLink(iot_host1, iot_switch)
        self.addLink(iot_host2, iot_switch)
        self.addLink(traffic_host1, traffic_switch)
        self.addLink(traffic_host2, traffic_switch)
        self.addLink(safety_host1, safety_switch)
        self.addLink(safety_host2, safety_switch)

        # Crea i 5 server
        wifi_server = self.addHost('server1')
        iot_server = self.addHost('server2')
        traffic_server = self.addHost('server3')
        safety_server = self.addHost('server4')
        communication_server = self.addHost('server5')

        # Collegamenti tra switch e server
        self.addLink(wifi_server, wifi_switch)
        self.addLink(iot_server, iot_switch)
        self.addLink(traffic_server, traffic_switch)
        self.addLink(safety_server, safety_switch)
        self.addLink(communication_server, communication_switch)

        # Definisci le subnet per ciascuna slice
        wifi_subnet = IPv4Network('192.168.1.0/24')
        iot_subnet = IPv4Network('192.168.2.0/24')
        traffic_subnet = IPv4Network('192.168.3.0/24')
        safety_subnet = IPv4Network('192.168.4.0/24')
        communication_subnet = IPv4Network('192.168.5.0/24')

        # Assegna gli indirizzi IP agli host nelle slice
        wifi_host1.setIP(str(wifi_subnet[1]))
        wifi_host2.setIP(str(wifi_subnet[2]))
        iot_host1.setIP(str(iot_subnet[1]))
        iot_host2.setIP(str(iot_subnet[2]))
        traffic_host1.setIP(str(traffic_subnet[1]))
        traffic_host2.setIP(str(traffic_subnet[2]))
        safety_host1.setIP(str(safety_subnet[1]))
        safety_host2.setIP(str(safety_subnet[2]))

if __name__ == '__main__':
    topo = CustomTopology()
    net = Mininet(
        topo=topo,
        switch=OVSKernelSwitch,
        build=False,
        autoSetMacs=True,
        autoStaticArp=True,
        link=TCLink,
    )
    net.build()

    # Configura il controller SDN
    controller = RemoteController('c0', ip='127.0.0.1', port=6633)
    net.addController(controller)

    net.start()
    CLI(net)
    net.stop()
