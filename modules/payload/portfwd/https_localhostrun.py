from base_module import BaseModule
import subprocess
import re
import sys
import time

class HttpsLocalhostrun(BaseModule):
    def __init__(self):
        super().__init__()
        self.description = "Port Forwarding using localhost.run (SSH Tunneling)"
        self.register_option("LOCAL_PORT", "5000", True, "Local port to forward")
        self.register_option("REMOTE_USER", "nokey", True, "User for localhost.run")

    def run(self):
        local_port = self.options["LOCAL_PORT"]["value"]
        user = self.options["REMOTE_USER"]["value"]

        # Perintah SSH yang lebih stabil
        cmd = [
            "ssh", "-R", f"80:localhost:{local_port}", 
            f"{user}@localhost.run", 
            "-T", 
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "ExitOnForwardFailure=yes",
            "-o", "ServerAliveInterval=60"
        ]

        try:
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            found_link = False
            # Membaca baris demi baris tanpa memblokir seluruh sistem
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                
                if line:
                    # Regex ketat untuk tunnel link
                    match = re.search(r'https?://[a-zA-Z0-9-]+\.(lhr\.life|localhost\.run)', line)
                    
                    if match:
                        tunnel_link = match.group(0)
                        # Filter junk
                        if any(x in tunnel_link.lower() for x in ["docs", "twitter", "admin", "openssh"]):
                            continue
                            
                        sys.stdout.write(f"\n\033[1;92m[*] Port Forwarding Link: \033[1;37m{tunnel_link}\033[0m\n")
                        sys.stdout.flush()
                        found_link = True
                    
                    # Jika SSH mati karena port lokal belum siap (Eporner/Phishing belum jalan)
                    if "forwarding failure" in line.lower():
                        sys.stdout.write(f"\033[1;31m[!] Error: Port {local_port} is not active locally!\033[0m\n")
                        break

            process.terminate()

        except KeyboardInterrupt:
            pass
        except Exception as e:
            sys.stdout.write(f"\n\033[1;31m[-] Tunnel Error: {e}\033[0m\n")
