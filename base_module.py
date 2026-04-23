class BaseModule:
    def __init__(self):
        self.options = {}
        self.description = "Tidak ada deskripsi."

    def register_option(self, key, default, required, description):
        # Memastikan key selalu UPPERCASE
        self.options[key.upper()] = {
            "value": default,
            "required": required,
            "desc": description
        }

    def run(self):
        print("[-] Error: Method 'run' belum didefinisikan di modul ini.")
