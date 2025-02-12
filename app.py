from flask import Flask, render_template, request, jsonify
from decode import decode_hex_message, format_duration
import paho.mqtt.client as mqtt

app = Flask(__name__)

# MQTT Configuration
BROKER_HOST = "36.92.168.180"
BROKER_PORT = 19383

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

@app.route('/publish', methods=['POST'])
def publish_message():
    try:
        imei = request.json.get('imei', '')
        payload = request.json.get('payload', '')

        if not imei or not payload:
            return jsonify({'error': 'IMEI and payload are required'}), 400

        # Create MQTT client
        client = mqtt.Client(protocol=mqtt.MQTTv5)
        
        # Connect to broker
        client.connect(BROKER_HOST, BROKER_PORT)
        
        # Publish message
        topic = f"lansitec/sub/{imei}"
        result = client.publish(topic, payload)
        
        # Disconnect
        client.disconnect()

        if result.rc == 0:
            return jsonify({'success': True, 'message': 'Message published successfully'})
        else:
            return jsonify({'error': 'Failed to publish message'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 
