# DHCP-SPOOFING

## Video (máx. 8 minutos)
[![Ver video en YouTube](https://img.youtube.com/vi/zBK1aAm94R4/0.jpg)](https://youtu.be/zBK1aAm94R4)

---

# Informe Técnico: DHCP Spoofing.

## I-) Objetivo y Mecánica del Script.
El propósito principal de este script es implementar un servidor DHCP malicioso (Rogue Server) en una red local con el fin de desviar e interceptar el tráfico de los usuarios. La herramienta emplea la biblioteca Scapy para supervisar el tráfico de red con el fin de encontrar peticiones DHCP DISCOVER. El script responde de forma instantánea con un DHCP OFFER y un DHCP ACK cuando un cliente auténtico busca conseguir una configuración de red, lo que genera competencia con el servidor legítimo. Conforme el script suministra los datos falsos, como un servidor DNS y un Default Gateway administrados por el atacante, logra una posición de Man-in-the-Middle (MitM), lo que posibilita que todo el tráfico de la víctima fluya físicamente a través del computador del atacante antes de salir a Internet.

<img width="777" height="718" alt="Screenshot 2026-02-10 221736" src="https://github.com/user-attachments/assets/16f2dcd3-9619-477b-bfde-e6a96906392b" />

---

## II-) Escenario de Laboratorio y Topología.
Se hizo una topología en un ambiente virtualizado a través de PNETLab, donde se llevó a cabo la prueba de los ataques. La estructura de red está compuesta por un router principal (R1), con la dirección IP 10.24.9.1; dos interruptores multicapa y una computadora atacante que utiliza Kali Linux (IP 10.24.9.18). La red está dividida según la dirección 10.24.9.0/24. Cuando se combina con un DHCP Starvation previo, el ataque se vuelve crítico, ya que impide que el servidor real responda y abre la vía para que el script DHCP-SPOOFING.py sea la única fuente de configuración para las estaciones de trabajo del segmento.

<img width="829" height="879" alt="Screenshot 2026-02-10 213221" src="https://github.com/user-attachments/assets/f6bfbcb1-31c5-4617-b004-ba153dfa3972" />

---


## III-) Requisitos y Parámetros de Operación.
Para que esta herramienta funcione de manera efectiva, es necesario tener privilegios de root, porque el script necesita operar con sockets de red de bajo nivel y hacer "sniffing" en puertos protegidos (67/68 UDP). Los parámetros establecidos para este ataque son los siguientes:

- **Interfaz (-i):** La interfaz eth0 de Kali Linux, que está conectada directamente al puerto Gi0/1 del conmutador.  
- **IP del servidor (-s):** Identificada como 10.24.9.18, determinando la identidad del servidor falso.  
- **Gateway (-g):** Además, tratando de obligar a las víctimas a que nos envíen su tráfico de salida, también apuntamos a la 10.24.9.18.  
- **DNS malicioso (-d):** Está diseñado para redirigir las solicitudes de nombres de dominio a un servidor que está bajo el control del atacante.

<img width="850" height="51" alt="Screenshot 2026-02-10 222138" src="https://github.com/user-attachments/assets/89cca584-46ff-4a5b-9a85-c5efdce4e1d0" />

---

## IV-) Análisis de Resultados y Capturas.
Durante las pruebas, se validó el ataque de con resultado exitoso de la víctima mediante el comando ipconfig en una computadora Windows. Se observó que la víctima aceptó la IP 10.24.9.233 (ya que va desde la .31 a la .254) y configuró como puerta de enlace predeterminada la dirección IP del atacante.

<img width="929" height="479" alt="Screenshot 2026-02-11 014234" src="https://github.com/user-attachments/assets/8f36c4ec-e889-4a01-958a-5ca51cf8b186" />

En la computadora de Kali, el script mostró en tiempo real el flujo del protocolo DHCP: la recepción de los mensajes DISCOVER y REQUEST, seguidos del envío de los paquetes maliciosos OFFER y ACK. El resumen final de la herramienta confirmó el estado "COMPROMETIDO" para la dirección MAC de la víctima, demostrando el control total sobre su configuración de red.

<img width="790" height="529" alt="Screenshot 2026-02-11 014402" src="https://github.com/user-attachments/assets/c5fbf57c-5ace-4df5-9eed-07e8f77452b1" />

---

## V-) Medidas de Mitigación y Protección.
La implementación de DHCP Snooping en los switches de la red es el método más eficaz para defenderse contra este ataque. Esta función establece una base de datos confiable en la que solamente los puertos enlazados al servidor DHCP oficial tienen permiso para transmitir mensajes OFFER o ACK. Si se detecta un paquete de este tipo en un puerto de usuario (como el del atacante), es inmediatamente desechado y el puerto queda bloqueado. Además, se aconseja emplear la inspección dinámica de ARP (DAI) para prevenir que el asaltante trate de hacerse pasar por otras identidades a través de ARP una vez que haya conseguido la IP, y poner en práctica VLANs aisladas para disminuir el alcance de los ataques de broadcast.

