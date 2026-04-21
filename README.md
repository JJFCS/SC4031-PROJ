## LICENSE PLATE RECOGNITION SYSTEM

this is an end-2-end IoT license plate recognition system that includes a cloud inference, multiple concurrent user support, and an online model updating


## 📋 TABLE OF CONTENTS

- [PROJECT OVERVIEW](#PROJECT-OVERVIEW)
- [SYSTEM ARCHITECTURE](#SYSTEM-ARCHITECTURE)
- [PREREQUISITES](#PREREQUISITES)
- [SETUP](#SETUP)
- [RUNNING THE SYSTEM](#RUNNING-THE-SYSTEM)
- [TESTING](#TESTING)
- [MODEL TRAINING](#MODEL-TRAINING)
- [FILE STRUCTURE](#FILE-STRUCTURE)


## 🎯 PROJECT OVERVIEW

**THIS PROJECT IMPLEMENTS A COMPLETE LICENSE PLATE RECOGNITION SYSTEM THAT..**

- WE USE AN IPHONE AS AN IOT DEVICE TO CAPTURE LICENSE PLATES IN REAL-TIME
- WE RUN CLOUD INFERENCE LOCALLY ON A MAC (ACTS AS THE CLOUD VM)
- WE SUPPORT MULTIPLE CONCURRENT USERS ACCESSING THE SERVICE SIMULTANEOUSLY
- WE IMPLEMENT ONLINE MODEL UPDATING AT RUNTIME USING USER CORRECTIONS
- WE TRAIN A CUSTOM CNN MODEL ON THE CCPD DATASET


## 🏗️ SYSTEM ARCHITECTURE

| COMPONENT | PORT | PURPOSE |
|-----------|------|---------|
| RECOGNITION SERVER | 5001 | OCR PROCESSING & ONLINE UPDATES |
| IPHONE BRIDGE | 5002 | SERVES HTTPS WEBPAGE TO IPHONE |


## 💻 PREREQUISITES

### HARDWARE REQUIREMENTS
- MAC
- IPHONE
- SAME WIFI NETWORK FOR BOTH DEVICES

### SOFTWARE REQUIREMENTS
- PYTHON 3.12.5
- PIP PACKAGE MANAGER
- OPENSSL (COMES WITH MACOS)
- IPHONE WITH SAFARI BROWSER

note this would work on windows too but i develop on a mac-os so this is more catered to that


## 🛠️ Setup

### STEP 1: CREATE PROJECT DIRECTORY

```bash
mkdir ~/documents/name-of-project
cd ~/documents/name-of-project
```

### STEP 2: CREATE A VIRTUAL ENVIRONMENT

```bash
# make sure to do it in the project root directory
# then activate the virtual environment
python3 -m venv venv
source venv/bin/activate
```

### STEP 3: INSTALL DEPENDENCIES

```bash
pip install flask flask-cors opencv-python numpy easyocr pillow requests torch torchvision
```

```bash
# alternatively we have generated a requirements.txt file so you can easily install
# the dependencies required.
# to then install the dependencies run the following commands:
pip freeze   > requirements.txt
pip install -r requirements.txt
```

**MAC SSL CERTIFICATE FIX**

```bash
# if easyOCR fails to download its detection model with SSL errors please run
# adjust the python version if different
/Applications/Python\ 3.12/Install\ Certificates.command
```

### STEP 4: GENERATE SSL CERTIFICATE (FOR HTTPS)

```bash
# since safari on iphone blocks camera access over http we make use of https instead
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

**important - the common name MUST be your laptop's IP address on your local network**

**upon completion this will create two files**
- cert.pem - SSL certificate
- key.pem  - private key

### STEP 5: DOWNLOAD DATASET FOR TRAINING

- download the CCPD2019 dataset from Kaggle - https://www.kaggle.com/datasets/binh234/ccpd2019

### STEP 6: UPDATE FILE PATHS

```python
# in train.py update the dataset path:
CCPD_PATH = "/path/to/your/CCPD/ccpd_base"
```


## 🚀 RUNNING THE SYSTEM

```bash
# terminal 1 - recognition server - on port 5001
cd ~/documents/name-of-project
source venv/bin/activate
python recognition-server.py
```

expected output:
```text
==================================================
LICENSE PLATE RECOGNITION SERVER
==================================================
Loading OCR engine...
OCR engine ready
==================================================
Server starting...
 * Running on http://0.0.0.0:5001
```

```bash
# terminal 2 - iphone bridge server - on port 5002
cd ~/documents/name-of-project
source venv/bin/activate
python iphone-bridge-https.py
```

expected output:
```text
==================================================
IPHONE LICENSE PLATE BRIDGE (HTTPS)
==================================================
https://192.168.1.100:5002
==================================================
 * Running on https://0.0.0.0:5002
```

### next we connect our iphone

1. open safari on your iphone
2. go to the ip shown in terminal 2
3. tap "show details" then "visit website" then refresh page if needed
4. tap "allow" when prompted for camera access
5. point your camera at a license plate and tap "CAPTURE"


## 🧪 TESTING

```bash
# test 1 - multiple concurrent users
python test-concurrent.py
```

expected output:
```text
==================================================
MULTIPLE CONCURRENT USERS TEST
==================================================
server is online
==================================================
starting concurrent test...
==================================================
Device Device_1 started
Device Device_1 req0: ✅ 36ms - Plate: NOT_FOUND
...
==================================================
ALL REQUESTS SUCCESSFUL. concurrent users test PASSED
==================================================
```

```bash
# test 2 - online model updating
python demo-online-update.py
```

expected output:
```text
==================================================
ONLINE MODEL UPDATING DEMONSTRATION
==================================================
server is online
    model version: 1

Step 1: Model misrecognizes a license plate
    model predicted: 'NOT_FOUND'
    correct plate is: 'XYZ789'

Step 2: User sends correction to cloud
    correction received
    model version: 2

Step 3: Cloud updates model at runtime
    model version increased from 1 to 2
    ONLINE MODEL UPDATE SUCCESSFUL
```


## 🤖 MODEL TRAINING

the training script:
- loads 5000 positive examples from ccpd_base
- loads 3021 negative examples from ccpd_np
- generates about 1979 synthetic negatives (noise + solid colors) for balance
- trains a custom CNN with about 655,489 parameters
- splits the data where we have 70% for training, 15% for validation, and 15% for testing
- achieves about a 98% test accuracy

```bash
# in the project root directory run the following to run the training
python train.py
```

**expected output**
```text
==================================================
LICENSE PLATE DETECTION MODEL TRAINING
==================================================

STEP 1 - LOADING DATASET
----------------------------------------
found 199996 valid positive examples
found 3021   valid negative examples
total 5000 positive examples
total 3021 negative + 1979 synthetic negatives

STEP 5 - TRAINING MODEL
----------------------------------------
epoch  1/20 - loss: 0.2130 - acc: 0.910 - val acc: 0.967
epoch 10/20 - loss: 0.0604 - acc: 0.986 - val acc: 0.985
epoch 20/20 - loss: 0.0179 - acc: 0.993 - val acc: 0.991

STEP 7 - TESTING ON UNSEEN DATA
----------------------------------------
test accuracy: 0.980 (98.0%)
model generalizes well

==================================================
TRAINING COMPLETED SUCCESSFULLY
==================================================
```

**performance notes**
the high accuracy (98%) is expected given the dataset composition:
- positive examples: real license plate images
- negative examples: mix of real no license plate cars and synthetic images


## 📁 File Structure

```text
name-of-project/
│
├── recognition-server.py      # Main OCR server (Port 5001)
├── iphone-bridge.py           # HTTPS bridge for iPhone (Port 5002)
├── train.py                   # Model training script
├── test-concurrent.py         # Multiple users test
├── demo-online_update.py      # Online model update demo
│
├── license_plate_model.pt     # Trained model (98% test accuracy)
├── training_config.json       # Training configuration
├── training_history.json      # Training metrics
│
├── cert.pem                   # SSL certificate
├── key.pem                    # SSL private key
│
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```















