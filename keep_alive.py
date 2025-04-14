from flask import Flask
from threading import Thread
import logging

# Flaskアプリの初期化
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/')
def home():
    return "Botは稼働中です！"

def run():
    """
    Flaskウェブサーバーを起動します。
    """
    try:
        app.run(host='0.0.0.0', port=8080, debug=False)
    except Exception as e:
        logging.error(f"ウェブサーバー起動中にエラーが発生しました: {e}")

def keep_alive():
    """
    Botを常時稼働させるためのWebサーバーをスレッドで起動します。
    """
    try:
        server = Thread(target=run, name="KeepAliveThread")
        server.daemon = True
        server.start()
        logging.info("Keep-aliveウェブサーバーが正常に起動しました。")
    except Exception as e:
        logging.error(f"Keep-aliveサーバーの起動に失敗しました: {e}")