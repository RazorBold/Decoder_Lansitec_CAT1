from flask import Flask, render_template, request, jsonify
from decode import decode_hex_message, format_duration

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/decode', methods=['POST'])
def decode():
    hex_message = request.json.get('hexMessage', '')
    try:
        decoded_message = decode_hex_message(hex_message)
        return jsonify(decoded_message)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000) 