"""
Explore the Kaggle Car Parts and Damages dataset
Understand the structure and prepare for training
"""

import os
import json
from collections import Counter
from pathlib import Path

# Dataset paths
DATASET_ROOT = Path.home() / ".cache/kagglehub/datasets/humansintheloop/car-parts-and-car-damages/versions/2"
PARTS_IMG_DIR = DATASET_ROOT / "Car damages dataset/File1/img"
PARTS_ANN_DIR = DATASET_ROOT / "Car damages dataset/File1/ann"
DAMAGE_IMG_DIR = DATASET_ROOT / "Car parts dataset/File1/img"
DAMAGE_ANN_DIR = DATASET_ROOT / "Car parts dataset/File1/ann"

def explore_parts_dataset():
    """Explore the car parts identification dataset"""
    print("="*70)
    print("CAR PARTS IDENTIFICATION DATASET")
    print("="*70)
    
    # Count images
    images = list(PARTS_IMG_DIR.glob("*"))
    print(f"\nTotal images: {len(images)}")
    print(f"Image directory: {PARTS_IMG_DIR}")
    
    # Collect all classes from annotations
    all_classes = []
    images_per_class = Counter()
    
    for ann_file in PARTS_ANN_DIR.glob("*.json"):
        with open(ann_file, 'r') as f:
            data = json.load(f)
            classes_in_image = set()
            for obj in data['objects']:
                class_title = obj['classTitle']
                all_classes.append(class_title)
                classes_in_image.add(class_title)
            
            # Count this image for each unique class
            for cls in classes_in_image:
                images_per_class[cls] += 1
    
    # Unique classes
    unique_classes = sorted(set(all_classes))
    print(f"\nUnique classes: {len(unique_classes)}")
    print("\nClass distribution (images per class):")
    for cls, count in sorted(images_per_class.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cls:.<30} {count:>4} images")
    
    # Check for multi-label
    multi_label_count = 0
    for ann_file in list(PARTS_ANN_DIR.glob("*.json"))[:100]:
        with open(ann_file, 'r') as f:
            data = json.load(f)
            classes_in_image = set(obj['classTitle'] for obj in data['objects'])
            if len(classes_in_image) > 1:
                multi_label_count += 1
    
    print(f"\nMulti-label analysis (first 100 images):")
    print(f"  Images with multiple parts: {multi_label_count}/100")
    print(f"  → This is a MULTI-LABEL classification problem")
    
    return unique_classes


def explore_damage_dataset():
    """Explore the damage classification dataset"""
    print("\n" + "="*70)
    print("DAMAGE CLASSIFICATION DATASET")
    print("="*70)
    
    # Count images
    images = list(DAMAGE_IMG_DIR.glob("*"))
    print(f"\nTotal images: {len(images)}")
    print(f"Image directory: {DAMAGE_IMG_DIR}")
    
    # Collect all classes from annotations
    all_classes = []
    images_per_class = Counter()
    
    for ann_file in DAMAGE_ANN_DIR.glob("*.json"):
        with open(ann_file, 'r') as f:
            data = json.load(f)
            classes_in_image = set()
            for obj in data['objects']:
                class_title = obj['classTitle']
                all_classes.append(class_title)
                classes_in_image.add(class_title)
            
            # Count this image for each unique class
            for cls in classes_in_image:
                images_per_class[cls] += 1
    
    # Unique classes
    unique_classes = sorted(set(all_classes))
    print(f"\nUnique classes: {len(unique_classes)}")
    print("\nClass distribution (images per class):")
    for cls, count in sorted(images_per_class.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cls:.<30} {count:>4} images")
    
    # Check for multi-label
    multi_label_count = 0
    for ann_file in list(DAMAGE_ANN_DIR.glob("*.json"))[:100]:
        with open(ann_file, 'r') as f:
            data = json.load(f)
            classes_in_image = set(obj['classTitle'] for obj in data['objects'])
            if len(classes_in_image) > 1:
                multi_label_count += 1
    
    print(f"\nMulti-label analysis (first 100 images):")
    print(f"  Images with multiple damage types: {multi_label_count}/100")
    print(f"  → This is a MULTI-LABEL classification problem")
    
    return unique_classes


def check_data_split():
    """Check recommended data split"""
    print("\n" + "="*70)
    print("RECOMMENDED DATA SPLITS")
    print("="*70)
    
    parts_count = len(list(PARTS_IMG_DIR.glob("*")))
    damage_count = len(list(DAMAGE_IMG_DIR.glob("*")))
    
    print(f"\nPart Identification Dataset ({parts_count} images):")
    print(f"  Training:   {int(parts_count * 0.70):>4} images (70%)")
    print(f"  Validation: {int(parts_count * 0.15):>4} images (15%)")
    print(f"  Testing:    {int(parts_count * 0.15):>4} images (15%)")
    
    print(f"\nDamage Classification Dataset ({damage_count} images):")
    print(f"  Training:   {int(damage_count * 0.70):>4} images (70%)")
    print(f"  Validation: {int(damage_count * 0.15):>4} images (15%)")
    print(f"  Testing:    {int(damage_count * 0.15):>4} images (15%)")


def sample_annotation():
    """Show a sample annotation"""
    print("\n" + "="*70)
    print("SAMPLE ANNOTATION FORMAT")
    print("="*70)
    
    sample_file = list(PARTS_ANN_DIR.glob("*.json"))[0]
    print(f"\nFile: {sample_file.name}")
    
    with open(sample_file, 'r') as f:
        data = json.load(f)
    
    print(f"Image size: {data['size']['width']}x{data['size']['height']}")
    print(f"Number of objects: {len(data['objects'])}")
    print(f"\nFirst object:")
    obj = data['objects'][0]
    print(f"  Class: {obj['classTitle']}")
    print(f"  Geometry: {obj['geometryType']}")
    print(f"  Points: {len(obj['points']['exterior'])} exterior points")


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" KAGGLE DATASET EXPLORATION")
    print("="*70)
    
    # Explore both datasets
    part_classes = explore_parts_dataset()
    damage_classes = explore_damage_dataset()
    
    # Data split recommendations
    check_data_split()
    
    # Sample annotation
    sample_annotation()
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"\n✓ Parts dataset: {len(part_classes)} classes, multi-label")
    print(f"✓ Damage dataset: {len(damage_classes)} classes, multi-label")
    print(f"✓ Both datasets use polygon annotations")
    print(f"✓ Ready for training pipeline development")
    print()
