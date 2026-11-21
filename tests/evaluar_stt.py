import os, sys, subprocess, re, csv, time, unicodedata
B = os.path.expanduser("~/jarvis-son")
W = B + "/whisper.cpp/build/bin/whisper-cli"
M = B + "/whisper.cpp/models/ggml-small-q5_1.bin"
AMB = sys.argv[1] if len(sys.argv) > 1 else "silencio"
LISTA = sys.argv[2] if len(sys.argv) > 2 else "frases.txt"
AC = os.environ.get("AC", "")
UMBRAL = 0.34
frases = [l.strip() for l in open(B + "/tests/" + LISTA, encoding="utf-8") if l.strip()]

def norm(t):
    t = unicodedata.normalize("NFD", t.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", "", t).split()

def wer(ref, hip):
    r, h = norm(ref), norm(hip)
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        p, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (r[i - 1] != h[j - 1]))
    return round(d[len(h)] / max(len(r), 1), 2)

m4a, wav = B + "/tmp_eval.m4a", B + "/tmp_eval.wav"
filas = []
for i, ref in enumerate(frases, 1):
    input(f'\n[{i}/{len(frases)}] Pulsa Enter, espera el aviso y di: "{ref}" ')
    for x in (m4a, wav):
        if os.path.exists(x): os.remove(x)
    subprocess.run(["termux-microphone-record", "-f", m4a, "-l", "6"], capture_output=True)
    time.sleep(1.2)
    print("  >>> HABLA YA <<<")
    time.sleep(4.3)
    subprocess.run(["termux-microphone-record", "-q"], capture_output=True)
    time.sleep(1)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", m4a, "-ar", "16000", "-ac", "1",
                    "-af", "highpass=f=100,dynaudnorm=f=150:g=15", wav])
    cmd = [W, "-m", M, "-f", wav, "-l", "es", "-nt", "-np", "-t", "4"]
    if AC:
        cmd += ["-ac", AC]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    seg = round(time.time() - t0, 1)
    hip = r.stdout.strip()
    e = wer(ref, hip)
    print("  oí:", hip, "| error:", e, "|", seg, "s")
    filas.append([ref, hip, e, seg])
for x in (m4a, wav):
    if os.path.exists(x): os.remove(x)
out = f"{B}/tests/resultados_stt_{AMB}.csv"
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["frase", "transcripcion", "error", "segundos"])
    w.writerows(filas)
ok = sum(1 for x in filas if x[2] <= UMBRAL)
print(f"\nUTILIZABLES ({AMB}): {ok}/{len(filas)}  (error <= {UMBRAL})")
print("Guardado en", out)
