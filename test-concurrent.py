# ====================================================================================================
# this script is to show that multiple IoT devices are using the service at the same time
# ====================================================================================================


# ====================================================================================================
import requests, random, threading, time
from datetime import datetime
# ====================================================================================================


# ====================================================================================================
RECOGNITION_URL = "http://localhost:5001/recognize"
REQUESTS_PER_DEVICE = 3
NUM_DEVICES     = 5
# ====================================================================================================


# ====================================================================================================
# this is just a small test image for testing connectivity- it is a 1x1 pixel of base64
TEST_IMAGE = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
# ====================================================================================================


# ====================================================================================================
class MockIoTDevice:
    """this is to simulate an IoT device - essentially like a phone"""
    
    def __init__(self, device_id):
        self.failed_requests     = 0
        self.device_id           = device_id
        self.successful_requests = 0
        self.response_times      = []

    def send_request(self, request_num):
        try:
            start_time = time.time()
            response   = requests.post(
                RECOGNITION_URL,
                json={
                    'image': TEST_IMAGE,
                    'device_id': f"{self.device_id}_{request_num}",
                    'timestamp': datetime.now().isoformat()
                },
                timeout=5
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            self.response_times.append(elapsed_ms)
            
            if response.status_code == 200:
                data = response.json()
                self.successful_requests += 1
                return True, elapsed_ms, data.get('plate', 'UNKNOWN')
            else:
                self.failed_requests += 1
                return False, elapsed_ms, f"HTTP {response.status_code}"
                
        except Exception as e:
            self.failed_requests += 1
            return False, 0, str(e)[:30]
    
    def run(self, num_requests):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📱 Device {self.device_id} started")
        
        for i in range(num_requests):
            success, elapsed, result = self.send_request(i)
            
            if success:
                print(f"   Device {self.device_id} req{i}: ✅ {elapsed:.0f}ms - Plate: {result}")  # emoticons make this more visually easier to see
            else:
                print(f"   Device {self.device_id} req{i}: ❌ Failed - {result}")  # emoticons make this more visually easier to see
            
            # have some random delay between requests (0.1-0.5 seconds)
            time.sleep(random.uniform(0.1, 0.5))
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Device {self.device_id} finished")
        print(f"   Success: {self.successful_requests}/{num_requests} | Avg time: {sum(self.response_times)/len(self.response_times) if self.response_times else 0:.0f}ms")
# ====================================================================================================


# ====================================================================================================
def run_concurrent_test():
    """here we are running multiple devices simultaneously"""
    
    print("="*70)
    print("MULTIPLE CONCURRENT USERS TEST")
    print("="*70)
    print(f"Testing the Configuration:")
    print(f"  - the number of IoT devices: {NUM_DEVICES}")
    print(f"  - the requests per device: {REQUESTS_PER_DEVICE}")
    print(f"  - the total requests: {NUM_DEVICES * REQUESTS_PER_DEVICE}")
    print(f"  - the server URL: {RECOGNITION_URL}")
    print("="*70)
    
    # i am going to check first if the server is even alive
    try:
        health_check = requests.get("http://localhost:5001/health", timeout=2)
        if health_check.status_code == 200:
            print("Server is online")
            print(f"   Model version: {health_check.json().get('model_version', 1)}")
        else:
            print("Server returned error")
            return
    except Exception as e:
        print(f"Cannot connect to server. please make sure recognition_server.py is running.")
        print(f"   Error: {e}")
        return
    
    print("\n" + "="*70)
    print("Starting concurrent test...")
    print("="*70 + "\n")

    # this is to create and start threads for each device
    devices = []
    threads = []
    start_time = time.time()
    
    for i in range(NUM_DEVICES):
        device = MockIoTDevice(f"Device_{i+1}")
        devices.append(device)
        
        thread = threading.Thread(target=device.run, args=(REQUESTS_PER_DEVICE,))
        threads.append(thread)
        thread.start()

        # this is just a small pause so that we can prevent all starting exactly at once
        time.sleep(0.05)
    
    for thread in threads:
        thread.join()

    total_time     = time.time() - start_time
    total_success  = sum(d.successful_requests for d in devices)
    total_requests = NUM_DEVICES * REQUESTS_PER_DEVICE
    all_response_times = [t for d in devices for t in d.response_times]
    
    print("\n" + "="*70)
    print("TEST RESULTS")
    print("="*70)
    print(f"the total devices: {NUM_DEVICES}")
    print(f"the total requests: {total_requests}")
    print(f"the successful requests: {total_success}")
    print(f"the failed requests: {total_requests - total_success}")
    print(f"the success rate: {(total_success/total_requests)*100:.1f}%")
    print(f"\nPERFORMANCE:")
    print(f"  - the total test duration: {total_time:.2f} seconds")
    print(f"  - the requests per second: {total_requests / total_time:.2f}")
    print(f"  - the average response time: {sum(all_response_times)/len(all_response_times) if all_response_times else 0:.0f}ms")
    print(f"  - the Min response time: {min(all_response_times) if all_response_times else 0:.0f}ms")
    print(f"  - the Max response time: {max(all_response_times) if all_response_times else 0:.0f}ms")

    # this is the individual device stats
    print(f"\nPER-DEVICE STATISTICS:")
    for device in devices:
        avg_time = sum(device.response_times)/len(device.response_times) if device.response_times else 0
        print(f"   {device.device_id}: {device.successful_requests}/{REQUESTS_PER_DEVICE} success, avg {avg_time:.0f}ms")
    
    print("="*70)
    
    if total_success == total_requests:
        print("all requests successful. concurrent users test passed")
    else:
        print(f"{total_requests - total_success} requests failed. please check server logs")
    
    print("="*70)
# ====================================================================================================


# ====================================================================================================
if __name__ == "__main__":
    # here i am running the main test
    run_concurrent_test()
# ====================================================================================================
