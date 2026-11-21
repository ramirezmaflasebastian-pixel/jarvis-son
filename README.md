# Jarvis-son V1

Prototipo académico de asistente de voz local offline (arquitectura por turnos) para dispositivos móviles.

## Inventario del Dispositivo de Pruebas
- **Modelo:** Samsung Galaxy S24 FE
- **Sistema Operativo:** Android (API 33+)
- **Arquitectura:** ARM64 (arm64-v8a)
- **Memoria RAM:** 8 GB (Supera el mínimo requerido de la cátedra)
- **Entorno de ejecución:** Termux (con soporte C++, CMake y FFmpeg)

## Estructura del Proyecto
- `src/include/` -> Lógica del orquestador y contratos entre módulos.
- `scripts/` -> Scripts de automatización y descarga verificada.
- `models/` -> Manifiesto de modelos locales (los pesos se descargan en local).
- `docs/tests/` -> Diagramas de estados y registros de latencia.
