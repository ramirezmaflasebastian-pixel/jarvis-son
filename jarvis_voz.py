from acciones import acciones as acciones_mod, corregir
import estadojson as EJ
import json, subprocess, time, urllib.request, os, re, threading, queue

BASE = os.path.expanduser("~/jarvis-son")
WHISPER = f"{BASE}/whisper.cpp/build/bin/whisper-cli"
WM_RAPIDO = f"{BASE}/whisper.cpp/models/ggml-base.bin"
WM_BUENO = f"{BASE}/whisper.cpp/models/ggml-small-q5_1.bin"
URL = "http://127.0.0.1:8080/v1/chat/completions"
CHUNK = 3
CMD_SECONDS = 4
GAP = 0.2
UMBRAL_DB = -38
CONFIRMA = "Sí, señor."
DEBUG = os.environ.get("DEBUG") == "1"
WAKE = re.compile(r"\b(?:j|y|h|ll|d|g|ch)[aeiouáéíóú]{0,2}r{1,2}[aeiou]?[vb][ií][sz]?\b", re.I)
BASURA = re.compile(r"subt[ií]tulos|gracias por ver|amara\.org|suscr|^\W*(?:qu[eé] pasa|gracias|ah|eh|mm+|hola)\W*$", re.I)
SISTEMA = "Eres Jarvis, un asistente de voz. Responde siempre en español, en una sola frase corta."
DEVNULL = subprocess.DEVNULL
DIAS = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
MESES = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto",
         "septiembre","octubre","noviembre","diciembre"]
historial = []
cola = queue.Queue()
ignorar_hasta = 0.0
reiniciar = threading.Event()
dur = [CHUNK]

def mic(*args):
    subprocess.run(["termux-microphone-record", *args], stdout=DEVNULL, stderr=DEVNULL)

def grabador():
    n = 0
    while True:
        f = f"{BASE}/c{n % 8}.m4a"
        n += 1
        if os.path.exists(f):
            os.remove(f)
        d = dur[0]
        dur[0] = CHUNK
        reiniciar.clear()
        t0 = time.time()
        mic("-f", f, "-l", "0")
        cortado = reiniciar.wait(d)
        mic("-q")
        if not cortado:
            cola.put((t0, f))
        time.sleep(GAP)

def convertir(f):
    wav = f.replace(".m4a", ".wav")
    for _ in range(4):
        if os.path.exists(wav):
            os.remove(wav)
        r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f,
                            "-ar", "16000", "-ac", "1", wav], capture_output=True)
        if r.returncode == 0 and os.path.exists(wav):
            return wav
        time.sleep(0.15)
    return None

def preparar(f):
    wav = convertir(f)
    if not wav:
        return None
    r = subprocess.run(["ffmpeg", "-i", wav, "-af", "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"mean_volume: (-?[\d.]+) dB", r.stderr)
    if (float(m.group(1)) if m else -99) < UMBRAL_DB:
        return None
    return wav

def oir(wav, bueno):
    n = wav.replace(".wav", "_n.wav")
    o = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav,
                        "-af", "highpass=f=100,dynaudnorm=f=150:g=15", n],
                       capture_output=True)
    if o.returncode == 0 and os.path.exists(n):
        wav = n
    if bueno:
        modelo, extra = WM_BUENO, ["-bs", "3", "-bo", "3"]
    else:
        modelo, extra = WM_RAPIDO, ["-bs", "1", "-bo", "1", "-nf", "-ac", "768"]
    r = subprocess.run([WHISPER, "-m", modelo, "-f", wav, "-l", "es", "-nt", "-np",
                        "-t", "4", *extra],
                       capture_output=True, text=True)
    t = r.stdout.strip()
    if re.fullmatch(r"[\[\(].*[\]\)]", t) or BASURA.search(t):
        return ""
    return t

NOTAS = f"{BASE}/notas.txt"
NUM = {"un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
       "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12,
       "quince": 15, "veinte": 20, "treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60}
APPS = [
    (r"you ?tube", ("YouTube", "com.google.android.youtube")),
    (r"whats ?app|guasap|wasap", ("WhatsApp", "com.whatsapp")),
    (r"chrome|navegador", ("Chrome", "com.android.chrome")),
    (r"c[aá]mara", ("la cámara", "com.sec.android.app.camera")),
    (r"ajustes|configuraci[oó]n", ("Ajustes", "com.android.settings")),
    (r"spotify", ("Spotify", "com.spotify.music")),
    (r"mapas|maps", ("Mapas", "com.google.android.apps.maps")),
    (r"calculadora", ("la calculadora", "com.sec.android.app.popupcalculator")),
    (r"telegram", ("Telegram", "org.telegram.messenger")),
    (r"instagram", ("Instagram", "com.instagram.android")),
    (r"tik ?tok", ("TikTok", "com.zhiliaoapp.musically")),
    (r"reloj", ("el reloj", "com.sec.android.app.clockpackage")),
]

def run(*cmd):
    return subprocess.run(list(cmd), capture_output=True, text=True)

def a_digitos(s):
    s = re.sub(r"\b(veinte|treinta|cuarenta|cincuenta)\s+y\s+(un|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve)\b",
               lambda m: str(NUM[m.group(1)] + NUM[m.group(2)]), s)
    s = re.sub(r"\bveinti(un|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve)\b",
               lambda m: str(20 + NUM[m.group(1)]), s)
    return s

def parse_tiempo(s):
    if re.search(r"\bmedia hora\b", s):
        return 1800, "media hora"
    pat = r"\b(\d+|" + "|".join(NUM) + r")\s+(segundo|minuto|hora)s?\b"
    m = re.search(pat, s)
    if not m:
        return None
    g = m.group(1)
    n = int(g) if g.isdigit() else NUM[g]
    mult = {"segundo": 1, "minuto": 60, "hora": 3600}[m.group(2)]
    return n * mult, f"{n} {m.group(2)}" + ("s" if n != 1 else "")

def aviso_fin(seg, texto):
    global ignorar_hasta
    time.sleep(seg)
    subprocess.run(["termux-vibrate", "-d", "800"])
    hablar(texto)
    time.sleep(0.4)
    ignorar_hasta = time.time()

def volumen(delta, maximo=False):
    r = run("termux-volume")
    try:
        info = [x for x in json.loads(r.stdout) if x["stream"] == "music"][0]
    except Exception:
        return "No pude leer el volumen."
    mx, v = info["max_volume"], info["volume"]
    nv = mx if maximo else max(0, min(mx, v + delta))
    run("termux-volume", "music", str(nv))
    return f"Volumen al {round(nv * 100 / mx)} por ciento."

def acciones(t):
    s = a_digitos(t.lower())
    m = re.search(r"\b(?:anota|apunta|an[oó]tame|ap[uú]ntame)\b(?:\s+que)?\s+(.+)", t, re.I)
    if m:
        with open(NOTAS, "a", encoding="utf-8") as fh:
            fh.write(time.strftime("%d/%m %H:%M") + " - " + m.group(1).strip(" ,.") + "\n")
        return "Anotado."
    if re.search(r"mis notas|qu[eé] anot[eé]|lee (?:las )?notas|qu[eé] notas", s):
        if not os.path.exists(NOTAS):
            return "No tienes notas."
        with open(NOTAS, encoding="utf-8") as fh:
            lineas = [l.split(" - ", 1)[-1].strip() for l in fh.read().splitlines() if l.strip()]
        if not lineas:
            return "No tienes notas."
        return "Tus últimas notas: " + ". ".join(lineas[-3:]) + "."
    if re.search(r"\b(temporizador|av[ií]same|alarma|timer)\b", s):
        r = parse_tiempo(s)
        if not r:
            return "No entendí el tiempo. Di, por ejemplo: temporizador de cinco minutos."
        seg, nombre = r
        threading.Thread(target=aviso_fin, args=(seg, f"Señor, terminó el temporizador de {nombre}."),
                         daemon=True).start()
        return f"Temporizador de {nombre} en marcha."
    if re.search(r"linterna|flash", s):
        if re.search(r"\b(apaga|apagar|desactiva|quita|cierra)", s):
            on = False
        elif re.search(r"\b(enciende|encender|prende|prender|activa|pon)", s):
            on = True
        else:
            return None
        r = run("termux-torch", "on" if on else "off")
        if r.returncode != 0:
            return "No pude usar la linterna. Revisa el permiso de cámara de Termux API."
        return "Linterna encendida." if on else "Linterna apagada."
    if re.search(r"\bbater[ií]a\b", s):
        r = run("termux-battery-status")
        try:
            d = json.loads(r.stdout)
            txt = f"Tienes {int(d['percentage'])} por ciento de batería"
            if d.get("status") == "CHARGING":
                txt += ", cargando"
            return txt + "."
        except Exception:
            return "No pude leer la batería."
    if re.search(r"\bvolumen\b|\bs[uú]bele\b|\bb[aá]jale\b", s):
        if re.search(r"m[aá]ximo|al tope", s):
            return volumen(0, True)
        if re.search(r"\b(sube|subir|aumenta|aumentar|s[uú]bele|m[aá]s alto|m[aá]s fuerte)\b", s):
            return volumen(2)
        if re.search(r"\b(baja|bajar|disminuye|reduce|b[aá]jale|m[aá]s bajo|menos)\b", s):
            return volumen(-2)
        return None
    if re.search(r"\b(abre|abrir|[aá]breme|inicia|lanza|ejecuta)\b", s):
        for pat, (nombre, pkg) in APPS:
            if re.search(pat, s):
                r = run("am", "start", "-a", "android.intent.action.MAIN",
                        "-c", "android.intent.category.LAUNCHER", "-p", pkg)
                if r.returncode != 0 or "Error" in (r.stdout + r.stderr):
                    return f"No pude abrir {nombre}."
                return f"Abriendo {nombre}."
        return "No conozco esa aplicación todavía."
    return None

def local(t):
    a = acciones(t)
    if a:
        return a
    s = t.lower()
    n = time.localtime()
    if re.search(r"\bqu[eé] hora\b|\bhora (es|son)\b|\bla hora\b|\bhora actual\b", s):
        h = n.tm_hour
        h12 = h % 12 or 12
        parte = "de la madrugada" if h < 6 else "de la mañana" if h < 12 else "de la tarde" if h < 19 else "de la noche"
        txt = ("Es la " if h12 == 1 else "Son las ") + str(h12)
        txt += f" y {n.tm_min}" if n.tm_min else " en punto"
        return f"{txt} {parte}."
    fe = re.search(r"\b[fv]echa\b|\bd[ií]a\b|\ba cu[aá]ntos\b", s)
    if fe and re.search(r"ma[ñn]ana", s) and not re.search(r"de la ma[ñn]ana", s):
        d = time.localtime(time.time() + 86400)
        return f"Mañana es {DIAS[d.tm_wday]} {d.tm_mday} de {MESES[d.tm_mon-1]}."
    if fe and re.search(r"\bayer\b", s):
        d = time.localtime(time.time() - 86400)
        return f"Ayer fue {DIAS[d.tm_wday]} {d.tm_mday} de {MESES[d.tm_mon-1]}."
    if fe:
        return f"Hoy es {DIAS[n.tm_wday]} {n.tm_mday} de {MESES[n.tm_mon-1]} de {n.tm_year}."
    return None

def preguntar(texto):
    historial.append({"role": "user", "content": texto})
    ahora = DIAS[time.localtime().tm_wday] + time.strftime(" %d/%m/%Y, %H:%M")
    sistema = {"role": "system", "content": SISTEMA + " Fecha y hora actual: " + ahora + ". Si no sabes algo, di que no lo sabes; nunca inventes datos."}
    datos = json.dumps({"messages": [sistema] + historial[-6:], "max_tokens": 80, "temperature": 0.5}).encode()
    req = urllib.request.Request(URL, data=datos, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.load(r)["choices"][0]["message"]["content"].strip()
    historial.append({"role": "assistant", "content": resp})
    return resp

def hablar(texto, vel=1.1):
    base = ["termux-tts-speak", "-l", "es", "-r", str(vel)]
    r = subprocess.run(base + ["-s", "MUSIC", texto], capture_output=True)
    if r.returncode != 0:
        subprocess.run(base + [texto])

def confirmar():
    global ignorar_hasta
    h = threading.Thread(target=hablar, args=(CONFIRMA, 1.3))
    h.start()
    time.sleep(0.5)
    ignorar_hasta = time.time()
    dur[0] = CMD_SECONDS
    reiniciar.set()
    EJ.registrar(estado="Grabando", transcripcion="", respuesta="")
    h.join()

def responder(texto):
    global ignorar_hasta
    print("Tú:", texto)
    _t0 = time.time()
    EJ.registrar(estado="Generando", transcripcion=texto, respuesta="")
    resp = local(corregir(texto))
    if resp is None:
        try:
            resp = acciones_mod(corregir(texto))
        except Exception as e:
            print('Error en acciones:', e)
            resp = None
    if resp is None:
        try:
            resp = preguntar(texto)
        except Exception as e:
            print("Error con el modelo:", e)
            EJ.registrar(estado="Error")
            ignorar_hasta = time.time()
            return
    _t1 = time.time()
    EJ.registrar(estado="Hablando", respuesta=resp)
    print("Jarvis:", resp)
    hablar(resp)
    time.sleep(0.4)
    ignorar_hasta = time.time()
    EJ.fin_turno(_t1 - _t0, time.time() - _t1)

oir = EJ.medido("stt", oir)
EJ.registrar(estado="Listo")
print("Escuchando en silencio. Di 'Jarvis', espera el 'Sí, señor' y pregunta. Ctrl+C para salir.")
mic("-q")
threading.Thread(target=grabador, daemon=True).start()
hablar("Listo")
ignorar_hasta = time.time()
esperando = False
pendiente = ""

while True:
    while cola.qsize() > 2:
        cola.get()
    t0, f = cola.get()
    if t0 < ignorar_hasta:
        continue
    wav = preparar(f)
    if esperando:
        esperando = False
        t = oir(wav, True) if wav else ""
        if DEBUG:
            print("orden:", t)
        m2 = WAKE.search(t)
        if m2:
            t = t[m2.end():]
        t = t.strip(" ,.:;!¡?¿")
        if t:
            responder((pendiente + " " + t).strip())
        pendiente = ""
        continue
    if not wav:
        continue
    t = oir(wav, False)
    if DEBUG and t:
        print("oí:", t)
    m = WAKE.search(t)
    if not m:
        continue
    resto = t[m.end():].strip(" ,.:;!¡?¿")
    if len(resto.split()) >= 3:
        t2 = oir(wav, True)
        m2 = WAKE.search(t2)
        if m2:
            t2 = t2[m2.end():]
        responder(t2.strip(" ,.:;!¡?¿") or resto)
    else:
        confirmar()
        pendiente = resto
        esperando = True
