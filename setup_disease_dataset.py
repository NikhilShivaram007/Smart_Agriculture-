from pathlib import Path


# =========================================================
# SMART AGRICULTURE
# MULTI-PLANT DISEASE DATASET SETUP
# =========================================================

print("=" * 65)
print("SMART AGRICULTURE - DISEASE DATASET SETUP")
print("=" * 65)


# =========================================================
# PROJECT FOLDER
# =========================================================

project_folder = Path(__file__).resolve().parent


# =========================================================
# MAIN DATASET FOLDER
# =========================================================

dataset_folder = project_folder / "disease_dataset"

dataset_folder.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================================
# PLANT DISEASE CLASSES
# =========================================================
#
# These names are prepared for a broad plant-disease model.
#
# The model can later be trained using images belonging
# to these folders.
#
# =========================================================

disease_classes = [

    # -----------------------------
    # APPLE
    # -----------------------------

    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___healthy",


    # -----------------------------
    # BLUEBERRY
    # -----------------------------

    "Blueberry___healthy",


    # -----------------------------
    # CHERRY
    # -----------------------------

    "Cherry___Powdery_mildew",
    "Cherry___healthy",


    # -----------------------------
    # CORN
    # -----------------------------

    "Corn___Cercospora_leaf_spot",
    "Corn___Common_rust",
    "Corn___Northern_Leaf_Blight",
    "Corn___healthy",


    # -----------------------------
    # GRAPE
    # -----------------------------

    "Grape___Black_rot",
    "Grape___Esca",
    "Grape___Leaf_blight",
    "Grape___healthy",


    # -----------------------------
    # PEACH
    # -----------------------------

    "Peach___Bacterial_spot",
    "Peach___healthy",


    # -----------------------------
    # PEPPER
    # -----------------------------

    "Pepper___Bacterial_spot",
    "Pepper___healthy",


    # -----------------------------
    # POTATO
    # -----------------------------

    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",


    # -----------------------------
    # RASPBERRY
    # -----------------------------

    "Raspberry___healthy",


    # -----------------------------
    # SOYBEAN
    # -----------------------------

    "Soybean___healthy",


    # -----------------------------
    # SQUASH
    # -----------------------------

    "Squash___Powdery_mildew",


    # -----------------------------
    # STRAWBERRY
    # -----------------------------

    "Strawberry___Leaf_scorch",
    "Strawberry___healthy",


    # -----------------------------
    # TOMATO
    # -----------------------------

    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites",
    "Tomato___Target_Spot",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___healthy"
]


# =========================================================
# CREATE FOLDERS
# =========================================================

created_count = 0

for class_name in disease_classes:

    class_folder = dataset_folder / class_name

    class_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    created_count += 1

    print(f"Created: {class_name}")


# =========================================================
# SUMMARY
# =========================================================

print()
print("=" * 65)

print(
    f"Successfully created {created_count} disease class folders."
)

print("=" * 65)

print()
print("Dataset location:")

print(dataset_folder)

print()
print("Example structure:")
print()

print("disease_dataset/")
print("│")

print("├── Apple___Apple_scab/")
print("├── Apple___Black_rot/")
print("├── Apple___healthy/")

print("├── Corn___Common_rust/")
print("├── Corn___healthy/")

print("├── Potato___Early_blight/")
print("├── Potato___Late_blight/")
print("├── Potato___healthy/")

print("├── Tomato___Early_blight/")
print("├── Tomato___Late_blight/")
print("└── Tomato___healthy/")

print()
print("Dataset folder preparation completed!")
print()
print(
    "IMPORTANT: These folders are only the structure."
)
print(
    "Training images must be placed in the correct class folders."
)
