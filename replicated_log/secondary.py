from flask import Flask, request, jsonify
import time
#import argparse
import logging
from random import choice

app = Flask(__name__)
messages = []

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

'''parser = argparse.ArgumentParser(description='Hazelcast map logging service')

parser.add_argument('--port', type=int, choices=[8001, 8002], help='Logging service port', required=True)
argv = parser.parse_args()

secondary_port = argv.port'''

@app.route('/replicate', methods=['POST'])
def replicate_message():
    #time.sleep(10)
    message = request.json.get('message')
    _id = request.json.get('id')

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    time.sleep(5)

    if message in messages:
        logger.info(f"Message already exists: {message}")
        return jsonify({'status': 'Message already exists'}), 200

    if _id > len(messages)-1:
        messages.extend([None] * (_id - len(messages)))

    '''if _id == 2 or _id == 3:
        logger.error(f"Simulated internal server error for message: {message}")
        return jsonify({'error': 'Internal Server Error'}), 500
    
    messages.insert(_id, message)'''

    if choice([True, False]):
        logger.error(f"Simulated internal server error for message: {message}")
        return jsonify({'error': 'Internal Server Error'}), 500

    logger.info(f"Replicated message: {message}")
    return jsonify({'status': 'Message replicated'}), 200

@app.route('/messages', methods=['GET'])
def get_messages():
    result = []
    for message in messages:
        if message is None:
            break
        result.append(message)
    logger.info(f"Messages array: {messages}")
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)
