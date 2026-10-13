from unittest.mock import patch

import frappe

from erpnext.setup.doctype.designation.test_designation import create_designation
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.appraisal_cycle.test_appraisal_cycle import create_appraisal_cycle
from hrms.hr.doctype.appraisal_template.test_appraisal_template import create_appraisal_template
from hrms.hr.doctype.employee_performance_feedback.test_employee_performance_feedback import (
	create_performance_feedback,
)
from hrms.hr.report.appraisal_overview.appraisal_overview import execute, get_data
from hrms.tests.test_utils import create_company
from hrms.tests.utils import HRMSTestSuite


class TestAppraisalOverview(HRMSTestSuite):
	def setUp(self):
		self.company = create_company("_Test Appraisal").name

		engineer = create_designation(designation_name="Engineer")
		engineer.appraisal_template = create_appraisal_template().name
		engineer.save()

		consultant = create_designation(designation_name="Consultant")
		consultant.appraisal_template = create_appraisal_template("Consultant").name
		consultant.save()

		self.employee1 = make_employee("employee1@example.com", company=self.company, designation="Engineer")
		self.employee2 = make_employee(
			"employee3@example.com", company=self.company, designation="Consultant"
		)
		self.reviewer = make_employee("reviewer@example.com", company=self.company, designation="Engineer")

	def test_appraisal_overview(self):
		cycle = create_appraisal_cycle(kra_evaluation_method="Manual Rating")
		cycle.create_appraisals()

		appraisal = frappe.get_doc("Appraisal", {"employee": self.employee1})
		appraisal = frappe.get_doc("Appraisal", appraisal.name)

		self.create_appraisal_data(appraisal)
		report = execute()
		data = report[1]

		expected_data = {
			"employee": self.employee1,
			"employee_name": appraisal.employee_name,
			"designation": appraisal.designation,
			"department": appraisal.department,
			"appraisal_cycle": cycle.name,
			"appraisal": appraisal.name,
			"avg_feedback_score": 3.85,
			"goal_score": 3.6,
			"self_score": 3.85,
			"final_score": 3.77,
			"feedback_count": 1,
		}

		self.assertEqual(len(data), 3)
		self.assertEqual(data[0], expected_data)

	def test_appraisal_filters(self):
		cycle = create_appraisal_cycle(kra_evaluation_method="Manual Rating")
		cycle.create_appraisals()

		report = execute({"designation": "Consultant"})
		data = report[1]

		self.assertEqual(len(data), 1)
		self.assertEqual(data[0].employee, self.employee2)

	def test_feedback_counts(self):
		cycle = create_appraisal_cycle(kra_evaluation_method="Manual Rating")
		cycle.create_appraisals()
		appraisals = dict(
			frappe.get_all(
				"Appraisal",
				filters={"appraisal_cycle": cycle.name},
				fields=["employee", "name"],
				as_list=True,
			)
		)

		for _ in range(2):
			create_performance_feedback(self.employee1, self.reviewer, appraisals[self.employee1]).submit()
		create_performance_feedback(self.employee1, self.reviewer, appraisals[self.employee1])
		cancelled = create_performance_feedback(self.employee1, self.reviewer, appraisals[self.employee1])
		cancelled.submit()
		cancelled.cancel()
		create_performance_feedback(self.employee2, self.reviewer, appraisals[self.employee2]).submit()

		with patch.object(frappe.db, "sql", wraps=frappe.db.sql) as sql:
			data = get_data({"appraisal_cycle": cycle.name})
		self.assertEqual(sql.call_count, 2, sql.call_args_list)

		self.assertEqual(
			{row.employee: row.feedback_count for row in data},
			{self.employee1: 2, self.employee2: 1, self.reviewer: 0},
		)

		with patch.object(frappe.db, "sql", wraps=frappe.db.sql) as sql:
			data = get_data({"appraisal_cycle": cycle.name, "employee": self.employee2})
		self.assertEqual(sql.call_count, 2, sql.call_args_list)
		self.assertEqual(len(data), 1)
		self.assertEqual(data[0].feedback_count, 1)

	def test_empty_appraisal_overview(self):
		with patch.object(frappe.db, "sql", wraps=frappe.db.sql) as sql:
			data = get_data({"appraisal_cycle": "_Test Missing Appraisal Cycle"})
		self.assertEqual(sql.call_count, 1, sql.call_args_list)
		self.assertEqual(data, [])

	def create_appraisal_data(self, appraisal):
		# GOAL SCORE
		appraisal.goals[0].score = 5  # 30% weightage
		appraisal.goals[1].score = 3  # 70% weightage

		# SELF APPRAISAL SCORE
		ratings = appraisal.self_ratings
		ratings[0].rating = 0.8  # 70% weightage
		ratings[1].rating = 0.7  # 30% weightage

		appraisal.save()

		# FEEDBACK SCORE
		feedback = create_performance_feedback(
			self.employee1,
			self.reviewer,
			appraisal.name,
		)
		ratings = feedback.feedback_ratings
		ratings[0].rating = 0.8  # 70% weightage
		ratings[1].rating = 0.7  # 30% weightage
		feedback.submit()
