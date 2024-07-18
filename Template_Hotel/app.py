import os
from flask import Flask
from CocoChat import *
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = os.urandom(24)

load_dotenv()

@app.route('/whatsapp', methods=['POST'])
def handle_whatsapp():
    return whatsapp_reply()

if __name__ == '__main__':
    app.run(debug=True)

