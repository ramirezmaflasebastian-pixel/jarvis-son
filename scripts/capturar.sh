#!/bin/bash
echo "Grabando audio durante 5 segundos... ¡Habla ahora!"
termux-microphone-record -f input_raw.wav -l 5 -d

# Esperar a que termine la grabación
sleep 6

echo "Normalizando audio a WAV mono 16 kHz con FFmpeg..."
ffmpeg -y -i input_raw.wav -ar 16000 -ac 1 -c:a pcm_s16le audio_final.wav

# Limpiar archivo temporal
rm input_raw.wav
echo "¡Listo! Audio guardado y normalizado como audio_final.wav"
