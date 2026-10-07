import argparse
import torch
import segmentation_models_pytorch as smp
from torch.utils.data import DataLoader
from data_loader import Sen1Floods11

bce = torch.nn.BCEWithLogitsLoss(reduction="none")

def loss_fn(logits, mask, valid):
    b = (bce(logits, mask) * valid).sum() / valid.sum().clamp(min=1)
    p = torch.sigmoid(logits) * valid
    m = mask * valid
    dice = 1 - (2 * (p * m).sum() + 1) / (p.sum() + m.sum() + 1)
    return b + dice

def iou_counts(logits, mask, valid):
    pred = (torch.sigmoid(logits) > 0.5).float() * valid
    m = mask * valid
    inter = (pred * m).sum().item()
    union = (pred + m - pred * m).sum().item()
    return inter, union

def main(base, epochs, lr, batch_size, out):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    train_dl = DataLoader(Sen1Floods11(base, "train"), batch_size=batch_size,
                          shuffle=True, num_workers=2)
    val_dl = DataLoader(Sen1Floods11(base, "val"), batch_size=batch_size,
                        shuffle=False, num_workers=2)

    model = smp.Unet(encoder_name="resnet34", encoder_weights="imagenet",
                     in_channels=2, classes=1, activation=None).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    best_iou = 0

    for epoch in range(epochs):
        model.train()
        total = 0
        for x, y, v in train_dl:
            x, y, v = x.to(device), y.to(device), v.to(device)
            opt.zero_grad()
            loss = loss_fn(model(x), y, v)
            loss.backward()
            opt.step()
            total += loss.item()

        model.eval()
        inter = union = 0
        with torch.no_grad():
            for x, y, v in val_dl:
                x, y, v = x.to(device), y.to(device), v.to(device)
                i, u = iou_counts(model(x), y, v)
                inter += i
                union += u
        iou = inter / max(union, 1)
        print(f"epoch {epoch+1}/{epochs}  train loss {total/len(train_dl):.3f}  val IoU {iou:.3f}")

        if iou > best_iou:
            best_iou = iou
            torch.save(model.state_dict(), out)

    print("best val IoU:", best_iou)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="path to Sen1Floods11_8Channel folder")
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--batch_size", type=int, default=4)
    ap.add_argument("--out", default="flood_unet_best.pt")
    args = ap.parse_args()
    main(args.base, args.epochs, args.lr, args.batch_size, args.out)