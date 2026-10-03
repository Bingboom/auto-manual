"""Align live captions to source-bound illustration centers."""
from itertools import pairwise
import math


def align_caption_centers(figure, centers):
    """Keep the shared caption grid, offsetting its labels to native centers."""
    if centers is None:
        return
    labels = figure.select(".hb-reference-caption-grid > .hb-reference-caption")
    if (not isinstance(centers, (list, tuple)) or len(centers) != len(labels)
            or not centers or any(isinstance(x, bool) or not isinstance(x, (int, float))
                                  or not math.isfinite(x) or not 0 < x < 100 for x in centers)
            or any(a >= b for a, b in pairwise(centers))):
        raise ValueError("caption centers must be ordered percentages, one per live caption")
    for index, (label, center) in enumerate(zip(labels, centers, strict=True)):
        shift = center * len(labels) - (index + .5) * 100
        label["style"] = f"transform:translateX({shift:g}%)"
