import numpy as np
import rasterio
import torch
from torch.utils.data import Dataset

SAR_BANDS = [4, 5]  # 0-indexed: bands 5,6 = VV, VH

def chip_id(token):
    return token.replace(".tif", "").replace("_image", "").replace("_label", "")

def read_split(split_dir, name):
    with open(f"{split_dir}/{name}.txt") as f:
        return [chip_id(t) for t in f.read().split()]

class Sen1Floods11(Dataset):
    def __init__(self, base, split, bands=SAR_BANDS):
        self.img_dir = f"{base}/image"
        self.lbl_dir = f"{base}/label"
        self.ids = read_split(f"{base}/split", split)
        self.bands = bands

    def __len__(self):
        return len(self.ids)

    def __getitem__(self, i):
        cid = self.ids[i]
        with rasterio.open(f"{self.img_dir}/{cid}_image.tif") as s:
            img = s.read()[self.bands].astype(np.float32)
        with rasterio.open(f"{self.lbl_dir}/{cid}_label.tif") as s:
            lbl = s.read(1)

        img = np.nan_to_num(img, nan=-50.0)
        img = (np.clip(img, -50, 5) + 50) / 55.0

        valid = (lbl != -1).astype(np.float32)
        mask = (lbl == 1).astype(np.float32)

        return (torch.from_numpy(img),
                torch.from_numpy(mask).unsqueeze(0),
                torch.from_numpy(valid).unsqueeze(0))