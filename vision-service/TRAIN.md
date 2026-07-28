# Vision AI Service — Model Training & Dataset Guide (Developer 1)

This guide provides step-by-step instructions for downloading satellite road extraction datasets, structuring training files, running occlusion-robust segmentation model training, and exporting model weights (`weights/roadnet.pt`) for portable offline deployment.

---

## 1. Dataset Options & File Layout

The Vision AI Service supports two primary training dataset paths:
1. **DeepGlobe Road Extraction Dataset** (Recommended)
2. **Custom GeoTIFF / Satellite PNG Imagery**

### Required File Structure
Whether downloading automatically or manually placing files, images and masks must follow this layout:

```text
vision-service/
  data/
    train/
      1_sat.jpg          # Satellite RGB image
      1_mask.png         # Binary road mask (white = road, black = background)
      2_sat.jpg
      2_mask.png
      3_sat.jpg
      3_mask.png
      ...
```

---

## 2. Option A: Automatic Dataset Download via KaggleHub

The vision service includes an automated script (`app/download.py`) powered by `kagglehub`.

### Step-by-Step Execution
1. Activate your virtual environment:
   ```bash
   cd vision-service
   .venv\Scripts\activate
   ```
2. Pre-warm the dataset cache:
   ```bash
   python -m app.download
   ```
3. `kagglehub` automatically downloads `balraj98/deepglobe-road-extraction-dataset`, resolves nested directories, and caches resolved pairs under `~/.cache/kagglehub/datasets/`.

---

## 3. Option B: Manual Dataset Download & Placement

If training on a Cloud GPU instance or custom rig without Kaggle API credentials:

1. Download the **DeepGlobe Road Extraction Dataset** from Kaggle or your cloud storage.
2. Create the destination directory:
   ```bash
   mkdir -p vision-service/data/train
   ```
3. Extract all `*_sat.jpg` satellite images and `*_mask.png` ground truth road masks directly into:
   `d:\Kratos\kratos\vision-service\data\train\`

---

## 4. Running Model Training

Training uses U-Net with an ImageNet-pretrained backbone (`resnet34` encoder) and occlusion-robust train-time augmentations (random rotations, flips, brightness/contrast jitter, and coarse dropout blocks simulating cloud, tree, or building shadows).

### Method 1: Using One-Click Batch Script (Recommended for Windows)
```cmd
cd vision-service
.\train.bat
```

### Method 2: Command Line Execution
```bash
cd vision-service
.venv\Scripts\activate
python -m app.model
```

### Training Output
- Training log tracks Loss, Dice Loss, BCE Loss, and Validation Loss.
- Best validation weights are automatically saved to:
  `vision-service/weights/roadnet.pt`

---

## 5. Exporting Model Checkpoints for Laptop Deployment

After training on a Cloud GPU or high-end rig:

1. Copy `vision-service/weights/roadnet.pt` to your laptop workspace.
2. Place it in your laptop's `vision-service/weights/roadnet.pt`.
3. Run `.\run_kratos.bat` on your laptop. The Vision Service automatically loads `roadnet.pt` for 100% offline inference with zero retraining needed!
