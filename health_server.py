from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def health():
    return "OK", 200

def run_health_server():
    app.run(host='0.0.0.0', port=8080)

def start_health_server():
    server = Thread(target=run_health_server)
    server.daemon = True
    server.start()