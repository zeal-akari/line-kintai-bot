import os
import datetime
import pytz

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# LINEトークンの取得（Renderの環境変数から）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise ValueError("LINEのトークンが設定されていません")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ユーザーIDと社員名の対応表
user_map = {
    "U48574bc03da24b86fc317be9c05905d5": "坂井陽",
    "U54a7a3235e5936055954f7284a2d49f9": "坂井正行",
    "U50a0d5c98616286c492d9c5e03b54896": "坂井幸代",
    "Ua94ec7c6897efc15bbb6f1c28c82f851": "齋子香織",
    "Uc89f3bf8f7084880bd3b02ebe87698f4": "谷澤陽一"
}

@app.route("/health_check", methods=["GET"])
def health_check():
    return "OK", 200

def record_to_sheet(user_id, message):
    name = user_map.get(user_id)
    if not name:
        return

    tz = pytz.timezone("Asia/Tokyo")
    now = datetime.datetime.now(tz)
    date_str = now.strftime("%Y/%m/%d")
    time_str = now.strftime("%H:%M:%S")

    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        '/etc/secrets/credentials.json', scope
    )
    client = gspread.authorize(creds)

    sheet = client.open("勤怠管理").worksheet(name)
    sheet.append_row([date_str, time_str, message])

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.strip()
    user_id = event.source.user_id

    print(f"record_to_sheet() を呼び出します：user_id={user_id}, msg={msg}")
    record_to_sheet(user_id, msg)

    user_name = user_map.get(user_id, "未登録ユーザー")
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"{user_name} さんの「{msg}」を記録しました。")
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
