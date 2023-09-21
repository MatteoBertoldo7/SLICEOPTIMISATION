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
        #metto soglia di allarme al 90% della banda che ha a disposizione il wifi pubblico
        self.soglia_di_allarme = 500000000 * 0.9  # 90% di 500 Mbps
        self.soglia_di_allarme_security = 80000000 * 0.85  # 85% di 80 Mbps
        self.last_measurement_time = time.time()
        self.slice_states = {'s1': 'on', 's2': 'on', 's3': 'on', 's4': 'on', 's5': 'on'}
        self.add_message_handler(SliceControlMessage, self.handle_slice_control_message)



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
            if utilizzo_banda > self.soglia_di_allarme_security:
                logging.warning("L'utilizzo della banda per lo switch %s ha superato la soglia di allarme.", dp_id)
                self.condividi_banda(dp_id, utilizzo_banda)
            elif utilizzo_banda > self.soglia_di_allarme:
                logging.warning("L'utilizzo della banda per lo switch %s ha superato la soglia di allarme.", dp_id)
                self.condividi_banda(dp_id, utilizzo_banda)              

    def condividi_banda(self, switch_id, utilizzo_slice):
        if switch_id == 's1':
            wifi_pubblico_utilizzo = self.byte_trasmessi.get(switch_id, 0) + self.byte_ricevuti.get(switch_id, 0)
            if wifi_pubblico_utilizzo > self.soglia_di_allarme:
                self.redistribuisci_banda(utilizzo_slice)
        elif switch_id == 's4':
            security_utilizzo = self.byte_trasmessi.get(switch_id, 0) + self.byte_ricevuti.get(switch_id, 0)
            if security_utilizzo > self.soglia_di_allarme_security:
                self.redistribuisci_banda_security(utilizzo_security)  # Cambia qui


    def redistribuisci_banda(self, utilizzo_wifi_pubblico):
        # Imposta manualmente le limitazioni di banda per 's3' (traffic) e 's2' (iot)
        if 's3' in self.byte_trasmessi: #normalmente è 100 totale (metto 60)
            self.byte_trasmessi['s3'] = 30 * 1024 * 1024  # 30 MB in byte
            self.byte_ricevuti['s3'] = 30 * 1024 * 1024  # 30 MB in byte
        if 's2' in self.byte_trasmessi: #normalmente è 50, metto a 30
            self.byte_trasmessi['s2'] = 15 * 1024 * 1024  # 15 MB in byte
            self.byte_ricevuti['s2'] = 15 * 1024 * 1024  # 15 MB in byte

        if utilizzo_wifi_pubblico < self.soglia_di_allarme * 0.66:
            # Reimposta le bande originali per 's2' e 's3' (50 e 100)
            self.byte_trasmessi['s2'] = 25 * 1024 * 1024 
            self.byte_ricevuti['s2'] = 25 * 1024 * 1024
            self.byte_trasmessi['s3'] = 50 * 1024 * 1024
            self.byte_ricevuti['s3'] = 50 * 1024 * 1024
        else:
            banda_restante = utilizzo_wifi_pubblico - (60 * 1024 * 1024 + 30 * 1024 * 1024)
            banda_per_area = banda_restante / 2

        for switch_id in self.byte_trasmessi:
            if switch_id != 's1':  # Cambia 's1' con l'ID corretto dello switch WiFi pubblico
                self.byte_trasmessi[switch_id] = banda_per_area
                self.byte_ricevuti[switch_id] = banda_per_area



    def redistribuisci_banda_security(self, utilizzo_security):
        # Imposta manualmente le limitazioni di banda per le altre slice
        self.byte_trasmessi['s1'] = 200 * 1024 * 1024  # 200 MB in byte
        self.byte_ricevuti['s1'] = 200 * 1024 * 1024  # 200 MB in byte
        self.byte_trasmessi['s2'] = 15 * 1024 * 1024  # 20 MB in byte
        self.byte_ricevuti['s2'] = 15 * 1024 * 1024  # 20 MB in byte
        self.byte_trasmessi['s3'] = 30 * 1024 * 1024  # 100 MB in byte
        self.byte_ricevuti['s3'] = 30 * 1024 * 1024  # 100 MB in byte

        if utilizzo_security < self.soglia_di_allarme_security * 0.66:
            # Reimposta le bande originali per 's1' 's2' e 's3' (500, 50 e 100)
            self.byte_trasmessi['s1'] = 250 * 1024 * 1024
            self.byte_ricevuti['s1'] = 250 * 1024 * 1024  
            self.byte_trasmessi['s2'] = 25 * 1024 * 1024 
            self.byte_ricevuti['s2'] = 25 * 1024 * 1024
            self.byte_trasmessi['s3'] = 50 * 1024 * 1024
            self.byte_ricevuti['s3'] = 50 * 1024 * 1024

        # Calcola la banda rimanente per la slice "security"
        banda_restante_security = utilizzo_security - (400 * 1024 * 1024 + 60 * 1024 * 1024 + 30 * 1024 * 1024)
        banda_restante_security = banda_restante_security / 2

        # Distribuisci la banda rimanente alla slice "security"
        if 's4' in self.byte_trasmessi:
            self.byte_trasmessi['s4'] = banda_restante_security
            self.byte_ricevuti['s4'] = banda_restante_security


    def handle_slice_control_message(self, msg):
        slice_id = msg.slice_id
        action = msg.action

        if action == 'on':
            self.slice_states[slice_id] = 'on'
            # Avvia la slice (es. abilita le regole del flusso)
        elif action == 'off':
            self.slice_states[slice_id] = 'off'
            # Spegni la slice (es. disabilita le regole del flusso)




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

class SliceControlMessage(object):
    def __init__(self, slice_id, action):
        self.slice_id = slice_id
        self.action = action  # 'on' o 'off'

