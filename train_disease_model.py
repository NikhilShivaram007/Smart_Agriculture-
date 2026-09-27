import os
import json
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms, models

# ==========================================================
# SETTINGS
# ==========================================================

DATASET_PATH = os.path.join(
    "dataset",
    "disease_dataset",
    "color"
)

MODEL_FOLDER = "disease_model"

MODEL_PATH = os.path.join(
    MODEL_FOLDER,
    "plant_disease_model.pth"
)

CLASSES_PATH = os.path.join(
    MODEL_FOLDER,
    "classes.json"
)

IMAGE_SIZE = 160
BATCH_SIZE = 4
EPOCHS = 1

# ==========================================================
# CHECK DATASET
# ==========================================================

if not os.path.exists(DATASET_PATH):
    print("ERROR: Dataset folder not found!")
    print("Expected location:")
    print(DATASET_PATH)
    exit()

print("Dataset found:")
print(DATASET_PATH)

# ==========================================================
# IMAGE TRANSFORM
# ==========================================================

transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# ==========================================================
# LOAD DATASET
# ==========================================================

print("\nLoading disease dataset...")

dataset = datasets.ImageFolder(
    DATASET_PATH,
    transform=transform
)

print("Total images:", len(dataset))
print("Total disease classes:", len(dataset.classes))

# ==========================================================
# SAVE CLASSES
# ==========================================================

os.makedirs(MODEL_FOLDER, exist_ok=True)

with open(CLASSES_PATH, "w", encoding="utf-8") as file:
    json.dump(dataset.classes, file, indent=4)

print("\nClasses saved to:")
print(CLASSES_PATH)

# ==========================================================
# TRAIN / VALIDATION SPLIT
# ==========================================================

total_size = len(dataset)

train_size = int(0.8 * total_size)

validation_size = total_size - train_size

train_dataset, validation_dataset = random_split(
    dataset,
    [train_size, validation_size]
)

print("\nTraining images:", len(train_dataset))
print("Validation images:", len(validation_dataset))

# ==========================================================
# DATA LOADERS
# ==========================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0
)

validation_loader = DataLoader(
    validation_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)

# ==========================================================
# DEVICE
# ==========================================================

device = torch.device("cpu")

print("\nUsing device:", device)

# ==========================================================
# LIGHTWEIGHT RESNET18
# ==========================================================

print("\nLoading lightweight ResNet18...")

try:
    weights = models.ResNet18_Weights.DEFAULT
    model = models.resnet18(weights=weights)
except Exception:
    print("Pretrained weights could not be loaded.")
    print("Using ResNet18 without pretrained weights.")
    model = models.resnet18(weights=None)

# ==========================================================
# FREEZE RESNET LAYERS
# ==========================================================

print("\nFreezing ResNet layers...")

for parameter in model.parameters():
    parameter.requires_grad = False

# ==========================================================
# CHANGE FINAL CLASSIFICATION LAYER
# ==========================================================

number_of_classes = len(dataset.classes)

model.fc = nn.Linear(
    model.fc.in_features,
    number_of_classes
)

model = model.to(device)

# ==========================================================
# LOSS FUNCTION
# ==========================================================

criterion = nn.CrossEntropyLoss()

# ==========================================================
# OPTIMIZER
# ==========================================================

optimizer = torch.optim.Adam(
    model.fc.parameters(),
    lr=0.001
)

# ==========================================================
# TRAINING
# ==========================================================

print("\n========================================")
print("STARTING LIGHTWEIGHT DISEASE TRAINING")
print("========================================")

for epoch in range(EPOCHS):

    model.train()

    # Keep frozen layers in evaluation mode
    model.layer1.eval()
    model.layer2.eval()
    model.layer3.eval()
    model.layer4.eval()

    running_loss = 0.0
    correct = 0
    total = 0

    for batch_number, (images, labels) in enumerate(train_loader):

        images = images.to(device)
        labels = labels.to(device)

        # Clear gradients
        optimizer.zero_grad()

        # Prediction
        outputs = model(images)

        # Calculate loss
        loss = criterion(outputs, labels)

        # Backpropagation
        loss.backward()

        # Update only final layer
        optimizer.step()

        running_loss += loss.item()

        _, predicted = torch.max(
            outputs,
            1
        )

        total += labels.size(0)

        correct += (
            predicted == labels
        ).sum().item()

        # Show progress
        if (batch_number + 1) % 100 == 0:
            print(
                f"Processed {batch_number + 1} batches..."
            )

    train_accuracy = (
        100 * correct / total
        if total > 0
        else 0
    )

    # ======================================================
    # VALIDATION
    # ======================================================

    model.eval()

    validation_correct = 0
    validation_total = 0

    with torch.no_grad():

        for images, labels in validation_loader:

            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            _, predicted = torch.max(
                outputs,
                1
            )

            validation_total += labels.size(0)

            validation_correct += (
                predicted == labels
            ).sum().item()

    validation_accuracy = (
        100 * validation_correct / validation_total
        if validation_total > 0
        else 0
    )

    average_loss = (
        running_loss / len(train_loader)
        if len(train_loader) > 0
        else 0
    )

    print("\n========================================")
    print(f"Epoch [{epoch + 1}/{EPOCHS}]")
    print(f"Loss: {average_loss:.4f}")
    print(f"Training Accuracy: {train_accuracy:.2f}%")
    print(f"Validation Accuracy: {validation_accuracy:.2f}%")
    print("========================================")

# ==========================================================
# SAVE MODEL
# ==========================================================

torch.save(
    model.state_dict(),
    MODEL_PATH
)

print("\n========================================")
print("TRAINING COMPLETED SUCCESSFULLY!")
print("========================================")

print("\nModel saved at:")
print(MODEL_PATH)

print("\nClasses saved at:")
print(CLASSES_PATH)

print("\nYou can now connect this model")
print("to the Flask disease detection page.")