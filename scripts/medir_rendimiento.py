"""Mide tiempos de respuesta de varios endpoints con la aplicación ya levantada.

Uso:  python scripts/medir_rendimiento.py [--n 10] [--hilos 1] [--url http://127.0.0.1:8000]

Imprime una tabla en Markdown y guarda el detalle en logs/mediciones.csv.
El primer escenario (POST) crea estudiantes; los GET se miden después.
"""
import argparse
import csv
import os
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import requests

ESTUDIANTE = {"nombre": "Prueba", "programa": "Ingeniería de Sistemas",
              "semestre": 5, "promedio": 4.0}

ESCENARIOS = [
    ("POST", "/estudiantes/", ESTUDIANTE),
    ("GET", "/", None),
    ("GET", "/estudiantes/", None),
    ("GET", "/estudiantes/1", None),
    ("GET", "/estudiantes/99999", None),
]


def una_solicitud(base, metodo, ruta, cuerpo):
    inicio = time.perf_counter()
    try:
        r = requests.request(metodo, base + ruta, json=cuerpo, timeout=60)
        codigo = str(r.status_code)
    except requests.RequestException as e:
        codigo = f"ERROR ({e.__class__.__name__})"
    return time.perf_counter() - inicio, codigo


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=10, help="solicitudes por escenario")
    p.add_argument("--hilos", type=int, default=1, help="solicitudes simultáneas")
    p.add_argument("--url", default="http://127.0.0.1:8000")
    a = p.parse_args()

    filas, detalle = [], []
    for metodo, ruta, cuerpo in ESCENARIOS:
        with ThreadPoolExecutor(max_workers=a.hilos) as pool:
            resultados = list(pool.map(
                lambda _: una_solicitud(a.url, metodo, ruta, cuerpo), range(a.n)))
        tiempos = [t for t, _ in resultados]
        codigos = Counter(c for _, c in resultados)
        filas.append((metodo, ruta, a.n, min(tiempos), max(tiempos),
                      sum(tiempos) / len(tiempos),
                      ", ".join(f"{c} ({v})" for c, v in codigos.items())))
        detalle += [(metodo, ruta, i + 1, round(t, 4), c)
                    for i, (t, c) in enumerate(resultados)]

    print(f"\nHilos: {a.hilos}\n")
    print("| Endpoint | Método | N.º pruebas | Mínimo (s) | Máximo (s) | Promedio (s) | HTTP |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    for m, r, n, mn, mx, pr, c in filas:
        print(f"| {r} | {m} | {n} | {mn:.3f} | {mx:.3f} | {pr:.3f} | {c} |")

    ruta_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "logs", "mediciones.csv")
    os.makedirs(os.path.dirname(ruta_csv), exist_ok=True)
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metodo", "endpoint", "prueba", "segundos", "http"])
        w.writerows(detalle)
    print(f"\nDetalle guardado en {os.path.normpath(ruta_csv)}")


if __name__ == "__main__":
    main()
