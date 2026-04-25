# Alpaca-Gemini

Sistema de trading autónomo de dos fases.

## Arquitectura
1. **El Oráculo (Fase 1):** Rutina programada en Claude que analiza el mercado y genera señales en `memory/pending_signal.json`.
2. **El Ejecutor (Fase 2):** Script local (`skills/alpaca_executor.py`) que vigila el repositorio, valida la señal y ejecuta la orden en Alpaca.

## Estructura
- `memory/`: Persistencia de señales y logs de auditoría.
- `skills/`: Lógica de ejecución y conexión con APIs.
- `TRADING-STRATEGY.md`: Reglas de negocio y gestión de riesgos.
- `CLAUDE.md`: Instrucciones de personalidad para el Oráculo.

## Requisitos
- Python 3.10+
- Cuenta en Alpaca (Paper o Live)
- Token de acceso de GitHub (con permisos de escritura)

## Configuración
Copia el archivo `env.template` a `.env` y completa tus credenciales:
```bash
cp env.template .env
```