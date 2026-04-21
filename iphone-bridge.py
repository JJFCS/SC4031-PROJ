# ====================================================================================================
# HTTPS version - works with iPhone camera
# the purpose of this is for the camera webpage to my iphone and then it will forward to the recognition server
# ====================================================================================================


# ====================================================================================================
from flask import Flask, render_template_string, request, jsonify
import requests, socket
# ====================================================================================================


# ====================================================================================================
app = Flask(__name__)
RECOGNITION_SERVER = "http://localhost:5001"  # note the change to 5001
# ====================================================================================================


# ====================================================================================================
CAMERA_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <title>License Plate Scanner</title>
    <style>
        * {
            margin:  0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            flex-direction: column;
            background: #000; height: 100vh; color: #fff;
            display   : flex;
        }
        
        .header {
            padding: 20px;
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .header h1 {
            font-size:  24px;
            font-weight: 600;
        }
        
        .header p {
            font-size: 12px;
            opacity:    0.8;
            margin-top: 5px;
        }
        
        .camera-container {
            background: #000;
            overflow: hidden;
            flex    : 1;
            position: relative;
        }
        
        #video {
            width:  100%;
            height: 100%;
            object-fit: cover;
        }
        
        .scan-frame {
            position:   absolute;
            pointer-events: none;
            border: 3px solid #00ff00;
            border-radius: 15px; height: 25%; left: 50%; width: 80%;
            box-shadow: 0 0 0 9999px rgba(0,0,0,0.5);
            animation: pulse 1.5s infinite;
            transform: translate(-50%, -50%);
            top: 50%;
        }
        
        @keyframes pulse {
            50%  { border-color: #00ff00; opacity: 1;   }
            0%   { border-color: #00ff00; opacity: 0.5; }
            100% { border-color: #00ff00; opacity: 0.5; }
        }
        
        .scan-line {
            position: absolute; top: 0; left: 0; width: 100%; height: 2px;
            background: #00ff00; animation: scan 2s linear infinite;
        }
        
        @keyframes scan {
            0%   { top: 0;    }
            100% { top: 100%; }
        }
        
        .controls {
            padding: 20px; background: rgba(0,0,0,0.9);
        }
        
        .capture-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); transition: transform 0.2s;
            border: none; border-radius: 50px; width: 100%; padding: 18px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            color: white;
        }
        
        .capture-btn:active {
            transform: scale(0.98);
        }
        
        .capture-btn:disabled {
            opacity: 0.5;
        }
        
        .result {
            margin-top: 15px; padding: 15px; text-align: center;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
        }
        
        .result-label {
            font-size: 12px; margin-bottom: 5px; opacity: 0.7;
        }
        
        .result-text {
            letter-spacing: 2px;
            font-size: 24px;
            font-weight: bold;
            font-family: 'Courier New', monospace;
        }
        
        .result-success {
            color: #00ff00;
        }
        
        .result-error {
            color: #ff4444;
        }
        
        .stats {
            font-size: 10px; margin-top: 10px; opacity: 0.5;
        }
        
        .loading {
            display: inline-block;
            height: 20px; width: 20px; margin-left: 10px;
            border: 2px solid #fff;
            border-radius: 50%;
            border-top-color: transparent;
            animation: spin 0.6s linear infinite;
            vertical-align: middle;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .error-message {
            background: rgba(255,68,68,0.2); color: #ff4444;
            border-radius: 10px; margin-top: 10px; padding: 10px; font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>License Plate Scanner</h1>
    </div>
    
    <div class="camera-container">
        <video id="video" autoplay playsinline muted></video>
        <div class="scan-frame">
            <div class="scan-line"></div>
        </div>
    </div>
    
    <div class="controls">
        <button class="capture-btn" id="captureBtn">
            CAPTURE LICENSE PLATE
        </button>
        
        <div class="result">
            <div class="result-label">DETECTED PLATE</div>
            <div class="result-text" id="resultText">Ready</div>
            <div class="stats" id="stats"></div>
        </div>
    </div>
    
    <canvas id="canvas" style="display:none;"></canvas>
    
    <script>
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const captureBtn = document.getElementById('captureBtn');
        const resultText = document.getElementById('resultText');
        const statsDiv = document.getElementById('stats');
        
        let isProcessing = false;
        let stream = null;
        
        // this is the function to start camera
        async function startCamera() {
            try {
                const constraints = {
                    video: {
                        facingMode: { exact: "environment" }
                    }
                };
                
                console.log('Requesting camera access...');
                stream = await navigator.mediaDevices.getUserMedia(constraints);
                video.srcObject = stream;
                resultText.textContent = 'Ready';
                resultText.className = 'result-text result-success';
                console.log('Camera started successfully');
                
            } catch (err) {
                console.error('Camera error:', err);
                
                // Try without facingMode constraint as fallback
                try {
                    console.log('Trying without facingMode...');
                    const fallbackStream = await navigator.mediaDevices.getUserMedia({ video: true });
                    video.srcObject = fallbackStream;
                    stream = fallbackStream;
                    resultText.textContent = 'Ready (front cam)';
                    console.log('Camera started with fallback');
                } catch (fallbackErr) {
                    resultText.innerHTML = 'Camera Error: ' + err.message;
                    resultText.className = 'result-text result-error';
                    statsDiv.innerHTML = 'Please allow camera access in Safari settings';
                }
            }
        }
        
        // Capture and send image
        async function captureAndSend() {
            if (isProcessing) {
                console.log('Already processing, ignoring capture');
                return;
            }
            
            if (!video.srcObject) {
                resultText.innerHTML = 'Camera not ready';
                resultText.className = 'result-text result-error';
                return;
            }
            
            isProcessing = true;
            captureBtn.disabled = true;
            resultText.innerHTML = 'Processing <span class="loading"></span>';
            resultText.className = 'result-text';
            
            try {
                // this is to ensure that the video has dimensions
                if (video.videoWidth === 0 || video.videoHeight === 0) {
                    throw new Error('Video not ready');
                }
                
                // this is to capture the current video frame
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                
                // Convert to JPEG
                const imageData = canvas.toDataURL('image/jpeg', 0.8);
                const startTime = Date.now();
                
                console.log('Sending to server...');
                
                // Send to server
                const response = await fetch('/recognize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        image: imageData, 
                        device_id: 'iphone_' + Date.now() 
                    })
                });
                
                const elapsed = Date.now() - startTime;
                const data = await response.json();
                
                console.log('Response received:', data);
                
                if (data.success) {
                    resultText.innerHTML = data.plate;
                    resultText.className = 'result-text result-success';
                    statsDiv.innerHTML = `${elapsed}ms | v${data.model_version}`;
                } else {
                    resultText.innerHTML = data.plate || 'No plate found';
                    resultText.className = 'result-text result-error';
                    statsDiv.innerHTML = 'Try again - position plate in frame';
                }
                
            } catch (err) {
                console.error('Capture error:', err);
                resultText.innerHTML = 'Error: ' + err.message;
                resultText.className = 'result-text result-error';
                statsDiv.innerHTML = 'Check server connection';
            } finally {
                isProcessing = false;
                captureBtn.disabled = false;

                // here we reset after 3 seconds
                setTimeout(() => {
                    if (!isProcessing && resultText.innerHTML !== 'Camera Error') {
                        resultText.innerHTML = 'Ready';
                        resultText.className = 'result-text';
                        statsDiv.innerHTML = '';
                    }
                }, 3000);
            }
        }
        
        // Start camera when page loads
        startCamera();
        
        // Capture button click
        captureBtn.addEventListener('click', captureAndSend);
        
        // Clean up on page unload
        window.addEventListener('beforeunload', () => {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        });
        
        // Log any errors to console
        window.onerror = function(msg, url, lineNo, columnNo, error) {
            console.error('Global error:', msg, error);
            return false;
        };
    </script>
</body>
</html>
'''
# ====================================================================================================


# ====================================================================================================
@app.route('/')
def index():
    return render_template_string(CAMERA_PAGE)
# ====================================================================================================


# ====================================================================================================
@app.route('/recognize', methods=['POST'])
def forward_recognize():
    try:
        response = requests.post(
            f"{RECOGNITION_SERVER}/recognize",
            json=request.get_json(),
            timeout=10
        )
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'plate': 'Server Unreachable'}), 500
# ====================================================================================================


# ====================================================================================================
@app.route('/update', methods=['POST'])
def forward_update():
    try:
        response = requests.post(
            f"{RECOGNITION_SERVER}/update",
            json=request.get_json(),
            timeout=10
        )
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
# ====================================================================================================


# ====================================================================================================
if __name__ == '__main__':
    import ssl
    
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print("="*60)
    print("IPHONE LICENSE PLATE BRIDGE (HTTPS)")
    print("="*60)
    print("HTTPS Bridge server running!")
    print("")
    print("On your iPhone, open Safari and go to:")
    print(f"   https://{local_ip}:5002")
    print("")
    print("="*60)

    # run with HTTPS
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('cert.pem', 'key.pem')

    app.run(host='0.0.0.0', port=5002, debug=False, ssl_context=context)
# ====================================================================================================
