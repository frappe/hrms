"""
Company Setup - Demo Data Generator for HRMS

Author: amezasor
Version: 1.0.1
"""

# import os
# import json
import frappe
from frappe.utils.nestedset import rebuild_tree
from hrms.demo_data.utils import load_data

# from frappe.utils import getdate, add_days, add_months, random_string
# from hrms.tests.test_utils import create_employee_grade

def create_demo_data(company="NovaSoft", abbr="NS", roster_path=None):
	"""
	Create comprehensive demo data for HRMS testing
	Usage: bench --site [sitename] execute hrms.company_setup.create_demo_data
	Or with company: bench --site [sitename] execute hrms.company_setup.create_demo_data --kwargs '{"company": "test1"}'
	"""
	frappe.set_user("Administrator")
	
	print(f"\n{'='*60}")
	print(f"Creating Demo Data for Company: {company}")
	print(f"{'='*60}\n")
	
	# 1 Setup warehouse types (required for company creation)
	print("Setting up Warehouse Types...")
	setup_warehouse_types()
	frappe.db.commit()

	# 2 Create basic doctypes (Holiday List, Shifts, Insurance, Designations)
	print("Setting up Basic DocTypes...")
	add_basic_doctypes()
	frappe.db.commit()

	# 3 Create company if it doesn't exist
	company_name = ensure_company_exists(company, abbr)

	# 4 Set default company
	print("Setting default company...")
	set_default_company(company_name)
	frappe.db.commit()

	# 4 Configure HR Settings (retirement age, etc.)
	print("Configuring HR Settings...")
	configure_hr_settings()
	frappe.db.commit()

	# 5 Configure departments (disable unwanted ones)
	print("Configuring Departments...")
	configure_departments(company_name)
	frappe.db.commit()

	# 6 Load employees roster
	print("Loading employees roster...")
	employees_data = load_data(roster_path, key="employees")

	# 7 Creating Employees
	print("Creating Employees...")
	create_users_and_employees(company_name, employees_data)

	# 8 Create Holiday List Assignments (required in develop branch)
	print("\nCreating Holiday List Assignments...")
	create_holiday_list_assignments(company_name, "US Holidays 2025")
	
	# 8 Update reports_to relationships
	print("\nSetting up reporting hierarchy...")
	update_reports_to(company_name, employees_data)

	# 9 Assign approvers to employees
	print("\nAssigning managers as approvers...")
	assign_approvers_to_employees(company_name)

	# Custom task updates
	print("\nUpdating employee profile...")
	update_employee_profile("derek.miles@novasoft.com") # Derek Miles

	print("\nUpdating employee emergency contact (relation)...")
	update_employee_emergency_contact("emily.santos@novasoft.com") # Emily Santos

	print("\nUpdating employee bank info...")
	update_employee_bank_info("luz.ortega@novasoft.com") # Luz Ortega

# ----------------------COMPANY CONFIG------------------------------------
def ensure_company_exists(company_name, abbr):
	"""Ensure company exists, create if it doesn't"""
	if frappe.db.exists("Company", company_name):
		print(f"✓ Company '{company_name}' already exists\n")
		return company_name
	
	print(f"Creating new company '{company_name}'...")
	
	try:		
		company = frappe.get_doc({
			"doctype": "Company",
			"company_name": company_name, # argument
			"abbr": abbr, # argument
			"default_currency": "USD",
			"country": "United States",
			"is_group": 0,
			"default_holiday_list": "US Holidays 2025", # dependency
			"valuation_method": "FIFO",
			"domain": "Technology",
			"date_of_establishment": "2025-01-01",
			"tax_id": "99-1234567"
		})
		
		company.insert(ignore_permissions=True)
		print(f"  ✓ Created company: {company_name} (abbr: {abbr})\n")
		return company.name
		
	except Exception as e:
		print(f"  ⚠ Error creating company: {str(e)}")
		print(f"  → Will try to use existing company or continue anyway...\n")
		
		# Try to find any existing company
		companies = frappe.get_all("Company", limit=1)
		if companies:
			fallback = companies[0].name
			print(f"  ✓ Using existing company: {fallback}\n")
			return fallback
		
		frappe.db.commit()
		return company_name

def set_default_company(company_name):
	"""Set the company as the default company for the site"""
	try:
		# Set as default in Global Defaults
		global_defaults = frappe.get_single("Global Defaults")
		global_defaults.default_company = company_name
		global_defaults.save(ignore_permissions=True)
		
		# Also set default currency
		frappe.db.set_default("company", company_name)
		frappe.db.set_default("currency", "USD")
		frappe.db.set_default("country", "United States")
		
		print(f"  ✓ Set {company_name} as default company")
		
	except Exception as e:
		print(f"  ⚠ Error setting default company: {str(e)[:60]}")

def configure_hr_settings():
	"""Configure HR Settings - set retirement age and other defaults"""
	try:
		hr_settings = frappe.get_single("HR Settings")
		hr_settings.retirement_age = "65"
		hr_settings.save(ignore_permissions=True)
		print("  ✓ Set retirement age to 65 years")
	except Exception as e:
		print(f"  ⚠ Error configuring HR Settings: {str(e)[:60]}")

# ----------------------FRAMEWORK DOCTYPES------------------------------------
def setup_warehouse_types():
	"""Create basic warehouse types required for company creation"""
	warehouse_types = [
		{"name": "Transit", "description": "Warehouse for goods in transit"},
		{"name": "Default", "description": "Default warehouse type"},
		{"name": "WIP", "description": "Work in Progress warehouse"},
		{"name": "Finished Goods", "description": "Warehouse for finished goods"},
		{"name": "Stores", "description": "Stores warehouse"}
	]
	
	created = []
	for wtype in warehouse_types:
		try:
			if not frappe.db.exists("Warehouse Type", wtype["name"]):
				doc = frappe.get_doc({
					"doctype": "Warehouse Type",
					"name": wtype["name"]
				})
				doc.insert(ignore_permissions=True)
				created.append(wtype["name"])
		except Exception as e:
			pass
	
	if created:
		print(f"  ✓ Created warehouse types: {', '.join(created)}")
	else:
		print(f"  ↻ Warehouse types already exist")
	
	return True

# ----------------------DOCTYPES------------------------------------
def add_basic_doctypes():
	"""Create all basic doctypes required before company setup"""
	print("Creating Basic DocTypes...")
	
	# 1. Create Holiday List
	print("\tCreating Holiday List...")
	create_holiday_list_us()
	
	# 2. Create Employee Health Insurance
	print("\tCreating Employee Health Insurance...")
	create_employee_health_insurance()
	
	# 3. Create Designations
	print("\tCreating Designations...")
	create_all_designations()

	# 4. Create Shift Types (depends on Holiday List)
	print("\tCreating Shift Types...")
	create_shift_types_basic()

	# 5. Create Shift Schedules (depends on Shift Type)
	print("\tCreating Shift Schedules...")
	create_shift_schedules()
	
	# 6. Create Genders
	print("\tCreating Genders...")
	create_genders()

	# 6. Create Employment Types
	# print("\tCreating Employment Types...")
	# create_employment_types()

	# 7. Create Employee Grades
	# print("Creating Employee Grades...")
	# grades = create_employee_grades()
	
	print("Basic DocTypes created successfully!\n")

def create_holiday_list_us():
	"""Create US Holiday List for 2025"""
	holiday_list_name = "US Holidays 2025"
	
	try:
		if frappe.db.exists("Holiday List", holiday_list_name):
			print(f"  ↻ Already exists: {holiday_list_name}")
			return holiday_list_name
		
		holidays = [
			{"holiday_date": "2025-01-01", "description": "New Year's Day", "is_half_day": 0},
			{"holiday_date": "2025-01-20", "description": "Martin Luther King Jr. Day", "is_half_day": 0},
			{"holiday_date": "2025-05-26", "description": "Memorial Day", "is_half_day": 0},
			{"holiday_date": "2025-07-04", "description": "Independence Day", "is_half_day": 0},
			{"holiday_date": "2025-09-01", "description": "Labor Day", "is_half_day": 0},
			{"holiday_date": "2025-11-27", "description": "Thanksgiving Day", "is_half_day": 0},
			{"holiday_date": "2025-11-28", "description": "Day After Thanksgiving", "is_half_day": 0},
			{"holiday_date": "2025-12-24", "description": "Christmas Eve", "is_half_day": 1},
			{"holiday_date": "2025-12-25", "description": "Christmas Day", "is_half_day": 0},
		]
		
		holiday_list = frappe.get_doc({
			"doctype": "Holiday List",
			"holiday_list_name": holiday_list_name,
			"from_date": "2025-01-01",
			"to_date": "2025-12-31",
			"color": "#EC864B",
			"holidays": holidays
		})
		holiday_list.insert(ignore_permissions=True)
		
		print(f"  ✓ Created: {holiday_list_name} with {len(holidays)} holidays")
		return holiday_list_name
		
	except Exception as e:
		print(f"  ⚠ Error creating holiday list: {str(e)[:80]}")
		return None

def create_shift_types_basic():
	"""Create Morning and Evening shift types"""
	shift_data = [
		{"name": "Morning", "start_time": "07:00:00", "end_time": "15:00:00", "holiday_list": "US Holidays 2025"},
		{"name": "Evening", "start_time": "12:00:00", "end_time": "20:00:00", "holiday_list": "US Holidays 2025"},
	]
	
	count = 0
	for shift in shift_data:
		try:
			if frappe.db.exists("Shift Type", shift["name"]):
				print(f"  ↻ Already exists: {shift['name']}")
				continue
			
			shift_type = frappe.get_doc({
				"doctype": "Shift Type",
				"name": shift["name"],
				"start_time": shift["start_time"],
				"end_time": shift["end_time"],
				"holiday_list": shift["holiday_list"]
			})
			shift_type.insert(ignore_permissions=True)
			print(f"  ✓ Created: {shift['name']} ({shift['start_time']} - {shift['end_time']})")
			count += 1
		except Exception as e:
			print(f"  ⚠ Error creating shift {shift['name']}: {str(e)[:60]}")
	
	if count > 0:
		print(f"  ✓ Created {count} shift types")

def create_shift_schedules():
	"""
	Create shift schedules for the company.
	Shift schedules define which days a shift type applies to.
	
	Creates:
	- weekly-morning: Morning shift on Monday-Friday
	- weekend-morning: Morning shift on Saturday-Sunday
	- weekly-evening: Evening shift on Monday-Friday
	"""
	schedule_data = [
		{
			"name": "weekly-morning",
			"shift_type": "Morning",
			"frequency": "Every Week",
			"days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
		},
		{
			"name": "weekend-morning",
			"shift_type": "Morning",
			"frequency": "Every Week",
			"days": ["Saturday", "Sunday"]
		},
		{
			"name": "weekly-evening",
			"shift_type": "Evening",
			"frequency": "Every Week",
			"days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
		},
	]
	
	count = 0
	for schedule in schedule_data:
		try:
			# Check if schedule already exists (by name)
			if frappe.db.exists("Shift Schedule", schedule["name"]):
				print(f"  ↻ Already exists: {schedule['name']}")
				continue
			
			# Verify shift type exists
			if not frappe.db.exists("Shift Type", schedule["shift_type"]):
				print(f"  ⚠ Shift Type '{schedule['shift_type']}' not found, skipping {schedule['name']}")
				continue
			
			# Create the shift schedule document
			doc = frappe.get_doc({
				"doctype": "Shift Schedule",
				"name": schedule["name"],
				"shift_type": schedule["shift_type"],
				"frequency": schedule["frequency"],
				"repeat_on_days": [{"day": day} for day in schedule["days"]]
			})
			
			# Insert (save) the document
			doc.insert(ignore_permissions=True)
			
			# Submit the document (required for shift schedules)
			doc.submit()
			
			print(f"  ✓ Created: {schedule['name']} ({schedule['shift_type']} - {', '.join(schedule['days'])})")
			count += 1
			
		except Exception as e:
			print(f"  ⚠ Error creating schedule {schedule['name']}: {str(e)[:60]}")
	
	if count > 0:
		print(f"  ✓ Created {count} shift schedules")

def create_employee_health_insurance():
	"""Create 3 fictional health insurance providers"""
	insurance_data = [
		{"name": "HI1", "health_insurance_name": "AmeriShield Health Network"},
		{"name": "HI2", "health_insurance_name": "Frontier Family Health"},
		{"name": "HI3", "health_insurance_name": "UnityCare National"},
	]
	
	count = 0
	for ins in insurance_data:
		try:
			if frappe.db.exists("Employee Health Insurance", ins["name"]):
				print(f"  ↻ Already exists: {ins['health_insurance_name']}")
				continue
			
			health_insurance = frappe.get_doc({
				"doctype": "Employee Health Insurance",
				"health_insurance_name": ins["health_insurance_name"]
			})
			health_insurance.insert(ignore_permissions=True)
			print(f"  ✓ Created: {ins['health_insurance_name']}")
			count += 1
		except Exception as e:
			print(f"  ⚠ Error creating insurance {ins['name']}: {str(e)[:60]}")
	
	if count > 0:
		print(f"  ✓ Created {count} health insurance providers")

def create_all_designations():
	"""Create all job title designations"""
	designations_data = [
		# Executive Leadership
		{"designation_name": "Chief Executive Officer (CEO)", "description": "Leads the entire company and sets overall strategic direction."},
		{"designation_name": "Chief Operating Officer (COO)", "description": "Oversees day-to-day operations and cross-functional execution."},
		{"designation_name": "Chief Technology Officer (CTO)", "description": "Leads technology strategy and engineering organizations."},
		{"designation_name": "Chief Financial Officer (CFO)", "description": "Oversees financial strategy, planning, and operations."},
		{"designation_name": "Chief People Officer (CPO)", "description": "Leads HR, talent, and organizational culture functions."},
		{"designation_name": "Chief Revenue Officer (CRO)", "description": "Responsible for all revenue-generating teams and strategy."},
		{"designation_name": "General Counsel (GC)", "description": "Leads legal strategy and oversees all corporate legal matters."},
		
		# Product & Design
		{"designation_name": "Director of Product", "description": "Leads product management teams and oversees product strategy."},
		{"designation_name": "Product Manager", "description": "Defines product features, strategy, and execution."},
		{"designation_name": "Head of Design", "description": "Oversees design functions including UX, UI, and visual design."},
		{"designation_name": "UX/UI Designer", "description": "Designs user experiences and interfaces for digital products."},
		
		# Data
		{"designation_name": "Head of Data", "description": "Leads data teams and overall data strategy."},
		{"designation_name": "Data Scientist", "description": "Builds models, analyzes data, and provides insights."},
		{"designation_name": "Data Analyst", "description": "Performs data analysis and reporting to support business decisions."},
		{"designation_name": "Technical Writer", "description": "Creates technical documentation for products and engineering teams."},
		
		# Engineering - Backend
		{"designation_name": "VP Engineering", "description": "Oversees engineering strategy, structure, and execution."},
		{"designation_name": "Engineering Manager (Backend)", "description": "Leads backend engineering teams and development processes."},
		{"designation_name": "Senior Backend Engineer", "description": "Develops complex backend systems and mentors others."},
		{"designation_name": "Backend Engineer", "description": "Builds and maintains backend systems and APIs."},
		{"designation_name": "QA Engineer", "description": "Tests software quality and ensures reliable releases."},
		
		# Engineering - Frontend
		{"designation_name": "Engineering Manager (Frontend)", "description": "Leads frontend engineering teams and development processes."},
		{"designation_name": "Senior Frontend Engineer", "description": "Builds advanced frontend systems and mentors engineers."},
		{"designation_name": "Frontend Engineer", "description": "Develops user-facing web applications and interfaces."},
		{"designation_name": "Frontend QA Engineer", "description": "Ensures quality and reliability of frontend applications."},
		
		# Engineering - Platform/Infra
		{"designation_name": "Engineering Manager (Platform/Infra)", "description": "Leads infrastructure and platform engineering teams."},
		{"designation_name": "DevOps Engineer", "description": "Manages CI/CD, deployment automation, and system reliability."},
		{"designation_name": "Security Engineer", "description": "Ensures platform and data security across systems."},
		{"designation_name": "Site Reliability Engineer (SRE)", "description": "Improves system performance, availability, and reliability."},
		{"designation_name": "IT Support Technician", "description": "Provides technical support and manages IT systems."},
		
		# Finance
		{"designation_name": "Senior Accountant", "description": "Manages complex accounting tasks and financial reporting."},
		{"designation_name": "FP&A Analyst", "description": "Supports budgeting, forecasting, and financial analysis."},
		{"designation_name": "Accountant", "description": "Handles daily accounting tasks and financial transactions."},
		
		# Operations
		{"designation_name": "Operations Coordinator", "description": "Supports business operations and administrative processes."},
		{"designation_name": "Office Manager", "description": "Manages office operations and facility needs."},
		{"designation_name": "Procurement / BizOps Analyst", "description": "Handles purchasing and supports business operations analysis."},
		
		# HR - Talent Acquisition
		{"designation_name": "Head of Talent Acquisition", "description": "Leads recruiting strategy and hiring operations."},
		{"designation_name": "Technical Recruiter", "description": "Recruits engineering and technical roles."},
		{"designation_name": "GTM Recruiter", "description": "Recruits sales, marketing, and customer-facing roles."},
		{"designation_name": "Recruiting Coordinator", "description": "Supports scheduling and candidate pipeline management."},
		
		# HR - Operations
		{"designation_name": "HR Operations Manager", "description": "Oversees HR processes, systems, and compliance."},
		{"designation_name": "HR Operations Specialist", "description": "Supports HR processes and employee administration."},
		{"designation_name": "Compensation & Benefits Analyst", "description": "Manages pay structures, benefits, and compensation analysis."},
		{"designation_name": "Payroll Specialist", "description": "Processes payroll and maintains employee pay records."},
		{"designation_name": "HR Business Partner (HRBP)", "description": "Supports leaders with people strategy and organizational guidance."},
		{"designation_name": "Employee Experience Manager", "description": "Designs employee engagement and workplace experience programs."},
		{"designation_name": "Learning & Development Specialist", "description": "Oversees training and professional development initiatives."},
		
		# Sales
		{"designation_name": "Head of Sales", "description": "Leads the sales organization and revenue-generation strategy."},
		{"designation_name": "Account Executive", "description": "Manages customer relationships and drives sales."},
		{"designation_name": "SDR (Sales Development Representative)", "description": "Generates leads and qualifies prospects for sales teams."},
		{"designation_name": "Sales Operations Manager", "description": "Optimizes sales processes, systems, and reporting."},
		{"designation_name": "Sales Analyst", "description": "Provides data analysis to support sales strategy."},
		
		# Marketing
		{"designation_name": "Marketing Director", "description": "Leads marketing teams and overall marketing strategy."},
		{"designation_name": "Brand/Content Marketer", "description": "Creates content and manages brand messaging."},
		{"designation_name": "Growth Marketer", "description": "Drives user acquisition and growth campaigns."},
		{"designation_name": "Events/Field Marketer", "description": "Manages events, field marketing, and on-site programs."},
		{"designation_name": "Paid Ads Specialist", "description": "Manages paid advertising campaigns across platforms."},
		{"designation_name": "SEO Specialist", "description": "Optimizes search visibility and organic traffic."},
		{"designation_name": "SEO/Content Specialist", "description": "Combines SEO expertise with content creation."},
		{"designation_name": "Marketing Operations", "description": "Manages marketing systems, automation, and analytics."},
		
		# Customer Success & Support
		{"designation_name": "Head of Customer Success", "description": "Leads customer success organization, driving customer retention, satisfaction, and growth."},
		{"designation_name": "Customer Success Manager", "description": "Supports customers and drives long-term adoption and retention."},
		{"designation_name": "Customer Support Specialist", "description": "Provides customer support and resolves issues."},
	]
	
	count = 0
	for des in designations_data:
		try:
			if frappe.db.exists("Designation", des["designation_name"]):
				print(f"  ↻ Already exists: {des['designation_name']}")
				continue
			
			designation = frappe.get_doc({
				"doctype": "Designation",
				"designation_name": des["designation_name"],
				"description": des["description"]
			})
			designation.insert(ignore_permissions=True)
			count += 1
		except Exception as e:
			print(f"  ⚠ Error creating designation {des['designation_name'][:30]}: {str(e)[:40]}")
	
	print(f"  ✓ Created {count} designations (out of {len(designations_data)} total)")

def configure_departments(company_name):
	"""Disable departments that are not needed for the company"""
	
	# List of departments to KEEP enabled
	required_departments = [
		"Management",
		"Research & Development",
		"Accounts",
		"Human Resources",
		"Legal",
		"Sales",
		"Operations",
		"Quality Management",
		"Marketing",
		"Customer Service",
		"Purchase"
	]
	
	# Get company abbreviation
	company_abbr = frappe.db.get_value("Company", company_name, "abbr")
	if not company_abbr:
		print(f"  ⚠ Could not find abbreviation for company: {company_name}")
		return
	
	# Get all departments for this company
	all_departments = frappe.get_all(
		"Department",
		filters={"company": company_name},
		fields=["name", "department_name", "disabled"]
	)
	
	enabled_count = 0
	disabled_count = 0
	
	for dept in all_departments:
		# Extract the base department name (without " - ABBR" suffix)
		base_name = dept.department_name
		
		if base_name in required_departments:
			# Enable if it was disabled
			if dept.disabled:
				frappe.db.set_value("Department", dept.name, "disabled", 0)
				print(f"  ✓ Enabled: {dept.name}")
			enabled_count += 1
		else:
			# Disable departments not in the required list
			if not dept.disabled:
				frappe.db.set_value("Department", dept.name, "disabled", 1)
				print(f"  ✗ Disabled: {dept.name}")
			disabled_count += 1
	
	frappe.db.commit()
	print(f"  Summary: {enabled_count} enabled, {disabled_count} disabled")

def create_genders():
	"""Create basic gender options"""
	genders = ["Male", "Female", "Other", "Prefer not to say"]
	
	count = 0
	for gender in genders:
		try:
			if frappe.db.exists("Gender", gender):
				continue
			
			doc = frappe.get_doc({
				"doctype": "Gender",
				"gender": gender
			})
			doc.insert(ignore_permissions=True)
			count += 1
		except Exception as e:
			print(f"  ⚠ Error creating gender {gender}: {str(e)[:40]}")
	
	if count > 0:
		print(f"  ✓ Created {count} genders")
	else:
		print(f"  ↻ Genders already exist")

# def create_employment_types():
# 	"""Create employment type options"""
# 	types = ["Full-time", "Part-time", "Contract", "Intern", "Temporary"]
	
# 	count = 0
# 	for emp_type in types:
# 		try:
# 			if frappe.db.exists("Employment Type", emp_type):
# 				continue
			
# 			doc = frappe.get_doc({
# 				"doctype": "Employment Type",
# 				"employment_type_name": emp_type
# 			})
# 			doc.insert(ignore_permissions=True)
# 			count += 1
# 		except Exception as e:
# 			print(f"  ⚠ Error creating employment type {emp_type}: {str(e)[:40]}")
	
# 	if count > 0:
# 		print(f"  ✓ Created {count} employment types")
# 	else:
# 		print(f"  ↻ Employment types already exist")

# TODO: Refactor to remove the need of create_employee_grade
# We need to check before adding, it is required for promotion tasks
# def create_employee_grades():
# 	"""Create employee grades"""
# 	grades_data = [
# 		{"name": "Junior", "base": 50000},
# 		{"name": "Mid-Level", "base": 75000},
# 		{"name": "Senior", "base": 100000},
# 		{"name": "Lead", "base": 125000},
# 		{"name": "Executive", "base": 150000}
# 	]
# 	
# 	grades = []
# 	for grade_data in grades_data:
# 		try:
# 			grade = create_employee_grade(grade_data["name"], default_base=grade_data["base"])
# 			grades.append(grade.name)
# 			print(f"  ✓ Created: {grade_data['name']}")
# 		except Exception as e:
# 			if frappe.db.exists("Employee Grade", grade_data["name"]):
# 				grades.append(grade_data["name"])
# 				print(f"  ↻ Already exists: {grade_data['name']}")
# 			else:
# 				print(f"  ⚠ Error with {grade_data['name']}: {str(e)}")
# 	
# 	return grades

# ----------------------EMPLOYEES------------------------------------
def create_users_and_employees(company_name, employees_data):
	"""
	Create User accounts and Employee records from the employees roster JSON.
	- HR Managers get HR User and HR Manager roles
	- HR employees get HR User role
	- Regular employees get Employee Self Service role
	"""
	# Disable user creation throttling for bulk import
	frappe.flags.in_import = True
	
	# Get company abbreviation for department lookup
	company_abbr = frappe.db.get_value("Company", company_name, "abbr")
	
	print(f"\n👥 Creating {len(employees_data)} Users and Employees...")
	
	user_count = 0
	employee_count = 0
	errors = []
	
	for emp_data in employees_data:
		first_name = emp_data["first_name"]
		middle_name = emp_data.get("middle_name", "")
		last_name = emp_data["last_name"]
		full_name = f"{first_name} {middle_name} {last_name}".replace("  ", " ").strip()
		
		# Generate emails
		email = f"{first_name.lower()}.{last_name.lower()}@{company_name.lower()}.com"
		personal_email = f"{first_name.lower()}.{last_name.lower()}@gmail.com"

		# Determine roles based on is_hr flag
		is_hr = emp_data.get("is_hr", False)

		# Only these specific people get HR Manager role
		hr_managers = [
			"Monica Priya Patel",
			"Rebecca Shaw", 
			"Samuel Lee",
			"Elena Petrova"
		]
		is_hr_manager = full_name in hr_managers
		
		try:
			# ========== CREATE USER ==========
			if not frappe.db.exists("User", email):
				user = frappe.get_doc({
					"doctype": "User",
					"email": email,
					"first_name": first_name,
					"middle_name": middle_name,
					"last_name": last_name,
					"send_welcome_email": 0,
					"new_password": f"{first_name.upper()}_{last_name.lower()}2025",
					# "roles": user_roles,
					"enabled": 1,
				})
				user.flags.ignore_throttle = True  # Bypass throttle check
				user.insert(ignore_permissions=True)
				user_count += 1
				frappe.db.commit()
			
			# ========== CREATE EMPLOYEE ==========
			# Check if employee already exists for this user
			existing_emp = frappe.db.get_value("Employee", {"user_id": email, "company": company_name}, "name")
			if existing_emp:
				print(f"  ↻ Employee Already exists: {full_name}")
				continue
			
			# Get department ID (format: "Department Name - ABBR")
			dept_name = emp_data.get("department")
			department_id = f"{dept_name} - {company_abbr}" if dept_name else None
			
			# Verify department exists
			if department_id and not frappe.db.exists("Department", department_id):
				# Try without abbreviation (some departments might be global)
				department_id = None
			
			# Get designation
			designation = emp_data.get("designation")
			if designation and not frappe.db.exists("Designation", designation):
				designation = None
			
			# Verify user account exists - User's primary key is the email itself
			existing_acc = email if frappe.db.exists("User", email) else None

			# Create employee
			employee = frappe.get_doc({
				"doctype": "Employee",
				"first_name": first_name,
				"middle_name": middle_name,
				"last_name": last_name,
				"employee_name": full_name,
				"gender": emp_data.get("gender"),
				"date_of_joining": emp_data.get("date_of_joining"),
				"date_of_birth": emp_data.get("date_of_birth"),
				"status": "Active",
				"company": company_name,
				"user_id": existing_acc,
				"department": department_id,
				"employment_type": "Full-time",
				"designation": designation,
				"cell_number": emp_data.get("cell_number"),
				"personal_email": personal_email,
				"company_email": email,
				"preferred_contact_email": "Company Email",
				"unsubscribed": 1,
				"person_to_be_contacted": emp_data.get("person_to_be_contacted"),
				"emergency_phone_number": emp_data.get("emergency_phone_number"),
				# "holiday_list": "US Holidays 2025",  # Legacy: develop branch requires Holiday List Assignment instead of direct field assignment
				"default_shift": "Morning",
				"salary_currency": "USD",
				"salary_mode": "Bank",
				"marital_status": emp_data.get("marital_status"),
				"passport_number": emp_data.get("passport_number"),
				"date_of_issue": emp_data.get("date_of_issue"),
				"valid_upto": emp_data.get("valid_up_to"),
				"place_of_issue": emp_data.get("place_of_issue")				
			})
			employee.flags.ignore_mandatory = True
			employee.insert(ignore_permissions=True)
			employee_count += 1
			frappe.db.commit()

			# ========== ASSIGN ROLES AFTER EMPLOYEE IS LINKED ==========
			# Remove auto-assigned "Employee" role first
			if frappe.db.exists("Has Role", {"parent": email, "role": "Employee"}):
				frappe.db.delete("Has Role", {"parent": email, "role": "Employee"})
				frappe.db.commit()
			
			# Build roles list based on role type
			if frappe.db.exists("User", email):
				if is_hr_manager:
					user_roles = ["HR User", "HR Manager"]
				elif is_hr:
					user_roles = ["HR User"]
				else:
					user_roles = ["Employee Self Service"]
			
				for role in user_roles:
					if not frappe.db.exists("Has Role", {"parent": email, "role": role}):
						frappe.get_doc({
							"doctype": "Has Role",
							"parent": email,
							"parenttype": "User",
							"parentfield": "roles",
							"role": role
						}).db_insert()
				
				frappe.db.commit()

		except Exception as e:
			errors.append(f"{full_name}: {str(e)[:50]}")
	
	# Print summary
	print(f"  ✓ Created {user_count} User accounts")
	print(f"  ✓ Created {employee_count} Employee records")
	
	if errors:
		print(f"  ⚠ {len(errors)} errors:")
		for err in errors[:5]:  # Show first 5 errors
			print(f"    - {err}")
		if len(errors) > 5:
			print(f"    ... and {len(errors) - 5} more")
	
	return employee_count

def create_holiday_list_assignments(company="NovaSoft", holiday_list_name="US Holidays 2025"):
    """
    Create Holiday List Assignments for all employees in the company.
    Required in ERPNext develop branch - direct field assignment no longer works.
    """
    print(f"\n  Creating Holiday List Assignments...")
    
    # Get the holiday list date range
    holiday_list_dates = frappe.db.get_value(
        "Holiday List", 
        holiday_list_name, 
        ["from_date", "to_date"],
        as_dict=True
    )
    
    if not holiday_list_dates:
        print(f"  ⚠ Holiday List '{holiday_list_name}' not found")
        return 0
    
    employees = frappe.get_all(
        "Employee",
        filters={"company": company, "status": "Active"},
        pluck="name"
    )
    
    created = 0
    for emp_id in employees:
        existing = frappe.db.exists("Holiday List Assignment", {
            "assigned_to": emp_id,
            "holiday_list": holiday_list_name
        })
        
        if not existing:
            assignment = frappe.get_doc({
                "doctype": "Holiday List Assignment",
                "applicable_for": "Employee",
                "assigned_to": emp_id,
                "holiday_list": holiday_list_name,
                "company": company,
                "from_date": holiday_list_dates.from_date,
                "to_date": holiday_list_dates.to_date
            })
            assignment.insert(ignore_permissions=True)
            assignment.submit()
            created += 1
    
    print(f"  ✓ Created {created} Holiday List Assignments")
    return created

def update_reports_to(company_name, employees_data):
	"""
	Update the reports_to field for all employees based on the roster JSON.
	Must be called AFTER all employees are created.
	
	The roster contains manager names (e.g., "Alice Kim"), but the Employee
	doctype requires the Employee ID (e.g., "HR-EMP-00001").
	"""
	print(f"\n Updating reports_to for {len(employees_data)} employees...")
	
	# Step 1: Build a lookup map of employee_name -> employee_id for this company
	# We need to match by name since that's what the JSON contains
	employees_in_company = frappe.get_all(
		"Employee",
		filters={"company": company_name, "status": "Active"},
		fields=["name", "employee_name"]
	)
	
	# Create lookup: employee_name -> employee_id
	name_to_id = {}
	for emp in employees_in_company:
		name_to_id[emp.employee_name] = emp.name
	
	print(f"  📋 Found {len(employees_in_company)} employees in {company_name}")
	
	# Step 2: Update each employee's reports_to field
	updated_count = 0
	skipped_count = 0
	errors = []
	
	for emp_data in employees_data:
		first_name = emp_data["first_name"]
		last_name = emp_data["last_name"]
		middle_name = emp_data.get("middle_name", "")
		full_name = f"{first_name} {middle_name} {last_name}".replace("  ", " ").strip()
		reports_to_name = emp_data.get("reports_to")
		
		# Skip if no manager (CEO, etc.)
		if not reports_to_name:
			skipped_count += 1
			continue
		
		# Get the employee ID for this person
		employee_id = name_to_id.get(full_name)
		if not employee_id:
			errors.append(f"{full_name}: Employee not found")
			continue
		
		# Get the manager's employee ID
		manager_id = name_to_id.get(reports_to_name)
		if not manager_id:
			errors.append(f"{full_name}: Manager '{reports_to_name}' not found")
			continue
		
		try:
			# Update the reports_to field
			frappe.db.set_value("Employee", employee_id, "reports_to", manager_id, update_modified=False)
			updated_count += 1
		except Exception as e:
			errors.append(f"{full_name}: {str(e)[:40]}")
	
	frappe.db.commit()
	
	# Print summary
	print(f"  ✓ Updated reports_to for {updated_count} employees")
	print(f"  ↻ Skipped {skipped_count} employees (no manager - top level)")
	
	if errors:
		print(f"  ⚠ {len(errors)} errors:")
		for err in errors[:5]:
			print(f"    - {err}")
		if len(errors) > 5:
			print(f"    ... and {len(errors) - 5} more")
	
	# IMPORTANT: Rebuild the nested set tree (lft/rgt values) for the Employee doctype
	# This is required for the organizational chart to display correctly, as it uses
	# the nested set model to determine hierarchy and count subordinates
	print("  🔄 Rebuilding Employee nested set tree (lft/rgt)...")
	try:
		# Try new signature first (frappe v15+)
		rebuild_tree("Employee")
	except TypeError:
		# Fall back to old signature if needed
		try:
			rebuild_tree("Employee", "reports_to")
		except Exception:
			pass
	frappe.db.commit()
	print("  ✓ Nested set tree rebuilt successfully")
	
	return updated_count

def assign_approvers_to_employees(company_name="NovaSoft"):
	"""
	Assign expense_approver, shift_request_approver, and leave_approver to all employees.
	The approver is set to the employee's manager (reports_to) user_id.
	
	Usage: 
		bench --site [sitename] execute demo_data.company_setup.assign_approvers_to_employees
		or with company:
		bench --site [sitename] execute demo_data.company_setup.assign_approvers_to_employees --kwargs '{"company_name": "NovaSoft"}'
	"""
	frappe.set_user("Administrator")
	
	print(f"\tAssigning Approvers for Company: {company_name}")
	
	# Get all active employees with a reports_to value
	employees = frappe.get_all(
		"Employee",
		filters={
			"company": company_name,
			"status": "Active",
			"reports_to": ["is", "set"]  # Only employees with a manager
		},
		fields=["name", "employee_name", "reports_to"]
	)
	
	print(f"  📋 Found {len(employees)} employees with managers\n")
	
	updated_count = 0
	skipped_count = 0
	errors = []
	
	for emp in employees:
		try:
			# Get the manager's user_id from their Employee record
			manager_user_id = frappe.db.get_value("Employee", emp.reports_to, "user_id")
			
			if not manager_user_id:
				errors.append(f"{emp.employee_name}: Manager '{emp.reports_to}' has no user_id")
				skipped_count += 1
				continue
			
			# Update the employee's approvers
			frappe.db.set_value(
				"Employee",
				emp.name,
				{
					"expense_approver": manager_user_id,
					"shift_request_approver": manager_user_id,
					"leave_approver": manager_user_id
				},
				update_modified=False
			)
			updated_count += 1
			
		except Exception as e:
			errors.append(f"{emp.employee_name}: {str(e)[:50]}")
	
	frappe.db.commit()
	
	# Print summary
	print(f"  ✓ Updated approvers for {updated_count} employees")
	print(f"  ↻ Skipped {skipped_count} employees (manager has no user account)")
	
	if errors:
		print(f"  ⚠ {len(errors)} errors:")
		for err in errors[:5]:
			print(f"    - {err}")
		if len(errors) > 5:
			print(f"    ... and {len(errors) - 5} more")
	
	return updated_count

# ----------------------UPDATES NEEDED FOR SPECIFIC TASKS------------------------------------
def update_employee_profile(employee_identifier):
	"""
	Update specific employee with custom bio, education, and work history.
	"""
	
	# Find employee by ID or email
	if frappe.db.exists("Employee", employee_identifier):
		employee_id = employee_identifier
	else:
		# Try to find by user_id (email)
		employee_id = frappe.db.get_value("Employee", {"user_id": employee_identifier}, "name")
	
	if not employee_id:
		print(f"  ⚠ Employee not found: {employee_identifier}")
		return None
	
	print(f"Updating Employee: {employee_id}")
	
	try:
		employee = frappe.get_doc("Employee", employee_id)
		
		# Update bio
		employee.bio = "I am a Customer Support Specialist with one year of experience, and I have a strong background in ticket management, live chat, and phone support. I am fluent in English and Portuguese."
		
		# Add education record (child table)
		employee.append("education", {
			"school_univ": "Brightwater College",
			"level": "Under Graduate",
			"maj_opt_subj": "Business Communications"
		})
		
		# Add external work history record (child table)
		employee.append("external_work_history", {
			"company_name": "NovaLink Solutions",
			"designation": "Intern"
		})
		
		employee.save(ignore_permissions=True)
		frappe.db.commit()

		# Remove auto-assigned "Employee" role
		remove_employee_role(employee_id)

		print(f"  ✓ Updated bio for {employee.employee_name}")
		
		return employee_id
		
	except Exception as e:
		print(f"  ⚠ Error updating employee: {str(e)}")
		return None

def update_employee_emergency_contact(employee_identifier):
	# Find employee by ID or email
	if frappe.db.exists("Employee", employee_identifier):
		employee_id = employee_identifier
	else:
		# Try to find by user_id (email)
		employee_id = frappe.db.get_value("Employee", {"user_id": employee_identifier}, "name")
	
	if not employee_id:
		print(f"  ⚠ Employee not found: {employee_identifier}")
		return None
	
	print(f"Updating Employee: {employee_id}")
	try:
		employee = frappe.get_doc("Employee", employee_id)
		
		# Update emergency contact
		employee.relation = "brother"
		employee.save(ignore_permissions=True)
		frappe.db.commit()

		# Remove auto-assigned "Employee" role
		remove_employee_role(employee_id)

		print(f"  ✓ Updated emergency contact for {employee.employee_name}")
		return employee_id
		
	except Exception as e:
		print(f"  ⚠ Error updating employee: {str(e)}")
		return None

def update_employee_bank_info(employee_identifier):
	# Find employee by ID or email
	if frappe.db.exists("Employee", employee_identifier):
		employee_id = employee_identifier
	else:
		# Try to find by user_id (email)
		employee_id = frappe.db.get_value("Employee", {"user_id": employee_identifier}, "name")
	
	if not employee_id:
		print(f"  ⚠ Employee not found: {employee_identifier}")
		return None
	
	print(f"Updating Employee: {employee_id}")
	try:
		employee = frappe.get_doc("Employee", employee_id)
		
		# Update bank account info
		employee.bank_name = "Continental First Bank"
		employee.bank_ac_no = "00482917355"
		employee.save(ignore_permissions=True)
		frappe.db.commit()

		# Remove auto-assigned "Employee" role
		remove_employee_role(employee_id)

		print(f"  ✓ Updated emergency contact for {employee.employee_name}")
		return employee_id

	except Exception as e:
		print(f"  ⚠ Error updating employee: {str(e)}")
		return None	

# --------------------------HELPER FUNCTIONS----------------------------
# def load_employees_roster(roster_path):
# 	"""Load the employees roster from JSON file"""
# 	employees_data = []
# 	if roster_path:
# 		print(f"📄 Loading roster from: {roster_path}")
# 		with open(roster_path, 'r') as f:
# 			data = json.load(f)
# 		employees_data = data.get("employees", [])
# 		print(f"  ✓ Loaded {len(employees_data)} employees from roster\n")
# 	return employees_data

def remove_employee_role(employee_id):
	"""Remove the auto-assigned 'Employee' role from the user linked to this employee."""
	user_id = frappe.db.get_value("Employee", employee_id, "user_id")
	if user_id and frappe.db.exists("Has Role", {"parent": user_id, "role": "Employee"}):
		frappe.db.delete("Has Role", {"parent": user_id, "role": "Employee"})
		frappe.db.commit()
