import os

DATASET_PATH = "dataset"

image_extensions = (".jpg", ".jpeg", ".png", ".webp")

print("\n===================================")
print("🦠 DISEASE DATASET SCANNER")
print("===================================")

if not os.path.exists(DATASET_PATH):
    print("❌ dataset folder not found!")
    exit()
f
total_images = 0
folders_found = []

for root, dirs, files in os.walk(DATASET_PATH):

    image_files = [
        file for file in files
        if file.lower().endswith(image_extensions)
    ]

    if image_files:
        relative_path = os.path.relpath(root, DATASET_PATH)

        folders_found.append(relative_path)

        print(f"\n📁 {relative_path}")
        print(f"   Images: {len(image_files)}")

        total_images += len(image_files)

print("\n===================================")
print(f"📂 Image Folders Found: {len(folders_found)}")
print(f"🖼️ Total Images: {total_images}")
print("===================================")

if total_images == 0:
    print("\n❌ No images found.")
    print("Check whether your dataset contains JPG, JPEG, PNG or WEBP files.")
else:
    print("\n✅ Dataset images found successfully!")