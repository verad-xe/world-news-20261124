"""world-news-20261124: deliver the generated front-page image.

The entry program for make.fun's "Sum up 24 November's world news in one
image" bounty. It copies the finished front-page image (entry.png, held in
this repository) into the output directory, byte for byte.

Standard library only, no network, no randomness: running it twice writes
identical bytes. The artwork itself was produced on Kaggle's free GPU with
an image-generation model (SDXL) and laid out as a newspaper front page.
"""

import hashlib
import os
import shutil
import sys

SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")

MAX_BYTES = 1048576
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"


def validate(path):
    """Check path holds a whole PNG or JPEG image within the size limit."""
    with open(path, "rb") as handle:
        magic = handle.read(8)
    if not (magic.startswith(PNG_MAGIC) or magic.startswith(JPEG_MAGIC)):
        raise ValueError(f"{path}: not a PNG or JPEG image")
    size = os.path.getsize(path)
    if size <= 0 or size > MAX_BYTES:
        raise ValueError(f"{path}: size {size} bytes is outside the limit")
    return size


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    size = validate(SOURCE)
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(output_dir, exist_ok=True)
    destination = os.path.join(output_dir, "entry.png")
    shutil.copyfile(SOURCE, destination)
    if validate(destination) != size:
        raise ValueError("output does not match the source image")
    print(f"wrote {destination} ({size} bytes, sha256 {sha256_of(destination)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
