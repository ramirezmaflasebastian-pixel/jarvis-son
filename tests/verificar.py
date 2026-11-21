import os, sys, json, subprocess, urllib.request
B = os.path.expanduser("~/jarvis-son")
sys.path.insert(0, B)
ok = fail = 0

def check(n, c, x=""):
    global ok, fail
    if c: ok += 1
    else: fail += 1
    print("  [OK]   " if c else "  [FALLA]", n, x)

def gguf(p):
    try: return open(p, "rb").read(4) == b"GGUF"
    except Exception: return False

print("== Archivos ==")
for n, p in [("llama-server", "llama.cpp/build/bin/llama-server"),
             ("whisper-cli", "whisper.cpp/build/bin/whisper-cli"),
             ("jarvis_voz.py", "jarvis_voz.py"), ("acciones.py", "acciones.py")]:
    check(n, os.path.exists(f"{B}/{p}"))

print("== Modelos ==")
check("LLM Qwen 1.5B (GGUF)", gguf(f"{B}/models/qwen2.5-1.5b-instruct-q4_k_m.gguf"))
for n in ["ggml-base.bin", "ggml-small-q5_1.bin"]:
    p = f"{B}/whisper.cpp/models/{n}"
    check("Whisper " + n, os.path.exists(p) and os.path.getsize(p) > 1e7)

print("== Servidor del modelo ==")
try:
    urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=5)
    check("llama-server activo", True)
    d = json.dumps({"messages": [{"role": "user", "content": "Di hola"}], "max_tokens": 20}).encode()
    q = urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions", d, {"Content-Type": "application/json"})
    t = json.loads(urllib.request.urlopen(q, timeout=60).read())
    check("El modelo responde", True, "->", t["choices"][0]["message"]["content"].strip())
except Exception:
    check("llama-server activo", False, "(arranca con: jarvisv)")

print("== Acciones locales ==")
try:
    from acciones import acciones, corregir
    check("Corrección de palabras", corregir("pagar la lintera") == "apaga la linterna")
    r = acciones("qué batería tengo")
    check("Batería", bool(r) and "batería" in r, "->", r)
    check("Orden desconocida pasa al modelo", acciones("cuéntame un chiste") is None)
except Exception as e:
    check("Módulo acciones", False, str(e))

c = subprocess.run(["python3", "-m", "py_compile", f"{B}/jarvis_voz.py"], capture_output=True)
check("jarvis_voz.py compila", c.returncode == 0)
print(f"\nRESULTADO: {ok} correctas, {fail} con fallo")
