from typing import Protocol
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import udp
from ryu.lib.packet import tcp
from ryu.lib.packet import icmp

class SimpleSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]
    
    hosts=["00:00:00:00:00:01","00:00:00:00:00:02","00:00:00:00:00:03","00:00:00:00:00:04",
           "00:00:00:00:00:05","00:00:00:00:00:06","00:00:00:00:00:07","00:00:00:00:00:08",
           "00:00:00:00:00:09", "00:00:00:00:00:0a", "00:00:00:00:00:0b", "00:00:00:00:00:0c", 
           "00:00:00:00:00:0d", "00:00:00:00:00:0e", "00:00:00:00:00:0f" ]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch, self).__init__(*args, **kwargs)

        # outport = self.mac_to_port[dpid][mac_address]
        self.mac_to_port = {
        }

        # out_port = slice_to_port[dpid][in_port]
        self.slice_to_port = {
            1: {1: 3, 2: 3, 3: 0}
        }

        self.end_switches = [1]
