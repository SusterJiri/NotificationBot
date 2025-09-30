import asyncio
import json
import time
import hmac
import hashlib
import secrets
import string
import requests
import re
import os
import websockets
from dotenv import load_dotenv

load_dotenv("config.env")

BINANCE_WS_BASE = "wss://api.binance.com/sapi/wss"
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TOPIC = "com_announcement_en"

def generate_random_string(length=16):
    return ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(length))

def get_binance_server_time():
    try:
        r = requests.get("https://api.binance.com/api/v3/time", timeout=5)
        server_time = int(r.json()["serverTime"])
        print(f"Server time: {server_time}")
        return server_time
    except Exception as e:
        print(f"Failed to get server time: {e}")
        # Fallback to local time
        local_time = int(time.time() * 1000)
        print(f"Using local time: {local_time}")
        return local_time

def create_signed_url(topic=TOPIC, recvWindow=30000):
    if not BINANCE_API_SECRET:
        raise RuntimeError("BINANCE_API_SECRET missing")

    timestamp = str(get_binance_server_time())

    params = {
        "random": generate_random_string(16),
        "recvWindow": str(recvWindow),
        "timestamp": timestamp,
        "topic": topic
    }

    sorted_items = sorted(params.items(), key=lambda kv: kv[0])
    payload = "&".join(f"{k}={v}" for k, v in sorted_items)

    print("Signature payload:", payload)

    signature = hmac.new(
        BINANCE_API_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    print("Signature:", signature)

    final_url = f"{BINANCE_WS_BASE}?{payload}&signature={signature}"
    return final_url

async def notify_telegram(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram not configured - missing BOT_TOKEN or CHAT_ID")
        return
    
    print(f"Sending Telegram message to chat {CHAT_ID}")
    print(f"Message: {text[:100]}")
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        response = requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)
        
        if response.status_code == 200:
            print("Telegram message sent successfully!")
        else:
            print(f"Telegram API error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Telegram send failed: {e}")
        print(f"URL: {url}")
        print(f"Chat ID: {CHAT_ID}")
        print(f"Bot token starts with: {BOT_TOKEN[:10] if BOT_TOKEN else 'None'}...")

async def send_ping(ws):
    while True:
        try:
            await asyncio.sleep(25)
            await ws.ping()
            print("WebSocket PING sent")
        except Exception as e:
            print(f"Ping error: {e}")
            break

async def listen_announcements():
    if not BINANCE_API_KEY:
        raise RuntimeError("BINANCE_API_KEY missing")
    
    print(f"API Key: {BINANCE_API_KEY[:10]}..." if BINANCE_API_KEY else "API Key: None")
    print(f"API Secret: {BINANCE_API_SECRET[:10]}..." if BINANCE_API_SECRET else "API Secret: None")

    while True:
        try:
            ws_url = create_signed_url()
            headers = [("X-MBX-APIKEY", BINANCE_API_KEY)]

            async with websockets.connect(ws_url, extra_headers=headers, ping_interval=None) as ws:
                sub = {"command": "SUBSCRIBE", "value": TOPIC}
                await ws.send(json.dumps(sub))

                ping_task = asyncio.create_task(send_ping(ws))

                try:
                    async for raw in ws:
                        try:
                            msg = json.loads(raw)
                            print("Received message:", msg)
                        except Exception as e:
                            print(f"Failed to parse JSON: {e}, raw: {raw}")
                            continue

                        if isinstance(msg, dict):
                            if msg.get("type") == "COMMAND" and msg.get("data") == "SUCCESS" and msg.get("subType") == "SUBSCRIBE":
                                test_text = "Bot connected successfully to Binance announcements!"
                                print(test_text)
                                await notify_telegram(test_text)
                            
                            elif "result" in msg:
                                print(f"Subscription result: {msg}")
                            
                            elif "data" in msg:
                                try:
                                    if isinstance(msg["data"], str):
                                        try:
                                            data_parsed = json.loads(msg["data"])
                                        except json.JSONDecodeError:
                                            print(f"Data is string but not JSON: {msg['data']}")
                                            continue
                                    else:
                                        data_parsed = msg["data"]
                                    
                                    title = data_parsed.get("title", "")
                                    content = data_parsed.get("content", "")
                                    body = data_parsed.get("body", "")
                                    description = data_parsed.get("description", "")
                                    catalog_name = data_parsed.get("catalogName", "")
                                    
                                    full_text = f"{title} {content} {body} {description} {catalog_name}".lower()
                                    
                                    if any(k in full_text for k in ["will list", "new listing", "trading pair", "binance will list", "will add", "binance will add"]):
                                        token_match = re.search(r'\(([A-Z]+)\)', title)
                                        token_symbol = token_match.group(1) if token_match else "Unknown"
                                        
                                        text = f"NEW LISTING ALERT! \nToken: {token_symbol}\n {title}\n\nCheck Binance now!"
                                        print(text)
                                        await notify_telegram(text)
                                
                                except Exception as e:
                                    print(f"Error processing data: {e}")
                            
                            else:
                                print(f"Other message type: {msg}")
                    
                    print("Message loop ended - connection closed by server")
                except websockets.exceptions.ConnectionClosed as e:
                    print(f"WebSocket connection closed: {e}")
                except Exception as e:
                    print(f"Error in message loop: {e}")
                finally:
                    ping_task.cancel()

        except Exception as e:
            print("Connection / processing error:", e)

        print("Reconnecting in 10s...")
        await asyncio.sleep(10)

if __name__ == "__main__":
    
    asyncio.run(listen_announcements())
