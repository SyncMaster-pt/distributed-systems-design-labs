from flask import Flask, request, jsonify
import aiohttp
import asyncio
import threading
import logging

app = Flask(__name__)
messages = []
secondary_servers = ['http://secondary1:8001', 'http://secondary2:8001']

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def replicate_message(session, server, message, _id):
    while True:
        try:
            async with session.post(f'{server}/replicate', json={'message': message, 'id': _id}) as response:
                if response.status == 200:
                    logger.info(f"Message replicated to {server}")
                    break
        except aiohttp.ClientResponseError as e:
            logger.error(f"Error replicating to {server}: HTTP error {e.status}")
            await asyncio.sleep(5)
        except aiohttp.ClientError as e:
            logger.error(f"Error replicating to {server}: {e}")
            await asyncio.sleep(5)

@app.route('/messages', methods=['POST'])
def add_message():
    message = request.json.get('message')
    w = request.json.get('w')

    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    if not w or w > len(secondary_servers) + 1:
        w = len(secondary_servers) + 1
    elif w < 1:
        return jsonify({'error': 'Concern must be an int greater than or equal to 1'}), 400

    if message in messages:
        logger.info(f"Message already exists: {message}")
        return jsonify({'status': 'Message already exists'}), 200
    
    messages.append(message)
    _id = messages.index(message)
    logger.info(f"Received message: {message}")

    async def replicate_to_secondary(concern):
            if concern == 1:
                async def replicate_to_all(message):
                    async with aiohttp.ClientSession() as session:
                        tasks = [replicate_message(session, server, message, _id) for server in secondary_servers]
                        await asyncio.gather(*tasks)
                threading.Thread(target=asyncio.run, args=(replicate_to_all(message),)).start()
            else:
                responses = []
                async with aiohttp.ClientSession() as session:
                    tasks = [replicate_message(session, server, message, _id) for server in secondary_servers]
                    for completed_task in asyncio.as_completed(tasks):
                        result = await completed_task
                        responses.append(result)
                        if len(responses) >= concern-1:
                            break
                return

    asyncio.run(replicate_to_secondary(concern=w))

    return jsonify({'status': 'Message added and replicated'}), 200

@app.route('/messages', methods=['GET'])
def get_messages():
    return jsonify(messages), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)