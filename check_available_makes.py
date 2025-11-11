import kagglehub
import pandas as pd
import os

# Download the dataset
path = kagglehub.dataset_download("natelee2003/vinapi")
csv_files = [f for f in os.listdir(path) if f.endswith('.csv')]
df = pd.read_csv(os.path.join(path, csv_files[0]), sep='\t')

# Clean up makes
make_column = 'MAKE'
unique_makes = df[make_column].dropna().unique()
cleaned_makes = []
for make in unique_makes:
    make_str = str(make).strip().strip('"').strip()
    if make_str and len(make_str) > 1 and make_str.replace(' ', '').replace('-', '').isalpha():
        cleaned_makes.append(make_str)

unique_makes = sorted(list(set(cleaned_makes)))

# List of makes available on oempartsonline.com
available_makes = [
    'acura', 'audi', 'bmw', 'ford', 'honda', 'hyundai', 'infiniti', 'jaguar',
    'kia', 'land rover', 'lexus', 'mazda', 'mitsubishi', 'nissan', 'porsche',
    'subaru', 'toyota', 'volkswagen', 'volvo', 'ram', 'dodge', 'chrysler', 
    'jeep', 'chevrolet', 'gmc', 'buick', 'cadillac'
]

# Find matching makes in dataset
matches = []
for make in unique_makes:
    if make.lower() in available_makes:
        matches.append(make)

print(f"Total unique makes in dataset: {len(unique_makes)}")
print(f"\nMakes available on oempartsonline.com that are in your dataset:")
print(f"{'='*60}")
for i, make in enumerate(matches, 1):
    count = len(df[df[make_column] == make])
    print(f"{i:2}. {make:20} - {count:,} VINs")
