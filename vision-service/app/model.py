"""
Segmentation model: U-Net (resnet34 encoder, ImageNet pretrained) via
segmentation_models_pytorch. Includes a standalone training loop you run
once offline (python -m app.model) to produce weights/roadnet.pt; the
FastAPI service only ever loads weights, it never trains at request time.
"""

import os

import segmentation_models_pytorch as smp
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from app.config import settings
from app.dataset import RoadDataset, train_val_split
from app.preprocess import train_transform, val_transform


def build_model():
    return smp.Unet(
        encoder_name=settings.ENCODER_NAME,
        encoder_weights="imagenet",
        in_channels=3,
        classes=1,
        activation=None,
    )


def load_model(device="cpu"):
    model = build_model()
    if os.path.exists(settings.MODEL_CHECKPOINT):
        state = torch.load(settings.MODEL_CHECKPOINT, map_location=device)
        model.load_state_dict(state)
    model.to(device)
    model.eval()
    return model


def train(epochs: int = 20, batch_size: int = 8, lr: float = 1e-4):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    split_dir = os.path.join(settings.DATA_DIR, "train")

    train_pairs, val_pairs = train_val_split(split_dir)
    print(f"Train pairs: {len(train_pairs)}")
    print(f"Validation pairs: {len(val_pairs)}")
    print(f"Device: {device}")

    train_ds = RoadDataset(split_dir, transform=train_transform(settings.IMG_SIZE))
    val_ds = RoadDataset(split_dir, transform=val_transform(settings.IMG_SIZE))

    # num_workers=0 is recommended on Windows while debugging
    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
    )

    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
    )

    model = build_model().to(device)

    dice_loss = smp.losses.DiceLoss(mode="binary")
    bce_loss = torch.nn.BCEWithLogitsLoss()

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    os.makedirs(settings.WEIGHTS_DIR, exist_ok=True)

    best_val = float("inf")

    print("\n========== Training Started ==========\n")

    for epoch in range(1, epochs + 1):

        print(f"\nEpoch {epoch}/{epochs}")

        #########################
        # Training
        #########################

        model.train()
        running_loss = 0.0

        train_bar = tqdm(
            train_loader,
            desc="Training",
            unit="batch",
            leave=True,
        )

        for images, masks in train_bar:

            images = images.to(device)
            masks = masks.to(device)

            optimizer.zero_grad()

            logits = model(images)

            loss = dice_loss(logits, masks) + bce_loss(logits, masks)

            loss.backward()

            optimizer.step()

            running_loss += loss.item() * images.size(0)

            train_bar.set_postfix(loss=f"{loss.item():.4f}")

        train_loss = running_loss / len(train_ds)

        #########################
        # Validation
        #########################

        model.eval()
        val_running = 0.0

        val_bar = tqdm(
            val_loader,
            desc="Validation",
            unit="batch",
            leave=True,
        )

        with torch.no_grad():
            for images, masks in val_bar:

                images = images.to(device)
                masks = masks.to(device)

                logits = model(images)

                loss = dice_loss(logits, masks) + bce_loss(logits, masks)

                val_running += loss.item() * images.size(0)

                val_bar.set_postfix(loss=f"{loss.item():.4f}")

        val_loss = val_running / len(val_ds)

        print(
            f"\nEpoch {epoch}/{epochs} "
            f"Train Loss: {train_loss:.4f} "
            f"Validation Loss: {val_loss:.4f}"
        )

        if val_loss < best_val:
            best_val = val_loss

            torch.save(model.state_dict(), settings.MODEL_CHECKPOINT)

            print(f"✅ Saved best model to {settings.MODEL_CHECKPOINT}")

    print("\n========== Training Complete ==========")


if __name__ == "__main__":
    train()
