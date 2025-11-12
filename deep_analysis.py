import kagglehub
import json
import os

# Load dataset
path = kagglehub.dataset_download('humansintheloop/car-parts-and-car-damages')
print(f"Dataset path: {path}\n")

# List directory structure
print("="*70)
print("DIRECTORY STRUCTURE:")
print("="*70)
for root, dirs, files in os.walk(path):
    level = root.replace(path, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    sub_indent = ' ' * 2 * (level + 1)
    
    # Show first few files in each directory
    for i, file in enumerate(files[:5]):
        print(f'{sub_indent}{file}')
    if len(files) > 5:
        print(f'{sub_indent}... and {len(files) - 5} more files')

# Find JSON files in different folders
print("\n" + "="*70)
print("ANALYZING JSON FILES FROM DIFFERENT FOLDERS:")
print("="*70)

json_files_by_folder = {}
for root, dirs, files in os.walk(path):
    folder_name = os.path.basename(root)
    json_files = [f for f in files if f.endswith('.json')]
    if json_files:
        json_files_by_folder[folder_name] = [os.path.join(root, f) for f in json_files]

# Analyze JSON files from each folder
for folder_name, json_files in json_files_by_folder.items():
    print(f"\n{'='*70}")
    print(f"Folder: {folder_name} ({len(json_files)} JSON files)")
    print(f"{'='*70}")
    
    # Analyze first JSON file
    if json_files:
        with open(json_files[0], 'r') as f:
            data = json.load(f)
        
        print(f"\nSample JSON file: {os.path.basename(json_files[0])}")
        print(f"\nKeys in JSON: {list(data.keys())}")
        
        # Show classes
        if 'classes' in data:
            print(f"\nClasses ({len(data['classes'])}):")
            for cls in data['classes']:
                print(f"  - {cls.get('title', 'N/A')}")
        
        # Show sample objects
        if 'objects' in data:
            print(f"\nObjects/Annotations ({len(data['objects'])}):")
            for i, obj in enumerate(data['objects'][:5]):
                class_title = obj.get('classTitle', 'N/A')
                print(f"  {i+1}. {class_title}")
            if len(data['objects']) > 5:
                print(f"  ... and {len(data['objects']) - 5} more objects")
        
        # Collect all unique class titles from ALL JSON files in this folder
        all_class_titles = set()
        print(f"\nAnalyzing all {len(json_files)} files in this folder...")
        for json_file in json_files[:100]:  # Check up to 100 files
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                if 'objects' in data:
                    for obj in data['objects']:
                        if 'classTitle' in obj:
                            all_class_titles.add(obj['classTitle'])
            except:
                pass
        
        if all_class_titles:
            print(f"\nUnique class titles found in this folder ({len(all_class_titles)}):")
            for title in sorted(all_class_titles):
                print(f"  • {title}")

print("\n" + "="*70)
print("ANALYSIS COMPLETE")
print("="*70)
