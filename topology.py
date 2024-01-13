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

        host_config = dict(inNamespace=True)
        slice1_link_config = dict()
        slice2_link_config = dict()
        slice3_link_config = dict()
        slice4_link_config = dict()
        connecting_slices_link_config = dict()
        host_link_config = dict()
        server_link_config = dict()

        # Aggiungi gli switch per le cinque slice
        #wifi_switch = self.addSwitch('s1')
        #iot_switch = self.addSwitch('s2')
        #traffic_switch = self.addSwitch('s3')
        #safety_switch = self.addSwitch('s4')
        #communication_switch = self.addSwitch('s5')
        #allarme_switch = self.addSwitch('s6')

        for i in range(5):
            sconfig = {"dpid": "%016x" % (i + 1)}
            self.addSwitch("s%d" % (i + 1), protocols="OpenFlow10", **sconfig)

        # Aggiungi gli host per le cinque slice (quinta non ha host)
        schoolrouter = self.addHost('h11', **host_config)
        townhallrouter = self.addHost('h12', **host_config)
        sismicsensor = self.addHost('h21', **host_config)
        watersensor = self.addHost('h22', **host_config)
        weathersensor = self.addHost('h23', **host_config)
        trafficlight = self.addHost('h31', **host_config)
        parkingsensor = self.addHost('h32', **host_config)
        webcams = self.addHost('h41', **host_config)
        sirens = self.addHost('h42', **host_config)

        # Crea i 6 server
        wifi_server = self.addHost('server1')
        uno_server = self.addHost('server2')
        due_server = self.addHost('server3')
        tre_server = self.addHost('server4')
        quattro_server = self.addHost('server5')
        datacollection_server = self.addHost('server6')

        # Collegamenti tra switch delle slice
        self.addLink('s1', 's5')
        self.addLink('s2', 's5')
        self.addLink('s3', 's5')
        self.addLink('s4', 's5')
        self.addLink('s2', 's6')
        self.addLink('s6', 's4')

        # Collegamenti tra switch e host delle slice
        self.addLink(schoolrouter, 's1')
        self.addLink(townhallrouter, 's1')
        self.addLink(sismicsensor, 's2')
        self.addLink(watersensor, 's2')
        self.addLink(weathersensor, 's2')
        self.addLink(sismicsensor, 's6')
        self.addLink(watersensor, 's6')
        self.addLink(sirens, 's6')
        self.addLink(trafficlight, 's3')
        self.addLink(parkingsensor, 's3')
        self.addLink(sirens, 's4')
        self.addLink(webcams, 's4')


        # Collegamenti tra switch e server
        self.addLink(wifi_server, 's1')
        self.addLink(uno_server, 's5')
        self.addLink(due_server, 's5')
        self.addLink(tre_server, 's5')
        self.addLink(quattro_server, 's5')
        self.addLink(datacollection_server, 's2')

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
        iot_host2.setIP(str(iot_subnet[3]))
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
