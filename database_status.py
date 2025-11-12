import pandas as pd

# Check current state
df = pd.read_csv('oem_parts_data.csv')

print('='*60)
print('FINAL OEM PARTS DATABASE STATUS')
print('='*60)
print()
print(f'Total Parts: {len(df):,}')
print(f'Total Makes: {df["make"].nunique()}')
print(f'Total Unique Part Types: {df["part_name"].nunique():,}')
print()
print('Coverage by Make:')
print('-'*60)

make_counts = df.groupby('make').agg({
    'part_number': 'count',
    'price': ['min', 'max', 'mean']
}).round(2)

make_counts.columns = ['Parts', 'Min_Price', 'Max_Price', 'Avg_Price']
make_counts = make_counts.sort_values('Parts', ascending=False)

for make, row in make_counts.iterrows():
    print(f'{make:.<20} {int(row["Parts"]):>6,} parts  (${row["Min_Price"]:>8.2f} - ${row["Max_Price"]:>8,.2f})')

print()
print('='*60)
print('MAKES WITH LIMITED DATA:')
print('='*60)
limited = make_counts[make_counts['Parts'] < 100]
for make, row in limited.iterrows():
    status = '⚠️ Very Limited' if row['Parts'] < 10 else '⚠️ Limited'
    print(f'{status} {make}: {int(row["Parts"])} parts')

print()
print('='*60)
print('WELL-COVERED MAKES (1000+ parts):')
print('='*60)
well_covered = make_counts[make_counts['Parts'] >= 1000]
print(f'✅ {len(well_covered)} makes have comprehensive coverage')
for make, row in well_covered.iterrows():
    print(f'  {make}: {int(row["Parts"]):,} parts')
