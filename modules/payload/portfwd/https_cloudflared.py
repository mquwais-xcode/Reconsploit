from base_module import BaseModule
import subprocess
import re
import sys

class HttpsCloudflared(BaseModule):
    def __init__(self):
        super().__init__()
        self.description = "Cloudflare Tunnel Port Forwarding"
        self.register_option("LOCAL_PORT", "8080", True, "Port to forward")

    def run(self):
        port = self.options["LOCAL_PORT"]["value"]
        if subprocess.call("command -v cloudflared", shell=True, stdout=subprocess.DEVNULL) != 0:
            print("[-] Error: cloudflared not installed.")
            return

        print(f"[*] Opening tunnel for port {port}...")
        cmd = ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        try:
            while True:
                line = process.stdout.readline()
                if not line: break
                match = re.search(r'https?://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                if match:
                    print(f"\n\033[1;92m[ URL ] {match.group(0)}\033[0m\n")
        except KeyboardInterrupt:
            process.terminate()
            print("\n[-] Tunnel closed.")
