from flask import Flask, request, jsonify
import aiohttp
import asyncio

app = Flask(__name__)
messages = []
secondary_servers = ['http://secondary1:8001', 'http://secondary2:8001']

async def replicate_message(session, server, message):
    while True:
        try:
            async with session.post(f'{server}/replicate', json={'message': message}) as response:
                if response.status == 200:
                    print(f"Message replicated to {server}")
                    break
        except aiohttp.ClientError as e:
            print(f"Error replicating to {server}: {e}")
            await asyncio.sleep(1)

@app.route('/messages', methods=['POST'])
def add_message():
    message = request.json.get('message')
    if not message:
        return jsonify({'error': 'No message provided'}), 400

    messages.append(message)
    print(f"Received message: {message}")

    async def replicate_to_all():
        async with aiohttp.ClientSession() as session:
            tasks = [replicate_message(session, server, message) for server in secondary_servers]
            await asyncio.gather(*tasks)

    asyncio.run(replicate_to_all())

    return jsonify({'status': 'Message added and replicated'}), 200

@app.route('/messages', methods=['GET'])
def get_messages():
    return jsonify(messages), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)