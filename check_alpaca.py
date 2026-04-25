import os
import alpaca_trade_api as tradeapi
from dotenv import load_dotenv

# Cargar credenciales usando la misma lógica que el daemon
REPO_PATH = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(REPO_PATH, '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(REPO_PATH, 'env.template')

load_dotenv(env_path)

api = tradeapi.REST(
    key_id=os.getenv('ALPACA_API_KEY'),
    secret_key=os.getenv('ALPACA_SECRET_KEY'),
    base_url='https://paper-api.alpaca.markets'
)

try:
    account = api.get_account()
    print(f"Estado de la cuenta: {account.status}")
    print(f"Valor del portafolio: ${account.portfolio_value}")
    
    positions = api.list_positions()
    print("\n--- Posiciones Actuales ---")
    if not positions:
        print("No hay posiciones abiertas.")
    for p in positions:
        print(f"Activo: {p.symbol} | Cantidad: {p.qty} | Valor Actual: ${p.market_value}")
except Exception as e:
    print(f"Error al conectar con Alpaca: {e}")