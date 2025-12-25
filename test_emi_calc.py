import unittest
import pandas as pd
import numpy as np
from emi_calc import calculate_emi_value, calculate_tenure_value, generate_amortization_schedule

class TestEMICalculator(unittest.TestCase):

    def test_calculate_emi_value(self):
        # Principal = 500,000, Rate = 8.5%, Tenure = 5 years
        # Expected EMI approx 10,258.38
        principal = 500000
        rate = 8.5
        tenure = 5
        emi = calculate_emi_value(principal, rate, tenure)
        self.assertAlmostEqual(emi, 10258.38, places=2)

    def test_calculate_tenure_value(self):
        # Principal = 500,000, Rate = 8.5%, EMI = 10,258.38
        # Expected Tenure approx 60 months
        principal = 500000
        rate = 8.5
        emi = 10258.38
        months = calculate_tenure_value(principal, rate, emi)
        self.assertAlmostEqual(months, 60, delta=0.1)

    def test_generate_amortization_schedule(self):
        principal = 10000
        rate = 10
        emi = 1000 # High EMI to pay off quickly
        # Approx 10-11 months
        
        # Calculate expected months first
        months = calculate_tenure_value(principal, rate, emi)
        
        df, total_interest = generate_amortization_schedule(principal, rate, emi, months)
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(len(df) > 0)
        # Final balance should be 0
        self.assertEqual(df.iloc[-1]["Remaining Balance"], "0.00")

    def test_zero_interest_rate(self):
        principal = 12000
        rate = 0
        tenure = 1
        emi = calculate_emi_value(principal, rate, tenure)
        self.assertEqual(emi, 1000)

if __name__ == '__main__':
    unittest.main()
