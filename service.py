# services/whatsapp_service.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()
# Move these to environment variables in real apps
ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
WHATSAPP_API_URL = f'https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages'

HEADERS = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json'
}

def send_order_confirmation(phone_number: str, order_id: str) -> dict:
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
        "name": "hello_world",
        "language": { "code": "en_US" }
        }
    }

    response = requests.post(WHATSAPP_API_URL, headers=HEADERS, json=payload)

    if response.status_code == 200:
        return {
            "status": "success",
            "message_id": response.json().get("messages")[0]["id"]
        }
    else:
        return {
            "status": "error",
            "response": response.json()
        }
