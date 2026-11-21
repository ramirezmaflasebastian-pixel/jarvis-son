import http.server, socketserver, os
B = os.path.expanduser("~/jarvis-son")
W = B + "/src/web"

class H(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        p = path.split("?")[0]
        if p == "/estado.json":
            return B + "/estado.json"
        return W + "/" + (os.path.basename(p) or "index.html")
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()
    def log_message(self, *a):
        pass

socketserver.TCPServer.allow_reuse_address = True
with socketserver.ThreadingTCPServer(("127.0.0.1", 8081), H) as s:
    print("Interfaz en http://127.0.0.1:8081  (Ctrl+C para salir)")
    s.serve_forever()
