import os, json, hashlib
B = os.path.expanduser("~/jarvis-son")
MODELOS = [
    ("Qwen2.5-1.5B-Instruct Q4_K_M", "llama.cpp/models/qwen2.5-1.5b-instruct-q4_k_m.gguf",
     "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF", "Apache-2.0", "SLM"),
    ("Whisper base", "whisper.cpp/models/ggml-base.bin",
     "https://huggingface.co/ggerganov/whisper.cpp", "MIT", "STT detección"),
    ("Whisper small q5_1", "whisper.cpp/models/ggml-small-q5_1.bin",
     "https://huggingface.co/ggerganov/whisper.cpp", "MIT", "STT comandos"),
]
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()
out = []
for nombre, ruta, origen, lic, uso in MODELOS:
    p = f"{B}/{ruta}"
    if os.path.exists(p):
        out.append({"nombre": nombre, "archivo": os.path.basename(p), "uso": uso,
                    "origen": origen, "licencia": lic,
                    "tamano_mb": round(os.path.getsize(p) / 1e6, 1), "sha256": sha(p)})
        print("OK", nombre)
    else:
        print("NO ENCONTRADO", ruta)
json.dump({"nota": "No se versionan pesos; descargar desde el origen y verificar SHA-256.",
           "modelos": out}, open(f"{B}/models/manifest.json", "w"), indent=2, ensure_ascii=False)
