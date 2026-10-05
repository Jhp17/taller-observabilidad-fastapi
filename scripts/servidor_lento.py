"""Servidor local que responde con retraso, para probar el timeout.

Uso:  python scripts/servidor_lento.py [segundos]   (por defecto 15)
Escucha en http://127.0.0.1:9000/
"""
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RETRASO = float(sys.argv[1]) if len(sys.argv) > 1 else 15.0


class Manejador(BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(RETRASO)
        cuerpo = json.dumps([{"id": 1, "name": "respuesta simulada"}]).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"Servidor lento en http://127.0.0.1:9000/ (retraso {RETRASO} s). Ctrl+C para salir.")
    ThreadingHTTPServer(("127.0.0.1", 9000), Manejador).serve_forever()
