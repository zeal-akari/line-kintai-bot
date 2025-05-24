import os
import datetime
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# LINE Messaging API 認証情報（環境変数から取得）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise ValueError("LINEのトークンかシークレットが設定されていません")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ユーザーIDと社員名の対応表（必要に応じて追加）
user_map = {
    "U48574bc03da24b86fc317be9c05905d5": "坂井陽",
    "Uxxxxxxxxxx2": "鈴木花子",
    "Uxxxxxxxxxx3": "佐藤健",
    "Uxxxxxxxxxx4": "田中花子",
    "Uxxxxxxxxxx5": "高橋一郎"
}

# Google Sheets に記録する関数
def record_to_sheet(user_id, message):
    name = user_map.get(user_id)
    if not name:
        return  # 登録されていないユーザーはスキップ

    now = datetime.datetime.now()
    date_str = now.strftime("%Y/%m/%d")
    time_str = now.strftime("%H:%M:%S")

    # Google Sheets API 認証
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        '/etc/secrets/credentials.json', scope
    )
    client = gspread.authorize(creds)

    # スプレッドシートを開き、対応するシート（タブ）を選択
    sheet = client.open("勤怠記録").worksheet(name)
    sheet.append_row([date_str, time_str, message])

# Webhookエンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# メッセージ受信時の処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.strip()
    user_id = event.source.user_id

    # 勤怠記録を実行
    record_to_sheet(user_id, msg)

    user_name = user_map.get(user_id, "未登録ユーザー")
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"{user_name} さんの「{msg}」を記録しました。")
    )


# アプリ起動
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
"# �ăf�v���C�����p�R�����g" 
