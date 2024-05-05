from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
import base64
import hashlib
import hmac
import json
import openai
import os
import sys

# Line Bot
line_bot_api = LineBotApi(os.environ.get('CHANNEL_ACCESS_TOKEN'))
channel_secret = os.environ.get('CHANNEL_SECRET')
handler = WebhookHandler(channel_secret)

# OpenAI Client
client = openai.OpenAI()


def linebot(request):
    if request.method != 'POST' or 'X-Line-Signature' not in request.headers:
        return 'Error: Invalid source', 403

    x_line_signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    hash = hmac.new(channel_secret.encode('utf-8'), body.encode('utf-8'), hashlib.sha256).digest()
    signature = base64.b64encode(hash).decode('utf-8')

    if x_line_signature != signature:
        return 'Invalid signature', 403

    try:
        json_data = json.loads(body)
        handler.handle(body, x_line_signature)

        if len(json_data['events']) == 0:
            return 'OK', 200

        reply_token = json_data['events'][0]['replyToken']
        user_input = json_data['events'][0]['message']['text']

        completions = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "system", "content": "Reply in Traditional Chinese unless otherwise specified."},
                {"role": "user", "content": f"{user_input}\n\nResponse:"}
            ]
        )

        message = completions.choices[0].message.content.strip()

        line_bot_api.reply_message(reply_token, TextSendMessage(message))

        return 'OK', 200
    except Exception as e:
        print(e, file=sys.stderr)

        return 'Unexpected Error', 500
