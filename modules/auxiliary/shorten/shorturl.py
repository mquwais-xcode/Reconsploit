from base_module import BaseModule
import requests
import re
import sys

class Shorturl(BaseModule):
    def __init__(self):
        super().__init__()
        self.description = "URL Shortener using shorturl.at service"
        
        # Register Options
        self.register_option("TARGET", "", True, "The long URL to shorten (e.g., https://google.com)")

    def run(self):
        long_url = self.options["TARGET"]["value"]
        
        if not long_url.startswith(("http://", "https://")):
            print(f"\n\033[1;31m[-] Error: URL must start with http:// or https://\033[0m")
            return

        print(f"\n\033[1;37m[*] Shortening URL: \033[1;31m{long_url}\033[0m")
        print(f"\033[1;37m[*] Connecting to shorturl.at...\033[0m")

        # Endpoint shorturl.at
        api_url = "https://www.shorturl.at/shortener.php"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"u": long_url}

        try:
            # Melakukan request POST
            response = requests.post(api_url, data=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Menggunakan Regex untuk mencari value di dalam ID 'shortenurl'
                # shorturl.at mengembalikan hasilnya di elemen <input id="shortenurl" ... value="shorturl.at/xyz">
                match = re.search(r'id="shortenurl"[^>]+value="([^"]+)"', response.text)
                
                if match:
                    short_link = match.group(1)
                    # Jika link tidak diawali https, tambahkan secara manual
                    if not short_link.startswith("http"):
                        short_link = "https://" + short_link
                        
                    print(f"\n\033[1;92m[*] SUCCESS! \033[0m")
                    print(f"\033[1;37m[+] Short URL: \033[1;32m{short_link}\033[0m")
                    print(f"\033[1;37m[*] Original : {long_url}\n\033[0m")
                else:
                    print("\033[1;31m[-] Error: Could not find shortened URL in response.\033[0m")
                    # Debugging jika struktur web berubah
                    # with open("debug_short.html", "w") as f: f.write(response.text)
            else:
                print(f"\033[1;31m[-] Server returned error code: {response.status_code}\033[0m")

        except requests.exceptions.RequestException as e:
            print(f"\n\033[1;31m[-] Request Error: {e}\033[0m")
        except Exception as e:
            print(f"\n\033[1;31m[-] Unexpected Error: {e}\033[0m")

