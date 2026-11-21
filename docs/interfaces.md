# Contrato entre módulos

Jarvis escribe `estado.json` (raíz del proyecto) en cada etapa; la interfaz lo lee.

| Campo | Significado |
|---|---|
| estado | Listo, Grabando, Generando, Hablando o Error |
| transcripcion | Última frase reconocida |
| respuesta | Última respuesta generada |
| t_stt, t_slm, t_tts | Segundos por etapa del último turno |
| turnos | Turnos completados en la sesión |
| actualizado | Hora Unix de la última escritura |

`metricas.csv`: una fila por turno (hora, t_stt, t_slm, t_tts). No guarda conversaciones.
Interfaz: `python3 src/gui.py` y abrir http://127.0.0.1:8081.
