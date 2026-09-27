import os

# Your dataset folder name
DATASET_PATH = "dataset"

# Image file types
image_extensions = (".jpg", ".jpeg", ".png", ".webp")

# Check if dataset folder exists
if not os.path.exists(DATASET_PATH):
    print("❌ dataset folder not found!")
    print("Example:")
    print("Project Folder")
    print("│")
    print("├── app.py")
    print("├── database.db")
    print("├── check_dataset.py")
    print("└── dataset/")
    exit()

# Get disease folders
folders = []

for folder in os.listdir(DATASET_PATH):
    folder_path = os.path.join(DATASET_PATH, folder)

    if os.path.isdir(folder_path):
        folders.append(folder)

print("\n===================================")
print("🦠 DISEASE DATASET INFORMATION")
print("===================================")

print(f"\nTotal Disease Classes: {len(folders)}")

total_images = 0

for folder in sorted(folders):

    folder_path = os.path.join(DATASET_PATH, folder)

    images = []

    for file in os.listdir(folder_path):

        if file.lower().endswith(image_extensions):
            images.append(file)

    print(f"{folder} → {len(images)} images")

    total_images += len(images)

print("\n===================================")
print(f"Total Images: {total_images}")
print("===================================")