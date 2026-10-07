# Module A - Flood Detection

Detects flooded pixels in Sentinel-1 radar images and reports the flood fraction per zone.

## What it does
Sentinel-1 chip (VV + VH) -> U-Net (ResNet34 encoder) -> flood probability per pixel -> 3x3 grid (Z1-Z9) -> JSON for Module B.

## Files
- data_loader.py - reads Sen1Floods11 chips and labels (SAR bands only, no-data pixels ignored)
- train.py - trains the U-Net (BCE + Dice loss, validation IoU)
- inference.py - image in, flood mask / probabilities out
- aggregate_zones.py - mask to flood_pct and mask_confidence per zone
- outputs/ - sample output JSON

## How to run
1. Install: `pip install -r requirements.txt`
2. Train (GPU recommended, e.g. Colab): `python train.py --base <path to Sen1Floods11_8Channel>`
3. Predict: `python inference.py --weights flood_unet_best.pt --image <chip>_image.tif --out outputs/sample_output.json`

## Output format (schema 1)
One object per zone, Z1 (top-left) to Z9 (bottom-right), row by row:
`{"zone_id": "Z1", "flood_pct": 0.62, "mask_confidence": 0.88}`
- flood_pct: fraction of valid pixels predicted as flood, 0 to 1
- mask_confidence: average model certainty in the zone, 0.5 to 1

## Results
- Validation IoU: 0.51 (67 chips, Sen1Floods11 hand-labelled split)
## Results new
- Test IoU: 0.59, test F1: 0.742 (67 held-out Sen1Floods11 chips; pixels without a label are ignored)
- Validation IoU: 0.51 (67 chips, used to pick the best epoch)
- Setup: U-Net, ResNet34 encoder (ImageNet pretrained), Sentinel-1 VV+VH input, BCE + Dice loss, 8 epochs, batch size 4, learning rate 1e-3

## Limitations
- Trained and evaluated on Sen1Floods11 only; no Nepal-labelled data.
- The sample JSON in outputs/ comes from a Sen1Floods11 test chip split into an equal 3x3 grid. It is NOT Nepal imagery.
- Model weights are not in the repo (shared via Drive).
