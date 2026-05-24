from flask import Flask, request, make_response
from openai import OpenAI
import hashlib
import xml.etree.ElementTree as ET
import time
import os

app = Flask(__name__)

TOKEN = os.environ.get("WECHAT_TOKEN", "mytoken")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

client = OpenAI(api_key=OPENAI_API_KEY)

def check_signature(signature, timestamp, nonce):
    tmp = sorted([TOKEN, timestamp, nonce])
    tmp_str = "".join(tmp).encode("utf-8")
    return hashlib.sha1(tmp_str).hexdigest() == signature

def ask_gpt(user_message):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是用户的贴心私人助理，用简洁友好的中文回复，像朋友聊天一样自然。"},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"抱歉，遇到了点问题：{str(e)}"

@app.route("/wechat", methods=["GET", "POST"])
def wechat():
    signature = request.args.get("signature", "")
    timestamp = request.args.get("timestamp", "")
    nonce = request.args.get("nonce", "")

    if request.method == "GET":
        if check_signature(signature, timestamp, nonce):
            return request.args.get("echostr", "")
        return "验证失败", 403

    if request.method == "POST":
        xml_data = ET.fromstring(request.data)
        msg_type = xml_data.find("MsgType").text
        from_user = xml_data.find("FromUserName").text
        to_user = xml_data.find("ToUserName").text

        if msg_type == "text":
            user_msg = xml_data.find("Content").text
            reply = ask_gpt(user_msg)
        else:
            reply = "目前只支持文字消息哦 😊"

        resp_xml = f"""<xml>
<ToUserName><![CDATA[{from_user}]]></ToUserName>
<FromUserName><![CDATA[{to_user}]]></FromUserName>
<CreateTime>{int(time.time())}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{reply}]]></Content>
</xml>"""
        response = make_response(resp_xml)
        response.content_type = "application/xml"
        return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
