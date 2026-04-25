#!/usr/bin/env python3
"""
daemon.py - Corre 24/7 en tu PC local
Monitorea GitHub por señales PENDING y ejecuta trades en Alpaca
"""

import json
import os
import sys
import time
import subprocess
from datetime import datetime
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi

# ─── CONFIG ───
# Detecta la ruta absoluta del repositorio (ajustado a tu estructura local)
REPO_PATH = os.path.dirname(os.path.abspath(__file__)) 
CHECK_INTERVAL = 60  # segundos entre checks

# Asegurar que la estructura de carpetas existe
os.makedirs(os.path.join(REPO_PATH, 'memory'), exist_ok=True)
os.makedirs(os.path.join(REPO_PATH, 'skills'), exist_ok=True)

# Cargar secrets (.env local)
load_dotenv(os.path.join(REPO_PATH, '.env'))

ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
MODE = os.getenv('ALPACA_PAPER', 'true').lower()

BASE_URL = 'https://paper-api.alpaca.markets' if MODE == 'true' else 'https://api.alpaca.markets'

# Guardrails (Configurables vía TRADING-STRATEGY.md en el futuro)
MAX_POSITION_PCT = 0.05
MIN_CASH_PCT = 0.20
MAX_TRADES_PER_WEEK = 3

# ─── FUNCIONES GIT ───

def git_pull():
    """Sincroniza con GitHub para ver si el Oráculo dejó una señal."""
    try:
        result = subprocess.run(
            ['git', 'pull', 'origin', 'main'],
            cwd=REPO_PATH, capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0
    except Exception as e:
        print(f"[{datetime.now()}] Git pull error: {e}")
        return False

def git_push(message):
    """Sube los resultados del trade y los logs a GitHub."""
    try:
        subprocess.run(['git', 'add', '.'], cwd=REPO_PATH, check=True)
        subprocess.run(['git', 'commit', '-m', message], cwd=REPO_PATH, check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], cwd=REPO_PATH, check=True)
        return True
    except Exception as e:
        print(f"[{datetime.now()}] Git push error: {e}")
        return False

# ─── FUNCIONES ALPACA ───

def get_api():
    return tradeapi.REST(key_id=ALPACA_API_KEY, secret_key=ALPACA_SECRET_KEY, base_url=BASE_URL)

def calculate_position_size(account, symbol):
    portfolio_value = float(account.portfolio_value)
    max_position = portfolio_value * MAX_POSITION_PCT
    
    api = get_api()
    last_trade = api.get_latest_trade(symbol)
    price = last_trade.price
    
    qty = int(max_position / price)
    buying_power = float(account.buying_power)
    min_cash = portfolio_value * MIN_CASH_PCT
    max_spend = buying_power - min_cash
    
    if qty * price > max_spend:
        qty = int(max_spend / price)
    
    return max(qty, 0), price

def count_trades_this_week():
    log_path = os.path.join(REPO_PATH, 'memory', 'TRADE-LOG.md')
    if not os.path.exists(log_path):
        return 0
    with open(log_path, 'r') as f:
        content = f.read()
    trades = [line for line in content.split('\n') if line.startswith('##') and 'EXECUTED' in line]
    return len(trades)

def execute_trade(signal_data):
    """Ejecuta trade en Alpaca con validaciones."""
    try:
        api = get_api()
        account = api.get_account()
        
        # Validar límite semanal
        weekly = count_trades_this_week()
        if weekly >= MAX_TRADES_PER_WEEK:
            return False, f"Weekly limit reached: {weekly}"
        
        # Calcular tamaño
        qty, price = calculate_position_size(account, signal_data['asset'])
        if qty <= 0:
            return False, "Calculated qty is 0"
        
        # Enviar orden
        order = api.submit_order(
            symbol=signal_data['asset'],
            qty=qty,
            side=signal_data['action'].lower(),
            type='market',
            time_in_force='day'
        )
        
        return True, {
            'order_id': str(order.id),
            'qty': qty,
            'price': price,
            'mode': MODE
        }
        
    except Exception as e:
        return False, str(e)

def main():
    # Configura la salida de consola para soportar UTF-8 (Emojis) en Windows
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')

    print(f"[{datetime.now()}] 🚀 Trading Daemon started")
    print(f"[{datetime.now()}] Mode: {MODE}")
    print(f"[{datetime.now()}] Checking every {CHECK_INTERVAL}s")
    
    # Ensure pending_signal.json exists and is valid JSON, or initialize it
    signal_path = os.path.join(REPO_PATH, 'memory', 'pending_signal.json')
    if not os.path.exists(signal_path) or os.path.getsize(signal_path) == 0:
        print(f"[{datetime.now()}] 🛠️ Inicializando {signal_path} con estado 'WAITING' por defecto.")
        default_signal = {
            "timestamp": datetime.now().isoformat(),
            "routine": "SYSTEM_INIT",
            "asset": "NONE",
            "action": "HOLD",
            "rationale": "Sistema inicializado. Esperando señal del Oráculo.",
            "confidence": "N/A",
            "source_urls": [],
            "status": "WAITING",
            "expires_at": (datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)).isoformat(), # Expires end of today
            "guardrails_check": {
                "weekly_trades": 0,
                "max_trades_ok": True,
                "universe_ok": True,
                "price_ok": True
            }
        }
        with open(signal_path, 'w', encoding='utf-8') as f:
            json.dump(default_signal, f, indent=2)
        git_push("System: Initialized memory/pending_signal.json with default WAITING state.")

    while True:
        try:
            # 1. Pull latest from GitHub
            git_pull()
            
            # 2. Leer señal pendiente (en la carpeta memory según tu diseño)
            signal_path = os.path.join(REPO_PATH, 'memory', 'pending_signal.json')
            
            try:
                with open(signal_path, 'r', encoding='utf-8') as f:
                    signal_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"[{datetime.now()}] ❌ Error al leer o decodificar {signal_path}: {e}. El archivo puede estar ausente, vacío o mal formado.")
                time.sleep(CHECK_INTERVAL)
                continue
            
            # 3. Verificar si hay señal PENDING
            if signal_data.get('status') != 'PENDING':
                print(f"[{datetime.now()}] 😴 Estado actual: {signal_data.get('status')}. Esperando PENDING...")
                time.sleep(CHECK_INTERVAL)
                continue
            
            # 4. Verificar expiración
            if 'expires_at' in signal_data:
                # Maneja offsets como -05:00 o Z
                exp_str = signal_data['expires_at'].replace('Z', '+00:00')
                expires = datetime.fromisoformat(exp_str)
                if expires.timestamp() < datetime.now().timestamp():
                    signal_data['status'] = 'EXPIRED'
                    with open(signal_path, 'w', encoding='utf-8') as f:
                        json.dump(signal_data, f, indent=2)
                    git_push(f"Signal expired: {signal_data['asset']}")
                    print(f"[{datetime.now()}] ⚠️ Signal expired")
                    continue
            
            # 5. Ejecutar trade
            print(f"[{datetime.now()}] 🔔 Signal detected: {signal_data['action']} {signal_data['asset']}")
            
            success, result = execute_trade(signal_data)
            
            # 6. Actualizar señal
            signal_data['status'] = 'PROCESSED' if success else 'FAILED'
            signal_data['execution'] = {
                'executed_at': datetime.now().isoformat(),
                'result': 'SUCCESS' if success else 'FAILED',
                'details': result,
                'mode': MODE
            }
            
            with open(signal_path, 'w', encoding='utf-8') as f:
                json.dump(signal_data, f, indent=2)
            
            # 7. Escribir en TRADE-LOG.md (Auditoría completa)
            log_path = os.path.join(REPO_PATH, 'memory', 'TRADE-LOG.md')
            log_entry = (
                f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} CT | {'EXECUTED' if success else 'FAILED'} | {signal_data['asset']} | {signal_data['action']}\n"
                f"**Signal Source:** {signal_data.get('routine', 'N/A')}\n"
                f"**Rationale:** {signal_data.get('rationale', 'N/A')}\n"
                f"**Order ID:** {result.get('order_id', 'N/A') if success else 'N/A'}\n"
                f"**Qty:** {result.get('qty', 'N/A') if success else 'N/A'}\n"
                f"**Price:** ${result.get('price', 'N/A') if success else 'N/A'}\n"
                f"**Mode:** {MODE}\n"
                f"**Status:** {'✅ FILLED' if success else f'❌ ERROR: {result}'}\n"
            )
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            
            # 8. Push a GitHub
            git_push(f"Trade {'executed' if success else 'failed'}: {signal_data['action']} {signal_data['asset']}")
            
            print(f"[{datetime.now()}] {'✅ Trade executed' if success else f'❌ Trade failed: {result}'}")

        except Exception as e:
            print(f"[{datetime.now()}] ❌ Daemon error: {e}")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()