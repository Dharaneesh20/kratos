"""
Augmentation pipelines, including synthetic occlusion (cloud/canopy patches)
applied to the input image only, so the model learns to infer road
continuity under partial visibility -- this is the "occlusion-robust"
differentiator for the demo.
"""

import albumentations as A


def train_transform(img_size: int):
    return A.Compose(
        [
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.5),
            A.RandomRotate90(p=0.5),
            A.RandomBrightnessContrast(p=0.3),
            # Synthetic occlusion: random opaque patches simulating cloud
            # cover / tree canopy. Mask ground truth stays untouched, so
            # the model must predict the hidden road segment.
            A.CoarseDropout(
                max_holes=6,
                max_height=img_size // 6,
                max_width=img_size // 6,
                min_holes=1,
                fill_value=0,
                mask_fill_value=None,  # do not touch the mask
                p=0.5,
            ),
        ]
    )


def val_transform(img_size: int):
    # No augmentation at validation time -- clean signal on model quality.
    return A.Compose([])
