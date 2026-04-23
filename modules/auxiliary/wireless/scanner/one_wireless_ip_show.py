from base_module import BaseModule
import subprocess
import socket
import threading
import sys
import re
from queue import Queue

class OneWirelessIpShow(BaseModule):
    def __init__(self):
        super().__init__()
        self.description = "Scan active IPs and MAC addresses in your network"
        self.register_option("SUBNET", "192.168.1", True, "First 3 octets (e.g., 192.168.1)")
        self.register_option("THREADS", "50", True, "Scanning speed")
        self.stop_event = threading.Event()

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except: return "127.0.0.1"

    def get_mac_address(self, ip):
        """Mengambil MAC Address dari ARP table sistem"""
        try:
            # Menjalankan perintah ip neighbor untuk melihat cache ARP
            output = subprocess.check_output(["ip", "neigh", "show", ip], stderr=subprocess.DEVNULL, text=True)
            # Regex untuk mencari format MAC address (xx:xx:xx:xx:xx:xx)
            mac = re.search(r"([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})", output)
            return mac.group(0) if mac else "Unknown/Static"
        except:
            return "Unknown"

    def scan_ip(self, ip_prefix, last_octet, results):
        if self.stop_event.is_set(): return

        target = f"{ip_prefix}.{last_octet}"
        cmd = ["ping", "-c", "1", "-W", "1", target]
        
        try:
            response = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if response.returncode == 0:
                mac = self.get_mac_address(target)
                # Langsung cetak sesuai format permintaanmu
                sys.stdout.write(f"\033[1;31m[-]\033[1;37m Detected \033[1;32m{target:<15}\033[1;37m | MAC: \033[1;33m{mac}\033[0m\n")
                sys.stdout.flush()
                results.append((target, mac))
        except: pass

    def run(self):
        self.stop_event.clear()
        ip_prefix = self.options["SUBNET"]["value"]
        thread_count = int(self.options["THREADS"]["value"])
        my_ip = self.get_local_ip()

        print(f"\n\033[1;32m[+]\033[1;37m Scanning wireless for IP...\033[0m")
        
        active_devices = []
        q = Queue()
        for i in range(1, 255): q.put(i)

        def worker():
            while not q.empty() and not self.stop_event.is_set():
                octet = q.get()
                self.scan_ip(ip_prefix, octet, active_devices)
                q.task_done()

        threads = []
        try:
            for _ in range(thread_count):
                t = threading.Thread(target=worker, daemon=True)
                t.start()
                threads.append(t)

            while not q.empty():
                q.join()
                break
                
        except KeyboardInterrupt:
            print(f"\n\033[1;33m[!] Stopping scan...\033[0m")
            self.stop_event.set()
        
        finally:
            self.stop_event.set()
            # Tampilkan ringkasan jika diperlukan
            print(f"\n\033[1;32m[+] Cleanup Selesai: Total {len(active_devices)} devices detected.\033[0m\n")
