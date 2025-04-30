import requests
import json
import time

API_KEY = "w0iwBGK1axMcwxB6D1S5dnFPaIXR9pvXnek7HHQPxfsR0aAX6c1dIsge9JDh1KkBKdDThVcAtYmoEZphzNEJGV"
API_ENDPOINT = "https://api.ataix.kz"

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

ASSET = "IMX"
QUOTE_CURRENCY = "USDT"
SLIPPAGE_LIMIT = 0.05

class TradingBot:
    def __init__(self, app):
        self.app = app
        self.running = True
        self.price_history = []

    def fetch_balance(self):
        try:
            res = requests.get(f"{API_ENDPOINT}/api/user/balances", headers=HEADERS)
            content = res.json()
            usdt = content.get("result", {}).get("available", {}).get("USDT", "0.0")
            balance = float(usdt)
            self.app.update_balance(balance)
            return balance
        except Exception as e:
            self.app.log(f"❌ Ошибка баланса: {str(e)}")
            return 0.0

    def get_symbol_list(self):
        try:
            response = requests.get(f"{API_ENDPOINT}/api/symbols", headers=HEADERS)
            return response.json().get("result", [])
        except Exception as e:
            self.app.log(f"❌ Ошибка списка пар: {str(e)}")
            return []

    def locate_pair(self, symbols):
        for item in symbols:
            if item.get("base", "").upper() == ASSET and item.get("quote", "").upper() == QUOTE_CURRENCY:
                try:
                    minimum = float(item.get("minTradeSize", 0.01))
                    market_price = float(item.get("ask", 0) or item.get("priceToCompare", 0))
                    self.app.log(f"✅ Найдена пара {item['symbol']}")
                    return item["symbol"], minimum, market_price
                except Exception as e:
                    self.app.log(f"❌ Ошибка обработки пары: {str(e)}")
        raise Exception("❌ Не найдена пара IMX/USDT")

    def smart_round(self, val, step):
        return round(round(val / step) * step, 6)

    def post_order(self, symbol, price, qty):
        body = {
            "symbol": symbol,
            "side": "buy",
            "type": "limit",
            "quantity": round(qty, 8),
            "price": round(price, 6)
        }
        resp = requests.post(f"{API_ENDPOINT}/api/orders", headers=HEADERS, json=body)
        result = resp.json()
        if result.get("status"):
            self.app.log(f"✅ Ордер создан по цене {price:.6f}")
            return result
        else:
            raise Exception(f"❌ Ошибка создания ордера: {result}")

    def run(self):
        self.running = True
        placed_orders = []

        while self.running:
            try:
                balance = self.fetch_balance()
                if balance <= 0:
                    self.app.log("⚠️ Недостаточно средств")
                    time.sleep(10)
                    continue

                symbols = self.get_symbol_list()
                trading_pair, min_qty, market_price = self.locate_pair(symbols)

                # Обновляем график
                self.price_history.append(market_price)
                if len(self.price_history) > 20:
                    self.price_history.pop(0)
                self.app.update_chart(self.price_history)

                levels = [0.02, 0.05, 0.08]
                used_funds = 0

                for diff in levels:
                    intended = market_price * (1 - diff)
                    limit_price = self.smart_round(intended, 0.001)
                    min_acceptable = self.smart_round(market_price * (1 - SLIPPAGE_LIMIT), 0.001)
                    if limit_price < min_acceptable:
                        limit_price = min_acceptable

                    cost = limit_price * min_qty
                    if used_funds + cost > balance:
                        self.app.log(f"🚫 Недостаточно баланса на ордер {limit_price:.6f}")
                        break

                    try:
                        order_resp = self.post_order(trading_pair, limit_price, min_qty)
                        order_id = (
                            order_resp.get("result", {}).get("orderID") or
                            order_resp.get("result", {}).get("id") or
                            order_resp.get("id") or
                            "unknown"
                        )
                        placed_orders.append({
                            "id": order_id,
                            "symbol": trading_pair,
                            "price": limit_price,
                            "amount": min_qty,
                            "status": "NEW"
                        })
                        used_funds += cost
                    except Exception as e:
                        self.app.log(f"❌ Ошибка ордера: {e}")

                with open("orders.json", "w", encoding="utf-8") as file:
                    json.dump(placed_orders, file, indent=4, ensure_ascii=False)

                self.app.log(f"✅ Завершён цикл торговли. Ордера сохранены.")

            except Exception as ex:
                self.app.log(f"❌ Ошибка торговли: {ex}")

            time.sleep(5)  # Ждём 5 секунд между циклами

