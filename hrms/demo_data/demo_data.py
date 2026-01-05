import frappe
from frappe.utils import getdate, add_days, add_months, random_string
from erpnext.setup.doctype.designation.test_designation import create_designation
from hrms.tests.test_utils import create_employee_grade

def create_demo_data(company="Agentix Company"):
	"""
	Create comprehensive demo data for HRMS testing
	Usage: bench --site [sitename] execute hrms.demo_data.create_demo_data
	Or with company: bench --site [sitename] execute hrms.demo_data.create_demo_data --kwargs '{"company": "My Company"}'
	"""
	frappe.set_user("Administrator")
	
	print(f"\n{'='*60}")
	print(f"Creating Demo Data for Company: {company}")
	print(f"{'='*60}\n")
	
	# 0a. Setup warehouse types (required for company creation)
	print("🏭 Setting up Warehouse Types...")
	setup_warehouse_types()
	
	# 0b. Create company if it doesn't exist
	company_name = ensure_company_exists(company)
	
	# 1. Create Departments
	print("📁 Creating Departments...")
	departments = create_departments(company_name)
	
	# 2. Create Designations
	print("👔 Creating Designations...")
	designations = create_designations()
	
	# 3. Create Employee Grades
	print("⭐ Creating Employee Grades...")
	grades = create_employee_grades()
	
	# 4. Create Holiday List
	print("📅 Creating Holiday List...")
	holiday_list = create_holiday_list(company_name)
	
	# 5. Create Employees
	print("👥 Creating Employees...")
	employees = create_employees(company_name, departments, designations, grades)
	
	# 6. Create Leave Allocations
	print("🏖️  Creating Leave Allocations...")
	create_leave_allocations(employees, company_name)
	
	# 7. Create Leave Applications
	print("📝 Creating Leave Applications...")
	create_leave_applications(employees)
	
	# 8. Create Expense Claims
	print("💰 Creating Expense Claims...")
	create_expense_claims(employees, company_name)
	
	# 9. Create Attendance Records
	print("✓ Creating Attendance Records...")
	create_attendance_records(employees, company_name)
	
	# === CRITICAL DocTypes ===
	print("\n🔴 Creating CRITICAL DocTypes...")
	
	# 10. Create Attendance Requests
	print("📋 Creating Attendance Requests...")
	create_attendance_requests(employees)
	
	# 11. Create Branches
	print("🏢 Creating Branches...")
	branches = create_branches(company_name)
	
	# 12. Create Salary Structures
	print("💼 Creating Salary Structures...")
	salary_structures = create_salary_structures(company_name)
	
	# 12.1 Assign Salary Structures to Employees
	if employees and salary_structures:
		print("📋 Assigning Salary Structures to Employees...")
		assign_salary_structures_to_employees(employees, company_name, salary_structures)
	
	# 13. Create Shift Types
	print("⏰ Creating Shift Types...")
	shift_types = create_shift_types(company_name)
	
	# 14. Create Shift Assignments
	print("📅 Creating Shift Assignments...")
	create_shift_assignments(employees, shift_types, company_name)
	
	# 15. Create Shift Requests
	print("🔄 Creating Shift Requests...")
	create_shift_requests(employees, shift_types)
	
	# === IMPORTANT DocTypes ===
	print("\n🟡 Creating IMPORTANT DocTypes...")
	
	# 16. Create Payroll Entries
	print("💵 Creating Payroll Entries...")
	create_payroll_entries(employees, company_name)
	
	# 17. Create Employee Advances
	print("💸 Creating Employee Advances...")
	create_employee_advances(employees, company_name)
	
	# 18. Create Job Openings
	print("📢 Creating Job Openings...")
	job_openings = create_job_openings(designations, company_name)
	
	# 19. Create Job Applicants
	print("👥 Creating Job Applicants...")
	job_applicants = create_job_applicants(job_openings, company_name)
	
	# 20. Create Interviews
	print("🎤 Creating Interviews...")
	create_interviews(designations)
	
	# 21. Create Job Offers
	print("📄 Creating Job Offers...")
	create_job_offers(job_applicants, designations, company_name)
	
	# 22. Create Appraisals
	print("⭐ Creating Appraisals...")
	create_appraisals(employees, company_name)
	
	# 23. Create Training Programs
	print("📚 Creating Training Programs...")
	training_programs = create_training_programs()
	
	# 24. Create Training Events
	print("🎓 Creating Training Events...")
	create_training_events(training_programs, company_name)
	
	# === SPECIALIZED DocTypes ===
	print("\n🟢 Creating SPECIALIZED DocTypes...")
	
	# 25. Create Additional Salaries
	print("💰 Creating Additional Salaries...")
	create_additional_salaries(employees, company_name)
	
	# 26. Create Employee Incentives
	print("🎁 Creating Employee Incentives...")
	create_employee_incentives(employees, company_name)
	
	# 27. Create Employee Onboardings
	print("👋 Creating Employee Onboardings...")
	create_employee_onboardings(employees, company_name)
	
	# 28. Create Employee Separations
	print("👔 Creating Employee Separations...")
	create_employee_separations(employees, company_name)
	
	# 29. Create Employee Transfers
	print("🔀 Creating Employee Transfers...")
	create_employee_transfers(employees, departments)
	
	# 30. Create Employee Promotions
	print("📈 Creating Employee Promotions...")
	create_employee_promotions(employees, designations)
	
	# 31. Create Travel Requests
	print("✈️ Creating Travel Requests...")
	create_travel_requests(employees, company_name)
	
	# 32. Create Vehicle Logs
	print("🚗 Creating Vehicle Logs...")
	create_vehicle_logs(employees, company_name)
	
	# 33. Create Goals
	print("🎯 Creating Goals...")
	create_goals(employees, company_name)
	
	frappe.db.commit()
	
	print(f"\n{'='*60}")
	print("✅ Demo Data Creation Complete!")
	print(f"{'='*60}")
	print(f"\nCreated:")
	print(f"  - Company: {company_name}")
	print(f"  - {len(departments)} Departments")
	print(f"  - {len(designations)} Designations")
	print(f"  - {len(grades)} Employee Grades")
	print(f"  - {len(employees)} Employees")
	print(f"  - Leave Allocations and Applications")
	print(f"  - Expense Claims")
	print(f"  - Attendance Records")
	print(f"  - {len(branches)} Branches")
	print(f"  - 2 Salary Structures")
	print(f"  - {len(shift_types)} Shift Types with Assignments")
	print(f"  - Payroll Entry, Employee Advances")
	print(f"  - Job Openings, Applicants, Interviews, Offers")
	print(f"  - Appraisals, Training Programs & Events")
	print(f"  - Additional Salaries, Employee Incentives")
	print(f"  - Employee Onboardings & Separations")
	print(f"  - Employee Transfers & Promotions")
	print(f"  - Travel Requests, Vehicle Logs, Goals")
	print(f"\n{'='*60}\n")
	
	if employees:
		print("Sample Employee Credentials:")
		print("  Email: alice.johnson@agentix.com")
		print("  Password: AgentixDemo@123!")
		print(f"\n{'='*60}\n")


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


def ensure_company_exists(company_name):
	"""Ensure company exists, create if it doesn't"""
	if frappe.db.exists("Company", company_name):
		print(f"✓ Company '{company_name}' already exists\n")
		return company_name
	
	print(f"⚙️  Creating new company '{company_name}'...")
	
	try:
		# Generate unique abbreviation from company name
		# Take first letter of each word (up to 3 words) or first 3-5 chars
		words = company_name.split()
		if len(words) > 1:
			abbr = ''.join(word[0].upper() for word in words[:3])
		else:
			abbr = company_name[:3].upper()
		
		# Make sure abbreviation is unique by adding number if needed
		original_abbr = abbr
		counter = 1
		while frappe.db.exists("Company", {"abbr": abbr}):
			abbr = f"{original_abbr}{counter}"
			counter += 1
		
		company = frappe.get_doc({
			"doctype": "Company",
			"company_name": company_name,
			"abbr": abbr,
			"default_currency": "USD",
			"country": "United States",
			"domain": "Services"
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
		
		return company_name


def create_departments(company):
	"""Create demo departments"""
	from erpnext.setup.doctype.department.department import get_abbreviated_name
	
	dept_names = [
		"Engineering",
		"Product Management",
		"Sales",
		"Marketing",
		"Human Resources",
		"Finance",
		"Customer Support",
		"Operations"
	]
	
	departments = []
	for dept_name in dept_names:
		try:
			docname = get_abbreviated_name(dept_name, company)
			
			if frappe.db.exists("Department", docname):
				departments.append(docname)
				print(f"  ↻ Already exists: {dept_name}")
				continue
			
			department = frappe.get_doc({
				"doctype": "Department",
				"department_name": dept_name,
				"company": company
			})
			department.insert(ignore_permissions=True)
			departments.append(department.name)
			print(f"  ✓ Created: {dept_name}")
		except Exception as e:
			print(f"  ⚠ Error with {dept_name}: {str(e)}")
	
	return departments


def create_designations():
	"""Create demo designations"""
	designation_names = [
		"Software Engineer",
		"Senior Software Engineer",
		"Engineering Manager",
		"Product Manager",
		"Sales Representative",
		"Marketing Manager",
		"HR Manager",
		"Financial Analyst",
		"Support Engineer",
		"Operations Manager"
	]
	
	designations = []
	for name in designation_names:
		try:
			designation = create_designation(designation_name=name)
			designations.append(designation.name)
			print(f"  ✓ Created: {name}")
		except Exception as e:
			if frappe.db.exists("Designation", name):
				designations.append(name)
				print(f"  ↻ Already exists: {name}")
			else:
				print(f"  ⚠ Error with {name}: {str(e)}")
	
	return designations


def create_employee_grades():
	"""Create employee grades"""
	grades_data = [
		{"name": "Junior", "base": 50000},
		{"name": "Mid-Level", "base": 75000},
		{"name": "Senior", "base": 100000},
		{"name": "Lead", "base": 125000},
		{"name": "Executive", "base": 150000}
	]
	
	grades = []
	for grade_data in grades_data:
		try:
			grade = create_employee_grade(grade_data["name"], default_base=grade_data["base"])
			grades.append(grade.name)
			print(f"  ✓ Created: {grade_data['name']}")
		except Exception as e:
			if frappe.db.exists("Employee Grade", grade_data["name"]):
				grades.append(grade_data["name"])
				print(f"  ↻ Already exists: {grade_data['name']}")
			else:
				print(f"  ⚠ Error with {grade_data['name']}: {str(e)}")
	
	return grades


def create_holiday_list(company):
	"""Create a holiday list for the company"""
	holiday_list_name = f"{company} Holidays"
	
	try:
		if frappe.db.exists("Holiday List", holiday_list_name):
			print(f"  ↻ Already exists: {holiday_list_name}")
			return holiday_list_name
		
		# Create holiday list
		current_year = getdate().year
		holiday_list = frappe.get_doc({
			"doctype": "Holiday List",
			"holiday_list_name": holiday_list_name,
			"from_date": f"{current_year}-01-01",
			"to_date": f"{current_year}-12-31",
			"holidays": [
				{"holiday_date": f"{current_year}-01-01", "description": "New Year's Day"},
				{"holiday_date": f"{current_year}-07-04", "description": "Independence Day"},
				{"holiday_date": f"{current_year}-12-25", "description": "Christmas Day"},
			]
		})
		holiday_list.insert(ignore_permissions=True)
		print(f"  ✓ Created: {holiday_list_name}")
		
		# Set as company default
		frappe.db.set_value("Company", company, "default_holiday_list", holiday_list_name)
		return holiday_list_name
	except Exception as e:
		print(f"  ⚠ Error: {str(e)}")
		return None


def create_employees(company, departments, designations, grades):
	"""Create demo employees with unique passwords"""
	employee_data = [
		{"first_name": "Alice", "last_name": "Johnson", "dept_idx": 0, "des_idx": 2, "grade_idx": 3},
		{"first_name": "Bob", "last_name": "Smith", "dept_idx": 0, "des_idx": 1, "grade_idx": 2},
		{"first_name": "Charlie", "last_name": "Brown", "dept_idx": 0, "des_idx": 0, "grade_idx": 1},
		{"first_name": "Diana", "last_name": "Prince", "dept_idx": 1, "des_idx": 3, "grade_idx": 2},
		{"first_name": "Edward", "last_name": "Norton", "dept_idx": 2, "des_idx": 4, "grade_idx": 2},
		{"first_name": "Fiona", "last_name": "Green", "dept_idx": 3, "des_idx": 5, "grade_idx": 3},
		{"first_name": "George", "last_name": "Taylor", "dept_idx": 4, "des_idx": 6, "grade_idx": 3},
		{"first_name": "Hannah", "last_name": "Wilson", "dept_idx": 5, "des_idx": 7, "grade_idx": 2},
		{"first_name": "Ian", "last_name": "Davis", "dept_idx": 6, "des_idx": 8, "grade_idx": 1},
		{"first_name": "Julia", "last_name": "Martinez", "dept_idx": 7, "des_idx": 9, "grade_idx": 3},
	]
	
	employees = []
	
	# Generate a random suffix for email addresses to ensure uniqueness
	import random
	random_suffix = random.randint(100000, 999999)
	
	for i, emp_data in enumerate(employee_data):
		try:
			# Create company-specific email with random suffix to allow same person in multiple companies
			email = f"{emp_data['first_name'].lower()}.{emp_data['last_name'].lower()}.{random_suffix}@agentix.com"
			
			# Check if employee already exists for THIS company with THIS email
			existing_emp = frappe.db.get_value("Employee", {"user_id": email, "company": company}, "name")
			if existing_emp:
				employees.append(existing_emp)
				print(f"  ↻ Already exists: {emp_data['first_name']} {emp_data['last_name']}")
				continue
			
			# Get department and designation safely
			department = departments[emp_data["dept_idx"]] if emp_data["dept_idx"] < len(departments) else None
			designation = designations[emp_data["des_idx"]] if emp_data["des_idx"] < len(designations) else (designations[0] if designations else None)
			grade = grades[emp_data["grade_idx"]] if grades and emp_data["grade_idx"] < len(grades) else None
			
			# Create user first with a strong password
			if not frappe.db.exists("User", email):
				user = frappe.get_doc({
					"doctype": "User",
					"email": email,
					"first_name": emp_data["first_name"],
					"last_name": emp_data["last_name"],
					"send_welcome_email": 0,
					"new_password": f"AgentixDemo@{i+1}23!"
				})
				user.insert(ignore_permissions=True)
			
			# Create employee without gender field
			employee_doc = {
				"doctype": "Employee",
				"first_name": emp_data["first_name"],
				"last_name": emp_data["last_name"],
				"company": company,
				"user_id": email,
				"date_of_joining": add_months(getdate(), -12),
				"status": "Active"
			}
			
			# Add optional fields
			if department:
				employee_doc["department"] = department
			if designation:
				employee_doc["designation"] = designation
			if grade:
				employee_doc["grade"] = grade
			
			employee = frappe.get_doc(employee_doc)
			employee.flags.ignore_mandatory = True
			employee.insert(ignore_permissions=True)
			employees.append(employee.name)
			print(f"  ✓ Created: {emp_data['first_name']} {emp_data['last_name']} ({email})")
		except Exception as e:
			print(f"  ⚠ Error creating {emp_data['first_name']}: {str(e)}")
	
	return employees


def create_leave_allocations(employees, company):
	"""Create leave allocations for employees"""
	if not employees:
		print("  ⚠ No employees found, skipping leave allocations")
		return
	
	leave_types = ["Casual Leave", "Sick Leave", "Privilege Leave"]
	
	current_year = getdate().year
	from_date = f"{current_year}-01-01"
	to_date = f"{current_year}-12-31"
	
	count = 0
	for emp in employees:
		for leave_type in leave_types:
			try:
				if not frappe.db.exists("Leave Type", leave_type):
					continue
				
				if frappe.db.exists("Leave Allocation", {
					"employee": emp,
					"leave_type": leave_type,
					"from_date": from_date,
					"to_date": to_date
				}):
					continue
				
				allocation = frappe.get_doc({
					"doctype": "Leave Allocation",
					"employee": emp,
					"leave_type": leave_type,
					"from_date": from_date,
					"to_date": to_date,
					"new_leaves_allocated": 15,
					"company": company
				})
				allocation.insert(ignore_permissions=True)
				allocation.submit()
				count += 1
			except Exception as e:
				pass  # Silent fail for leave allocations
	
	if count > 0:
		print(f"  ✓ Created {count} leave allocations")


def create_leave_applications(employees):
	"""Create sample leave applications"""
	if not employees:
		print("  ⚠ No employees found, skipping leave applications")
		return
	
	leave_types = ["Casual Leave", "Sick Leave"]
	count = 0
	
	for i, emp in enumerate(employees[:5]):
		try:
			leave_type = leave_types[i % len(leave_types)]
			
			if not frappe.db.exists("Leave Type", leave_type):
				continue
			
			from_date = add_days(getdate(), 7 + i)
			to_date = add_days(from_date, 2)
			
			leave_app = frappe.get_doc({
				"doctype": "Leave Application",
				"employee": emp,
				"leave_type": leave_type,
				"from_date": from_date,
				"to_date": to_date,
				"description": f"Personal work - Demo leave application",
				"status": "Open"
			})
			leave_app.insert(ignore_permissions=True)
			count += 1
		except Exception as e:
			pass  # Silent fail
	
	if count > 0:
		print(f"  ✓ Created {count} leave applications")


def create_expense_claims(employees, company):
	"""Create sample expense claims"""
	if not employees:
		print("  ⚠ No employees found, skipping expense claims")
		return
	
	expense_types = ["Travel", "Food", "Others"]
	count = 0
	
	for i, emp in enumerate(employees[:5]):
		try:
			expense_type = expense_types[i % len(expense_types)]
			if not frappe.db.exists("Expense Claim Type", expense_type):
				continue
			
			amount = float(100 * (i + 1))  # Ensure it's a float
			
			expense = frappe.get_doc({
				"doctype": "Expense Claim",
				"employee": emp,
				"company": company,
				"posting_date": getdate(),  # Required for currency calculations
				"expense_approver": "Administrator",
				"expenses": [{
					"expense_type": expense_type,
					"description": f"Demo expense claim",
					"amount": amount,
					"sanctioned_amount": amount,  # Add sanctioned amount
					"expense_date": add_days(getdate(), -i)
				}]
			})
			expense.flags.ignore_mandatory = True
			expense.insert(ignore_permissions=True)
			count += 1
		except Exception as e:
			print(f"  ⚠ Expense Claim error: {str(e)[:80]}")
	
	if count > 0:
		print(f"  ✓ Created {count} expense claims")


def create_attendance_records(employees, company):
	"""Create attendance records for past 30 days"""
	if not employees:
		print("  ⚠ No employees found, skipping attendance records")
		return
	
	total_count = 0
	for emp in employees:
		count = 0
		for day_offset in range(1, 31):
			try:
				attendance_date = add_days(getdate(), -day_offset)
				
				if frappe.db.exists("Attendance", {"employee": emp, "attendance_date": attendance_date}):
					continue
				
				# Most days present, skip weekends
				if day_offset % 7 in [0, 6]:
					continue
				
				attendance = frappe.get_doc({
					"doctype": "Attendance",
					"employee": emp,
					"attendance_date": attendance_date,
					"status": "Present",
					"company": company
				})
				attendance.insert(ignore_permissions=True)
				count += 1
			except Exception as e:
				pass  # Silent fail
		total_count += count
	
	if total_count > 0:
		print(f"  ✓ Created {total_count} attendance records")


# ==================== CRITICAL DocTypes ====================

def create_attendance_requests(employees):
	"""Create attendance requests for work from home"""
	if not employees:
		return
	
	count = 0
	for i, emp in enumerate(employees[:3]):
		try:
			from_date = add_days(getdate(), 5 + i)
			to_date = add_days(from_date, 1)
			
			request = frappe.get_doc({
				"doctype": "Attendance Request",
				"employee": emp,
				"from_date": from_date,
				"to_date": to_date,
				"reason": "Work From Home",
				"explanation": "Demo attendance request"
			})
			request.insert(ignore_permissions=True)
			count += 1
		except Exception as e:
			pass
	
	if count > 0:
		print(f"  ✓ Created {count} attendance requests")


def create_branches(company):
	"""Create company branches"""
	branch_names = ["Head Office", "Branch Office 1", "Branch Office 2"]
	branches = []
	
	for branch_name in branch_names:
		try:
			if frappe.db.exists("Branch", branch_name):
				branches.append(branch_name)
				continue
			
			branch = frappe.get_doc({
				"doctype": "Branch",
				"branch": branch_name
			})
			branch.insert(ignore_permissions=True)
			branches.append(branch.name)
			print(f"  ✓ Created: {branch_name}")
		except Exception as e:
			pass
	
	return branches


def create_salary_structures(company):
	"""Create salary structures"""
	structures = []
	
	# Get company abbreviation for unique naming
	company_abbr = frappe.db.get_value("Company", company, "abbr") or "DEMO"
	
	base_structure_names = ["Standard Salary Structure", "Executive Salary Structure"]
	
	for base_name in base_structure_names:
		try:
			# Create company-specific structure name
			struct_name = f"{base_name} - {company_abbr}"
			
			if frappe.db.exists("Salary Structure", struct_name):
				structures.append(struct_name)
				print(f"  ↻ Already exists: {struct_name}")
				continue
			
			structure = frappe.get_doc({
				"doctype": "Salary Structure",
				"name": struct_name,
				"company": company,
				"is_active": "Yes",
				"payroll_frequency": "Monthly"
			})
			structure.insert(ignore_permissions=True)
			structures.append(structure.name)
			print(f"  ✓ Created: {struct_name}")
		except Exception as e:
			print(f"  ⚠ Salary Structure error ({struct_name}): {str(e)[:80]}")
	
	return structures


def assign_salary_structures_to_employees(employees, company, salary_structures):
	"""Assign salary structures to employees"""
	if not employees or not salary_structures:
		return
	
	count = 0
	for i, emp in enumerate(employees):
		try:
			# Alternate between salary structures
			structure = salary_structures[i % len(salary_structures)]
			
			# Get employee doc
			employee = frappe.get_doc("Employee", emp)
			
			# Set payroll-related fields on employee
			try:
				cost_center = frappe.db.get_value("Company", company, "cost_center")
				if cost_center:
					employee.db_set("payroll_cost_center", cost_center, update_modified=False)
			except:
				pass
			
			employee.db_set("salary_mode", "Bank", update_modified=False)
			
			# Create Salary Structure Assignment
			if not frappe.db.exists("Salary Structure Assignment", {
				"employee": emp,
				"salary_structure": structure,
				"from_date": employee.date_of_joining
			}):
				assignment = frappe.get_doc({
					"doctype": "Salary Structure Assignment",
					"employee": emp,
					"salary_structure": structure,
					"company": company,
					"from_date": employee.date_of_joining,
					"base": 50000 + (i * 5000),  # Base salary varies per employee
					"variable": 0
				})
				assignment.flags.ignore_mandatory = True
				assignment.insert(ignore_permissions=True)
				count += 1
		except Exception as e:
			print(f"  ⚠ Salary Structure Assignment error: {str(e)[:80]}")
	
	if count > 0:
		print(f"  ✓ Assigned salary structures to {count} employees")


def create_shift_types(company):
	"""Create shift types"""
	shifts = []
	shift_data = [
		{"name": "Morning Shift", "start_time": "09:00:00", "end_time": "17:00:00"},
		{"name": "Evening Shift", "start_time": "14:00:00", "end_time": "22:00:00"},
		{"name": "Night Shift", "start_time": "22:00:00", "end_time": "06:00:00"}
	]
	
	for shift in shift_data:
		try:
			if frappe.db.exists("Shift Type", shift["name"]):
				shifts.append(shift["name"])
				continue
			
			shift_type = frappe.get_doc({
				"doctype": "Shift Type",
				"name": shift["name"],
				"start_time": shift["start_time"],
				"end_time": shift["end_time"]
			})
			shift_type.insert(ignore_permissions=True)
			shifts.append(shift_type.name)
			print(f"  ✓ Created: {shift['name']}")
		except Exception as e:
			pass
	
	return shifts


def create_shift_assignments(employees, shift_types, company):
	"""Assign shifts to employees"""
	if not employees or not shift_types:
		return
	
	count = 0
	for i, emp in enumerate(employees[:3]):
		try:
			shift_assignment = frappe.get_doc({
				"doctype": "Shift Assignment",
				"employee": emp,
				"shift_type": shift_types[i % len(shift_types)],
				"start_date": getdate(),
				"company": company,
				"status": "Active"
			})
			shift_assignment.insert(ignore_permissions=True)
			count += 1
		except Exception as e:
			pass
	
	if count > 0:
		print(f"  ✓ Created {count} shift assignments")


def create_shift_requests(employees, shift_types):
	"""Create shift change requests"""
	if not employees or not shift_types:
		return
	
	count = 0
	for i, emp in enumerate(employees[:2]):
		try:
			shift_request = frappe.get_doc({
				"doctype": "Shift Request",
				"employee": emp,
				"from_date": add_days(getdate(), 7),
				"to_date": add_days(getdate(), 14),
				"shift_type": shift_types[0] if shift_types else None,
				"status": "Draft",
				"company": frappe.db.get_value("Employee", emp, "company")
			})
			shift_request.flags.ignore_mandatory = True
			shift_request.insert(ignore_permissions=True)
			count += 1
		except Exception as e:
			pass
	
	if count > 0:
		print(f"  ✓ Created {count} shift requests")


# ==================== IMPORTANT DocTypes ====================

def create_payroll_entries(employees, company):
	"""Create payroll entry"""
	if not employees:
		return
	
	try:
		payroll_entry = frappe.get_doc({
			"doctype": "Payroll Entry",
			"company": company,
			"posting_date": getdate(),
			"start_date": add_days(getdate(), -30),
			"end_date": add_days(getdate(), -1),
			"payroll_frequency": "Monthly"
		})
		payroll_entry.flags.ignore_mandatory = True
		payroll_entry.insert(ignore_permissions=True)
		print(f"  ✓ Created 1 payroll entry")
	except Exception as e:
		pass


def create_employee_advances(employees, company):
	"""Create employee advance payments"""
	if not employees:
		return
	
	count = 0
	for i, emp in enumerate(employees[:2]):
		try:
			advance = frappe.get_doc({
				"doctype": "Employee Advance",
				"employee": emp,
				"company": company,
				"posting_date": getdate(),
				"purpose": "Personal Emergency",
				"advance_amount": 1000 * (i + 1),
				"status": "Draft"
			})
			advance.insert(ignore_permissions=True)
			count += 1
		except Exception as e:
			pass
	
	if count > 0:
		print(f"  ✓ Created {count} employee advances")


def create_job_openings(designations, company):
	"""Create job openings"""
	if not designations:
		return []
	
	openings = []
	count = 0
	for i in range(3):
		try:
			job_opening = frappe.get_doc({
				"doctype": "Job Opening",
				"job_title": f"Open Position {i+1}",
				"designation": designations[i % len(designations)],
				"company": company,
				"status": "Open"
			})
			job_opening.insert(ignore_permissions=True)
			openings.append(job_opening.name)
			count += 1
		except Exception as e:
			pass
	
	if count > 0:
		print(f"  ✓ Created {count} job openings")
	return openings


def create_job_applicants(job_openings, company):
	"""Create job applicants"""
	if not job_openings:
		return []
	
	applicants = []
	count = 0
	for i, opening in enumerate(job_openings[:3]):
		try:
			applicant = frappe.get_doc({
				"doctype": "Job Applicant",
				"applicant_name": f"Candidate {i+1}",
				"email_id": f"candidate{i+1}@example.com",
				"job_title": opening,
				"status": "Open"
			})
			applicant.insert(ignore_permissions=True)
			applicants.append(applicant.name)
			count += 1
		except Exception as e:
			pass
	
	if count > 0:
		print(f"  ✓ Created {count} job applicants")
	
	return applicants


def create_interviews(designations):
	"""Create interview records"""
	if not designations:
		return
	
	# First check if we have any Job Applicants
	existing_applicants = frappe.get_all("Job Applicant", fields=["name"], limit=5)
	if not existing_applicants:
		return
	
	count = 0
	for i in range(min(2, len(existing_applicants))):
		try:
			interview = frappe.get_doc({
				"doctype": "Interview",
				"job_applicant": existing_applicants[i].name,
				"scheduled_on": add_days(getdate(), 5 + i),
				"from_time": "10:00:00",
				"to_time": "11:00:00",
				"status": "Pending",
				"designation": designations[0] if designations else None
			})
			interview.flags.ignore_mandatory = True
			interview.insert(ignore_permissions=True)
			count += 1
		except Exception as e:
			pass
	
	if count > 0:
		print(f"  ✓ Created {count} interviews")


def create_job_offers(job_applicants, designations, company):
	"""Create job offers"""
	if not job_applicants or not designations:
		return
	
	count = 0
	for i, applicant in enumerate(job_applicants[:2]):
		try:
			job_offer = frappe.get_doc({
				"doctype": "Job Offer",
				"job_applicant": applicant,
				"applicant_name": frappe.db.get_value("Job Applicant", applicant, "applicant_name"),
				"designation": designations[i % len(designations)],
				"company": company,
				"offer_date": getdate(),
				"status": "Awaiting Response"
			})
			job_offer.flags.ignore_mandatory = True
			job_offer.insert(ignore_permissions=True)
			count += 1
		except Exception as e:
			pass
	
	if count > 0:
		print(f"  ✓ Created {count} job offers")


def create_appraisals(employees, company):
	"""Create performance appraisals"""
	if not employees:
		return
	
	# First create appraisal cycle
	current_year = getdate().year
	cycle_name = f"{current_year} Performance Review"
	
	try:
		if not frappe.db.exists("Appraisal Cycle", cycle_name):
			cycle = frappe.get_doc({
				"doctype": "Appraisal Cycle",
				"cycle_name": cycle_name,
				"start_date": f"{current_year}-01-01",
				"end_date": f"{current_year}-12-31",
				"company": company
			})
			cycle.flags.ignore_mandatory = True
			cycle.insert(ignore_permissions=True)
			print(f"  ✓ Created: {cycle_name}")
	except Exception as e:
		pass
	
	count = 0
	for i, emp in enumerate(employees[:3]):
		try:
			appraisal = frappe.get_doc({
				"doctype": "Appraisal",
				"employee": emp,
				"company": company,
				"start_date": add_months(getdate(), -6),
				"end_date": getdate(),
				"status": "Draft",
				"appraisal_cycle": cycle_name
			})
			appraisal.flags.ignore_mandatory = True
			appraisal.insert(ignore_permissions=True)
			count += 1
		except Exception as e:
			pass
	
	if count > 0:
		print(f"  ✓ Created {count} appraisals")


def create_training_programs():
	"""Create training programs"""
	programs = []
	program_names = ["Leadership Development", "Technical Skills", "Communication Skills"]
	
	for prog_name in program_names:
		try:
			if frappe.db.exists("Training Program", prog_name):
				programs.append(prog_name)
				continue
			
			program = frappe.get_doc({
				"doctype": "Training Program",
				"training_program": prog_name,
				"description": f"Demo {prog_name} program"
			})
			program.flags.ignore_mandatory = True
			program.insert(ignore_permissions=True)
			programs.append(program.name)
			print(f"  ✓ Created: {prog_name}")
		except Exception as e:
			print(f"  ⚠ Training Program error ({prog_name}): {str(e)[:80]}")
	
	return programs


def create_training_events(training_programs, company):
	"""Create training events"""
	if not training_programs:
		return
	
	# Get company abbreviation for unique naming
	company_abbr = frappe.db.get_value("Company", company, "abbr") or "DEMO"
	
	count = 0
	for i, program in enumerate(training_programs[:2]):
		try:
			# Create unique event name per company
			event_name = f"{program} - {company_abbr} - Session {i+1}"
			
			# Check if already exists
			if frappe.db.exists("Training Event", event_name):
				continue
			
			event = frappe.get_doc({
				"doctype": "Training Event",
				"event_name": event_name,
				"training_program": program,
				"company": company,
				"start_time": add_days(getdate(), 10 + i),
				"end_time": add_days(getdate(), 12 + i),
				"status": "Scheduled"
			})
			event.flags.ignore_mandatory = True
			event.insert(ignore_permissions=True)
			count += 1
		except Exception as e:
			print(f"  ⚠ Training Event error: {str(e)[:80]}")
	
	if count > 0:
		print(f"  ✓ Created {count} training events")


# ==================== SPECIALIZED DocTypes ====================

def create_additional_salaries(employees, company):
	"""Create additional salary components"""
	if not employees:
		return
	
	# First create salary component
	try:
		if not frappe.db.exists("Salary Component", "Bonus"):
			component = frappe.get_doc({
				"doctype": "Salary Component",
				"salary_component": "Bonus",
				"type": "Earning"
			})
			component.insert(ignore_permissions=True)
	except Exception as e:
		print(f"  ⚠ Salary Component creation error: {str(e)[:80]}")
	
	count = 0
	for i, emp in enumerate(employees[:2]):
		try:
			additional_salary = frappe.get_doc({
				"doctype": "Additional Salary",
				"employee": emp,
				"company": company,
				"salary_component": "Bonus",
				"amount": 500,
				"payroll_date": getdate(),
				"type": "Earning"
			})
			additional_salary.flags.ignore_mandatory = True
			additional_salary.insert(ignore_permissions=True)
			count += 1
		except Exception as e:
			print(f"  ⚠ Additional Salary error: {str(e)[:80]}")
	
	if count > 0:
		print(f"  ✓ Created {count} additional salaries")


def create_employee_incentives(employees, company):
	"""Create employee incentive records"""
	if not employees:
		return
	
	count = 0
	for i, emp in enumerate(employees[:2]):
		try:
			incentive = frappe.get_doc({
				"doctype": "Employee Incentive",
				"employee": emp,
				"company": company,
				"incentive_amount": 1000,
				"payroll_date": getdate()
			})
			incentive.flags.ignore_mandatory = True
			incentive.insert(ignore_permissions=True)
			count += 1
		except Exception as e:
			print(f"  ⚠ Employee Incentive error: {str(e)[:80]}")
	
	if count > 0:
		print(f"  ✓ Created {count} employee incentives")


def create_employee_onboardings(employees, company):
	"""Create employee onboarding records"""
	# Get company abbreviation for unique naming
	company_abbr = frappe.db.get_value("Company", company, "abbr") or "DEMO"
	
	count = 0
	for i in range(1):
		try:
			# Create unique employee name per company
			employee_name = f"New Hire {company_abbr}-{i+1}"
			
			onboarding = frappe.get_doc({
				"doctype": "Employee Onboarding",
				"employee_name": employee_name,
				"company": company,
				"date_of_joining": add_days(getdate(), 15 + i),
				"status": "Pending"
			})
			onboarding.flags.ignore_mandatory = True
			onboarding.insert(ignore_permissions=True)
			count += 1
		except Exception as e:
			print(f"  ⚠ Employee Onboarding error: {str(e)[:80]}")
	
	if count > 0:
		print(f"  ✓ Created {count} employee onboardings")


def create_employee_separations(employees, company):
	"""Create employee separation records"""
	count = 0
	for i in range(1):
		try:
			separation = frappe.get_doc({
				"doctype": "Employee Separation",
				"employee_name": f"Departing Employee {i+1}",
				"company": company,
				"resignation_letter_date": getdate(),
				"status": "Pending"
			})
			separation.flags.ignore_mandatory = True
			separation.insert(ignore_permissions=True)
			count += 1
		except Exception as e:
			pass
	
	if count > 0:
		print(f"  ✓ Created {count} employee separations")


def create_employee_transfers(employees, departments):
	"""Create employee transfer records"""
	if not employees or not departments or len(departments) < 2:
		return
	
	count = 0
	for i, emp in enumerate(employees[:2]):
		try:
			transfer = frappe.get_doc({
				"doctype": "Employee Transfer",
				"employee": emp,
				"transfer_date": add_days(getdate(), 30),
				"new_department": departments[(i + 1) % len(departments)],
				"company": frappe.db.get_value("Employee", emp, "company")
			})
			transfer.flags.ignore_mandatory = True
			transfer.insert(ignore_permissions=True)
			count += 1
		except Exception as e:
			pass
	
	if count > 0:
		print(f"  ✓ Created {count} employee transfers")


def create_employee_promotions(employees, designations):
	"""Create employee promotion records"""
	if not employees or not designations or len(designations) < 2:
		return
	
	count = 0
	for i, emp in enumerate(employees[:2]):
		try:
			promotion = frappe.get_doc({
				"doctype": "Employee Promotion",
				"employee": emp,
				"promotion_date": add_days(getdate(), 60),
				"new_designation": designations[(i + 1) % len(designations)]
			})
			promotion.insert(ignore_permissions=True)
			count += 1
		except Exception as e:
			pass
	
	if count > 0:
		print(f"  ✓ Created {count} employee promotions")


def create_travel_requests(employees, company):
	"""Create travel request records"""
	if not employees:
		return
	
	# First create Purpose of Travel
	purposes = ["Business Meeting", "Client Visit", "Training"]
	for purpose in purposes:
		try:
			if not frappe.db.exists("Purpose of Travel", purpose):
				doc = frappe.get_doc({
					"doctype": "Purpose of Travel",
					"purpose_of_travel": purpose
				})
				doc.insert(ignore_permissions=True)
		except Exception as e:
			pass
	
	count = 0
	for i, emp in enumerate(employees[:2]):
		try:
			travel = frappe.get_doc({
				"doctype": "Travel Request",
				"employee": emp,
				"company": company,
				"from_date": add_days(getdate(), 20 + i),
				"to_date": add_days(getdate(), 25 + i),
				"purpose_of_travel": purposes[i % len(purposes)],
				"travel_type": "Domestic"
			})
			travel.flags.ignore_mandatory = True
			travel.insert(ignore_permissions=True)
			count += 1
		except Exception as e:
			pass
	
	if count > 0:
		print(f"  ✓ Created {count} travel requests")


def create_vehicle_logs(employees, company):
	"""Create vehicle log records"""
	if not employees:
		return
	
	# First create vehicles
	vehicles = []
	for i in range(2):
		try:
			plate = f"ABC-{123+i*100}"
			if not frappe.db.exists("Vehicle", plate):
				vehicle = frappe.get_doc({
					"doctype": "Vehicle",
					"license_plate": plate,
					"make": "Toyota",
					"model": "Camry"
				})
				vehicle.flags.ignore_mandatory = True
				vehicle.insert(ignore_permissions=True)
				vehicles.append(plate)
		except Exception as e:
			pass
	
	if not vehicles:
		return
	
	count = 0
	for i, emp in enumerate(employees[:2]):
		try:
			vehicle_log = frappe.get_doc({
				"doctype": "Vehicle Log",
				"employee": emp,
				"date": getdate(),
				"odometer": 1000 + (i * 100),
				"purpose": "Business Travel",
				"license_plate": vehicles[i % len(vehicles)]
			})
			vehicle_log.flags.ignore_mandatory = True
			vehicle_log.insert(ignore_permissions=True)
			count += 1
		except Exception as e:
			pass
	
	if count > 0:
		print(f"  ✓ Created {count} vehicle logs")


def create_goals(employees, company):
	"""Create employee goals"""
	if not employees:
		return
	
	count = 0
	for i, emp in enumerate(employees[:3]):
		try:
			goal = frappe.get_doc({
				"doctype": "Goal",
				"employee": emp,
				"goal_name": f"Quarterly Goal {i+1}",
				"start_date": getdate(),
				"end_date": add_months(getdate(), 3),
				"status": "Active"
			})
			goal.insert(ignore_permissions=True)
			count += 1
		except Exception as e:
			pass
	
	if count > 0:
		print(f"  ✓ Created {count} goals")