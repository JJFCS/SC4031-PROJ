# ====================================================================================================
# this script loads the CCPD dataset images and trains a neural network
# then we are also making use of negative examples from CCPD_NP which represents cars without license plates
# then we also included some error handling for corrupted images
# ====================================================================================================


# ====================================================================================================
import os, json, glob, random
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import numpy as np
from datetime import datetime
# ====================================================================================================


# ====================================================================================================
print("="*60)
print("LICENSE PLATE DETECTION MODEL TRAINING")
print("="*60)
CCPD_PATH = "/Users/onncera/Documents/onncera NTU/Y-xx/sem - z/INTERNET OF THINGS/SC4031-PROJ/CCPD"
# ====================================================================================================


# ====================================================================================================
def generate_synthetic_negatives(num_samples=500):
    """ this is a backup or fallback in case we do not have enough real negative examples then we generate synthetic ones"""
    negatives = []
    temp_dir = "/tmp/negative_samples"  # just creating a placeholder to store the negative samples
    os.makedirs(temp_dir, exist_ok=True)

    # this is for the random noise images (50%)
    for i in range(num_samples // 2):
        random_noise = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        temp_path = os.path.join(temp_dir, f"noise_{i}.jpg")
        Image.fromarray(random_noise).save(temp_path)
        negatives.append(temp_path)

    # this is for the solid color images (50%)
    colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255), (0,255,255), (128,128,128)]
    for i in range(num_samples - (num_samples // 2)):
        color = random.choice(colors)
        solid_color = np.full((64, 64, 3), color, dtype=np.uint8)
        temp_path = os.path.join(temp_dir, f"solid_{i}.jpg")
        Image.fromarray(solid_color).save(temp_path)
        negatives.append(temp_path)
    
    return negatives
# ====================================================================================================


# ====================================================================================================
def is_valid_image(file_path):
    """to check if an image file is valid and readable"""
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False
# ====================================================================================================


# ====================================================================================================
class LicensePlateDataset(Dataset):
    """our dataset which includes positive and negative examples"""
    def __init__(self, image_paths, labels, transform=None):
        valid_paths  = []
        valid_labels = []
        
        print(f"validating {len(image_paths)} images")
        for i, (path, label) in enumerate(zip(image_paths, labels)):
            if is_valid_image(path):
                valid_paths.append(path)
                valid_labels.append(label)
            else:
                print(f"skipping invalid image: {os.path.basename(path)}")
        
        self.image_paths = valid_paths
        self.labels = valid_labels
        self.transform = transform
        
        print(f"{len(self.image_paths)} valid images loaded")
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        image = Image.open(img_path).convert('RGB')
        label = torch.tensor([self.labels[idx]], dtype=torch.float32)
        
        if self.transform:
            image = self.transform(image)
        return image, label
# ====================================================================================================


# ====================================================================================================
print("\nSTEP 1 - LOADING DATASET")
print("-" * 40)

positive_folder = os.path.join(CCPD_PATH, "ccpd_base")
negative_folder = os.path.join(CCPD_PATH, "ccpd_np")

if not os.path.exists(positive_folder):
    print(f"positive folder not found: {positive_folder}")
    print(f"please update CCPD_PATH to your CCPD folder")
    exit(1)

# here is where we load our positive examples that we get from ccpd_base directory
all_positive_raw = glob.glob(os.path.join(positive_folder, "*.jpg"))
print(f"found {len(all_positive_raw)} potential positive examples")

# now we check out of all of the positive examples we have , which ones are considered valid
all_positive = [p for p in all_positive_raw if is_valid_image(p)]
print(f"found {len(all_positive)} valid positive examples - ccpd_base")

# here is where we load our negative examples that we get from ccpd_np directory
if os.path.exists(negative_folder):
    all_negative_raw = glob.glob(os.path.join(negative_folder, "*.jpg"))
    print(f"found {len(all_negative_raw)} potential negative examples")

    all_negative_real = [n for n in all_negative_raw if is_valid_image(n)]
    print(f"found {len(all_negative_real)} valid negative examples - ccpd_np")
else:
    print(f"ccpd_np folder not found at: {negative_folder}")
    print(f"falling back to synthetic negatives only")
    all_negative_real = []
# ====================================================================================================


# ====================================================================================================
# Configuration for balanced dataset
NUM_POSITIVES = min(5000, len(all_positive))  # for now we set this to 5000 examples
NUM_NEGATIVES = NUM_POSITIVES  # match number of negatives to positives

# Take first N positives
positive_subset = all_positive[:NUM_POSITIVES]
print(f"\nthere are {len(positive_subset)} positive examples for training")

# get negatives (up to NUM_NEGATIVES)
real_negatives_to_use = all_negative_real[:min(len(all_negative_real), NUM_NEGATIVES)]
remaining_needed = NUM_NEGATIVES - len(real_negatives_to_use)

print(f"there are {len(real_negatives_to_use)} negative examples from ccpd_np")

# Generate synthetic negatives if needed
if remaining_needed > 0:
    print(f"then we generate {remaining_needed} synthetic negatives to reach {NUM_NEGATIVES} total")
    synthetic_negatives = generate_synthetic_negatives(remaining_needed)
    negative_subset = real_negatives_to_use + synthetic_negatives
else:
    negative_subset = real_negatives_to_use
    # this is for when we have more real negatives than needed , then we use a random subset
    if len(all_negative_real) > NUM_NEGATIVES:
        negative_subset = random.sample(all_negative_real, NUM_NEGATIVES)

print(f"total negatives: {len(negative_subset)} ({len(real_negatives_to_use)} real + {remaining_needed} synthetic)")
# ====================================================================================================


# ====================================================================================================
# just combining positives and negatives
all_images = positive_subset + negative_subset
all_labels = [1.0] * len(positive_subset) + [0.0] * len(negative_subset)

# shuffle together so batches have mixed classes
combined = list(zip(all_images, all_labels))
random.shuffle(combined)
all_images, all_labels = zip(*combined)
all_images = list(all_images)
all_labels = list(all_labels)

print(f"\ntotal images: {len(all_images)}")
print(f"- positive (plate - yes): {len(positive_subset)} ({len(positive_subset)/len(all_images)*100:.1f}%)")
print(f"- negative (plate - no):  {len(negative_subset)} ({len(negative_subset)/len(all_images)*100:.1f}%)")
# ====================================================================================================


# ====================================================================================================
# here we split into 70% for training, 15% for validation, and 15% for testing
total     = len(all_images)
train_end = int(total * 0.70)
val_end   = int(total * 0.85)

train_images = all_images[:train_end]
train_labels = all_labels[:train_end]

val_images = all_images[train_end:val_end]
val_labels = all_labels[train_end:val_end]

test_images = all_images[val_end:]
test_labels = all_labels[val_end:]

print(f"\nsplit:")
print(f"- training:   {len(train_images)} (70%)")
print(f"- validation: {len(val_images)} (15%)")
print(f"- test:       {len(test_images)} (15%)")
# ====================================================================================================


# ====================================================================================================
# image transformations
transform = transforms.Compose([
    transforms.Resize((64, 64)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

val_dataset   = LicensePlateDataset(val_images, val_labels, transform=transform)
train_dataset = LicensePlateDataset(train_images, train_labels, transform=transform)
test_dataset  = LicensePlateDataset(test_images, test_labels, transform=transform)

# this is to ensure that we only create loaders if the datasets have images
if len(train_dataset) == 0:
    print("ERROR: no valid training images found")
    exit(1)

val_loader   = DataLoader(val_dataset,   batch_size=16, shuffle=False) if len(val_dataset)  > 0 else None
train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
test_loader  = DataLoader(test_dataset,  batch_size=16, shuffle=False) if len(test_dataset) > 0 else None

print("\nCCPD dataset loaded successfully!")
# ====================================================================================================


# ====================================================================================================
print("\nSTEP 2 - PREPROCESSING DATA")
print("-" * 40)
print("the resizing of images to 64x64")
print("the normalizing of pixel values")
print("the data is ready for training")
# ====================================================================================================


# ====================================================================================================
print("\nSTEP 3 - BUILDING MODEL ARCHITECTURE")
print("-" * 40)

class LicensePlateDetector(nn.Module):
    """CNN for license plate detection"""
    def __init__(self):
        super(LicensePlateDetector, self).__init__()
        
        self.conv1 = nn.Conv2d(3,  16,  kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(16, 32,  kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(32, 64,  kernel_size=3, padding=1)
        self.conv4 = nn.Conv2d(64, 128, kernel_size=3, padding=1)

        self.bn1 = nn.BatchNorm2d(16)
        self.bn2 = nn.BatchNorm2d(32)
        self.bn3 = nn.BatchNorm2d(64)
        self.bn4 = nn.BatchNorm2d(128)
        
        self.pool = nn.MaxPool2d(2, 2)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.3)
        
        self.fc1 = nn.Linear(128 * 4 * 4, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, 1)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        x = self.pool(self.relu(self.bn1(self.conv1(x))))
        x = self.pool(self.relu(self.bn2(self.conv2(x))))
        x = self.pool(self.relu(self.bn3(self.conv3(x))))
        x = self.pool(self.relu(self.bn4(self.conv4(x))))
        x = x.view(x.size(0), -1)
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.sigmoid(self.fc3(x))
        return x

model = LicensePlateDetector()
total_params = sum(p.numel() for p in model.parameters())

print(f"the model: custom CNN for license plate detection")
print(f"the total parameters: {total_params:,}")
print(f"the model size: ~{total_params * 4 / 1024:.1f} KB")
# ====================================================================================================


# ====================================================================================================
print("\nSTEP 4 - TRAINING CONFIGURATION")
print("-" * 40)

EPOCHS = 20
LEARNING_RATE = 0.001
criterion = nn.BCELoss()
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

print(f"epochs: {EPOCHS}")
print(f"learning rate: {LEARNING_RATE}")
print(f"loss function: binary cross entropy")
print(f"optimizer: adam")
# ====================================================================================================


# ====================================================================================================
print("\nSTEP 5 - TRAINING MODEL")
print("-" * 40)
print("   training progress:")

training_history = []

for epoch in range(EPOCHS):
    model.train()
    correct = 0
    the_running_loss = 0.0
    total = 0
    
    for images, labels in train_loader:
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        the_predicted = (outputs > 0.5).float()
        correct += (the_predicted == labels).sum().item()
        the_running_loss += loss.item()
        total += labels.size(0)
    
    avg_loss = the_running_loss / len(train_loader)
    train_accuracy = correct / total
    
    # Validation
    model.eval()
    val_correct = 0
    val_total = 0
    if val_loader is not None:
        with torch.no_grad():
            for images, labels in val_loader:
                outputs = model(images)
                the_predicted = (outputs > 0.5).float()
                val_correct += (the_predicted == labels).sum().item()
                val_total += labels.size(0)
        val_accuracy = val_correct / val_total if val_total > 0 else 0
    else:
        val_accuracy = 0
    
    training_history.append({
        'epoch': epoch + 1,
        'train_loss': avg_loss,
        'train_accuracy': train_accuracy,
        'val_accuracy': val_accuracy
    })
    
    if (epoch + 1) % 5 == 0 or epoch == 0 or epoch == EPOCHS - 1:
        print(f"   epoch {epoch+1:2d}/{EPOCHS} - loss: {avg_loss:.4f} - acc: {train_accuracy:.3f} - val acc: {val_accuracy:.3f}")
# ====================================================================================================


# ====================================================================================================
print("\nSTEP 6 - VALIDATION RESULTS")
print("-" * 40)

final_val_accuracy = training_history[-1]['val_accuracy']
print(f"validation accuracy: {final_val_accuracy:.3f} ({final_val_accuracy*100:.1f}%)")
# ====================================================================================================


# ====================================================================================================
print("\nSTEP 7 - TESTING ON UNSEEN DATA")
print("-" * 40)

if test_loader is not None:
    model.eval()
    test_total   = 0
    test_correct = 0
    test_loss    = 0.0

    with torch.no_grad():
        for images, labels in test_loader:
            outputs = model(images)
            loss = criterion(outputs, labels)
            test_loss += loss.item()
            
            the_predicted = (outputs > 0.5).float()
            test_correct += (the_predicted == labels).sum().item()
            test_total   += labels.size(0)
    
    test_accuracy = test_correct / test_total if test_total > 0 else 0
    avg_test_loss = test_loss / len(test_loader) if len(test_loader) > 0 else 0
    
    print(f"test images: {len(test_dataset)} (completely unseen during training)")
    print(f"test accuracy: {test_accuracy:.3f} ({test_accuracy*100:.1f}%)")
    print(f"test loss: {avg_test_loss:.4f}")

    print(f"\naccuracy comparison:")
    print(f"validation accuracy: {final_val_accuracy:.3f}")
    print(f"test accuracy:       {test_accuracy:.3f}")
    print(f"difference:          {abs(final_val_accuracy - test_accuracy):.3f}")
    
    if abs(final_val_accuracy - test_accuracy) < 0.1:
        print("model generalizes well")
else:
    print("no test images available")
    test_accuracy = 0
# ====================================================================================================


# ====================================================================================================
print("\nSTEP 8 - SAVING MODEL")
print("-" * 40)

torch.save(model.state_dict(), 'license_plate_model.pt')
print("model saved: license_plate_model.pt")

# Save training config
config = {
    "dataset": "CCPD (ccpd_base + ccpd_np)",
    "dataset_source": "https://www.kaggle.com/datasets/binh234/ccpd2019",
    "positive_source": "ccpd_base (license plates)",
    "negative_source": "ccpd_np (cars without plates) + synthetic fallback",
    "positive_examples_used": len(positive_subset),
    "real_negatives_used": len(real_negatives_to_use),
    "synthetic_negatives_used": remaining_needed if remaining_needed > 0 else 0,
    "split_ratio": {"train": 0.70, "validation": 0.15, "test": 0.15},
    "train_images": len(train_dataset),
    "validation_images": len(val_dataset) if val_dataset else 0,
    "test_images": len(test_dataset) if test_dataset else 0,
    "epochs": EPOCHS,
    "learning_rate": LEARNING_RATE,
    "optimizer": "Adam",
    "loss_function": "Binary Cross Entropy",
    "validation_accuracy": final_val_accuracy,
    "test_accuracy": test_accuracy,
    "total_parameters": total_params,
    "training_date": datetime.now().isoformat()
}

with open('training_config.json', 'w') as f:
    json.dump(config, f, indent=2)
print("training config saved: training_config.json")

# Save training history
with open('training_history.json', 'w') as f:
    json.dump(training_history, f, indent=2)
print("training history saved: training_history.json")
# ====================================================================================================


# ====================================================================================================
print("\n" + "="*60)
print("TRAINING COMPLETED SUCCESSFULLY")
print("="*60)
print(f"results:")
print(f"- validation accuracy: {final_val_accuracy:.3f}")
print(f"- test accuracy:       {test_accuracy:.3f}")
print("="*60)
