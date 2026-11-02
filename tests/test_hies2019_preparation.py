"""Public synthetic checks; no HIES microdata are committed."""
import importlib.util
from decimal import Decimal
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / 'scripts/clean_hies2019_eesi.py'
spec = importlib.util.spec_from_file_location('clean_hies2019', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class HiesPreparationTests(unittest.TestCase):
    def test_reporting_period_boundaries(self):
        self.assertEqual(module.monthly_factor('food', '101')[0], Decimal(52) / 12)
        for code in ('3001', '3041', '3061', '3101', '3201'):
            self.assertEqual(module.monthly_factor('nonfood', code)[0], Decimal(1) / 6)
        for code in ('2421', '2422', '2609', '2613', '3301', '3339', '3501'):
            self.assertEqual(module.monthly_factor('nonfood', code)[0], Decimal(1) / 12)
        for code in ('2001', '2101', '2608', '3341', '3342', '3405'):
            self.assertEqual(module.monthly_factor('nonfood', code)[0], Decimal(1))

    def test_unknown_period_is_rejected(self):
        for category, code in (('nonfood', '3340'), ('food', '3405'), ('other', '2001')):
            with self.assertRaises(ValueError):
                module.monthly_factor(category, code)

    def test_missing_is_distinct_from_zero(self):
        self.assertIsNone(module.number(' '))
        self.assertEqual(module.number('0'), Decimal(0))
        for value in ('nan', 'inf', '-1', 'unknown'):
            with self.assertRaises(ValueError):
                module.number(value)

    def test_year_rollover_and_invalid_month(self):
        self.assertEqual(module.prior_month(2019, 1), '2018-12')
        self.assertEqual(module.prior_month(2019, 4), '2019-03')
        with self.assertRaises(ValueError):
            module.prior_month(2019, 13)


if __name__ == '__main__':
    unittest.main()
