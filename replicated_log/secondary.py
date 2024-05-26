from flask import Flask, request, jsonify
import time
import argparse

app = Flask(__name__)
messages = []

'''parser = argparse.ArgumentParser(description='Hazelcast map logging service')

parser.add_argument('--port', type=int, choices=[8001, 8002], help='Logging service port', required=True)
argv = parser.parse_args()

secondary_port = argv.port'''

@app.route('/replicate', methods=['POST'])
def replicate_message():
    message = request.json.get('message')
    if not message:
        return jsonify({'error': 'No message provided'}), 400

    time.sleep(5)

    messages.append(message)
    print(f"Replicated message: {message}")
    return jsonify({'status': 'Message replicated'}), 200

@app.route('/messages', methods=['GET'])
def get_messages():
    return jsonify(messages), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)
