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
MAX_DIMENSION = 1024
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"
PNG_IEND = b"\x00\x00\x00\x00IEND\xaeB`\x82"
JPEG_EOI = b"\xff\xd9"


def image_dimensions(data):
    """Parse width and height from a PNG IHDR chunk or a JPEG SOF marker."""
    if data.startswith(PNG_MAGIC):
        if len(data) < 33 or data[12:16] != b"IHDR":
            raise ValueError("PNG header is missing the IHDR chunk")
        width = int.from_bytes(data[16:20], "big")
        height = int.from_bytes(data[20:24], "big")
        return width, height
    if data.startswith(JPEG_MAGIC):
        index = 2
        while index + 9 < len(data):
            if data[index] != 0xFF:
                raise ValueError("JPEG marker stream is malformed")
            marker = data[index + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                          0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                height = int.from_bytes(data[index + 5:index + 7], "big")
                width = int.from_bytes(data[index + 7:index + 9], "big")
                return width, height
            length = int.from_bytes(data[index + 2:index + 4], "big")
            if length < 2:
                raise ValueError("JPEG segment length is invalid")
            index += 2 + length
        raise ValueError("JPEG SOF marker not found")
    raise ValueError("not a PNG or JPEG image")


def validate(path):
    """Check path holds a whole PNG or JPEG image within the size limit."""
    with open(path, "rb") as handle:
        data = handle.read()
    magic = data[:8]
    if not (magic.startswith(PNG_MAGIC) or magic.startswith(JPEG_MAGIC)):
        raise ValueError(f"{path}: not a PNG or JPEG image")
    size = len(data)
    if size <= 0 or size > MAX_BYTES:
        raise ValueError(f"{path}: size {size} bytes is outside the limit")
    if data.startswith(PNG_MAGIC):
        if not data.endswith(PNG_IEND):
            raise ValueError(f"{path}: PNG is truncated (no IEND chunk)")
    else:
        if not data.endswith(JPEG_EOI):
            raise ValueError(f"{path}: JPEG is truncated (no EOI marker)")
    width, height = image_dimensions(data)
    if width <= 0 or height <= 0 or width > MAX_DIMENSION or height > MAX_DIMENSION:
        raise ValueError(
            f"{path}: dimensions {width}x{height} exceed the "
            f"{MAX_DIMENSION}x{MAX_DIMENSION} limit"
        )
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
