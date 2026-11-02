"""Preserve the existing synthetic 100 rows and append 200 reproducible new IDs."""
import csv
import random
from datetime import date
from pathlib import Path

from generate_module1_pilot_data import generate_hr_rows, RANDOM_SEED

ROOT = Path(__file__).resolve().parents[1]


def main():
    with (ROOT / 'pilot-data/module1_hr_pilot_100_employees.csv').open(encoding='utf-8-sig', newline='') as stream:
        original = list(csv.DictReader(stream))
    if len(original) != 100 or len({row['EmployeeID'] for row in original}) != 100:
        raise ValueError('Expected the original 100 distinct pilot employees')
    random.seed(RANDOM_SEED)
    additions = generate_hr_rows(300)[100:]
    for row in additions:
        observed = date.fromisoformat(row['ObservationDate'])
        row['JoinDate'] = observed.replace(year=observed.year - int(row['YearsAtCompany'])).isoformat()
        row['ResignationDate'] = observed.isoformat() if row['Attrition'] == 'Yes' else ''
    combined = original + additions
    if len({row['EmployeeID'] for row in combined}) != 300:
        raise ValueError('Employee ID collision')
    output = ROOT / 'pilot-data/module1_hr_pilot_300_employees.csv'
    with output.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(original[0]))
        writer.writeheader()
        writer.writerows(combined)
    print('Created synthetic HR pilot: 300 unique employee IDs; original 100 preserved.')


if __name__ == '__main__':
    main()
