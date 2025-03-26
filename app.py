from flask import Flask, request, abort
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

from linebot.models import ImageMessage

import os
from datetime import date

from dotenv import load_dotenv
load_dotenv()  # 加載 .env 文件


app = Flask(__name__)

# 設定 LINE Bot API

configuration = Configuration(access_token=os.getenv("Line_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("Line_handler"))

# 定義使用者的資料夾
user_directories = {
    'U87a2b80c7f3f9fd6435329e9d0bad43f': 'C:/Users/11021041.TWKEDING/KD_python/司機截圖',
    # 其他使用者對應的資料夾...
}

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@line_handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    """處理使用者傳送的圖片訊息"""
    message_id = event.message.id
    user_id = event.source.user_id

    # 取得圖片內容
    with ApiClient(configuration) as api_client:
        messaging_api = MessagingApi(api_client)
        message_content = messaging_api.get_message_content(message_id)

    print(f"接收到來自 {user_id} 的圖片，訊息 ID: {message_id}")

    # 檢查使用者目錄是否存在
    parent_directory = user_directories.get(user_id)
    if parent_directory:
        today_directory = os.path.join(parent_directory, str(date.today()))
        os.makedirs(today_directory, exist_ok=True)

        # 儲存圖片
        image_path = os.path.join(today_directory, f"{message_id}.jpg")
        with open(image_path, 'wb') as f:
            for chunk in message_content:
                f.write(chunk)

        # 回覆訊息
        with ApiClient(configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="圖片已成功儲存！")]
                )
            )
    else:
        # 若無對應使用者資料夾，回覆錯誤訊息
        with ApiClient(configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="抱歉，找不到對應的存儲位置。")]
                )
            )

@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    """處理文字訊息"""
    print(f"收到文字訊息: {event.message.text}")
    user_id = event.source.user_id
    print(user_id)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
