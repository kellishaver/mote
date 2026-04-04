# uping.py
# Minimal ICMP ping for MicroPython on ESP32.
# Returns round-trip time in ms or None on timeout.

import socket
import struct
import time

def _checksum(data):
    if len(data) & 1:
        data += b'\x00'
    s = 0
    for i in range(0, len(data), 2):
        s += (data[i] << 8) + data[i + 1]
    s = (s >> 16) + (s & 0xFFFF)
    s += s >> 16
    return ~s & 0xFFFF


def ping(host, timeout_ms=20000):
    """Ping a host by IP address string. Returns RTT in ms or None on timeout."""
    try:
        addr = socket.getaddrinfo(host, 1)[0][-1]
    except (OSError, IndexError):
        return None

    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, 1)  # IPPROTO_ICMP = 1
    sock.settimeout(timeout_ms / 1000)

    # Build ICMP echo request
    # Type=8 (echo request), Code=0, Checksum=0 (placeholder), ID, Seq
    pkt_id = time.ticks_ms() & 0xFFFF
    seq = 1
    header = struct.pack('>BBHHH', 8, 0, 0, pkt_id, seq)
    payload = b'mote' * 8  # 32 bytes payload
    cs = _checksum(header + payload)
    header = struct.pack('>BBHHH', 8, 0, cs, pkt_id, seq)
    packet = header + payload

    try:
        start = time.ticks_ms()
        sock.sendto(packet, addr)

        while True:
            elapsed = time.ticks_diff(time.ticks_ms(), start)
            if elapsed >= timeout_ms:
                sock.close()
                return None
            try:
                resp = sock.recv(512)
            except OSError:
                sock.close()
                return None

            if len(resp) >= 28:
                # IP header is 20 bytes, ICMP starts at offset 20
                icmp_type = resp[20]
                icmp_id = (resp[24] << 8) | resp[25]
                if icmp_type == 0 and icmp_id == pkt_id:
                    rtt = time.ticks_diff(time.ticks_ms(), start)
                    sock.close()
                    return rtt
    except Exception:
        pass

    sock.close()
    return None
