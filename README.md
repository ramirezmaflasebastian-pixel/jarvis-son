# Jarvis-son V1

Prototipo académico de asistente de voz local offline (arquitectura por turnos) para dispositivos móviles[cite: 1, 8].

## Inventario del Dispositivo de Pruebas
- **Modelo:** Samsung Galaxy S24 FE
- **Sistema Operativo:** Android (API 33+)[cite: 1, 12, 24]
- **Arquitectura:** ARM64 (arm64-v8a)[cite: 1, 24]
- **Memoria RAM:** 8 GB (Supera el mínimo requerido de la cátedra)[cite: 1]
- **Entorno de ejecución:** Termux (con soporte C++, CMake y FFmpeg)[cite: 3, 6]

## Estructura del Proyecto
- `src/include/` -> Lógica del orquestador y contratos entre módulos[cite: 5].
- `scripts/` -> Scripts de automatización y descarga verificada[cite: 5].
- `models/` -> Manifiesto de modelos locales (los pesos se descargan en local)[cite: 5, 11].
- `docs/tests/` -> Diagramas de estados y registros de latencia[cite: 5, 8].
