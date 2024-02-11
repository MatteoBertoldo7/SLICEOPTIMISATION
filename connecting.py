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

    hosts = ["00:00:00:00:00:01", "00:00:00:00:00:02", "00:00:00:00:00:03", "00:00:00:00:00:04",
             "00:00:00:00:00:05", "00:00:00:00:00:06", "00:00:00:00:00:07", "00:00:00:00:00:08",
             "00:00:00:00:00:09", "00:00:00:00:00:0a", "00:00:00:00:00:0b", "00:00:00:00:00:0c",
             "00:00:00:00:00:0d", "00:00:00:00:00:0e", "00:00:00:00:00:0f"]

    hosts_slice1 = ["00:00:00:00:00:01", "00:00:00:00:00:02"]
    hosts_slice2 = ["00:00:00:00:00:03", "00:00:00:00:00:04"]
    hosts_slice3 = ["00:00:00:00:00:05", "00:00:00:00:00:06", "00:00:00:00:00:07", "00:00:00:00:00:08"]
    hosts_slice4 = ["00:00:00:00:00:09", "00:00:00:00:00:0a", "00:00:00:00:00:0b"]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch, self).__init__(*args, **kwargs)

        self.mac_to_port = {
            6: {"00:00:00:00:00:0c": 1, "00:00:00:00:00:0d": 2, "00:00:00:00:00:0e": 3, "00:00:00:00:00:0f": 4,
                "00:00:00:00:00:01": 5, "00:00:00:00:00:02": 5, "00:00:00:00:00:05": 6, "00:00:00:00:00:06": 6,
                "00:00:00:00:00:07": 6, "00:00:00:00:00:08": 6, "00:00:00:00:00:09": 7, "00:00:00:00:00:0a": 7,
                "00:00:00:00:00:0b": 7, "00:00:00:00:00:03": 8, "00:00:00:00:00:04": 8}
        }

        # out_port = slice_to_port[dpid][in_port]
        #self.slice_to_port = {
            #12: {1: 1, 2: 1, 3: 1, 4: 0, 5: 0, 6: 0}
        #}
        #self.slice_to_port1 = {
            #12: {1: 1, 2: 1, 3: 1, 4: 0, 5: 0, 6: 0}
        #}

        #self.slice_to_port2 = {
            #12: {1: 2, 2: 2, 3: 2, 4: 0, 5: 0, 6: 0}
        #}

        #self.slice_to_port3 = {
            #12: {1: 3, 2: 3, 3: 3, 4: 0, 5: 0, 6: 0}
        #}

        #self.slice_to_port3 = {
            #12: {1: 3, 2: 3, 3: 3, 4: 0, 5: 0, 6: 0}
        #}

    def add_flow(self, datapath, in_port, dst, src, actions, protocol):
        ofproto = datapath.ofproto
        if protocol == 1:  # udp
            proto = 0x11
        elif protocol == 2:  # tcp
            proto = 0x06
        else:  # icmp
            proto = 0x01

        match = datapath.ofproto_parser.OFPMatch(
            in_port=in_port,
            dl_dst=haddr_to_bin(dst), dl_src=haddr_to_bin(src),
            dl_type=ether_types.ETH_TYPE_IP,
            nw_proto=proto)

        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, cookie=0,
            command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            priority=ofproto.OFP_DEFAULT_PRIORITY,
            flags=ofproto.OFPFF_SEND_FLOW_REM, actions=actions)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        #self.mac_to_port.setdefault(dpid, {})

        # learn a mac address to avoid FLOOD next time.
        #self.mac_to_port[dpid][src] = msg.in_port

        #self.logger.info("LOG packet in %s %s %s %s", dpid, src, dst, msg.in_port)

        out_port = 0

        if dpid in self.mac_to_port:
            if dst in self.mac_to_port[dpid]:
                out_port = self.mac_to_port[dpid][dst]
            else:
                out_port = ofproto.OFPP_FLOOD
        else:
            out_port = ofproto.OFPP_FLOOD

        protocol = 0
        if pkt.get_protocol(udp.udp):
            protocol = 1  # UDP
        elif pkt.get_protocol(tcp.tcp):
            protocol = 2  # TCP
        elif pkt.get_protocol(icmp.icmp):
            protocol = 3  # ICMP

        if protocol not in [1, 2, 3]:
            return

        # filter the udp packets, sending them to the corresponding server
        #if pkt.get_protocol(udp.udp) and msg.in_port != 4 and msg.in_port != 5 and msg.in_port != 6:
            #out_port = 3 + msg.in_port  # if arrives from slice1, send to server1 etc
            #protocol = 1  # udp
        #elif (pkt.get_protocol(icmp.icmp)):
            #protocol = 3
            #if (dst in self.hosts_slice1):
                #out_port = self.slice_to_port1[dpid][msg.in_port]
            #elif (dst in self.hosts_slice2):
                #out_port = self.slice_to_port2[dpid][msg.in_port]
            #elif (dst in self.hosts_slice3):
                #out_port = self.slice_to_port3[dpid][msg.in_port]
            #elif (dst in self.hosts_slice4):
                #out_port = self.slice_to_port4[dpid][msg.in_port]
            # also making sure that packets aren't coming from server
            #elif (msg.in_port != 4 and msg.in_port != 5 and msg.in_port != 6):
                #out_port = 3 + msg.in_port
        #elif (pkt.get_protocol(tcp.tcp)):
            #protocol = 2
            # handles communication towards slice1
            #if (dst in self.hostSlice1):
                # slice2 has to use TCP port 3000, slice3 has to use TCP but can use any port
                #if ((src in self.hostSlice2 and (pkt.get_protocol(tcp.tcp).dst_port == 3000 or pkt.get_protocol(
                        #tcp.tcp).src_port == 3000)) or src in self.hostSlice3):
                   # out_port = self.slice_to_port1[dpid][msg.in_port]
                # filter remaning packets, sending them to the corresponding server
                # also making sure that packets aren't coming from servers
                #elif (msg.in_port != 4 and msg.in_port != 5 and msg.in_port != 6):
                    #out_port = 3 + msg.in_port
            # handles communication towards slice2
            #elif (dst in self.hostSlice2):
                # similar to first case
                #if ((src in self.hostSlice1 and (pkt.get_protocol(tcp.tcp).dst_port == 3000 or pkt.get_protocol(
                        #tcp.tcp).src_port == 3000)) or src in self.hostSlice3):
                    #out_port = self.slice_to_port2[dpid][msg.in_port]
                #elif (msg.in_port != 4 and msg.in_port != 5 and msg.in_port != 6):
                    #out_port = 3 + msg.in_port
            # handles communication towards slice3
            #elif (dst in self.hostSlice3):
                #out_port = self.slice_to_port3[dpid][msg.in_port]
            #elif (msg.in_port != 4 and msg.in_port != 5 and msg.in_port != 6):
                #out_port = 3 + msg.in_port

        # drop packets if protocol is not TCP, UDP or ICMP
        #else:
            #return

        #if out_port == 0 or (not pkt.get_protocol(udp.udp) and (dst in self.servers)):
            # drop packets recieved from servers (they are filter servers)
            #return

        actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        # install an additional column for the packet type
        if out_port != ofproto.OFPP_FLOOD and dst in self.hosts and src in self.hosts and protocol != 0:
            self.add_flow(datapath, msg.in_port, dst, src, actions, protocol)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port,
            actions=actions, data=data)

        self.logger.info("[LOG] switch:%s %s %s inPort:%s outPort:%d, protocol:%d", dpid, src, dst, msg.in_port,
                         out_port, protocol)
        datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def _port_status_handler(self, ev):
        msg = ev.msg
        reason = msg.reason
        port_no = msg.desc.port_no

        ofproto = msg.datapath.ofproto
        if reason == ofproto.OFPPR_ADD:
            self.logger.info("Port added %s", port_no)
        elif reason == ofproto.OFPPR_DELETE:
            self.logger.info("Port deleted %s", port_no)
        elif reason == ofproto.OFPPR_MODIFY:
            self.logger.info("Port modified %s", port_no)
        else:
            self.logger.info("Illeagal port state %s %s", port_no, reason)