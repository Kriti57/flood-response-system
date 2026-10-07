import argparse
import numpy as np
import rasterio
import torch
import torch.nn.functional as F
import segmentation_models_pytorch as smp

from aggregate_zones import aggregate_grid, save_json

SAR_BANDS = [4, 5]   # bands 5,6 = VV, VH. Must match data_loader.py

def load_model(weights_path, device=None):
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    model = smp.Unet(encoder_name="resnet34", encoder_weights=None,
                     in_channels=2, classes=1, activation=None)
    model.load_state_dict(torch.load(weights_path, map_location=device))
    return model.to(device).eval(), device

def load_chip(image_path):
    """Read VV/VH and scale them exactly as in training (data_loader.py)."""
    with rasterio.open(image_path) as src:
        img = src.read()[SAR_BANDS].astype(np.float32)
    valid = np.isfinite(img).all(axis=0)             # False where radar data is missing
    img = np.nan_to_num(img, nan=-50.0)
    img = (np.clip(img, -50, 5) + 50) / 55.0
    return img, valid

def predict_prob(model, device, img):
    """img: (2, H, W) -> flood probability map (H, W), values 0-1."""
    _, H, W = img.shape
    x = torch.from_numpy(img).unsqueeze(0).to(device)
    pad_h, pad_w = (-H) % 32, (-W) % 32              # U-Net needs sizes divisible by 32
    x = F.pad(x, (0, pad_w, 0, pad_h))
    with torch.no_grad():
        prob = torch.sigmoid(model(x))[0, 0]
    return prob[:H, :W].cpu().numpy()

def predict_mask(prob, threshold=0.5):
    """Binary flood mask: 1 = flood, 0 = not flood."""
    return (prob > threshold).astype(np.uint8)

def run(weights, image, out):
    model, device = load_model(weights)
    img, valid = load_chip(image)
    prob = predict_prob(model, device, img)
    records = aggregate_grid(prob, valid)
    save_json(records, out)
    return prob, valid, records

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", default="outputs/sample_output.json")
    args = ap.parse_args()
    run(args.weights, args.image, args.out)
    print("saved", args.out)