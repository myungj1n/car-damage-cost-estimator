import kagglehub
import pandas as pd
import os
import json

# Load the car parts/damages dataset
print("Loading car parts and damages dataset...")
path = kagglehub.dataset_download("humansintheloop/car-parts-and-car-damages")
print(f"Dataset path: {path}")

# List all files in the dataset
print(f"\nFiles in dataset:")
for root, dirs, files in os.walk(path):
    for file in files:
        file_path = os.path.join(root, file)
        rel_path = os.path.relpath(file_path, path)
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        print(f"  {rel_path:60} ({file_size:.2f} MB)")

# Try to find and read any JSON or CSV files with part/damage information
print("\n" + "="*70)
print("Analyzing dataset contents...")
print("="*70)

# Look for annotation files
json_files = []
for root, dirs, files in os.walk(path):
    for file in files:
        if file.endswith('.json'):
            json_files.append(os.path.join(root, file))

if json_files:
    print(f"\nFound {len(json_files)} JSON files. Analyzing first one...")
    with open(json_files[0], 'r') as f:
        sample_data = json.load(f)
    print(f"\nSample JSON structure:")
    print(json.dumps(sample_data, indent=2)[:1000])
    
    # Extract unique part/damage types
    part_types = set()
    damage_types = set()
    
    for json_file in json_files[:100]:  # Check first 100 files
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                
            # Try different possible structures
            if isinstance(data, dict):
                # Look for categories, labels, or annotations
                if 'categories' in data:
                    for cat in data['categories']:
                        if isinstance(cat, dict) and 'name' in cat:
                            part_types.add(cat['name'])
                
                if 'annotations' in data:
                    for ann in data['annotations']:
                        if isinstance(ann, dict) and 'category_name' in ann:
                            part_types.add(ann['category_name'])
                        if isinstance(ann, dict) and 'damage' in ann:
                            damage_types.add(ann['damage'])
                            
                # Check for other common keys
                for key in ['objects', 'labels', 'parts', 'damages']:
                    if key in data:
                        if isinstance(data[key], list):
                            for item in data[key]:
                                if isinstance(item, dict) and 'name' in item:
                                    part_types.add(item['name'])
                                elif isinstance(item, str):
                                    part_types.add(item)
        except:
            pass
    
    print(f"\n\nUnique car parts found in dataset ({len(part_types)} total):")
    print("="*70)
    for i, part in enumerate(sorted(part_types), 1):
        print(f"{i:3}. {part}")
    
    if damage_types:
        print(f"\n\nUnique damage types found ({len(damage_types)} total):")
        print("="*70)
        for i, damage in enumerate(sorted(damage_types), 1):
            print(f"{i:3}. {damage}")

# Now load OEM parts data
print("\n\n" + "="*70)
print("Loading OEM Parts Data...")
print("="*70)

oem_df = pd.read_csv('oem_parts_data.csv')
print(f"\nOEM Parts Dataset Shape: {oem_df.shape}")
print(f"Columns: {oem_df.columns.tolist()}")
print(f"\nFirst few rows:")
print(oem_df.head())

# Get unique part names from OEM data
oem_part_names = oem_df['part_name'].dropna().unique()
print(f"\n\nUnique OEM parts available ({len(oem_part_names)} total):")
print("="*70)
for i, part in enumerate(sorted(oem_part_names)[:50], 1):
    print(f"{i:3}. {part[:60]}")
if len(oem_part_names) > 50:
    print(f"... and {len(oem_part_names) - 50} more parts")

print("\n\n" + "="*70)
print("ANALYSIS SUMMARY")
print("="*70)
print(f"Car parts/damages dataset parts: {len(part_types)}")
print(f"OEM pricing dataset parts: {len(oem_part_names)}")
print("\nSaving analysis to 'dataset_comparison.txt'...")
