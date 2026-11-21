import csv, os
B = os.path.expanduser("~/jarvis-son")
f = B + "/metricas.csv"
if not os.path.exists(f):
    raise SystemExit("No hay metricas.csv todavía: usa Jarvis primero")
filas = list(csv.DictReader(open(f)))
def pct(v, p):
    v = sorted(v)
    return v[min(len(v) - 1, int(round(p / 100 * (len(v) - 1))))]
print("Turnos:", len(filas))
for c, n in [("t_stt", "Voz a texto"), ("t_slm", "Generación"), ("t_tts", "Voz (TTS)")]:
    v = [float(x[c]) for x in filas]
    print(f"{n:12} p50={pct(v,50):6.2f}s  p95={pct(v,95):6.2f}s  máx={max(v):6.2f}s")
