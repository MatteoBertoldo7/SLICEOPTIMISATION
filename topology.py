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
        allarme_switch = self.addSwitch('s6')

        # Aggiungi gli host per le cinque slice (quinta non ha host)
        schoolrouter = self.addHost('h11')
        townhallrouter = self.addHost('h12')
        sismicsensor = self.addHost('h21')
        watersensor = self.addHost('h22')
        weathersensor = self.addHost('h23')
        trafficlight = self.addHost('h31')
        parkingsensor = self.addHost('h32')
        webcams = self.addHost('h41')
        sirens = self.addHost('h42')

        # Collegamenti tra switch delle slice
        self.addLink(wifi_switch, communication_switch, bw=500, delay='10ms', loss=0, use_htb=True)
        self.addLink(iot_switch, communication_switch, bw=50, delay='25ms', loss=0, use_htb=True)
        self.addLink(traffic_switch, communication_switch, bw=100, delay='2ms', loss=0, use_htb=True)
        self.addLink(safety_switch, communication_switch, bw=80, delay='8ms', loss=0, use_htb=True)
        self.addLink(iot_switch, allarme_switch, bw=50, delay='25ms', loss=0, use_htb=True)
        self.addLink(allarme_switch, safety_switch, bw=50, delay='25ms', loss=0, use_htb=True)

        # Collegamenti tra switch e host delle slice
        self.addLink(schoolrouter, wifi_switch)
        self.addLink(townhallrouter, wifi_switch)
        self.addLink(sismicsensor, iot_switch)
        self.addLink(watersensor, iot_switch)
        self.addLink(weathersensor, iot_switch)
        self.addLink(sismicsensor, allarme_switch)
        self.addLink(watersensor, allarme_switch)
        self.addLink(sirens, allarme_switch)        
        self.addLink(trafficlight, traffic_switch)
        self.addLink(parkingsensor, traffic_switch)
        self.addLink(sirens, safety_switch)
        self.addLink(webcams, safety_switch)

        # Crea i 6 server
        wifi_server = self.addHost('server1')
        uno_server = self.addHost('server2')
        due_server = self.addHost('server3')
        tre_server = self.addHost('server4')
        quattro_server = self.addHost('server5')
        datacollection_server = self.addHost('server4')


        # Collegamenti tra switch e server
        self.addLink(wifi_server, wifi_switch)
        self.addLink(uno_server, communication_switch)
        self.addLink(due_server, communication_switch)
        self.addLink(tre_server, communication_switch)
        self.addLink(quattro_server, communication_switch)
        self.addLink(datacollection_server, iot_switch)

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
