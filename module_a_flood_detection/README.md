# Module A — Flood Detection

## Overview

This module detects flooded areas from satellite images using a **U-Net image segmentation model**.

The module takes a satellite image as input and produces a **flood mask**, showing which parts of the image are affected by water/flooding.

The flood information is then converted into a percentage for each zone and passed to **Module B — Risk Scoring**.

---

## How It Works

```text
Satellite Image
       ↓
   U-Net Model
       ↓
   Flood Mask
       ↓
Flooded Area (%)
       ↓
Module B — Risk Scoring
```

---

## Dataset

We use the **Sen1Floods11** dataset for training and evaluation.

The dataset contains:

* Satellite images
* Corresponding flood labels/masks
* Training, validation, and test splits

The dataset is **not stored in this GitHub repository** because of its large size.

---

## Main Tasks

This module is responsible for:

1. Loading satellite images and flood masks
2. Preprocessing the images
3. Training the U-Net segmentation model
4. Predicting flood masks for new images
5. Calculating the percentage of flooded area
6. Sending the flood information to the next module

---

## Expected Output

For each zone, this module provides:

```json
{
  "zone_id": "Z1",
  "flood_pct": 0.62,
  "mask_confidence": 0.88
}
```

### Fields

* `zone_id` — Identifier of the affected zone
* `flood_pct` — Percentage of the zone detected as flooded
* `mask_confidence` — Confidence of the flood segmentation result

The output follows the shared project schema.

---

## Project Files

| File                 | Purpose                                                            |
| -------------------- | ------------------------------------------------------------------ |
| `data_loader.py`     | Loads and preprocesses satellite images and masks                  |
| `train.py`           | Trains the U-Net model                                             |
| `inference.py`       | Generates flood masks for new images                               |
| `evaluate.py`        | Evaluates model performance                                        |
| `aggregate_zones.py` | Converts pixel-level predictions into zone-level flood percentages |

---

## Model

The module uses a **U-Net segmentation model** with a pretrained encoder.

The model performs pixel-level classification:

```text
Satellite Image
      ↓
     U-Net
      ↓
Each pixel → Flood / Not Flood
```

---

## Evaluation

The model will be evaluated using:

* **IoU (Intersection over Union)**
* **F1 Score**

These metrics measure how closely the predicted flood mask matches the actual flood mask.

---

## Important

* Do not upload the dataset or trained model files to GitHub unless specifically required.
* Keep dataset paths/configuration separate from the source code.
* Follow the shared project schema when sending output to other modules.
* Changes to shared schemas should be discussed with the team before modifying them.

