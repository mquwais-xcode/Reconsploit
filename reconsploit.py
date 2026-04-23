#!/usr/bin/env python3
import os
import sys
import importlib.util
import readline
import threading
import time

# --- Banner & Colors ---
try:
    from ui.banner import showbanner
except ImportError:
    def showbanner():
        print("\033[1;31m[!] Banner module not found.\033[0m")

# ANSI Codes for Prompt (Escaped for Readline)
RED = "\001\033[1;31m\002"
WHITE = "\001\033[1;37m\002"
GREEN = "\001\033[0;32m\002"
CYAN = "\001\033[0;36m\002"
RESET = "\001\033[0m\002"

class ReconSploit:
    MODULE_DIR = "modules"
    VERSION = "1.5.0"
    CODENAME = "KARMA"

    def __init__(self):
        if not os.path.exists(self.MODULE_DIR): 
            os.makedirs(self.MODULE_DIR)
        self.current_mod_instance = None
        self.current_mod_name = None
        self.current_payload_instance = None
        self.current_payload_name = None
        self.mod_type = None 
        self.running = True

    def count_modules(self):
        stats = {"total": 0, "auxiliary": 0, "evasion": 0, "exploits": 0, "payload": 0}
        for root, _, files in os.walk(self.MODULE_DIR):
            for file in files:
                if file.endswith(".py") and file not in ["__init__.py", "base_module.py"]:
                    stats["total"] += 1
                    path = root.lower()
                    for cat in stats.keys():
                        if cat in path: stats[cat] += 1
        return stats

    def show_banner(self):
        os.system("clear")
        showbanner()
        stats = self.count_modules()
        print(f"   {WHITE}+=[ {RED}ReconSploit {WHITE}V{self.VERSION} {RED}{self.CODENAME}")
        print(f"  {WHITE}+==[ {CYAN}{stats['auxiliary']} {WHITE}Auxiliary --- {GREEN}{stats['evasion']} {WHITE}Evasion")
        print(f"  {WHITE}+=[ {RED}{stats['exploits']} {WHITE}Exploits --- \033[1;30m{stats['payload']} {WHITE}Payload\n")

    def start(self):
        self.show_banner()
        while self.running:
            try:
                mod_display = ""
                if self.current_mod_name:
                    p_color = RED
                    if self.mod_type == "auxiliary": p_color = CYAN
                    elif self.mod_type == "evasion": p_color = GREEN
                    mod_display = f"({p_color}{self.current_mod_name}{WHITE})"

                prompt = f"{RED}R{WHITE}econSploit{mod_display}$> {GREEN}"
                user_input = input(prompt).strip()
                print(RESET, end="")

                if not user_input: continue
                parts = user_input.split()
                cmd = parts[0].lower()
                args = parts[1:]

                if cmd in ['help', '?']: self.show_help()
                elif cmd == 'show': self.handle_show(args)
                elif cmd == 'auxshow': self.list_modules("auxiliary")
                elif cmd == 'evashow': self.list_modules("evasion")
                elif cmd == 'use': 
                    self.load_module(args[0] if args else None)
                elif cmd == 'aux': 
                    self.load_module(args[0] if args else None, "auxiliary")
                elif cmd == 'exploit': 
                    self.load_module(args[0] if args else None, "exploits")
                elif cmd == 'eva': 
                    self.load_module(args[0] if args else None, "evasion")
                elif cmd == 'set': self.handle_set(args)
                elif cmd in ['run', 'exploit']: self.execute_mod()
                elif cmd == 'back': self.go_back()
                elif cmd == 'clear': self.show_banner()
                elif cmd in ['exit', 'quit']: self.running = False
                else: print(f"{RED}[-] Error: Unknown command '{cmd}'{RESET}")

            except KeyboardInterrupt: print(f"\n{WHITE}[*] Use 'exit' to quit.")
            except EOFError: break
            except Exception as e: print(f"{RED}[!] Global Error: {e}{RESET}")

    def list_modules(self, filter_cat=""):
        print(f"\n{WHITE}Available {filter_cat.capitalize()} Modules:")
        print(f"{RED}" + "=" * 65)
        found = False
        for root, _, files in os.walk(self.MODULE_DIR):
            if filter_cat and filter_cat not in root.lower(): continue
            for file in files:
                if file.endswith(".py") and file not in ["__init__.py", "base_module.py"]:
                    rel_path = os.path.relpath(os.path.join(root, file), self.MODULE_DIR)
                    print(f"  {RED}{rel_path.replace('.py', '')}")
                    found = True
        if not found: print(f"  {WHITE}No modules found in this category.")
        print("")

    def handle_show(self, args):
        if not args: 
            print(f"{RED}[-] Error: Usage 'show <modules|options|payloads>'{RESET}")
            return
        sub = args[0].lower()
        if sub == 'payloads':
            if self.current_mod_instance and hasattr(self.current_mod_instance, 'payloads'):
                print(f"\n{WHITE}Compatible Payloads for {RED}{self.current_mod_name}{WHITE}:")
                for p in self.current_mod_instance.payloads:
                    print(f"  {CYAN}{p}")
                print("")
            else: print(f"{RED}[-] Error: No module selected or module has no payloads.{RESET}")
        elif sub == 'options': self.show_options()
        elif sub in ['modules', 'exploits', 'auxiliary', 'evasion']:
            self.list_modules(sub.rstrip('s'))
        else: print(f"{RED}[-] Error: Unknown category '{sub}'{RESET}")

    def load_module(self, name, mtype=None):
        if not name:
            print(f"{RED}[-] Error: Please specify a module name.{RESET}")
            return

        # Cerdas mencari Path: Cek path asli, lalu cek path dengan prefix mtype
        possible_paths = [name]
        if mtype and not name.startswith(mtype):
            possible_paths.append(f"{mtype}/{name}")

        target_path = None
        for p in possible_paths:
            full_path = os.path.join(self.MODULE_DIR, f"{p}.py")
            if os.path.exists(full_path):
                target_path = full_path
                actual_name = p
                break
        
        if not target_path:
            print(f"{RED}[-] Error: Module '{name}' not found.{RESET}")
            return

        try:
            spec = importlib.util.spec_from_file_location("mod", target_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            
            # Format class: modul_name.py -> class ModulName
            file_base = os.path.basename(target_path).replace(".py", "")
            class_name = "".join(x.capitalize() for x in file_base.split("_"))
            
            if not hasattr(mod, class_name):
                print(f"{RED}[-] Error: Class '{class_name}' not found in module.{RESET}")
                return

            self.current_mod_instance = getattr(mod, class_name)()
            self.current_mod_name = actual_name
            # Deteksi tipe berdasarkan path jika mtype tidak dipaksa
            if "auxiliary" in actual_name: self.mod_type = "auxiliary"
            elif "evasion" in actual_name: self.mod_type = "evasion"
            else: self.mod_type = "exploits"
            
            self.current_payload_instance = self.current_payload_name = None
            print(f"\n{RED}[+] {WHITE}Module Loaded: {actual_name}")
        except Exception as e: 
            print(f"{RED}[-] Error loading module: {e}{RESET}")

    def handle_set(self, args):
        if len(args) < 2:
            print(f"{RED}[-] Error: Usage 'set <KEY> <VALUE>'{RESET}")
            return
        
        key, val = args[0].upper(), " ".join(args[1:])

        if key == "PAYLOAD":
            if self.current_mod_instance and self.mod_type == "exploits":
                self.load_payload(val)
            else:
                print(f"{RED}[-] Error: Set an exploit module first.{RESET}")
        elif self.current_mod_instance and key in self.current_mod_instance.options:
            self.current_mod_instance.options[key]['value'] = val
            print(f"{WHITE}{key} => {val}")
        elif self.current_payload_instance and key in self.current_payload_instance.options:
            self.current_payload_instance.options[key]['value'] = val
            print(f"{WHITE}{key} (payload) => {val}")
        else:
            print(f"{RED}[-] Error: Option '{key}' not found.{RESET}")

    def load_payload(self, name):
        supported = getattr(self.current_mod_instance, 'payloads', [])
        if name not in supported:
            print(f"{RED}[-] Error: Payload not compatible. Type 'show payloads'.{RESET}")
            return
        
        full_path = os.path.join(self.MODULE_DIR, f"{name}.py")
        if os.path.exists(full_path):
            try:
                spec = importlib.util.spec_from_file_location("pld", full_path)
                pld = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(pld)
                class_name = "".join(x.capitalize() for x in os.path.basename(full_path).replace(".py","").split("_"))
                self.current_payload_instance = getattr(pld, class_name)()
                self.current_payload_name = name
                print(f"{CYAN}[+] {WHITE}Payload Linked: {name}")
            except Exception as e: print(f"{RED}[-] Payload Error: {e}{RESET}")
        else: print(f"{RED}[-] Error: Payload file not found.{RESET}")

    def show_options(self):
        if not self.current_mod_instance:
            print(f"{RED}[-] Error: Select a module first.{RESET}")
            return
        print(f"\n{WHITE}Module Options ({self.current_mod_name}):")
        print(f"{RED}" + "-" * 50)
        for k, v in self.current_mod_instance.options.items():
            print(f"  {RED}{k:<15} {WHITE}{str(v['value']):<30}")
        
        if self.current_payload_instance:
            print(f"\n{WHITE}Payload Options ({self.current_payload_name}):")
            print(f"{CYAN}" + "-" * 50)
            for k, v in self.current_payload_instance.options.items():
                print(f"  {CYAN}{k:<15} {WHITE}{str(v['value']):<30}")
        print("")

    def go_back(self):
        self.current_mod_instance = self.current_mod_name = None
        self.current_payload_instance = self.current_payload_name = None
        self.mod_type = None

    def execute_mod(self):
        if not self.current_mod_instance:
            print(f"{RED}[-] Error: No module loaded.{RESET}")
            return

        print(f"\n{RED}[$] {WHITE}Launching Module Engine...")
        
        def run_ex():
            try:
                self.current_mod_instance.run()
            except Exception as e:
                print(f"\n{RED}[Module Error] {e}{RESET}")

        ex_thread = threading.Thread(target=run_ex, daemon=True)
        ex_thread.start()
        time.sleep(1.5)

        if self.current_payload_instance:
            # Sync Port otomatis jika ada
            if "LPORT" in self.current_mod_instance.options and "LOCAL_PORT" in self.current_payload_instance.options:
                self.current_payload_instance.options["LOCAL_PORT"]["value"] = self.current_mod_instance.options["LPORT"]["value"]

            print(f"{CYAN}[*] Initializing Payload Stream...")
            try:
                self.current_payload_instance.run()
            except KeyboardInterrupt: print(f"\n{RED}[!] Stopping Payload...")
            except Exception as e: print(f"\n{RED}[Payload Error] {e}{RESET}")
        else:
            try:
                while ex_thread.is_alive(): time.sleep(1)
            except KeyboardInterrupt: pass

        print(f"\n{RED}[*] Execution Finished.{RESET}\n")

    def show_help(self):
        print(f"\n{WHITE}Core Commands:")
        print(f"  {'show <cat>':<18} List modules (exploits, auxiliary, evasion, payloads)")
        print(f"  {'auxshow':<18} Shortcut for show auxiliary")
        print(f"  {'evashow':<18} Shortcut for show evasion")
        print(f"  {'exploit <name>':<18} Use an exploit module")
        print(f"  {'aux <name>':<18} Use an auxiliary module")
        print(f"  {'eva <name>':<18} Use an evasion module")
        print(f"  {'set <K> <V>':<18} Set options or payload")
        print(f"  {'run / exploit':<18} Execute current module")
        print(f"  {'back':<18} Unload current module")
        print(f"  {'exit':<18} Exit ReconSploit\n")

if __name__ == "__main__":
    ReconSploit().start()
