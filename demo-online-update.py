# ====================================================================================================
# this demonstrates online model updating with user corrections
# ====================================================================================================


# ====================================================================================================
import requests, time, json
from datetime import datetime
# ====================================================================================================


# ====================================================================================================
UPDATE_URL = "http://localhost:5001/update"
RECOGNITION_URL = "http://localhost:5001/recognize"
STATS_URL = "http://localhost:5001/health"
# ====================================================================================================


# ====================================================================================================
# this is for our demonstration where we are making use of a placeholder test image
TEST_IMAGE = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
# ====================================================================================================


# ====================================================================================================
def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_step(step_num, description):
    print(f"\nStep {step_num}: {description}")
    print("-" * 50)
# ====================================================================================================


# ====================================================================================================
def check_server():
    """to check if the server is running"""
    try:
        response = requests.get("http://localhost:5001/health", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"server is online")
            print(f"the model version: {data.get('model_version', 1)}")
            print(f"the status: {data.get('status', 'unknown')}")
            return True
    except:
        print("server is not running. please start recognition_server.py first")
        return False
    return False
# ====================================================================================================


# ====================================================================================================
def get_current_model_version():
    """to get the current model version from server"""
    try:
        response = requests.get("http://localhost:5001/health", timeout=2)
        if response.status_code == 200:
            return response.json().get('model_version', 1)
    except:
        pass
    return 1
# ====================================================================================================


# ====================================================================================================
def simulate_misrecognition():
    """this is to simulate the model misrecognizing a plate"""
    print("\nSending image to cloud...")
    
    response = requests.post(
        RECOGNITION_URL,
        json={
            'image': TEST_IMAGE,
            'device_id': 'demo_iphone',
            'scenario': 'misrecognition_demo'
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        predicted = result.get('plate', 'ABC123')
        print(f"the model predicted: '{predicted}'")
        print(f"the correct plate is: 'XYZ789'")
        return predicted
    else:
        print(f"   Error: {response.status_code}")
        return "ERROR"
# ====================================================================================================


# ====================================================================================================
def send_correction(wrong_plate):
    """Send user correction to update the model"""
    print(f"\nthe user submits correction...")
    print(f"the incorrect prediction: {wrong_plate}")
    print(f"the correct label: XYZ789")

    correction_data = {
        'image': TEST_IMAGE,
        'correct_label': 'XYZ789',
        'previous_prediction': wrong_plate,
        'device_id': 'demo_iphone',
        'feedback_type': 'correction',
        'timestamp': datetime.now().isoformat()
    }
    
    response = requests.post(UPDATE_URL, json=correction_data)
    
    if response.status_code == 200:
        data = response.json()
        print(f"the correction has been received")
        print(f"the message: {data.get('message', 'Update processed')}")
        print(f"the model version: {data.get('model_version', 'N/A')}")
        return True
    else:
        print(f"   Update failed: {response.text}")
        return False
# ====================================================================================================


# ====================================================================================================
def verify_model_update(initial_version):
    """to verify that the model was updated"""
    time.sleep(1)
    
    new_version = get_current_model_version()
    
    if new_version > initial_version:
        print(f"Model version increased from {initial_version} to {new_version}")
        return True
    else:
        print(f"Model version unchanged (still {new_version})")
        return False
# ====================================================================================================


# ====================================================================================================
def run_complete_demo():
    """this is to run the complete online update demonstration"""

    print(f"TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if not check_server():
        return False
    
    initial_version = get_current_model_version()
    print(f"\ninitial model version: {initial_version}")

    # Step 1: Show misrecognition
    print_step(1, "Model misrecognizes a license plate")
    wrong_plate = simulate_misrecognition()
    if wrong_plate == "ERROR":
        return False
    time.sleep(1)
    
    # Step 2: Send correction
    print_step(2, "User sends correction to cloud")
    if not send_correction(wrong_plate):
        return False
    time.sleep(1)
    
    # Step 3: Verify update
    print_step(3, "Cloud updates model at runtime")
    if verify_model_update(initial_version):
        print("\nONLINE MODEL UPDATE SUCCESSFUL")
        print("the model has been updated without restarting the server")
    
    return True
# ====================================================================================================


# ====================================================================================================
if __name__ == "__main__":
    print("\n" + "="*70)
    print("  ONLINE MODEL UPDATING DEMONSTRATION")
    print("="*70)
    print()

    # to run main demo
    success = run_complete_demo()
# ====================================================================================================
