import struct  # Untuk decode IEEE 754 float
from datetime import datetime

def format_duration(seconds):
    if seconds >= 60:
        minutes = seconds // 60
        return f'{minutes} minutes'
    return f'{seconds} seconds'

def decode_ieee754(hex_str):
    """Convert hex string to IEEE 754 float"""
    try:
        # Pack hex string into bytes and unpack as float
        return struct.unpack('!f', bytes.fromhex(hex_str))[0]
    except Exception:
        return None

def decode_utc_time(hex_str):
    """Convert hex timestamp to UTC datetime"""
    try:
        timestamp = int(hex_str, 16)
        return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')
    except Exception:
        return None

def calculate_rssi(hex_value):
    """Calculate RSSI from hex value"""
    decimal_value = int(hex_value, 16)
    return decimal_value - 256

def decode_parameter_command(param_type, param_value):
    """Decode parameter command based on type"""
    param_types = {
        '01': {
            'name': 'Heartbeat Period',
            'format': lambda x: f'{int(x, 16)} minutes'
        },
        '05': {
            'name': 'BLE Receiving Duration',
            'format': lambda x: f'{int(x, 16)}s'
        },
        '06': {
            'name': 'GNSS Receiving Duration',
            'format': lambda x: f'{int(x, 16)}s'
        },
        '0A': {
            'name': 'Bluetooth Position Beacon UUID Filter',
            'format': lambda x: '-'.join([x[i:i+2] for i in range(0, len(x), 2)])
        }
    }
    
    if param_type in param_types:
        param_info = param_types[param_type]
        return {
            'Parameter': param_info['name'],
            'Value': param_value,
            'Description': param_info['format'](param_value)
        }
    return {
        'Parameter': f'Unknown (Type: {param_type})',
        'Value': param_value,
        'Description': 'Unknown parameter type'
    }

def decode_hex_message(hex_message):
    parts = []
    
    # Check message type first
    if len(hex_message) >= 2:
        msg_type = hex_message[0]
        
        if msg_type == '1':  # Registration message
            # Define field lengths for Type 1
            field_lengths = [2,      # Type Bit Field
                            8,      # State Bit Field
                            2,      # Reserved
                            4,      # Heartbeat Period
                            4,      # BLE Position Report Interval
                            2,      # BLE Receiving Duration
                            4,      # GNSS Position Report Interval
                            2,      # GNSS Receiving Duration
                            4,      # Asset Beacon Report Interval
                            2,      # Asset Beacon Receiving Duration
                            4,      # Software Version
                            16,     # IMSI
                            4,      # Message ID
                            8]      # Reserved
            
            # Split the message
            current_pos = 0
            for length in field_lengths:
                if current_pos + length <= len(hex_message):
                    parts.append(hex_message[current_pos:current_pos + length])
                    current_pos += length
            
            result = {}
            
            # Decode Type Bit Field
            if len(parts) >= 1:
                type_field = parts[0]
                result['Type Bit Field'] = {
                    'Value': type_field,
                    'Description': 'Registration message'
                }
            
            # Decode State Bit Field
            if len(parts) >= 2:
                state_field = parts[1]
                state_descriptions = {
                    'BLE': (state_field[0] == 'F', 'BLE sign is "1" (enabled)'),
                    'GNSS': (state_field[0] == 'F', 'GNSS sign is "1" (enabled)'),
                    'Network Status Check': (state_field[0] == 'F', 'Network Status Check sign is "1" (enabled)'),
                    'Power Switch': (state_field[0] == 'F', 'Power Switch sign is "1" (enabled)'),
                    'Asset beacon sort enable': (state_field[1] == '3', 'Asset beacon sort enable is "1"'),
                    'GNSS failure report send function': (state_field[1] == '3', 'GNSS failure report send function is "1"'),
                    'Asset management enable': (state_field[2] == '8', 'Asset management enable is "1"'),
                    'Position Report Mode': (state_field[4] == '0', 'Position Report Mode is "00"'),
                    'Tamper Detection enable': (state_field[5] == '4', 'Tamper Detection enable is "1"')
                }
                
                status_dict = {}
                for key, (is_enabled, _) in state_descriptions.items():
                    status_dict[key] = "Enabled" if is_enabled else "Disabled"
                    
                result['State Bit Field'] = {
                    'Value': state_field,
                    'Status': status_dict
                }
            
            # Decode Heartbeat Period
            if len(parts) >= 4:
                hb_period = int(parts[3], 16)
                result['Heartbeat Period Bit Field'] = {
                    'Value': parts[3],
                    'Description': f'Heartbeat period is {hb_period * 30 // 60} minutes ({hb_period} * 30s)'
                }
            
            # Decode BLE Position Report Interval
            if len(parts) >= 5:
                ble_interval = int(parts[4], 16)
                result['BLE Position Report Interval Bit Field'] = {
                    'Value': parts[4],
                    'Description': f'BLE Position Report Interval is {ble_interval * 5 // 60} minutes ({ble_interval} * 5s)'
                }
            
            # Decode BLE Receiving Duration
            if len(parts) >= 6:
                ble_duration = int(parts[5], 16)
                result['BLE Receiving Duration Bit Field'] = {
                    'Value': parts[5],
                    'Description': f'BLE Receiving Duration is {ble_duration}s ({ble_duration} * 1s)'
                }
            
            # Decode GNSS Position Report Interval
            if len(parts) >= 7:
                gnss_interval = int(parts[6], 16)
                result['GNSS Position Report Interval Bit Field'] = {
                    'Value': parts[6],
                    'Description': f'GNSS Position Report Interval is {gnss_interval * 5 // 60} minutes'
                }
            
            # Decode GNSS Receiving Duration
            if len(parts) >= 8:
                gnss_duration = int(parts[7], 16)
                result['GNSS Receiving Duration Bit Field'] = {
                    'Value': parts[7],
                    'Description': f'GNSS Receiving Duration is {gnss_duration * 5}s ({gnss_duration} * 5s)'
                }
            
            # Decode Asset Beacon Report Interval
            if len(parts) >= 9:
                asset_interval = int(parts[8], 16)
                result['Asset Beacon Report Interval Bit Field'] = {
                    'Value': parts[8],
                    'Description': f'Asset Beacon Report Interval is {asset_interval * 5 // 60} minutes ({asset_interval} * 5s)'
                }
            
            # Decode Asset Beacon Receiving Duration
            if len(parts) >= 10:
                asset_duration = int(parts[9], 16)
                result['Asset Beacon Receiving Duration Bit Field'] = {
                    'Value': parts[9],
                    'Description': f'Asset Beacon Receiving Duration is {asset_duration}s ({asset_duration} * 1s)'
                }
            
            # Decode Software Version
            if len(parts) >= 11:
                sw_version = parts[10]
                major = int(sw_version[:2], 16)
                minor = int(sw_version[2:], 16)
                result['Software Version Bit Field'] = {
                    'Value': parts[10],
                    'Description': f'Firmware version is {major}.{minor:02d} ver'
                }
            
            # Decode IMSI
            if len(parts) >= 12:
                imsi = parts[11][:-1]  # Remove last character (F is reserved)
                result['IMSI Bit Field'] = {
                    'Value': parts[11],
                    'Description': f'International Mobile Subscriber Identity (IMSI): {imsi}'
                }
            
            # Decode Message ID
            if len(parts) >= 13:
                message_id = int(parts[12], 16)
                result['Message ID Bit Field'] = {
                    'Value': parts[12],
                    'Description': f'Message ID: {message_id:04x}, sequence number of downlink messages'
                }
            
            return result
            
        elif msg_type == '2':  # Heartbeat message
            # Define the field lengths for Type 2 message
            field_lengths = [2,  # Type Bit Field
                            8,  # State Bit Field
                            2,  # VOL Bit Field
                            2,  # VOL Percent Bit Field
                            2,  # BLE Receiving Count
                            2,  # GNSS-on Count
                            4,  # Temperature
                            4,  # Movement Duration
                            4,  # Reserved
                            4,  # Reserved
                            4,  # Message ID
                            8   # Reserved
                            ]
            
            # Split the message according to field lengths
            current_pos = 0
            for length in field_lengths:
                if current_pos + length <= len(hex_message):
                    parts.append(hex_message[current_pos:current_pos + length])
                    current_pos += length
            
            result = {}
            
            # Decode Type Bit Field
            if len(parts) >= 1:
                type_field = parts[0]
                if type_field[0] != '2':  # If not type 2, return early
                    return {'error': 'Not a Heartbeat message (Type 2)'}
                
                result['Type Bit Field'] = {
                    'Value': type_field,
                    'Description': 'Heartbeat message'
                }
            
            # Decode State Bit Field
            if len(parts) >= 2:
                state_field = parts[1]
                state_descriptions = {
                    'BLE': (state_field[0] == 'F', 'BLE sign is "1" (enabled)'),
                    'GNSS': (state_field[0] == 'F', 'GNSS sign is "1" (enabled)'),
                    'Network Status Check': (state_field[0] == 'F', 'Network Status Check sign is "1" (enabled)'),
                    'Power Switch': (state_field[0] == 'F', 'Power Switch sign is "1" (enabled)'),
                    'Asset beacon sort enable': (state_field[1] == '3', 'Asset beacon sort enable is "1"'),
                    'GNSS failure report send function': (state_field[1] == '3', 'GNSS failure report send function is "1"'),
                    'Asset management enable': (state_field[2] == '8', 'Asset management enable is "1"'),
                    'Position Report Mode': (state_field[4] == '0', 'Position Report Mode is "00"'),
                    'Tamper Detection enable': (state_field[5] == '4', 'Tamper Detection enable is "1"')
                }
                
                status_dict = {}
                for key, (is_enabled, _) in state_descriptions.items():
                    status_dict[key] = "Enabled" if is_enabled else "Disabled"
                    
                result['State Bit Field'] = {
                    'Value': state_field,
                    'Status': status_dict
                }

            # Decode Type 2 specific fields
            if len(parts) >= 3:
                vol_value = int(parts[2], 16)
                result['VOL Bit Field'] = {
                    'Value': parts[2],
                    'Description': f'Battery voltage is {vol_value * 0.1:.1f}V'
                }
            
            if len(parts) >= 4:
                vol_percent = int(parts[3], 16)
                result['VOL Percent Bit Field'] = {
                    'Value': parts[3],
                    'Description': f'Battery voltage is {vol_percent}%'
                }
            
            if len(parts) >= 5:
                ble_count = int(parts[4], 16)
                result['BLE Receiving Count Bit Field'] = {
                    'Value': parts[4],
                    'Description': f'The BLE receiving time is {ble_count} in one heartbeat period'
                }
            
            if len(parts) >= 6:
                gnss_count = int(parts[5], 16)
                result['GNSS-on Count Bit Field'] = {
                    'Value': parts[5],
                    'Description': f'GNSS is turned on {gnss_count} times in one heartbeat period'
                }
            
            if len(parts) >= 7:
                temp_hex = parts[6]
                temp_value = temp_hex[-2:]  # Mengambil 2 digit terakhir saja
                result['Temperature Bit Field'] = {
                    'Value': temp_hex,
                    'Description': f'The temperature is {temp_value}°C'
                }
            
            if len(parts) >= 8:
                movement_duration = int(parts[7], 16)
                result['Movement Duration Bit Field'] = {
                    'Value': parts[7],
                    'Description': f'In one heartbeat period, the device had moved {movement_duration} times, {movement_duration*5}s'
                }
            
            if len(parts) >= 11:  # Skip 2 reserved fields
                message_id = int(parts[10], 16)
                result['Message ID Bit Field'] = {
                    'Value': parts[10],
                    'Description': f'Message ID is {message_id:04x}, and one downlink message is received'
                }
            
            return result
            
        elif msg_type == '3':  # GNSS Position message
            # Define field lengths for Type 3
            field_lengths = [2,      # Type Bit Field
                           8,      # Longitude
                           8,      # Latitude
                           8,      # UTC Time
                           4,      # Reserved
                           4,      # Reserved
                           2]      # Reserved
            
            # Split the message
            current_pos = 0
            for length in field_lengths:
                if current_pos + length <= len(hex_message):
                    parts.append(hex_message[current_pos:current_pos + length])
                    current_pos += length
            
            result = {}
            
            # Decode Type Bit Field
            if len(parts) >= 1:
                type_field = parts[0]
                result['Type Bit Field'] = {
                    'Value': type_field,
                    'Description': f'GNSS Position message, Location {"succeeded" if type_field[1] == "0" else "failed"}'
                }
            
            # Decode Latitude (sekarang pertama)
            if len(parts) >= 2:
                latitude = decode_ieee754(parts[1])
                result['Latitude Bit Field'] = {
                    'Value': parts[1],
                    'Description': f'Latitude: {latitude:.6f}° (IEEE 754)'
                }
            
            # Decode Longitude (sekarang kedua)
            if len(parts) >= 3:
                longitude = decode_ieee754(parts[2])
                result['Longitude Bit Field'] = {
                    'Value': parts[2],
                    'Description': f'Longitude: {longitude:.6f}° (IEEE 754)'
                }
            
            # Decode UTC Time
            if len(parts) >= 4:
                utc_time = decode_utc_time(parts[3])
                result['Time Bit Field'] = {
                    'Value': parts[3],
                    'Description': f'UTC Time: {utc_time}'
                }
            
            return result
            
        elif msg_type == '4':  # Beacon message
            # Define field lengths for Type 4
            field_lengths = [2,      # Type Bit Field
                           2,      # Beacon Count
                           4,      # Major 1
                           4,      # Minor 1
                           2,      # RSSI 1
                           4,      # Major 2
                           4,      # Minor 2
                           2,      # RSSI 2
                           4,      # Reserved
                           4,      # Reserved
                           2]      # Reserved
            
            # Split the message
            current_pos = 0
            for length in field_lengths:
                if current_pos + length <= len(hex_message):
                    parts.append(hex_message[current_pos:current_pos + length])
                    current_pos += length
            
            result = {}
            
            # Decode Type Bit Field
            if len(parts) >= 1:
                type_field = parts[0]
                result['Type Bit Field'] = {
                    'Value': type_field,
                    'Description': f'Beacon message, {"Position beacon report" if type_field[1] == "0" else "Other type"}'
                }
            
            # Decode Beacon Count
            if len(parts) >= 2:
                beacon_count = int(parts[1], 16)
                result['Beacon Count Bit Field'] = {
                    'Value': parts[1],
                    'Description': f'Number of beacons: {beacon_count}'
                }
            
            # Decode first beacon
            if len(parts) >= 5:
                result['Beacon 1'] = {
                    'Value': f'Major: {parts[2]}, Minor: {parts[3]}, RSSI: {parts[4]}',
                    'Description': (
                        f'Major: 0x{parts[2]} ({int(parts[2], 16)})\n'
                        f'Minor: 0x{parts[3]} ({int(parts[3], 16)})\n'
                        f'RSSI: {calculate_rssi(parts[4])} dBm'
                    )
                }
            
            # Decode second beacon if exists
            if len(parts) >= 8:
                result['Beacon 2'] = {
                    'Value': f'Major: {parts[5]}, Minor: {parts[6]}, RSSI: {parts[7]}',
                    'Description': (
                        f'Major: 0x{parts[5]} ({int(parts[5], 16)})\n'
                        f'Minor: 0x{parts[6]} ({int(parts[6], 16)})\n'
                        f'RSSI: {calculate_rssi(parts[7])} dBm'
                    )
                }
            
            return result
            
        elif msg_type == '5':  # Alarm message
            # Define field lengths for Type 5
            field_lengths = [2,      # Type Bit Field
                           2,      # Alarm Bit Field
                           2]      # Reserved
            
            # Split the message
            current_pos = 0
            for length in field_lengths:
                if current_pos + length <= len(hex_message):
                    parts.append(hex_message[current_pos:current_pos + length])
                    current_pos += length
            
            result = {}
            
            # Decode Type Bit Field
            if len(parts) >= 1:
                type_field = parts[0]
                result['Type Bit Field'] = {
                    'Value': type_field,
                    'Description': 'Alarm message'
                }
            
            # Decode Alarm Bit Field
            if len(parts) >= 2:
                alarm_field = parts[1]
                alarm_types = {
                    '01': 'Low battery alarm',
                    '02': 'Power off alarm',
                    '03': 'Power on alarm',
                    '04': 'Movement alarm',
                    '05': 'Tamper detection alarm',
                    # Add more alarm types if needed
                }
                result['Alarm Bit Field'] = {
                    'Value': alarm_field,
                    'Description': alarm_types.get(alarm_field, 'Unknown alarm type')
                }
            
            return result
            
        elif msg_type == '6':  # Configuration Parameter Response
            result = {}
            
            # Decode Type Bit Field
            result['Type Bit Field'] = {
                'Value': hex_message[:2],
                'Description': 'Configuration Parameter Response message'
            }
            
            # Remove type field from message
            param_data = hex_message[2:]
            
            # Parse parameters
            params = []
            current_pos = 0
            param_count = 1
            
            while current_pos < len(param_data):
                param_type = param_data[current_pos:current_pos + 2]
                current_pos += 2
                
                # Special handling for UUID (type 0A)
                if param_type == '0A':
                    param_value = param_data[current_pos:]
                    param_length = len(param_value)
                else:
                    # For other parameter types, read 4 bytes
                    param_value = param_data[current_pos:current_pos + 4]
                    param_length = 4
                    current_pos += 4
                
                if param_type and param_value:
                    decoded_param = decode_parameter_command(param_type, param_value)
                    result[f'Parameter {param_count}'] = {
                        'Value': f'Type: {param_type}, Value: {param_value}',
                        'Description': (
                            f'{decoded_param["Parameter"]}\n'
                            f'Value: {decoded_param["Description"]}'
                        )
                    }
                    param_count += 1
                
                if param_type == '0A':  # If UUID parameter, break after processing
                    break
            
            return result
            
        else:
            return {'error': 'Unsupported message type'}
    
    return {'error': 'Invalid message format'}


