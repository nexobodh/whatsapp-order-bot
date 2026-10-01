import os
import re
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

INSTANCE_ID = os.getenv("INSTANCE_ID")
API_TOKEN = os.getenv("API_TOKEN")

GREEN_API_BASE_URL = f"https://api.green-api.com/waInstance{INSTANCE_ID}"

def send_whatsapp_message(chat_id, text):
    url = f"{GREEN_API_BASE_URL}/sendMessage/{API_TOKEN}"
    payload = {"chatId": chat_id, "message": text}
    headers = {"Content-Type": "application/json"}
    try:
        requests.post(url, json=payload, headers=headers, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")

@app.route("/", methods=["GET"])
def health_check():
    return "WhatsApp Order Bot is Running!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    if not data or data.get("typeWebhook") != "incomingMessageReceived":
        return jsonify({"status": "ignored"}), 200

    message_data = data.get("messageData", {})
    sender_data = data.get("senderData", {})
    chat_id = sender_data.get("chatId")

    text_message = (
        message_data.get("textMessageData", {}).get("textMessage") or
        message_data.get("extendedTextMessageData", {}).get("text") or ""
    )

    # Simple & error-free Regex pattern extraction
    order_match = re.search(r"Order Reference:\s*([^\n]+)", text_message, re.IGNORECASE)
    service_match = re.search(r"Service:\s*([^\n]+)", text_message, re.IGNORECASE)
    mobile_match = re.search(r"Mobile:\s*((\+?88)?01[3-9]\d{8})", text_message, re.IGNORECASE)

    if order_match and mobile_match:
        order_ref = order_match.group(1).strip()
        service = service_match.group(1).strip() if service_match else "N/A"
        mobile = mobile_match.group(1).strip()

        reply_text = (
            f"ধন্যবাদ!\n\n"
            f"আপনার অর্ডারটি আমরা সফলভাবে পেয়েছি।\n"
            f"• Order Reference: {order_ref}\n"
            f"• Service: {service}\n\n"
            f"আমরা দ্রুত আপনার মোবাইল নম্বর ({mobile})-এ যোগাযোগ করব।"
        )
        
        send_whatsapp_message(chat_id, reply_text)
        return jsonify({"status": "success"}), 200

    return jsonify({"status": "ignored"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
