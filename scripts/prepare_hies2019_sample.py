"""Extract a minimal private 100-wage-earner HIES sample without changing app data."""
import argparse
import csv
import hashlib
import io
import json
import random
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
HH = ('district', 'sector', 'month', 'psu', 'snumber', 'hhno', 'nhh')
DEBT = ('bank_amount', 'samurtdhi_amount', 'finance_amount', 'employer_amount',
        'lender_amount', 'credit_cards_amount', 'retail_shop_amount',
        'pawning_amount', 'instalement_amount', 'other_amount')


def rows(archive, name):
    with archive.open(name) as stream:
        yield from csv.DictReader(io.TextIOWrapper(stream, encoding='utf-8-sig'))


def key(row):
    return tuple(row[field].strip() for field in HH)


def positive(value):
    try:
        number = Decimal(value.strip())
        return number.is_finite() and number > 0
    except InvalidOperation:
        return False


def write_csv(path, records, fields):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    output = ROOT / 'data' / 'private' / 'hies2019_100'
    with ZipFile(args.source) as archive:
        # Keys stay in memory and are never exported. Demography is used only
        # to exclude minors and ambiguous person matches.
        demographics = defaultdict(list)
        for row in rows(archive, 'SEC_1_DEMOGRAPHIC_25%.CSV'):
            demographics[key(row) + (row['person_serial_no'].strip(),)].append(row['age'].strip())
        income = list(rows(archive, 'SEC_5_1_EMP_INCOME_25%.CSV'))
        person_counts = Counter(key(row) + (row['person_serial_no'].strip(),) for row in income)
        eligible = []
        for row in income:
            person = key(row) + (row['person_serial_no'].strip(),)
            ages = demographics.get(person, [])
            if (person_counts[person] == 1 and len(ages) == 1 and
                    ages[0].isdigit() and int(ages[0]) >= 18 and positive(row['wages_salaries'])):
                eligible.append(row)
        # Reproducible demo sample. One person per household prevents repeated
        # household expenditure being interpreted as independent observations.
        random.Random(2019).shuffle(eligible)
        selected = []
        seen = set()
        for row in eligible:
            if key(row) not in seen:
                selected.append(row)
                seen.add(key(row))
            if len(selected) == 100:
                break
        if len(selected) != 100:
            raise ValueError('Fewer than 100 eligible distinct households')
        aliases = {key(row): f'HIES19-{i:04d}' for i, row in enumerate(selected, 1)}
        debt = defaultdict(list)
        for row in rows(archive, 'SEC_6_B_DEBTNESS_25%.CSV'):
            if key(row) in aliases:
                debt[key(row)].append(row)
        sample = []
        for row in selected:
            matches = debt.get(key(row), [])
            if len(matches) != 1:
                raise ValueError('Selected household has missing or ambiguous debt record')
            record = {'SampleID': aliases[key(row)], 'SurveyYear': 2019,
                      'SurveyMonth': int(row['month']),
                      'WagesSalariesReported': row['wages_salaries'].strip(),
                      'AllowancesReported': row['allowences'].strip(),
                      'BonusReported': row['bonus'].strip(),
                      'IncomePrimarySecondaryCode': row['pri_sec'].strip()}
            for field in DEBT:
                record['Household_' + field + '_reported'] = matches[0][field].strip()
            sample.append(record)
        expenses = []
        for filename, category, code, value, inkind in (
            ('SEC_4_1_FOOD_EXP_25%.CSV', 'food', 'code', 'value', 'inkind_value'),
            ('SEC_4_2_NONFOOD_25%.CSV', 'nonfood', 'nf_code', 'nf_value', 'nf_inkind_value'),
        ):
            for row in rows(archive, filename):
                if key(row) in aliases:
                    expenses.append({'SampleID': aliases[key(row)], 'Scope': 'household',
                                     'Category': category, 'ItemCode': row[code].strip(),
                                     'ValueReported': row[value].strip(),
                                     'InKindValueReported': row[inkind].strip()})
        assert len(sample) == len({r['SampleID'] for r in sample}) == 100
        assert {r['SampleID'] for r in expenses} == {r['SampleID'] for r in sample}
        assert not set(HH).intersection(sample[0])
        output.mkdir(parents=True, exist_ok=True)
        write_csv(output / 'wage_earners_100.csv', sample, list(sample[0]))
        write_csv(output / 'household_expenses.csv', expenses, list(expenses[0]))
        manifest = {
            'source_file': args.source.name,
            'source_sha256': hashlib.sha256(args.source.read_bytes()).hexdigest(),
            'sample_count': len(sample), 'households': len(aliases),
            'expense_rows': len(expenses), 'eligible_income_rows': len(eligible),
            'seed': 2019, 'survey_year': 2019,
            'selection': 'Shuffle eligible adult positive-wage recipients with unique person income/demographic matches; take first person from each of 100 distinct households.',
            'missing_values': 'Blank source values remain blank, not zero.',
            'scope': 'Income is person-level; debt and expenses are household-level.',
            'periods': 'Raw source reporting periods retained; monthly conversion not verified or performed.',
            'not_available': ['tenure', 'performance', 'job satisfaction', 'promotions', 'attrition'],
            'integration': 'Separate private research sample, not uploaded, not joined to synthetic HR, no EESI score calculated.',
            'sources': ['https://nada.statistics.gov.lk/index.php/catalog/476/data-dictionary'],
        }
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'sample_count': len(sample), 'expense_rows': len(expenses), 'output': str(output)}))


if __name__ == '__main__':
    main()
