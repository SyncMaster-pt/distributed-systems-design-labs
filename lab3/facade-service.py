from flask import Flask, jsonify, request, abort
from random import choice
import requests, socket, threading
import uuid

logging_service_ports = [8003, 8004, 8005]
logging_service_open_ports = []
messages_service = "http://127.0.0.1:8002/messages"

app = Flask(__name__)

def is_service_available():
    for port in logging_service_ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect(('127.0.0.1', port))
            if port not in logging_service_open_ports:
                logging_service_open_ports.append(port)
        except Exception as e:
            if port in logging_service_open_ports:
                logging_service_open_ports.remove(port)

@app.route('/', methods=['GET', 'POST'])
def facade_requests():
    if not logging_service_open_ports:
        return jsonify({"error": "Sorry, logging services are disabled"}), 500
    else:
        port = choice(logging_service_open_ports)

    if request.method == 'GET':
        try:
            logging_response = requests.get(f"http://127.0.0.1:{port}/logging")
            logging_response.raise_for_status()
            messages_response = requests.get(messages_service)
            messages_response.raise_for_status()
        except requests.RequestException as e:
            return jsonify({"error": str(e)}), 500
        return jsonify({"logs": logging_response.text, "messages": messages_response.text}), 200
    
    elif request.method == 'POST':
        try:
            if request.is_json:
                data = request.get_json()
                message = data.get('msg')
            else:
                message = request.form.get("msg")
            if not message:
                return jsonify({"error": "There is no message"}), 400
            id = str(uuid.uuid4())
            data = {"id": id, "msg": message}
            response = requests.post(f"http://localhost:{port}/logging", data=data)
            response.raise_for_status()
            return jsonify(data), 200
        except requests.RequestException as e:
            return jsonify({"error": str(e)}), 500
        
    else:
        abort(400)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=app.run, kwargs={"port": 8000})
    flask_thread.daemon = True
    flask_thread.start()

    while 1:
        is_service_available()
