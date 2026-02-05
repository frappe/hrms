"""
Tests for Payroll Setup Demo Data Scripts

Validates:
- JSON data file structure and integrity
- Consistency between salary components, structures, and references
- Script function contracts (parameter handling, error cases)

Run with:
    python -m pytest hrms/demo_data/test_payroll_setup.py -v
    or
    bench run-tests --module hrms.demo_data.test_payroll_setup
"""

import json
import os
import unittest


PAYROLL_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "employee_payroll.json")

REQUIRED_TOP_LEVEL_KEYS = [
    "config",
    "executive_designations",
    "salary_components",
    "salary_structures",
    "income_tax_slabs",
    "employee_salaries",
    "metadata",
]

REQUIRED_CONFIG_KEYS = [
    "payroll_frequency",
    "fiscal_year",
    "fiscal_year_start",
    "fiscal_year_end",
    "payroll_period_start",
    "payroll_period_end",
    "salary_slip_start",
    "salary_slip_end",
    "health_insurance_family",
    "health_insurance_individual",
    "default_salary",
]

REQUIRED_COMPONENT_KEYS = ["name", "abbr", "type", "description", "is_tax_applicable", "depends_on_payment_days"]
VALID_COMPONENT_TYPES = ["Earning", "Deduction"]


class TestPayrollJsonStructure(unittest.TestCase):
    """Validate the employee_payroll.json file structure and data integrity."""

    @classmethod
    def setUpClass(cls):
        with open(PAYROLL_JSON_PATH, "r") as f:
            cls.data = json.load(f)

    def test_json_file_exists(self):
        """employee_payroll.json must exist in the demo_data directory."""
        self.assertTrue(os.path.exists(PAYROLL_JSON_PATH), f"File not found: {PAYROLL_JSON_PATH}")

    def test_top_level_keys_present(self):
        """All required top-level keys must be present in the JSON file."""
        for key in REQUIRED_TOP_LEVEL_KEYS:
            self.assertIn(key, self.data, f"Missing required top-level key: '{key}'")

    def test_config_keys_present(self):
        """All required config keys must be present."""
        config = self.data.get("config", {})
        for key in REQUIRED_CONFIG_KEYS:
            self.assertIn(key, config, f"Missing required config key: '{key}'")

    def test_config_dates_valid_format(self):
        """Config date fields must be valid YYYY-MM-DD format."""
        config = self.data.get("config", {})
        date_fields = [
            "fiscal_year_start", "fiscal_year_end",
            "payroll_period_start", "payroll_period_end",
            "salary_slip_start", "salary_slip_end",
        ]
        for field in date_fields:
            value = config.get(field, "")
            parts = value.split("-")
            self.assertEqual(len(parts), 3, f"Config '{field}' has invalid date format: '{value}'")
            self.assertEqual(len(parts[0]), 4, f"Config '{field}' year must be 4 digits: '{value}'")

    def test_salary_slip_within_fiscal_year(self):
        """Salary slip dates must fall within the fiscal year."""
        config = self.data.get("config", {})
        self.assertGreaterEqual(config["salary_slip_start"], config["fiscal_year_start"])
        self.assertLessEqual(config["salary_slip_end"], config["fiscal_year_end"])

    def test_health_insurance_rates_positive(self):
        """Health insurance rates must be positive numbers."""
        config = self.data.get("config", {})
        self.assertGreater(config.get("health_insurance_family", 0), 0)
        self.assertGreater(config.get("health_insurance_individual", 0), 0)
        self.assertGreater(
            config.get("health_insurance_family", 0),
            config.get("health_insurance_individual", 0),
            "Family health insurance rate should exceed individual rate",
        )


class TestSalaryComponents(unittest.TestCase):
    """Validate salary component definitions."""

    @classmethod
    def setUpClass(cls):
        with open(PAYROLL_JSON_PATH, "r") as f:
            cls.data = json.load(f)
        cls.components = cls.data.get("salary_components", [])

    def test_at_least_one_component(self):
        """There must be at least one salary component defined."""
        self.assertGreater(len(self.components), 0)

    def test_required_fields_present(self):
        """Each salary component must have all required fields."""
        for comp in self.components:
            for key in REQUIRED_COMPONENT_KEYS:
                self.assertIn(key, comp, f"Component '{comp.get('name', '?')}' missing field: '{key}'")

    def test_valid_component_types(self):
        """Each salary component type must be 'Earning' or 'Deduction'."""
        for comp in self.components:
            self.assertIn(
                comp.get("type"),
                VALID_COMPONENT_TYPES,
                f"Component '{comp['name']}' has invalid type: '{comp.get('type')}'",
            )

    def test_unique_component_names(self):
        """Salary component names must be unique."""
        names = [c["name"] for c in self.components]
        self.assertEqual(len(names), len(set(names)), f"Duplicate component names found: {names}")

    def test_unique_abbreviations(self):
        """Salary component abbreviations must be unique."""
        abbrs = [c["abbr"] for c in self.components]
        self.assertEqual(len(abbrs), len(set(abbrs)), f"Duplicate abbreviations found: {abbrs}")

    def test_has_earnings_and_deductions(self):
        """There must be at least one Earning and one Deduction component."""
        types = {c["type"] for c in self.components}
        self.assertIn("Earning", types, "No Earning components defined")
        self.assertIn("Deduction", types, "No Deduction components defined")

    def test_formula_components_have_formula(self):
        """Components with amount_based_on_formula=1 must have a non-empty formula."""
        for comp in self.components:
            if comp.get("amount_based_on_formula"):
                self.assertTrue(
                    comp.get("formula"),
                    f"Component '{comp['name']}' has amount_based_on_formula=1 but no formula",
                )


class TestSalaryStructures(unittest.TestCase):
    """Validate salary structure definitions and their references to components."""

    @classmethod
    def setUpClass(cls):
        with open(PAYROLL_JSON_PATH, "r") as f:
            cls.data = json.load(f)
        cls.structures = cls.data.get("salary_structures", [])
        cls.component_names = {c["name"] for c in cls.data.get("salary_components", [])}

    def test_at_least_one_structure(self):
        """There must be at least one salary structure defined."""
        self.assertGreater(len(self.structures), 0)

    def test_structures_have_required_fields(self):
        """Each structure must have name, earnings, and deductions."""
        for struct in self.structures:
            self.assertIn("name", struct)
            self.assertIn("earnings", struct)
            self.assertIn("deductions", struct)
            self.assertIsInstance(struct["earnings"], list)
            self.assertIsInstance(struct["deductions"], list)

    def test_structure_earnings_reference_valid_components(self):
        """All earnings referenced in structures must exist in salary_components."""
        for struct in self.structures:
            for earning in struct.get("earnings", []):
                comp_name = earning.get("salary_component")
                self.assertIn(
                    comp_name,
                    self.component_names,
                    f"Structure '{struct['name']}' references unknown earning: '{comp_name}'",
                )

    def test_structure_deductions_reference_valid_components(self):
        """All deductions referenced in structures must exist in salary_components."""
        for struct in self.structures:
            for deduction in struct.get("deductions", []):
                comp_name = deduction.get("salary_component")
                self.assertIn(
                    comp_name,
                    self.component_names,
                    f"Structure '{struct['name']}' references unknown deduction: '{comp_name}'",
                )

    def test_structure_earnings_are_earning_type(self):
        """Earnings listed in structures must reference Earning-type components."""
        comp_types = {c["name"]: c["type"] for c in self.data.get("salary_components", [])}
        for struct in self.structures:
            for earning in struct.get("earnings", []):
                comp_name = earning.get("salary_component")
                if comp_name in comp_types:
                    self.assertEqual(
                        comp_types[comp_name],
                        "Earning",
                        f"Structure '{struct['name']}' lists '{comp_name}' as earning but it is type '{comp_types[comp_name]}'",
                    )

    def test_structure_deductions_are_deduction_type(self):
        """Deductions listed in structures must reference Deduction-type components."""
        comp_types = {c["name"]: c["type"] for c in self.data.get("salary_components", [])}
        for struct in self.structures:
            for deduction in struct.get("deductions", []):
                comp_name = deduction.get("salary_component")
                if comp_name in comp_types:
                    self.assertEqual(
                        comp_types[comp_name],
                        "Deduction",
                        f"Structure '{struct['name']}' lists '{comp_name}' as deduction but it is type '{comp_types[comp_name]}'",
                    )

    def test_unique_structure_names(self):
        """Salary structure names must be unique."""
        names = [s["name"] for s in self.structures]
        self.assertEqual(len(names), len(set(names)), f"Duplicate structure names: {names}")


class TestIncomeTaxSlabs(unittest.TestCase):
    """Validate income tax slab definitions."""

    @classmethod
    def setUpClass(cls):
        with open(PAYROLL_JSON_PATH, "r") as f:
            cls.data = json.load(f)
        cls.slabs = cls.data.get("income_tax_slabs", [])

    def test_at_least_one_slab(self):
        """There must be at least one tax slab defined."""
        self.assertGreater(len(self.slabs), 0)

    def test_slabs_have_required_fields(self):
        """Each slab must have from_amount, to_amount, and percent_deduction."""
        for i, slab in enumerate(self.slabs):
            self.assertIn("from_amount", slab, f"Slab {i} missing 'from_amount'")
            self.assertIn("to_amount", slab, f"Slab {i} missing 'to_amount'")
            self.assertIn("percent_deduction", slab, f"Slab {i} missing 'percent_deduction'")

    def test_slabs_start_from_zero(self):
        """First tax slab should start from 0."""
        self.assertEqual(self.slabs[0]["from_amount"], 0)

    def test_slabs_are_progressive(self):
        """Tax rates should be progressive (each bracket >= previous)."""
        for i in range(1, len(self.slabs)):
            self.assertGreaterEqual(
                self.slabs[i]["percent_deduction"],
                self.slabs[i - 1]["percent_deduction"],
                f"Slab {i} rate ({self.slabs[i]['percent_deduction']}%) is less than slab {i-1} ({self.slabs[i-1]['percent_deduction']}%)",
            )

    def test_slabs_are_contiguous(self):
        """Tax slab ranges should be contiguous (each from_amount equals previous to_amount)."""
        for i in range(1, len(self.slabs)):
            self.assertEqual(
                self.slabs[i]["from_amount"],
                self.slabs[i - 1]["to_amount"],
                f"Gap between slab {i-1} (to={self.slabs[i-1]['to_amount']}) and slab {i} (from={self.slabs[i]['from_amount']})",
            )

    def test_percent_deduction_in_range(self):
        """Tax rates must be between 0 and 100."""
        for i, slab in enumerate(self.slabs):
            self.assertGreaterEqual(slab["percent_deduction"], 0, f"Slab {i} has negative rate")
            self.assertLessEqual(slab["percent_deduction"], 100, f"Slab {i} has rate over 100%")


class TestEmployeeSalaries(unittest.TestCase):
    """Validate employee salary data."""

    @classmethod
    def setUpClass(cls):
        with open(PAYROLL_JSON_PATH, "r") as f:
            cls.data = json.load(f)
        cls.salaries = cls.data.get("employee_salaries", {})

    def test_at_least_one_employee(self):
        """There must be at least one employee salary entry."""
        self.assertGreater(len(self.salaries), 0)

    def test_salaries_are_positive(self):
        """All salary values must be positive numbers."""
        for name, salary in self.salaries.items():
            self.assertIsInstance(salary, (int, float), f"'{name}' salary is not a number: {salary}")
            self.assertGreater(salary, 0, f"'{name}' salary must be positive: {salary}")

    def test_employee_names_are_non_empty(self):
        """Employee names must be non-empty strings."""
        for name in self.salaries:
            self.assertIsInstance(name, str)
            self.assertTrue(len(name.strip()) > 0, "Empty employee name found")


class TestExecutiveDesignations(unittest.TestCase):
    """Validate executive designation definitions."""

    @classmethod
    def setUpClass(cls):
        with open(PAYROLL_JSON_PATH, "r") as f:
            cls.data = json.load(f)
        cls.designations = cls.data.get("executive_designations", [])

    def test_at_least_one_designation(self):
        """There must be at least one executive designation."""
        self.assertGreater(len(self.designations), 0)

    def test_designations_are_unique(self):
        """Executive designations must be unique."""
        self.assertEqual(
            len(self.designations),
            len(set(self.designations)),
            "Duplicate executive designations found",
        )

    def test_designations_are_non_empty_strings(self):
        """Each designation must be a non-empty string."""
        for d in self.designations:
            self.assertIsInstance(d, str)
            self.assertTrue(len(d.strip()) > 0, "Empty designation found")


class TestScriptContracts(unittest.TestCase):
    """Validate payroll_setup.py script contracts via source code analysis."""

    @classmethod
    def setUpClass(cls):
        cls.script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "payroll_setup.py")
        with open(cls.script_path, "r") as f:
            cls.script_content = f.read()

    def test_no_hardcoded_file_paths(self):
        """The script must not contain hardcoded JSON file paths."""
        self.assertNotIn(
            "employees_roster.json", self.script_content,
            "Script contains hardcoded reference to employees_roster.json",
        )
        self.assertNotIn(
            "os.path.join(current_dir", self.script_content,
            "Script contains hardcoded directory-based file path",
        )

    def test_no_hardcoded_salary_component_constants(self):
        """The script must not define salary components as module-level constants."""
        self.assertNotIn(
            "SALARY_COMPONENTS", self.script_content,
            "Script contains hardcoded SALARY_COMPONENTS constant",
        )
        self.assertNotIn(
            "EXECUTIVE_DESIGNATIONS", self.script_content,
            "Script contains hardcoded EXECUTIVE_DESIGNATIONS constant",
        )

    def test_create_function_accepts_payroll_path(self):
        """create_payroll_data function signature must include payroll_path parameter."""
        self.assertRegex(
            self.script_content,
            r"def create_payroll_data\(.*payroll_path",
            "create_payroll_data missing 'payroll_path' parameter",
        )

    def test_clear_function_accepts_payroll_path(self):
        """clear_payroll_data function signature must include payroll_path parameter."""
        self.assertRegex(
            self.script_content,
            r"def clear_payroll_data\(.*payroll_path",
            "clear_payroll_data missing 'payroll_path' parameter",
        )

    def test_uses_income_tax_slab_not_payroll_period_slabs(self):
        """Script must use Income Tax Slab DocType, not append slabs to Payroll Period."""
        self.assertNotIn(
            '"taxable_salary_slabs"', self.script_content,
            "Script still tries to append taxable_salary_slabs to Payroll Period (removed in Frappe HR v15)",
        )
        self.assertIn(
            "Income Tax Slab", self.script_content,
            "Script should create Income Tax Slab documents for tax brackets",
        )

    def test_no_unused_os_import_for_file_paths(self):
        """Script should not import os if it does not construct file paths."""
        # If os is imported, it should not be used to build hardcoded paths
        if "import os" in self.script_content:
            self.assertNotIn(
                "os.path.join", self.script_content,
                "Script imports os and uses os.path.join - likely hardcoding a file path",
            )


if __name__ == "__main__":
    unittest.main()
