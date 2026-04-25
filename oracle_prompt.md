# 🤖 ROUTINE: EL ORÁCULO (GitHub-Centric)
## Trigger: 8:25 AM CT, Monday-Friday

---

## 🎯 OBJECTIVE
Analyze pre-market conditions and emit a trading signal. All outputs go to GitHub repository.

---

## 📋 PRE-FLIGHT CHECKLIST
1. Read `TRADING-STRATEGY.md` from repo — understand universe and criteria
2. Read `memory/TRADE-LOG.md` — check this week's trade count
3. Read `memory/pending_signal.json` — if status=PENDING, abort (previous signal not processed)
4. Check if today is a market trading day (not holiday)

If any check fails → Write HOLD signal and exit.

---

## 🔍 RESEARCH PHASE
Use web search to gather market intelligence:

**Queries to run:**
- "S&P 500 futures pre-market today"
- "VIX index today level"
- "earnings surprises pre-market S&P 500 today"
- "analyst upgrades downgrades today"
- "macro news Fed speakers today"

---

## 🧠 ANALYSIS PHASE
Evaluate against strategy criteria. Only emit signal if:
- Signal strength: STRONG (conviction HIGH)
- Asset: S&P 500 or NASDAQ 100 constituent
- Price > $5
- Weekly trades < 3 (count from TRADE-LOG.md)
- No pending signal already in queue

---

## 📝 OUTPUT: Signal Schema
Write the following JSON to `memory/pending_signal.json`:

```json
{
  "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
  "routine": "EL_ORACULO",
  "asset": "TICKER",
  "action": "BUY" | "SELL" | "HOLD",
  "rationale": "...",
  "confidence": "HIGH" | "LOW" | "N/A",
  "source_urls": ["url1", "url2"],
  "status": "PENDING",
  "expires_at": "YYYY-MM-DDTHH:MM:SSZ",
  "guardrails_check": {
    "weekly_trades": 0,
    "max_trades_ok": true,
    "universe_ok": true,
    "price_ok": true
  }
}
```

**Detalles del JSON:**
-   `status`: Debe ser "PENDING" si emites una señal de BUY/SELL. Debe ser "WAITING" si emites una señal de WAIT.
-   `last_update`: La fecha y hora actual en formato ISO 8601 (ej. "2024-04-25T15:30:00Z").
-   `signal.ticker`: El símbolo del activo (ej. "AAPL"). Si `action` es "WAIT", debe ser `null`.
-   `signal.action`: "BUY", "SELL", o "WAIT".
-   `signal.reason`: Una explicación clara y concisa de tu decisión, incluyendo las fuentes consultadas y los criterios cumplidos/no cumplidos.
-   `signal.confidence_score`: Un valor numérico entre 0 y 100. 0 para "WAIT", >70 para BUY/SELL.
-   `signal.routine`: Siempre "Oracle_v1".
-   `signal.expires_at`: La fecha y hora de cierre del mercado del día actual en formato ISO 8601. Esto asegura que la señal no se ejecute al día siguiente si el ejecutor se retrasa.
-   `execution`: Siempre un objeto vacío `{}`. Esto será llenado por el ejecutor.

**Ejemplo de Salida (para una señal de COMPRA):**
```json
{
    "status": "PENDING",
    "last_update": "2024-04-25T15:30:00Z",
    "signal": {
        "ticker": "MSFT",
        "action": "BUY",
        "reason": "Microsoft (MSFT) mostró un fuerte impulso pre-mercado tras un reporte de ganancias positivo y una mejora de calificación de analistas. Los futuros del S&P 500 también están al alza. Cumple con los criterios de universo y precio. [Fuente: Bloomberg, Reuters]",
        "confidence_score": 85,
        "routine": "Oracle_v1",
        "expires_at": "2024-04-25T20:00:00Z"
    },
    "execution": {}
}
```

**Ejemplo de Salida (para una señal de ESPERA):**
```json
{
    "status": "WAITING",
    "last_update": "2024-04-25T15:30:00Z",
    "signal": {
        "ticker": null,
        "action": "WAIT",
        "reason": "Condiciones de mercado inciertas: el índice VIX muestra alta volatilidad y hay declaraciones macroeconómicas importantes del Fed programadas para hoy. No se identificó una oportunidad de alta convicción que cumpla con todos los criterios de riesgo.",
        "confidence_score": 0,
        "routine": "Oracle_v1",
        "expires_at": "2024-04-25T20:00:00Z"
    },
    "execution": {}
}
```

---

## 💾 Integración con GitHub
Una vez que hayas generado el JSON, este será guardado automáticamente en `memory/pending_signal.json` en el repositorio de GitHub y se realizará un `git commit` y `git push`. Tu tarea es *solo* generar el JSON en el formato especificado.