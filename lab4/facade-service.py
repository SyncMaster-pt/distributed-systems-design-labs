from flask import Flask, jsonify, request, abort
from random import choice
import requests, socket, threading
import uuid
import pika

logging_service_ports = [8003, 8004, 8005]
logging_service_open_ports = []
messages_service_ports = [8006, 8007]
messages_service_open_ports = []

app = Flask(__name__)

def is_service_available(service_ports, service_open_ports):
    for port in service_ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect(('127.0.0.1', port))
            if port not in service_open_ports:
                service_open_ports.append(port)
        except Exception as e:
            if port in service_open_ports:
                service_open_ports.remove(port)

@app.route('/', methods=['GET', 'POST'])
def facade_requests():
    if not logging_service_open_ports:
        return jsonify({"error": "Sorry, logging services are disabled"}), 500
    elif not messages_service_open_ports:
        return jsonify({"error": "Sorry, messages services are disabled"}), 500
    else:
        logging_port = choice(logging_service_open_ports)
        messages_port = choice(messages_service_open_ports)

    if request.method == 'GET':
        try:
            logging_response = requests.get(f"http://127.0.0.1:{logging_port}/logging")
            logging_response.raise_for_status()
            messages_response = requests.get(f"http://127.0.0.1:{messages_port}/messages")
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
            response = requests.post(f"http://localhost:{logging_port}/logging", data=data)
            response.raise_for_status()

            #Insert message to the RabbitMQ queue
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 5672))
            channel = connection.channel()
            channel.queue_declare(queue='lab4_messages')
            channel.basic_publish(exchange='', routing_key='lab4_messages', body=message)
            connection.close()
            
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
        is_service_available(logging_service_ports, logging_service_open_ports)
        is_service_available(messages_service_ports, messages_service_open_ports)
