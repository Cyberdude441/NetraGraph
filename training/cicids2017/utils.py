import os
import hashlib
import torch

def hardware_status():
    gpu = torch.cuda.is_available()

    print("-" * 50)
    print("GPU available    :", gpu)

    if gpu:
        print("GPU name         :", torch.cuda.get_device_name(0))

    print("CUDA availability:", gpu)
    print("training device  :", "GPU" if gpu else "CPU")
    print("-" * 50)

def sha256_file(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()
