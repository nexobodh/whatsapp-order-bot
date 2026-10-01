import os
import re
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

INSTANCE_ID = os.getenv("INSTANCE_ID")
API_TOKEN = os.getenv("API_TOKEN")

GREEN_API_BASE_URL = f"https://api.green-api.com/waInstance{INSTANCE_ID}"

# সম্পূর্ণ মেসেজ থেকে সব ডাটা রিড করার জন্য অ্যাডভান্সড Regex
ORDER_PARSER = re.compile(
    r"Order Reference:\s*(?P[^\n]+)\n"
    r"Service:\s*(?P[^\n]+)\n"
    r"(?:Amount:\s*(?P[^\n]+)\n)?"
    r"(?:Customer:\s*(?P[^\n]+)\n)?"
    r"Mobile:\s*(?P(\+?88)?01[3-9]\d{8})",
    re.DOTALL | re.IGNORECASE
)

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

    match = ORDER_PARSER.search(text_message)
    if match:
        extracted = match.groupdict()
        order_ref = extracted.get('order_ref', '').strip()
        service = extracted.get('service', '').strip()
        customer = extracted.get('customer', 'Customer').strip()
        mobile = extracted.get('mobile', '').strip()

        # ডায়নামিক কাস্টম রিপ্লাই মেসেজ
        reply_text = (
            f"ধন্যবাদ {customer}!\n\n"
            f"আপনার অর্ডারটি আমরা সফলভাবে রিসিভ করেছি।\n"
            f"• Order Ref: {order_ref}\n"
            f"• Service: {service}\n\n"
            f"আমরা খুব দ্রুত আপনার মোবাইল নম্বর ({mobile})-এ যোগাযোগ করব।"
        )
        
        send_whatsapp_message(chat_id, reply_text)
        return jsonify({"status": "success"}), 200

    return jsonify({"status": "ignored"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))