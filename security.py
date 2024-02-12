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

    linked_hosts = ["00:00:00:00:00:01", "00:00:00:00:00:02", "00:00:00:00:00:05", "00:00:00:00:00:06",
                    "00:00:00:00:00:09", "00:00:00:00:00:0a", "00:00:00:00:00:0c"]

    udp_dst = ["00:00:00:00:00:05", "00:00:00:00:00:06"]

    udp_src = ["00:00:00:00:00:02"]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch, self).__init__(*args, **kwargs)

        # outport = self.mac_to_port[dpid][mac_address]
        self.mac_to_port = {
            1: {"00:00:00:00:00:01": 1, "00:00:00:00:00:02": 2, "00:00:00:00:00:05": 3, "00:00:00:00:00:06": 3,
                "00:00:00:00:00:09": 3, "00:00:00:00:00:0a": 3, "00:00:00:00:00:0c": 3}
        }

    def add_flow(self, datapath, in_port, dst, src, actions):
        ofproto = datapath.ofproto

        match = datapath.ofproto_parser.OFPMatch(
            in_port=in_port,
            dl_dst=haddr_to_bin(dst), dl_src=haddr_to_bin(src))

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

        protocol = 0
        if pkt.get_protocol(udp.udp):
            protocol = 1  # UDP
        elif pkt.get_protocol(tcp.tcp):
            protocol = 2  # TCP
        elif pkt.get_protocol(icmp.icmp):
            protocol = 3  # ICMP

        if protocol not in [1, 2, 3]:
            return

        out_port = 0

        if dpid in self.mac_to_port:
            if dst in self.mac_to_port[dpid]:
                self.logger.info('[LOG] entra in IF: dpid:%s, src:%s, dst:%s', dpid, src, dst)
                out_port = self.mac_to_port[dpid][dst]

        #if not pkt.get_protocol(tcp.tcp) and src in self.udp_src and dst in self.udp_dst:
            #out_port = 3  # force port towards s5 for udp packets from 02 towards 05 or 06
        if not pkt.get_protocol(tcp.tcp):
            if (src in self.udp_src and dst in self.udp_dst):
                out_port = 3
            elif (src in self.udp_dst and dst in self.udp_src):
                out_port = 2

        actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != 0 and dst in self.linked_hosts:
            self.add_flow(datapath, msg.in_port, dst, src, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port,
            actions=actions, data=data)

        self.logger.info("[LOG] switch:%s src:%s dst:%s inPort:%s outPort:%d, protocol:%d", dpid, src, dst, msg.in_port,
                         out_port, protocol)
        if out_port != 0:
            datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def _port_status_handler(self, ev):
        msg = ev.msg
        reason = msg.reason
        port_no = msg.desc.port_no

        ofproto = msg.datapath.ofproto
        if reason == ofproto.OFPPR_ADD:
            self.logger.info("port added %s", port_no)
        elif reason == ofproto.OFPPR_DELETE:
            self.logger.info("port deleted %s", port_no)
        elif reason == ofproto.OFPPR_MODIFY:
            self.logger.info("port modified %s", port_no)
        else:
            self.logger.info("Illegal port state %s %s", port_no, reason)
