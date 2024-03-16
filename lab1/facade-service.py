from flask import Flask, jsonify, request, abort
import requests
import uuid

logging_service = "http://127.0.0.1:8001/logging"
messages_service = "http://127.0.0.1:8002/messages"

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def facade_requests():
    if request.method == 'GET':
        try:
            logging_response = requests.get(logging_service)
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
            response = requests.post(logging_service, data=data)
            response.raise_for_status()
            return jsonify(data), 200
        except requests.RequestException as e:
            return jsonify({"error": str(e)}), 500
        
    else:
        abort(400)

if __name__ == '__main__':
    app.run(port=8000)
