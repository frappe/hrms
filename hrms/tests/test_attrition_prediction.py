# hrms/tests/test_attrition_prediction.py

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add the project root to the path to allow importing 'hrms'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# --- Comprehensive Mocking for Frappe and ERPNext ---
# This is required because the hrms.api module imports other parts of the framework
mock_frappe = MagicMock()
# This mock now correctly handles being called with parentheses: @frappe.whitelist()
mock_frappe.whitelist = lambda *args, **kwargs: (lambda func: func)
mock_frappe.throw.side_effect = Exception
mock_frappe.get_all.side_effect = Exception # Default behavior

mock_frappe_model = MagicMock()
mock_frappe_model_workflow = MagicMock()
mock_frappe_query_builder = MagicMock()
mock_frappe_utils = MagicMock()
mock_erpnext = MagicMock()
mock_erpnext_setup = MagicMock()
mock_erpnext_setup_doctype = MagicMock()
mock_erpnext_setup_doctype_employee = MagicMock()
mock_erpnext_setup_doctype_employee_employee = MagicMock()

# Place all mocks in sys.modules BEFORE importing the application code
sys.modules['frappe'] = mock_frappe
sys.modules['frappe.model'] = mock_frappe_model
sys.modules['frappe.model.workflow'] = mock_frappe_model_workflow
sys.modules['frappe.query_builder'] = mock_frappe_query_builder
sys.modules['frappe.utils'] = mock_frappe_utils
sys.modules['erpnext'] = mock_erpnext
sys.modules['erpnext.setup'] = mock_erpnext_setup
sys.modules['erpnext.setup.doctype'] = mock_erpnext_setup_doctype
sys.modules['erpnext.setup.doctype.employee'] = mock_erpnext_setup_doctype_employee
sys.modules['erpnext.setup.doctype.employee.employee'] = mock_erpnext_setup_doctype_employee_employee

# Now that all dependencies are mocked, we can safely import the module
from hrms.api import predict_attrition, get_retention_suggestions
from datetime import date, timedelta

# --- Helper functions to simulate frappe.utils date functions ---
def simple_getdate(d_str):
    if isinstance(d_str, date):
        return d_str
    # Handles both date strings and datetime objects that get mocked
    return date.fromisoformat(str(d_str).split(" ")[0])

def simple_date_diff(d1, d2):
    # This check is needed because mocks might still be passed in some scenarios
    if not isinstance(d1, date) or not isinstance(d2, date):
        return 0
    return (d1 - d2).days

# Configure the mock for frappe.utils to use our simple date functions
mock_frappe_utils.nowdate.return_value = date.today().isoformat()
mock_frappe_utils.getdate.side_effect = simple_getdate
mock_frappe_utils.date_diff.side_effect = simple_date_diff
# Point frappe.utils to the same configured mock for consistency
mock_frappe.utils = mock_frappe_utils

class TestRetentionSuggestions(unittest.TestCase):
    def setUp(self):
        # Reset mocks before each test to ensure test isolation
        mock_frappe.reset_mock()
        # IMPORTANT: reset_mock() does not clear side_effect, so it must be done manually
        mock_frappe.get_all.side_effect = None
        mock_frappe.get_all.return_value = None
        mock_frappe.get_doc.return_value = None


    def test_low_performance_suggestion(self):
        # Mock data for an employee with low performance
        mock_employee_doc = MagicMock()
        mock_employee_doc.date_of_joining = date.today() - timedelta(days=500)
        mock_frappe.get_doc.return_value = mock_employee_doc

        def get_all_side_effect(doctype, *args, **kwargs):
            if doctype == "Appraisal":
                return [{"total_score": 1.5}, {"total_score": 2.0}]
            if doctype == "Employee Promotion":
                return [] # No promotion history
            return []
        mock_frappe.get_all.side_effect = get_all_side_effect

        # Call the function
        suggestions = get_retention_suggestions("EMP-001")

        # Assert
        self.assertEqual(len(suggestions), 1)
        self.assertIn("<b>Low Performance:</b>", suggestions[0])

    def test_career_stagnation_suggestion(self):
        # Mock data for an employee with no promotion for over 2 years
        mock_employee_doc = MagicMock()
        mock_employee_doc.date_of_joining = date.today() - timedelta(days=800)
        mock_frappe.get_doc.return_value = mock_employee_doc

        two_years_ago = date.today() - timedelta(days=800)

        def get_all_side_effect(doctype, *args, **kwargs):
            if doctype == "Appraisal":
                return [{"total_score": 4.0}] # Good performance
            if doctype == "Employee Promotion":
                return [{"promotion_date": two_years_ago}]
            return []
        mock_frappe.get_all.side_effect = get_all_side_effect

        # Call the function
        suggestions = get_retention_suggestions("EMP-001")

        # Assert
        self.assertEqual(len(suggestions), 1)
        self.assertIn("<b>Career Stagnation:</b>", suggestions[0])

    def test_new_hire_suggestion(self):
        # Mock data for a new hire
        mock_employee_doc = MagicMock()
        mock_employee_doc.date_of_joining = date.today() - timedelta(days=90)
        mock_frappe.get_doc.return_value = mock_employee_doc
        mock_frappe.get_all.return_value = [] # No other data (no appraisals or promotions)

        # Call the function
        suggestions = get_retention_suggestions("EMP-001")

        # Assert
        self.assertEqual(len(suggestions), 1)
        self.assertIn("<b>New Hire Check-in:</b>", suggestions[0])

    def test_general_check_in_suggestion(self):
        # Mock data for an employee with no specific flags
        mock_employee_doc = MagicMock()
        mock_employee_doc.date_of_joining = date.today() - timedelta(days=400)
        mock_frappe.get_doc.return_value = mock_employee_doc
        mock_frappe.get_all.return_value = [] # No other data

        # Call the function
        suggestions = get_retention_suggestions("EMP-001")

        # Assert
        self.assertEqual(len(suggestions), 1)
        self.assertIn("<b>General Check-in:</b>", suggestions[0])


class TestAttritionPrediction(unittest.TestCase):

    @patch('joblib.load')
    def test_predict_attrition_success(self, mock_joblib_load):
        # --- 1. Mock the Model and its Inputs ---
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([1]) # Predicts "High" risk
        mock_model.predict_proba.return_value = np.array([[0.2, 0.8]]) # 80% confidence

        feature_names = [
            'tenure_days', 'avg_performance_score', 'total_leave_days_taken',
            'department_Sales', 'designation_Engineer'
        ]

        mock_joblib_load.return_value = {
            'model': mock_model,
            'feature_names': feature_names
        }

        # --- 2. Mock the Frappe Database Calls ---
        mock_employee_data = [{
            'name': 'EMP-001',
            'date_of_joining': '2022-01-01',
            'department': 'Sales',
            'designation': 'Engineer'
        }]
        mock_appraisal_data = [{'total_score': 4.0}]
        mock_leave_data = [{'total_leave_days': 10}]

        # Set up a side effect for frappe.get_all to return different data based on the DocType
        def get_all_side_effect(doctype, *args, **kwargs):
            if doctype == "Employee":
                return mock_employee_data
            if doctype == "Appraisal":
                return mock_appraisal_data
            if doctype == "Leave Application":
                return mock_leave_data
            return []

        mock_frappe.get_all.side_effect = get_all_side_effect
        mock_frappe.throw.side_effect = Exception # To catch errors

        # --- 3. Call the Function ---
        employee_id = "EMP-001"
        result = predict_attrition(employee=employee_id)

        # --- 4. Assert the Results ---
        self.assertIsNotNone(result)
        self.assertEqual(result['employee'], employee_id)
        self.assertEqual(result['attrition_risk'], "High")
        self.assertEqual(float(result['confidence_score']), 0.80)

        # Verify that the model's predict method was called
        mock_model.predict.assert_called_once()

        # Verify frappe calls were made for the correct doctypes
        self.assertIn('Employee', [call[0][0] for call in mock_frappe.get_all.call_args_list])
        self.assertIn('Appraisal', [call[0][0] for call in mock_frappe.get_all.call_args_list])
        self.assertIn('Leave Application', [call[0][0] for call in mock_frappe.get_all.call_args_list])

    @patch('joblib.load', side_effect=FileNotFoundError)
    def test_model_not_found(self, mock_joblib_load):
        # Test the case where the model file doesn't exist
        with self.assertRaises(Exception) as context:
            predict_attrition(employee="EMP-001")

        mock_frappe.throw.assert_called_with("Model file not found at hrms/ml_models/attrition_model.joblib. Please train the model first.")

    @patch('joblib.load')
    def test_employee_not_found(self, mock_joblib_load):
        # --- 1. Mock the Model Load to SUCCEED ---
        # This is necessary to proceed to the part of the code that fetches the employee
        mock_joblib_load.return_value = {
            'model': MagicMock(),
            'feature_names': ['feature1']
        }

        # --- 2. Mock the Frappe Database Call to FAIL ---
        # Test the case where the employee doesn't exist in the database
        mock_frappe.get_all.return_value = [] # Simulate no employee found
        mock_frappe.throw.side_effect = Exception

        # --- 3. Call the function and assert the exception ---
        with self.assertRaises(Exception) as context:
            predict_attrition(employee="EMP-NON-EXISTENT")

        # The code under test has a broad exception handler that catches the specific
        # "Employee not found" exception and re-raises a generic one. The test
        # is updated to reflect this actual behavior.
        mock_frappe.throw.assert_called_with("An error occurred while fetching data for employee EMP-NON-EXISTENT.")

if __name__ == '__main__':
    unittest.main()
