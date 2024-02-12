#!/usr/bin/env python3

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import OVSKernelSwitch, RemoteController, OVSSwitch
from mininet.link import TCLink
from ipaddress import IPv4Network
import socket

class CustomTopology(Topo):
    def __init__(self):
        # Inizializzazione
        Topo.__init__(self)

        host_config = dict(inNamespace=True)
        connecting_slice_link_config = dict(bw=50)
        host_link_config = dict()

        for i in range(5):
            sconfig = {"dpid": "%016x" % (i + 1)}
            self.addSwitch("s%d" % (i + 1), protocols="OpenFlow10", **sconfig)

        # Aggiungi gli host per le cinque slice (quinta non ha host)
        webcams = self.addHost('01', mac="00:00:00:00:00:01", **host_config)
        sirens = self.addHost('02', mac="00:00:00:00:00:02", **host_config)
        trafficlight = self.addHost('03', mac="00:00:00:00:00:03", **host_config)
        parkingsensor = self.addHost('04', mac="00:00:00:00:00:04", **host_config)
        sismicsensor = self.addHost('05', mac="00:00:00:00:00:05", **host_config)
        watersensor = self.addHost('06', mac="00:00:00:00:00:06", **host_config)
        weathersensor = self.addHost('07', mac="00:00:00:00:00:07", **host_config)
        schoolrouter = self.addHost('09', mac="00:00:00:00:00:09", **host_config)
        townhallrouter = self.addHost('0a', mac="00:00:00:00:00:0a", **host_config)

        # Crea i 6 server
        uno_server = self.addHost('server1', mac="00:00:00:00:00:0c", **host_config)
        due_server = self.addHost('server2', mac="00:00:00:00:00:0d", **host_config)
        tre_server = self.addHost('server3', mac="00:00:00:00:00:0e", **host_config)
        quattro_server = self.addHost('server4', mac="00:00:00:00:00:0f", **host_config)
        proxyserver = self.addHost('server5', mac="00:00:00:00:00:0b", **host_config)
        datacollectionserver = self.addHost('server6', mac="00:00:00:00:00:08", **host_config)

        # Collegamenti tra switch delle slice
        self.addLink('s1', 's5', 3, 5, **connecting_slice_link_config)
        self.addLink('s2', 's5', 3, 8, **connecting_slice_link_config)
        self.addLink('s3', 's5', 1, 6, **connecting_slice_link_config)
        self.addLink('s4', 's5', 1, 7, **connecting_slice_link_config)

        # Collegamenti tra switch e host delle slice
        self.addLink(webcams, 's1', 1, 1, **host_link_config)
        self.addLink(sirens, 's1', 1, 2, **host_link_config)
        #self.addLink(sirens, 's5', 2, 3, **host_link_config)
        self.addLink(trafficlight, 's2', 1, 1, **host_link_config)
        self.addLink(parkingsensor, 's2', 1, 2, **host_link_config)
        self.addLink(sismicsensor, 's3', 1, 2, **host_link_config)
        #self.addLink(sismicsensor, 's5', 2, 1, **host_link_config)
        self.addLink(watersensor, 's3', 1, 3, **host_link_config)
        #self.addLink(watersensor, 's5', 2, 2, **host_link_config)
        self.addLink(weathersensor, 's3', 1, 5, **host_link_config)
        self.addLink(schoolrouter, 's4', 1, 4, **host_link_config)
        self.addLink(townhallrouter, 's4', 1, 2, **host_link_config)

        # Collegamenti tra switch e server
        self.addLink(uno_server, 's5', 1, 1, **host_link_config)
        self.addLink(due_server, 's5', 1, 2, **host_link_config)
        self.addLink(tre_server, 's5', 1, 3, **host_link_config)
        self.addLink(quattro_server, 's5', 1, 4, **host_link_config)
        self.addLink(proxyserver, 's4', 1, 3, **host_link_config)
        self.addLink(datacollectionserver, 's3', 1, 4, **host_link_config)


if __name__ == '__main__':
    topo = CustomTopology()
    net = Mininet(
        topo=topo,
        switch=OVSKernelSwitch,
        build=False,
        autoSetMacs=False,
        autoStaticArp=True,
        link=TCLink,
    )
    net.build()
    net.start()

    net['s1'].cmd("ovs-vsctl set-controller s1 tcp:127.0.0.1:6633")
    net['s2'].cmd("ovs-vsctl set-controller s2 tcp:127.0.0.1:6634")
    net['s3'].cmd("ovs-vsctl set-controller s3 tcp:127.0.0.1:6635")
    net['s4'].cmd("ovs-vsctl set-controller s4 tcp:127.0.0.1:6636")
    net['s5'].cmd("ovs-vsctl set-controller s5 tcp:127.0.0.1:6637")
    CLI(net)
    net.stop()
