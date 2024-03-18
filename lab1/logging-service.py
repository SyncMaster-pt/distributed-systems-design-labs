from flask import Flask, jsonify, request, abort

logging_data = {}

app = Flask(__name__)

@app.route('/logging', methods=['GET', 'POST'])
def logging_requests():
    if request.method == 'GET':
        if logging_data:
            return jsonify(list(logging_data.values()))
        else:
            return "There is no messages"
        
    elif request.method == 'POST':
        id = request.form['id']
        message = request.form['msg']
        logging_data[id] = message
        print(f"Received message: {message}")
        return "Message was recevived by logging service", 201
    
    else:
        abort(400)

if __name__ == '__main__':
    app.run(port=8001)