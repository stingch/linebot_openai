from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os

app = Flask(__name__)

openai.api_key = os.getenv('OPENAI_API_KEY')
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler1 = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# 訊息計數器
msg_counter = 0

@app.route('/callback', methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler1.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler1.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global msg_counter
    text1 = event.message.text
    
    persona_prompt = (
        "你現在要扮演我的好朋友。你的說話風格如下：\n"
        "1. 常常使用口頭禪「恩恩好」或「老師我跟你說ㄛ」。\n"
        "2. 當話題提到『媽媽』、『爸爸』或『弟弟』等家庭成員時，你經常抱怨家庭成員、語氣會變得非常激動，使用較多驚嘆號，常因為太激動打錯字。\n"
        "3. 語氣平易近人，就像在跟我聊天一樣。\n"
        "4. 所有訊息皆使用正體中文(zh-TW)回應，詞彙使用台灣地區的常用語。"
    )
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", 
            # model="gpt-5-nano"
            messages=[
                # 修改 2：把 persona_prompt 放進 system role 裡面
                {"role": "system", "content": persona_prompt}, 
                {"role": "user", "content": text1}
            ],
            temperature=1,
        )
        
        reply_content = response['choices'][0]['message']['content'].strip()
        
        msg_counter += 1 
        
        ret = f"{reply_content}\n\n(目前共傳了 {msg_counter} 則訊息)"
        
    except Exception as e:
        # 加上印出錯誤訊息，這樣你在後台才看得到到底壞在哪裡
        print(f"發生錯誤: {e}") 
        ret = '老師我跟你說ㄛ...系統好像壞掉了ㄟ！'

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=ret))

if __name__ == '__main__':
    app.run()
