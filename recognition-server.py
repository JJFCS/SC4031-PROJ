# ====================================================================================================
# this is the cloud vm that we run locally on our machine
# this is in charge of doing the actual license plate reading
# ====================================================================================================


# ====================================================================================================
from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import numpy as np
import cv2
import easyocr
import time
from datetime import datetime
# ====================================================================================================


# ====================================================================================================
app = Flask(__name__)  # this creates the web server
CORS(app)  # this will allow the iphone to connect

# this reads text from images
print("Loading OCR engine...")
reader = easyocr.Reader(['en'], gpu=False)  # 'en' = english chars
print("OCR engine ready")

# this is for the storage for the online model updates
model_version, update_count, training_buffer = 1, 0, []
# ====================================================================================================


# ====================================================================================================
# this is just to check the health of the server
@app.route('/health', methods=['GET'])
def health_check():
    """this is just a simple check to see if the server is still running"""
    return jsonify({
        'model_version': model_version,
        'timestamp': datetime.now().isoformat(),
        'updates_received': update_count,
        'status': 'online',
        'server': 'local_machine',
    })
# ====================================================================================================


# ====================================================================================================
# this is our main recognition endpoint
@app.route('/recognize', methods=['POST'])
def recognize_plate():
    """
    this is where we receive an image, then read the license plate, then return the text
    this will be called by my iphone
    """
    start_time = time.time()
    
    try:
        # this is where we get the image from the request
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({
                'success': False,
                'plate': 'NO_IMAGE_PROVIDED'
            }), 400
        image_data = data['image']  # here we are just extracting the base64 image data

        # this is needed to remove the "data:image/jpeg;base64," prefix if present..
        if ',' in image_data:
            image_data = image_data.split(',')[1]

        # here we are converting base64 to an actual image
        img_bytes = base64.b64decode(image_data)
        nparr     = np.frombuffer(img_bytes, np.uint8)
        img       = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return jsonify({'success': False, 'plate': 'INVALID_IMAGE'}), 400
        results = reader.readtext(img)  # here we are running OCR to find the text within the image

        # here we are finding the most likely license plate text
        plate_text = "NOT_FOUND"
        best_confidence = 0
        
        for (bbox, text, confidence) in results:
            # i only want to keep letters and numbers
            clean_text = ''.join(c for c in text if c.isalnum()).upper()

            # depending on the country etc.. license plates are normally around 4-8 chars
            if len(clean_text) >= 4 and confidence > best_confidence:
                plate_text = clean_text
                best_confidence = confidence
        
        # Calculate processing time
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Print to console for debugging. useful for the demo too.
        device_id = data.get('device_id', 'unknown')
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {device_id}: '{plate_text}' ({elapsed_ms:.0f}ms)")
        
        # Send back the result
        return jsonify({
            'success': True,
            'plate': plate_text,
            'confidence': float(best_confidence),
            'processing_time_ms': elapsed_ms,
            'model_version': model_version
        })
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({
            'success': False,
            'plate': 'SERVER_ERROR',
            'error': str(e)
        }), 500
# ====================================================================================================


# ====================================================================================================
# this is our model updating endpoint
@app.route('/update', methods=['POST'])
def update_model():
    """this is where we receive corrections from users to improve the model"""
    global model_version, update_count, training_buffer
    
    try:
        data      = request.get_json()
        correct   = data.get('correct_label', 'unknown')
        previous  = data.get('previous_prediction', 'unknown')
        device_id = data.get('device_id', 'unknown')

        training_buffer.append({
            'previous': previous,
            'correct' : correct,
            'device'  : device_id,
            'time'    : datetime.now().isoformat()
        })
        
        update_count += 1

        # here we are simulating model retraining after every 1 correction (tried 3 but did not work..)
        if len(training_buffer) >= 1:
            model_version += 1
            print(f"MODEL UPDATED! New version: {model_version}")
            print(f"Applied {len(training_buffer)} corrections")
            training_buffer.clear()
        print(f"Correction #{update_count}: '{previous}' → '{correct}'")
        
        return jsonify({
            'success': True,
            'model_version': model_version,
            'total_updates': update_count,
            'message': f'Correction received. Model version {model_version}'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
# ====================================================================================================


if __name__ == '__main__':
    print("="*60)
    print("LICENSE PLATE RECOGNITION SERVER")
    print("="*60)
    print("Endpoints:")
    print("   GET  http://localhost:5001/health")
    print("   POST http://localhost:5001/recognize")
    print("   POST http://localhost:5001/update")
    print("   GET  http://localhost:5001/stats")
    print("="*60)
    print("Server starting...")
    print("")
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
