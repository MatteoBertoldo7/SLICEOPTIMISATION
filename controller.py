from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet
import logging
import time

class SDNController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SDNController, self).__init__(*args, **kwargs)
        self.byte_trasmessi = {}
        self.byte_ricevuti = {}
        self.soglia_di_allarme = 1000000
        self.last_measurement_time = time.time()

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        current_time = time.time()
        elapsed_time = current_time - self.last_measurement_time
        self.last_measurement_time = current_time
        msg = ev.msg
        dp_id = msg.datapath.id

        for stat in msg.body:
            byte_trasmessi = stat.byte_count
            byte_ricevuti = stat.packet_count * 1024
            self.byte_trasmessi[dp_id] = byte_trasmessi
            self.byte_ricevuti[dp_id] = byte_ricevuti

            utilizzo_banda = (byte_trasmessi + byte_ricevuti) / elapsed_time
            if utilizzo_banda > self.soglia_di_allarme:
                logging.warning("L'utilizzo della banda per lo switch %s ha superato la soglia di allarme.", dp_id)
                self.condividi_banda(dp_id, utilizzo_banda)

    def condividi_banda(self, switch_id, utilizzo_wifi_pubblico):
        if switch_id == 's1':  # Cambia 's1' con l'ID corretto dello switch WiFi pubblico
            wifi_pubblico_utilizzo = self.byte_trasmessi.get(switch_id, 0) + self.byte_ricevuti.get(switch_id, 0)
            if wifi_pubblico_utilizzo > 0.9 * self.soglia_di_allarme:
                self.redistribuisci_banda(utilizzo_wifi_pubblico)

    def redistribuisci_banda(self, utilizzo_wifi_pubblico):
        # Imposta manualmente le limitazioni di banda per 's3' (traffic) e 's2' (iot)
        if 's3' in self.byte_trasmessi:
            self.byte_trasmessi['s3'] = 100 * 1024 * 1024  # 100 MB in byte
            self.byte_ricevuti['s3'] = 100 * 1024 * 1024  # 100 MB in byte
        if 's2' in self.byte_trasmessi:
            self.byte_trasmessi['s2'] = 50 * 1024 * 1024  # 50 MB in byte
            self.byte_ricevuti['s2'] = 50 * 1024 * 1024  # 50 MB in byte

        num_aree_di_rete = len(self.byte_trasmessi)
        if num_aree_di_rete > 2:
            banda_restante = utilizzo_wifi_pubblico - (100 * 1024 * 1024 + 50 * 1024 * 1024)
            banda_per_area = banda_restante / (num_aree_di_rete - 2)
        
        for switch_id in self.byte_trasmessi:
            if switch_id != 's1':  # Cambia 's1' con l'ID corretto dello switch WiFi pubblico
                self.byte_trasmessi[switch_id] = banda_per_area
                self.byte_ricevuti[switch_id] = banda_per_area

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        pkt = packet.Packet(msg.data)

        eth_pkt = pkt.get_protocol(ethernet.ethernet)

        if eth_pkt:
            src_mac = eth_pkt.src
            dst_mac = eth_pkt.dst
            dp_id = msg.datapath.id
            byte_trasmessi = self.byte_trasmessi.get(dp_id, 0)
            byte_ricevuti = self.byte_ricevuti.get(dp_id, 0)
            utilizzo_banda = (byte_trasmessi + byte_ricevuti) / elapsed_time

            if utilizzo_banda > self.soglia_di_allarme:
                logging.warning("L'utilizzo della banda ha superato la soglia di allarme.")

if __name__ == '__main__':
    from ryu.cmd import manager
    manager.main(['ryu', 'controller.py'])
