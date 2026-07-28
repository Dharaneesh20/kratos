import cv2
import numpy as np

from app.services.skeletonize import prune_short_branches, to_skeleton


def test_prune_short_branches_removes_spur():
    mask = np.zeros((80, 80), dtype=np.uint8)
    cv2.line(mask, (10, 40), (70, 40), 1, 5)
    cv2.line(mask, (40, 40), (40, 46), 1, 3)

    skeleton = to_skeleton(mask)
    before = int(skeleton.sum())
    pruned = prune_short_branches(skeleton, min_branch_len_px=8)
    after = int(pruned.sum())

    assert after < before
