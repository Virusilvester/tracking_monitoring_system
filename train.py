# File: train.py

import argparse
from pathlib import Path
import yaml
import torch
from lib.yolov5 import train

def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', type=str, default='yolov5s.pt', help='initial weights path')
    parser.add_argument('--data', type=str, default='data/coco128.yaml', help='dataset.yaml path')
    parser.add_argument('--epochs', type=int, default=300)
    parser.add_argument('--batch-size', type=int, default=16, help='total batch size for all GPUs')
    parser.add_argument('--img-size', type=int, default=640, help='train, val image size (pixels)')
    parser.add_argument('--device', default='cpu', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--workers', type=int, default=8, help='maximum number of dataloader workers')
    return parser.parse_args()

def main(opt):
    # Load configuration
    with open(opt.data) as f:
        data_dict = yaml.safe_load(f)
    
    # Setup device
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    
    # Initialize training parameters
    hyp = 'hyperparameters.yaml'  # Update this to the correct path for hyperparameters
    
    # Start training
    train.run(
        weights=opt.weights,
        data=opt.data,
        epochs=opt.epochs,
        batch_size=opt.batch_size,
        imgsz=opt.img_size,
        device=opt.device,
        workers=opt.workers,
        hyp=hyp  # Ensure this is a path to a YAML file
    )

if __name__ == '__main__':
    opt = parse_opt()
    main(opt) 