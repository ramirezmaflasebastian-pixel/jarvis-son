import json, os, time, csv, threading
B = os.path.expanduser("~/jarvis-son")
RUTA = B + "/estado.json"
LOG = B + "/metricas.csv"
_lock = threading.Lock()
_dato = {"estado": "Listo", "transcripcion": "", "respuesta": "",
         "t_stt": 0, "t_slm": 0, "t_tts": 0, "turnos": 0, "actualizado": 0}
ultimo = {}

def registrar(**kw):
    with _lock:
        _dato.update(kw)
        _dato["actualizado"] = time.time()
        tmp = RUTA + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_dato, f, ensure_ascii=False)
        os.replace(tmp, RUTA)

def medido(nombre, fn):
    def w(wav, bueno=False):
        t0 = time.time()
        r = fn(wav, bueno)
        ultimo[nombre if bueno else nombre + "_rapido"] = round(time.time() - t0, 2)
        return r
    return w

def fin_turno(t_slm, t_tts):
    _dato["turnos"] += 1
    nuevo = not os.path.exists(LOG)
    with open(LOG, "a", newline="") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["hora", "t_stt", "t_slm", "t_tts"])
        w.writerow([time.strftime("%H:%M:%S"), ultimo.get("stt", 0), round(t_slm, 2), round(t_tts, 2)])
    registrar(estado="Listo", t_stt=ultimo.get("stt", 0), t_slm=round(t_slm, 2), t_tts=round(t_tts, 2))
