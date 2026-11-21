import re, json, subprocess, threading, time

def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout

def _decir(txt):
    subprocess.run(["termux-tts-speak", "-l", "es", txt])

NUMS = {"un":1,"uno":1,"una":1,"dos":2,"tres":3,"cuatro":4,"cinco":5,
        "seis":6,"siete":7,"ocho":8,"nueve":9,"diez":10,"quince":15,
        "veinte":20,"treinta":30}

def _num(s):
    s = s.strip()
    return int(s) if s.isdigit() else NUMS.get(s)

APPS = {
    r"whats|wasap|guasap": ("WhatsApp", "com.whatsapp"),
    r"youtube|yutub": ("YouTube", "com.google.android.youtube"),
    r"c[aá]mara": ("la cámara", "com.sec.android.app.camera"),
    r"chrome|navegador": ("Chrome", "com.android.chrome"),
    r"ajustes|configuraci": ("Ajustes", "com.android.settings"),
    r"calculadora": ("la calculadora", "com.sec.android.app.popupcalculator"),
    r"mapas": ("Mapas", "com.google.android.apps.maps"),
    r"spotify": ("Spotify", "com.spotify.music"),
    r"instagram": ("Instagram", "com.instagram.android"),
    r"telegram": ("Telegram", "org.telegram.messenger"),
    r"galer[ií]a|fotos": ("la galería", "com.sec.android.gallery3d"),
    r"reloj": ("el reloj", "com.sec.android.app.clockpackage"),
}

def _abrir(t):
    if not re.search(r"a\s*br|enciend|prend|lanz|inici|ejecut|entra a|ve a", t):
        return None
    for patron, (nombre, paquete) in APPS.items():
        if re.search(patron, t):
            o = subprocess.run(["am", "start", "-a", "android.intent.action.MAIN",
                                "-c", "android.intent.category.LAUNCHER", "-p", paquete],
                               capture_output=True, text=True)
            if "Error" in o.stdout + o.stderr:
                return f"No pude abrir {nombre}."
            return f"Abriendo {nombre}."
    return None

def acciones(t):
    t = t.lower()
    r = _abrir(t)
    if r:
        return r

    if re.search(r"bater|bate\s*ri", t):
        d = json.loads(_run(["termux-battery-status"]))
        extra = ", cargando" if d.get("status") == "CHARGING" else ""
        return f"La batería está al {d['percentage']} por ciento{extra}."

    if re.search(r"l[ie]nt|intern|linterna|luz|flash", t):
        if re.search(r"pag|desactiv|quit|cierr|corta|off", t):
            _run(["termux-torch", "off"]); return "Linterna apagada."
        _run(["termux-torch", "on"]); return "Linterna encendida."

    if re.search(r"volumen", t):
        vols = json.loads(_run(["termux-volume"]))
        m = next(v for v in vols if v["stream"] == "music")
        mx, cur = m["max_volume"], m["volume"]
        if re.search(r"sube|aumenta|m[aá]s", t): n = min(mx, cur + 2)
        elif re.search(r"baja|reduce|menos", t): n = max(0, cur - 2)
        else:
            x = re.search(r"(\d+)", t)
            if not x: return None
            n = round(int(x.group(1)) * mx / 100)
        _run(["termux-volume", "music", str(n)])
        return "Hecho."

    if re.search(r"temporizador|av[ií]same en", t):
        x = re.search(r"(\w+)\s+(segundo|minuto|hora)", t)
        if not x: return None
        n = _num(x.group(1))
        if not n: return None
        mult = {"segundo":1, "minuto":60, "hora":3600}[x.group(2)]
        def aviso():
            time.sleep(n * mult)
            _run(["termux-vibrate", "-d", "800"])
            _decir("Señor, el temporizador ha terminado.")
        threading.Thread(target=aviso, daemon=True).start()
        return f"Temporizador de {n} {x.group(2)}{'s' if n > 1 else ''} activado."

    return None


import difflib
VOCAB = ["enciende", "apaga", "linterna", "batería", "volumen", "sube", "baja",
         "temporizador", "minutos", "segundos", "alarma", "anota", "apunta",
         "notas", "abre", "calculadora", "cámara", "ajustes", "whatsapp",
         "youtube", "spotify", "instagram", "telegram", "chrome", "mapas"]
ALIAS = {"pagar": "apaga", "paga": "apaga", "pagas": "apaga", "pag": "apaga",
         "lanterna": "linterna", "bateria": "batería", "temporizado": "temporizador"}

def corregir(t):
    salida = []
    for w in t.lower().split():
        b = w.strip(".,;:¡!¿?")
        if b in ALIAS:
            salida.append(ALIAS[b]); continue
        if len(b) >= 5 and not b.isdigit():
            m = difflib.get_close_matches(b, VOCAB, n=1, cutoff=0.82)
            if m:
                salida.append(m[0]); continue
        salida.append(w)
    return " ".join(salida)
