# hrms/tests/test_kpi_engine.py

import unittest
from unittest.mock import patch, MagicMock
from datetime import date

# Mock the frappe module before importing the kpi_engine
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
mock_frappe = MagicMock()
mock_frappe_utils = MagicMock()
sys.modules['frappe'] = mock_frappe
sys.modules['frappe.utils'] = mock_frappe_utils

# Now import the module under test
from hrms.utils.kpi_engine import calculate_and_store_kpis_for_period
from frappe.utils import getdate

def simple_getdate(d_str):
    if isinstance(d_str, date):
        return d_str
    return date.fromisoformat(str(d_str).split(" ")[0])

mock_frappe_utils.getdate.side_effect = simple_getdate

class TestKPIEngine(unittest.TestCase):
    def setUp(self):
        mock_frappe.reset_mock()
        mock_frappe.get_all.side_effect = None
        mock_frappe.new_doc.return_value = MagicMock()

    def test_kpi_calculation(self):
        # --- Mock Data ---
        employees = [{"name": "EMP-001"}]
        completed_tasks = [
            {
                "name": "TASK-001",
                "due_date": getdate("2025-09-15"),
                "completion_date": getdate("2025-09-10"), # Completed on time
                "estimated_time": 10.0,
                "actual_time": 8.0
            },
            {
                "name": "TASK-002",
                "due_date": getdate("2025-09-15"),
                "completion_date": getdate("2025-09-20"), # Completed late
                "estimated_time": 5.0,
                "actual_time": 10.0
            }
        ]

        # --- Configure Mocks ---
        def get_all_side_effect(doctype, *args, **kwargs):
            if doctype == "Employee":
                return employees
            if doctype == "Task":
                return completed_tasks
            return []
        mock_frappe.get_all.side_effect = get_all_side_effect

        mock_kpi_docs = []
        def new_doc_side_effect(doctype):
            if doctype == "KPI Value":
                mock_doc = MagicMock()
                mock_kpi_docs.append(mock_doc)
                return mock_doc
        mock_frappe.new_doc.side_effect = new_doc_side_effect

        # --- Call the function ---
        calculate_and_store_kpis_for_period(period_start="2025-09-01", period_end="2025-09-30")

        # --- Assertions ---
        self.assertEqual(len(mock_kpi_docs), 3) # 3 KPIs were created

        # Find the specific KPI docs for easier assertion
        kpi_values = {doc.kpi_name: doc.value for doc in mock_kpi_docs}

        self.assertEqual(kpi_values["Task Completion Count"], 2)
        self.assertEqual(kpi_values["On-Time Delivery %"], 50.0)
        self.assertAlmostEqual(kpi_values["Effort Accuracy"], 83.33, places=2)

        # Check that insert was called for each doc
        for doc in mock_kpi_docs:
            doc.insert.assert_called_once()

        mock_frappe.db.commit.assert_called_once()

if __name__ == '__main__':
    unittest.main()
