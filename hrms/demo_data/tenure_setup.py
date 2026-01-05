"""
Tenure Setup - Demo Data Generator for HRMS Employee Lifecycle

This script initializes employee lifecycle/tenure activities including:
- Employee Onboarding Templates and Onboardings
- Training Programs, Events, Results, and Feedback
- Skills and Employee Skill Maps
- Employee Promotions and Transfers
- Employee Separation Templates, Separations, Exit Interviews, F&F Statements
- Grievance Types and Employee Grievances
- Daily Work Summary Groups and Summaries

Usage: 
    bench --site [sitename] execute hrms.demo_data.tenure_setup.create_tenure_data
    Or with company:
    bench --site [sitename] execute hrms.demo_data.tenure_setup.create_tenure_data --kwargs '{"company": "NovaSoft"}'

Author: Generated for HRMS Demo
Version: 1.0.0
"""

import frappe
from frappe.utils import getdate, add_days, add_months, nowdate, now_datetime
import random


def create_tenure_data(company="NovaSoft"):
    """
    Create comprehensive employee lifecycle demo data for HRMS testing.
    Should be run AFTER company_setup.py and recruitment_setup.py have been executed.
    """
    frappe.set_user("Administrator")
    
    print(f"\n{'='*60}")
    print(f"Creating Employee Lifecycle Data for Company: {company}")
    print(f"{'='*60}\n")
    
    # Verify company exists
    if not frappe.db.exists("Company", company):
        print(f"❌ Company '{company}' not found. Please run company_setup.py first.")
        return
    
    # Get company abbreviation
    company_abbr = frappe.db.get_value("Company", company, "abbr")
    
    # ===================== ONBOARDING =====================
    # 1. Create Onboarding Templates
    print("📋 Creating Onboarding Templates...")
    onboarding_templates = create_onboarding_templates(company, company_abbr)
    frappe.db.commit()
    
    # 2. Create Employee Onboardings (requires job applicants/offers from recruitment_setup)
    print("🚀 Creating Employee Onboardings...")
    onboardings = create_employee_onboardings(company, onboarding_templates)
    frappe.db.commit()
    
    # ===================== TRAINING =====================
    # 3. Create Training Programs
    print("📚 Creating Training Programs...")
    training_programs = create_training_programs(company)
    frappe.db.commit()
    
    # 4. Create Training Events
    print("📅 Creating Training Events...")
    training_events = create_training_events(company, training_programs)
    frappe.db.commit()
    
    # 5. Create Training Results
    print("📊 Creating Training Results...")
    training_results = create_training_results(training_events)
    frappe.db.commit()
    
    # 6. Create Training Feedback
    print("💬 Creating Training Feedback...")
    training_feedback = create_training_feedback(training_events)
    frappe.db.commit()
    
    # ===================== SKILLS =====================
    # 7. Create Skills
    print("🛠️ Creating Skills...")
    skills = create_skills()
    frappe.db.commit()
    
    # 8. Create Employee Skill Maps
    print("🗺️ Creating Employee Skill Maps...")
    skill_maps = create_employee_skill_maps(company, skills, training_events)
    frappe.db.commit()
    
    # ===================== LIFECYCLE EVENTS =====================
    # 9. Create Employee Promotions
    print("📈 Creating Employee Promotions...")
    promotions = create_employee_promotions(company, company_abbr)
    frappe.db.commit()
    
    # 10. Create Employee Transfers
    print("🔄 Creating Employee Transfers...")
    transfers = create_employee_transfers(company, company_abbr)
    frappe.db.commit()
    
    # ===================== SEPARATION =====================
    # 11. Create Separation Templates
    print("📋 Creating Separation Templates...")
    separation_templates = create_separation_templates(company, company_abbr)
    frappe.db.commit()
    
    # 12. Create Employee Separations
    print("👋 Creating Employee Separations...")
    separations = create_employee_separations(company, separation_templates)
    frappe.db.commit()
    
    # 13. Create Exit Interviews
    print("🎤 Creating Exit Interviews...")
    exit_interviews = create_exit_interviews(company, separations)
    frappe.db.commit()
    
    # 14. Create Full and Final Statements
    print("💰 Creating Full and Final Statements...")
    fnf_statements = create_fnf_statements(company, separations)
    frappe.db.commit()
    
    # ===================== GRIEVANCES =====================
    # 15. Create Grievance Types
    print("📝 Creating Grievance Types...")
    grievance_types = create_grievance_types()
    frappe.db.commit()
    
    # 16. Create Employee Grievances
    print("⚠️ Creating Employee Grievances...")
    grievances = create_employee_grievances(company, grievance_types)
    frappe.db.commit()
    
    # ===================== DAILY WORK SUMMARY =====================
    # 17. Create Daily Work Summary Groups
    print("📧 Creating Daily Work Summary Groups...")
    summary_groups = create_daily_work_summary_groups(company)
    frappe.db.commit()
    
    # 18. Create Daily Work Summaries
    print("📝 Creating Daily Work Summaries...")
    summaries = create_daily_work_summaries(summary_groups)
    frappe.db.commit()
    
    print(f"\n{'='*60}")
    print("✅ Employee Lifecycle Data Creation Complete!")
    print(f"{'='*60}")
    print(f"\nCreated:")
    print(f"  - {len(onboarding_templates)} Onboarding Templates")
    print(f"  - {len(onboardings)} Employee Onboardings")
    print(f"  - {len(training_programs)} Training Programs")
    print(f"  - {len(training_events)} Training Events")
    print(f"  - {len(training_results)} Training Results")
    print(f"  - {len(training_feedback)} Training Feedback Records")
    print(f"  - {len(skills)} Skills")
    print(f"  - {len(skill_maps)} Employee Skill Maps")
    print(f"  - {len(promotions)} Employee Promotions")
    print(f"  - {len(transfers)} Employee Transfers")
    print(f"  - {len(separation_templates)} Separation Templates")
    print(f"  - {len(separations)} Employee Separations")
    print(f"  - {len(exit_interviews)} Exit Interviews")
    print(f"  - {len(fnf_statements)} Full and Final Statements")
    print(f"  - {len(grievance_types)} Grievance Types")
    print(f"  - {len(grievances)} Employee Grievances")
    print(f"  - {len(summary_groups)} Daily Work Summary Groups")
    print(f"  - {len(summaries)} Daily Work Summaries")
    print(f"\n{'='*60}\n")


# ============================================================================
# ONBOARDING MODULE
# ============================================================================

def create_onboarding_templates(company, company_abbr):
    """Create onboarding templates for different departments/roles"""
    
    templates_data = [
        {
            "title": "Engineering Onboarding",
            "department": f"Research & Development - {company_abbr}",
            "activities": [
                {"activity_name": "Setup Development Environment", "user": None, "role": "System Manager", "begin_on": 0, "duration": 1, "description": "Install IDEs, configure Git, setup local development environment"},
                {"activity_name": "Access to Code Repositories", "user": None, "role": "System Manager", "begin_on": 0, "duration": 1, "description": "Grant access to GitHub/GitLab repositories"},
                {"activity_name": "Security Training", "user": None, "role": "HR Manager", "begin_on": 1, "duration": 2, "description": "Complete mandatory security awareness training"},
                {"activity_name": "Architecture Overview", "user": None, "role": "System Manager", "begin_on": 2, "duration": 3, "description": "Review system architecture and design patterns"},
                {"activity_name": "Pair Programming Session", "user": None, "role": "System Manager", "begin_on": 5, "duration": 5, "description": "Work with a senior engineer on first tasks"},
                {"activity_name": "First PR Review", "user": None, "role": "System Manager", "begin_on": 10, "duration": 4, "description": "Complete first pull request with code review"},
            ]
        },
        {
            "title": "Sales Onboarding",
            "department": f"Sales - {company_abbr}",
            "activities": [
                {"activity_name": "CRM System Training", "user": None, "role": "HR Manager", "begin_on": 0, "duration": 2, "description": "Learn to use the CRM system for tracking leads and opportunities"},
                {"activity_name": "Product Knowledge Training", "user": None, "role": "HR Manager", "begin_on": 2, "duration": 3, "description": "Deep dive into product features, benefits, and competitive positioning"},
                {"activity_name": "Sales Playbook Review", "user": None, "role": "HR Manager", "begin_on": 3, "duration": 2, "description": "Review sales methodology, scripts, and best practices"},
                {"activity_name": "Shadow Senior Sales Rep", "user": None, "role": "HR Manager", "begin_on": 5, "duration": 5, "description": "Observe sales calls and meetings with experienced rep"},
                {"activity_name": "First Sales Call (Supervised)", "user": None, "role": "HR Manager", "begin_on": 10, "duration": 2, "description": "Make first supervised sales call with feedback"},
            ]
        },
        {
            "title": "HR Onboarding",
            "department": f"Human Resources - {company_abbr}",
            "activities": [
                {"activity_name": "HRMS System Training", "user": None, "role": "HR Manager", "begin_on": 0, "duration": 3, "description": "Learn to use Frappe HRMS for employee management"},
                {"activity_name": "Policy and Compliance Review", "user": None, "role": "HR Manager", "begin_on": 1, "duration": 2, "description": "Review company policies, labor laws, and compliance requirements"},
                {"activity_name": "Benefits Administration Training", "user": None, "role": "HR Manager", "begin_on": 3, "duration": 2, "description": "Learn benefits enrollment and administration processes"},
                {"activity_name": "Payroll Process Overview", "user": None, "role": "HR Manager", "begin_on": 5, "duration": 2, "description": "Understand payroll cycles, deductions, and processing"},
                {"activity_name": "Employee Relations Workshop", "user": None, "role": "HR Manager", "begin_on": 7, "duration": 3, "description": "Learn conflict resolution and employee relations best practices"},
            ]
        },
        {
            "title": "General Onboarding",
            "department": None,
            "activities": [
                {"activity_name": "Welcome and Office Tour", "user": None, "role": "HR Manager", "begin_on": 0, "duration": 1, "description": "Introduction to the office, facilities, and team members"},
                {"activity_name": "IT Setup and Equipment", "user": None, "role": "System Manager", "begin_on": 0, "duration": 1, "description": "Laptop setup, email configuration, and access credentials", "required_for_employee_creation": 1},
                {"activity_name": "HR Paperwork and Benefits", "user": None, "role": "HR Manager", "begin_on": 0, "duration": 2, "description": "Complete employment forms, tax documents, and benefits enrollment", "required_for_employee_creation": 1},
                {"activity_name": "Company Culture Training", "user": None, "role": "HR Manager", "begin_on": 1, "duration": 1, "description": "Learn about company values, mission, and culture"},
                {"activity_name": "Team Introduction Meeting", "user": None, "role": "HR Manager", "begin_on": 2, "duration": 1, "description": "Meet with direct team and understand team dynamics"},
                {"activity_name": "Manager 1:1 Meeting", "user": None, "role": "HR Manager", "begin_on": 3, "duration": 1, "description": "Initial meeting with manager to discuss expectations and goals"},
            ]
        },
    ]
    
    created_templates = []
    
    for template_data in templates_data:
        try:
            if frappe.db.exists("Employee Onboarding Template", {"title": template_data["title"]}):
                print(f"  ↻ Already exists: {template_data['title']}")
                existing = frappe.get_doc("Employee Onboarding Template", {"title": template_data["title"]})
                created_templates.append(existing.name)
                continue
            
            activities = []
            for activity in template_data["activities"]:
                activities.append({
                    "activity_name": activity["activity_name"],
                    "user": activity.get("user"),
                    "role": activity.get("role"),
                    "begin_on": activity.get("begin_on", 0),
                    "duration": activity.get("duration", 1),
                    "description": activity.get("description", ""),
                    "required_for_employee_creation": activity.get("required_for_employee_creation", 0)
                })
            
            doc = frappe.get_doc({
                "doctype": "Employee Onboarding Template",
                "title": template_data["title"],
                "company": company,
                "department": template_data.get("department"),
                "activities": activities
            })
            doc.insert(ignore_permissions=True)
            created_templates.append(doc.name)
            print(f"  ✓ Created: {template_data['title']}")
            
        except Exception as e:
            print(f"  ⚠ Error creating template {template_data['title']}: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_templates)} onboarding templates")
    return created_templates


def create_employee_onboardings(company, onboarding_templates):
    """Create employee onboarding records for recent hires"""
    
    created_onboardings = []
    
    # Get the general onboarding template
    general_template = None
    for template in onboarding_templates:
        if "General" in template:
            general_template = template
            break
    
    if not general_template and onboarding_templates:
        general_template = onboarding_templates[0]
    
    # Get job offers (any status) from recruitment_setup
    job_offers = frappe.get_all(
        "Job Offer",
        filters={"company": company},
        fields=["name", "job_applicant", "designation", "status"],
        limit=10
    )
    
    # First, create onboardings for job offers
    for job_offer in job_offers:
        try:
            # Check if onboarding already exists for this job offer
            if frappe.db.exists("Employee Onboarding", {"job_offer": job_offer.name}):
                print(f"  ↻ Already exists for job offer: {job_offer.name}")
                continue
            
            # Get job applicant details
            applicant = frappe.get_doc("Job Applicant", job_offer.job_applicant)
            
            # Determine which template to use based on designation
            template_to_use = general_template
            for template in onboarding_templates:
                if "Engineering" in template and ("Engineer" in (job_offer.designation or "") or "Developer" in (job_offer.designation or "")):
                    template_to_use = template
                    break
                elif "Sales" in template and ("Sales" in (job_offer.designation or "") or "SDR" in (job_offer.designation or "")):
                    template_to_use = template
                    break
                elif "HR" in template and ("HR" in (job_offer.designation or "") or "Recruit" in (job_offer.designation or "")):
                    template_to_use = template
                    break
            
            # Create the onboarding document
            boarding_begins = add_days(getdate(nowdate()), random.randint(-30, 7))
            date_of_joining = add_days(boarding_begins, random.randint(0, 7))
            
            # Determine status based on job offer status
            if job_offer.status == "Accepted":
                boarding_status = random.choice(["In Process", "Completed"])
            else:
                boarding_status = "Pending"
            
            doc = frappe.get_doc({
                "doctype": "Employee Onboarding",
                "job_applicant": job_offer.job_applicant,
                "job_offer": job_offer.name,
                "employee_name": applicant.applicant_name,
                "employee_onboarding_template": template_to_use,
                "company": company,
                "boarding_begins_on": boarding_begins,
                "date_of_joining": date_of_joining,
                "boarding_status": boarding_status,
                "notify_users_by_email": 0
            })
            doc.insert(ignore_permissions=True)
            
            # Submit if status is not Pending
            if doc.boarding_status in ["In Process", "Completed"]:
                doc.submit()
            
            created_onboardings.append(doc.name)
            print(f"  ✓ Created: {doc.name} for {applicant.applicant_name} ({boarding_status})")
            
        except Exception as e:
            print(f"  ⚠ Error creating onboarding for {job_offer.name}: {str(e)[:60]}")
    
    # If we don't have enough onboardings from job offers, create demo onboardings
    # by using job applicants directly (without job offers)
    if len(created_onboardings) < 5:
        # Job Applicant doesn't have a company field, so we filter by status only
        job_applicants = frappe.get_all(
            "Job Applicant",
            filters={"status": ["in", ["Open", "Replied", "Hold"]]},
            fields=["name", "applicant_name", "designation"],
            limit=8
        )
        
        for applicant_data in job_applicants:
            if len(created_onboardings) >= 8:
                break
                
            try:
                # Check if onboarding already exists for this applicant
                if frappe.db.exists("Employee Onboarding", {"job_applicant": applicant_data.name}):
                    continue
                
                # Need to find or create a job offer for this applicant
                existing_offer = frappe.get_all(
                    "Job Offer",
                    filters={"job_applicant": applicant_data.name},
                    limit=1
                )
                
                if not existing_offer:
                    # Create a simple job offer for the applicant
                    job_offer_doc = frappe.get_doc({
                        "doctype": "Job Offer",
                        "job_applicant": applicant_data.name,
                        "applicant_name": applicant_data.applicant_name,
                        "company": company,
                        "designation": applicant_data.designation or "Backend Engineer",
                        "offer_date": add_days(getdate(nowdate()), random.randint(-14, 0)),
                        "status": "Accepted"
                    })
                    job_offer_doc.insert(ignore_permissions=True)
                    offer_name = job_offer_doc.name
                else:
                    offer_name = existing_offer[0].name
                
                template_to_use = general_template
                
                boarding_begins = add_days(getdate(nowdate()), random.randint(-21, 14))
                date_of_joining = add_days(boarding_begins, random.randint(0, 7))
                boarding_status = random.choice(["Pending", "In Process", "Completed"])
                
                doc = frappe.get_doc({
                    "doctype": "Employee Onboarding",
                    "job_applicant": applicant_data.name,
                    "job_offer": offer_name,
                    "employee_name": applicant_data.applicant_name,
                    "employee_onboarding_template": template_to_use,
                    "company": company,
                    "boarding_begins_on": boarding_begins,
                    "date_of_joining": date_of_joining,
                    "boarding_status": boarding_status,
                    "notify_users_by_email": 0
                })
                doc.insert(ignore_permissions=True)
                
                if doc.boarding_status in ["In Process", "Completed"]:
                    doc.submit()
                
                created_onboardings.append(doc.name)
                print(f"  ✓ Created: {doc.name} for {applicant_data.applicant_name} ({boarding_status})")
                
            except Exception as e:
                print(f"  ⚠ Error creating onboarding: {str(e)[:60]}")
    
    if not created_onboardings:
        print("  ⚠ No job offers or applicants found. Run recruitment_setup.py first.")
    
    print(f"  ✓ Created {len(created_onboardings)} employee onboardings")
    return created_onboardings


# ============================================================================
# TRAINING MODULE
# ============================================================================

def create_training_programs(company):
    """Create training programs"""
    
    programs_data = [
        {
            "training_program": "New Employee Orientation",
            "status": "Scheduled",
            "trainer_name": "HR Training Team",
            "trainer_email": "training@company.com",
            "description": "<p>Comprehensive orientation program for all new employees covering company policies, culture, and basic tools.</p>"
        },
        {
            "training_program": "Leadership Development Program",
            "status": "Scheduled",
            "trainer_name": "External Consulting Group",
            "trainer_email": "leadership@consulting.com",
            "description": "<p>Advanced leadership training for managers and team leads focusing on communication, delegation, and strategic thinking.</p>"
        },
        {
            "training_program": "Technical Skills Bootcamp",
            "status": "Scheduled",
            "trainer_name": "Engineering Team Leads",
            "trainer_email": "engineering@company.com",
            "description": "<p>Intensive technical training covering modern development practices, cloud infrastructure, and best practices.</p>"
        },
        {
            "training_program": "Sales Excellence Workshop",
            "status": "Scheduled",
            "trainer_name": "Sales Training Partners",
            "trainer_email": "sales.training@partners.com",
            "description": "<p>Sales methodology, negotiation techniques, and customer relationship management training.</p>"
        },
        {
            "training_program": "Data Privacy and Security",
            "status": "Completed",
            "trainer_name": "Security Team",
            "trainer_email": "security@company.com",
            "description": "<p>Mandatory training on data protection, GDPR compliance, and security best practices.</p>"
        },
        {
            "training_program": "Diversity and Inclusion Workshop",
            "status": "Scheduled",
            "trainer_name": "D&I Committee",
            "trainer_email": "diversity@company.com",
            "description": "<p>Building an inclusive workplace culture through awareness, empathy, and best practices.</p>"
        },
    ]
    
    created_programs = []
    
    for program_data in programs_data:
        try:
            if frappe.db.exists("Training Program", program_data["training_program"]):
                print(f"  ↻ Already exists: {program_data['training_program']}")
                created_programs.append(program_data["training_program"])
                continue
            
            doc = frappe.get_doc({
                "doctype": "Training Program",
                "training_program": program_data["training_program"],
                "status": program_data["status"],
                "company": company,
                "trainer_name": program_data["trainer_name"],
                "trainer_email": program_data["trainer_email"],
                "description": program_data["description"]
            })
            doc.insert(ignore_permissions=True)
            created_programs.append(doc.name)
            print(f"  ✓ Created: {program_data['training_program']}")
            
        except Exception as e:
            print(f"  ⚠ Error creating program {program_data['training_program']}: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_programs)} training programs")
    return created_programs


def create_training_events(company, training_programs):
    """Create training events with employee attendees"""
    
    # Get active employees for this company
    employees = frappe.get_all(
        "Employee",
        filters={"company": company, "status": "Active"},
        fields=["name", "employee_name", "department"]
    )
    
    if not employees:
        print("  ⚠ No active employees found")
        return []
    
    events_data = [
        {
            "event_name": "Q1 New Employee Orientation Batch 1",
            "training_program": "New Employee Orientation",
            "type": "Seminar",
            "level": "Beginner",
            "event_status": "Completed",
            "location": "Main Conference Room A",
            "course": "Company Orientation",
            "introduction": "<p>Welcome to the company! This orientation covers everything you need to know to get started.</p>",
            "start_offset_days": -60,
            "duration_hours": 8,
            "employee_count": 8
        },
        {
            "event_name": "Leadership Workshop - Spring 2025",
            "training_program": "Leadership Development Program",
            "type": "Workshop",
            "level": "Intermediate",
            "event_status": "Completed",
            "location": "Executive Training Center",
            "course": "Leadership Fundamentals",
            "introduction": "<p>This workshop focuses on developing leadership skills for current and aspiring managers.</p>",
            "start_offset_days": -45,
            "duration_hours": 16,
            "employee_count": 6
        },
        {
            "event_name": "Cloud Architecture Deep Dive",
            "training_program": "Technical Skills Bootcamp",
            "type": "Workshop",
            "level": "Advance",
            "event_status": "Scheduled",
            "location": "Tech Lab 2",
            "course": "AWS/Cloud Infrastructure",
            "introduction": "<p>Advanced training on cloud architecture patterns, AWS services, and infrastructure as code.</p>",
            "start_offset_days": 14,
            "duration_hours": 24,
            "employee_count": 10
        },
        {
            "event_name": "Sales Methodology Certification",
            "training_program": "Sales Excellence Workshop",
            "type": "Seminar",
            "level": "Intermediate",
            "event_status": "Scheduled",
            "location": "Sales Training Room",
            "course": "MEDDIC Sales Methodology",
            "has_certificate": 1,
            "introduction": "<p>Certification course on the MEDDIC sales methodology for enterprise sales.</p>",
            "start_offset_days": 21,
            "duration_hours": 12,
            "employee_count": 7
        },
        {
            "event_name": "Annual Security Awareness Training",
            "training_program": "Data Privacy and Security",
            "type": "Internet",
            "level": "",
            "event_status": "Completed",
            "location": "Online",
            "course": "Security Awareness 2025",
            "introduction": "<p>Mandatory annual security awareness training covering phishing, data protection, and security best practices.</p>",
            "start_offset_days": -30,
            "duration_hours": 2,
            "employee_count": 15
        },
    ]
    
    created_events = []
    
    for event_data in events_data:
        try:
            if frappe.db.exists("Training Event", event_data["event_name"]):
                print(f"  ↻ Already exists: {event_data['event_name']}")
                created_events.append(event_data["event_name"])
                continue
            
            # Calculate dates
            start_time = add_days(getdate(nowdate()), event_data["start_offset_days"])
            start_datetime = f"{start_time} 09:00:00"
            end_datetime = f"{start_time} {9 + min(event_data['duration_hours'], 8)}:00:00"
            
            # Select random employees for this event
            selected_employees = random.sample(employees, min(event_data["employee_count"], len(employees)))
            
            employee_rows = []
            for emp in selected_employees:
                status = "Completed" if event_data["event_status"] == "Completed" else "Open"
                employee_rows.append({
                    "employee": emp.name,
                    "employee_name": emp.employee_name,
                    "department": emp.department,
                    "status": status,
                    "attendance": "Present" if event_data["event_status"] == "Completed" else "",
                    "is_mandatory": 1 if "Security" in event_data["event_name"] else 0
                })
            
            # Find the training program
            training_program = None
            if event_data["training_program"] in training_programs:
                training_program = event_data["training_program"]
            
            doc = frappe.get_doc({
                "doctype": "Training Event",
                "event_name": event_data["event_name"],
                "training_program": training_program,
                "type": event_data["type"],
                "level": event_data.get("level", ""),
                "event_status": event_data["event_status"],
                "has_certificate": event_data.get("has_certificate", 0),
                "company": company,
                "location": event_data["location"],
                "course": event_data["course"],
                "start_time": start_datetime,
                "end_time": end_datetime,
                "introduction": event_data["introduction"],
                "employees": employee_rows
            })
            doc.insert(ignore_permissions=True)
            
            # Submit if completed
            if event_data["event_status"] == "Completed":
                doc.submit()
            
            created_events.append(doc.name)
            print(f"  ✓ Created: {event_data['event_name']} ({len(employee_rows)} attendees)")
            
        except Exception as e:
            print(f"  ⚠ Error creating event {event_data['event_name']}: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_events)} training events")
    return created_events


def create_training_results(training_events):
    """Create training results for completed events"""
    
    created_results = []
    grades = ["A", "A-", "B+", "B", "B-", "C+", "C"]
    
    for event_name in training_events:
        try:
            event = frappe.get_doc("Training Event", event_name)
            
            # Only create results for completed events
            if event.event_status != "Completed":
                continue
            
            # Check if result already exists
            if frappe.db.exists("Training Result", {"training_event": event_name}):
                print(f"  ↻ Already exists for: {event_name}")
                continue
            
            employee_results = []
            for emp in event.employees:
                if emp.attendance == "Present":
                    employee_results.append({
                        "employee": emp.employee,
                        "employee_name": emp.employee_name,
                        "department": emp.department,
                        "hours": random.uniform(2, 8),
                        "grade": random.choice(grades),
                        "comments": random.choice([
                            "Excellent participation and understanding",
                            "Good engagement throughout the session",
                            "Solid performance, room for improvement",
                            "Active learner, asked great questions",
                            "Completed all exercises successfully"
                        ])
                    })
            
            if not employee_results:
                continue
            
            doc = frappe.get_doc({
                "doctype": "Training Result",
                "training_event": event_name,
                "employees": employee_results
            })
            doc.insert(ignore_permissions=True)
            doc.submit()
            
            created_results.append(doc.name)
            print(f"  ✓ Created result for: {event_name}")
            
        except Exception as e:
            print(f"  ⚠ Error creating result for {event_name}: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_results)} training results")
    return created_results


def create_training_feedback(training_events):
    """Create training feedback from employees for completed events"""
    
    created_feedback = []
    
    feedback_templates = [
        "The training was very informative and well-structured. I learned a lot about {topic} and feel more confident in my role.",
        "Great session! The trainer was knowledgeable and engaging. Would recommend improvements in the hands-on exercises.",
        "Excellent training on {topic}. The real-world examples were particularly helpful. Looking forward to applying these learnings.",
        "Good overview of {topic}. The pace was appropriate and the materials were well-prepared.",
        "Very valuable training. The interactive discussions helped reinforce the key concepts around {topic}.",
    ]
    
    for event_name in training_events:
        try:
            event = frappe.get_doc("Training Event", event_name)
            
            # Only create feedback for completed events
            if event.event_status != "Completed":
                continue
            
            # Select a subset of attendees to provide feedback
            feedback_count = min(3, len(event.employees))
            selected_employees = random.sample(list(event.employees), feedback_count)
            
            for emp in selected_employees:
                # Check if feedback already exists
                if frappe.db.exists("Training Feedback", {
                    "employee": emp.employee,
                    "training_event": event_name
                }):
                    continue
                
                topic = event.course or event.event_name
                feedback_text = random.choice(feedback_templates).format(topic=topic)
                
                doc = frappe.get_doc({
                    "doctype": "Training Feedback",
                    "employee": emp.employee,
                    "training_event": event_name,
                    "feedback": feedback_text
                })
                doc.insert(ignore_permissions=True)
                doc.submit()
                
                created_feedback.append(doc.name)
            
            if feedback_count > 0:
                print(f"  ✓ Created {feedback_count} feedback for: {event_name}")
            
        except Exception as e:
            print(f"  ⚠ Error creating feedback for {event_name}: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_feedback)} training feedback records")
    return created_feedback


# ============================================================================
# SKILLS MODULE
# ============================================================================

def create_skills():
    """Create skill master data"""
    
    skills_data = [
        # Technical Skills
        "Python", "JavaScript", "TypeScript", "React", "Vue.js", "Node.js",
        "SQL", "PostgreSQL", "MongoDB", "Redis",
        "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes",
        "Git", "CI/CD", "Agile/Scrum", "DevOps",
        "Machine Learning", "Data Analysis", "Data Visualization",
        "API Design", "Microservices", "System Design",
        # Soft Skills
        "Communication", "Leadership", "Problem Solving", "Critical Thinking",
        "Team Collaboration", "Project Management", "Time Management",
        "Presentation Skills", "Negotiation", "Conflict Resolution",
        # Business Skills
        "Sales", "Marketing", "Customer Service", "Business Analysis",
        "Financial Analysis", "Strategic Planning", "Risk Management",
        "HR Management", "Recruitment", "Employee Relations",
    ]
    
    created_skills = []
    
    for skill_name in skills_data:
        try:
            if frappe.db.exists("Skill", skill_name):
                created_skills.append(skill_name)
                continue
            
            doc = frappe.get_doc({
                "doctype": "Skill",
                "skill_name": skill_name
            })
            doc.insert(ignore_permissions=True)
            created_skills.append(doc.name)
            
        except Exception as e:
            print(f"  ⚠ Error creating skill {skill_name}: {str(e)[:40]}")
    
    print(f"  ✓ Created/verified {len(created_skills)} skills")
    return created_skills


def create_employee_skill_maps(company, skills, training_events):
    """Create employee skill maps with skills and trainings"""
    
    # Get active employees
    employees = frappe.get_all(
        "Employee",
        filters={"company": company, "status": "Active"},
        fields=["name", "employee_name", "designation", "department"],
        limit=20  # Create skill maps for up to 20 employees
    )
    
    # Skill mapping by department/role
    department_skills = {
        "Research & Development": ["Python", "JavaScript", "Git", "AWS", "Docker", "API Design", "Agile/Scrum", "Problem Solving"],
        "Sales": ["Sales", "Negotiation", "Communication", "Presentation Skills", "CRM", "Customer Service"],
        "Marketing": ["Marketing", "Data Analysis", "Communication", "Presentation Skills", "SEO", "Content Strategy"],
        "Human Resources": ["HR Management", "Recruitment", "Employee Relations", "Communication", "Conflict Resolution"],
        "Accounts": ["Financial Analysis", "Data Analysis", "SQL", "Risk Management", "Communication"],
        "Operations": ["Project Management", "Time Management", "Problem Solving", "Communication", "Process Improvement"],
    }
    
    created_maps = []
    
    for emp in employees:
        try:
            # Check if skill map already exists
            if frappe.db.exists("Employee Skill Map", emp.name):
                print(f"  ↻ Already exists for: {emp.employee_name}")
                continue
            
            # Determine skills based on department
            dept_base = emp.department.split(" - ")[0] if emp.department else ""
            available_skills = department_skills.get(dept_base, ["Communication", "Problem Solving", "Team Collaboration"])
            
            # Add some random skills
            all_skills = list(set(available_skills + random.sample(skills, min(3, len(skills)))))
            
            # Create skill entries
            skill_entries = []
            for skill_name in all_skills[:5]:  # Max 5 skills per employee
                if frappe.db.exists("Skill", skill_name):
                    skill_entries.append({
                        "skill": skill_name,
                        "proficiency": random.uniform(0.4, 1.0),  # Rating 0.4 to 1.0
                        "evaluation_date": add_days(getdate(nowdate()), random.randint(-180, 0))
                    })
            
            # Get trainings this employee attended
            training_entries = []
            for event_name in training_events:
                event = frappe.get_doc("Training Event", event_name)
                for attendee in event.employees:
                    if attendee.employee == emp.name and event.event_status == "Completed":
                        training_entries.append({
                            "training": event_name,
                            "training_date": getdate(event.end_time)
                        })
                        break
            
            doc = frappe.get_doc({
                "doctype": "Employee Skill Map",
                "employee": emp.name,
                "employee_skills": skill_entries,
                "trainings": training_entries[:5]  # Max 5 trainings
            })
            doc.insert(ignore_permissions=True)
            created_maps.append(doc.name)
            print(f"  ✓ Created skill map for: {emp.employee_name} ({len(skill_entries)} skills)")
            
        except Exception as e:
            print(f"  ⚠ Error creating skill map for {emp.employee_name}: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_maps)} employee skill maps")
    return created_maps


# ============================================================================
# EMPLOYEE LIFECYCLE EVENTS
# ============================================================================

def create_employee_promotions(company, company_abbr):
    """Create employee promotion records"""
    
    # Get all active employees first
    all_employees = frappe.get_all(
        "Employee",
        filters={
            "company": company,
            "status": "Active",
        },
        fields=["name", "employee_name", "designation", "department", "date_of_joining"]
    )
    
    # Filter out C-level employees manually (to avoid duplicate key issue in filters)
    excluded_titles = ["Chief", "CEO", "CTO", "CFO", "CPO", "CRO", "COO", "Director", "Head of", "VP"]
    employees = [
        e for e in all_employees 
        if e.designation and not any(title in e.designation for title in excluded_titles)
    ]
    
    # Sort by date of joining
    employees.sort(key=lambda x: x.date_of_joining or "9999-12-31")
    
    # No need for 6-month filter for demo data - use all eligible employees
    promotable = employees[:15]  # Get top 15 candidates
    
    if not promotable:
        print("  ⚠ No promotable employees found")
        return []
    
    # Expanded promotion paths
    promotion_paths = {
        "Backend Engineer": "Senior Backend Engineer",
        "Frontend Engineer": "Senior Frontend Engineer",
        "Data Analyst": "Data Scientist",
        "Account Executive": "Sales Operations Manager",
        "HR Operations Specialist": "HR Operations Manager",
        "SDR (Sales Development Representative)": "Account Executive",
        "DevOps Engineer": "Site Reliability Engineer (SRE)",
        "QA Engineer": "Senior Backend Engineer",
        "Customer Support Specialist": "Customer Success Manager",
        "Accountant": "Senior Accountant",
        "Technical Recruiter": "Head of Talent Acquisition",
        "Brand/Content Marketer": "Marketing Director",
        "Growth Marketer": "Marketing Director",
        "FP&A Analyst": "Senior Accountant",
        "Recruiting Coordinator": "Technical Recruiter",
        "IT Support Technician": "DevOps Engineer",
        "Product Manager": "Director of Product",
        "UX/UI Designer": "Head of Design",
        "Security Engineer": "Engineering Manager (Platform/Infra)",
        "Site Reliability Engineer (SRE)": "Engineering Manager (Platform/Infra)",
        "Sales Analyst": "Sales Operations Manager",
        "SEO Specialist": "Marketing Director",
        "Paid Ads Specialist": "Marketing Director",
        "Events/Field Marketer": "Marketing Director",
        "Learning & Development Specialist": "HR Operations Manager",
        "Payroll Specialist": "Compensation & Benefits Analyst",
    }
    
    created_promotions = []
    skipped = 0
    
    for emp in promotable:
        if len(created_promotions) >= 6:  # Create up to 6 promotions
            break
            
        try:
            new_designation = promotion_paths.get(emp.designation)
            if not new_designation:
                # Try generic promotion for Engineers
                if emp.designation and "Engineer" in emp.designation and "Senior" not in emp.designation:
                    new_designation = "Senior " + emp.designation
                elif emp.designation and "Specialist" in emp.designation:
                    new_designation = emp.designation.replace("Specialist", "Manager")
                elif emp.designation and "Analyst" in emp.designation:
                    new_designation = "Senior " + emp.designation if "Senior" not in emp.designation else None
                elif emp.designation and "Recruiter" in emp.designation and "Head" not in emp.designation:
                    new_designation = "Head of Talent Acquisition"
                elif emp.designation and "Marketer" in emp.designation:
                    new_designation = "Marketing Director"
                else:
                    skipped += 1
                    continue
            
            if not new_designation:
                skipped += 1
                continue
            
            # Check if designation exists
            if not frappe.db.exists("Designation", new_designation):
                # Try to find a similar designation
                similar = frappe.get_all(
                    "Designation",
                    filters={"designation_name": ["like", f"%{new_designation.split()[0]}%"]},
                    limit=1
                )
                if similar:
                    new_designation = similar[0].name
                else:
                    skipped += 1
                    continue
            
            # Check if promotion already exists for this employee
            existing = frappe.get_all(
                "Employee Promotion",
                filters={"employee": emp.name, "docstatus": ["!=", 2]},
                limit=1
            )
            if existing:
                print(f"  ↻ Promotion already exists for: {emp.employee_name}")
                continue
            
            promotion_date = add_days(getdate(nowdate()), random.randint(-60, -7))
            
            doc = frappe.get_doc({
                "doctype": "Employee Promotion",
                "employee": emp.name,
                "promotion_date": promotion_date,
                "company": company,
                "promotion_details": [
                    {
                        "property": "Designation",
                        "current": emp.designation,
                        "new": new_designation,
                        "fieldname": "designation"
                    }
                ]
            })
            doc.insert(ignore_permissions=True)
            doc.submit()
            
            created_promotions.append(doc.name)
            print(f"  ✓ Created promotion: {emp.employee_name} ({emp.designation} → {new_designation})")
            
        except Exception as e:
            print(f"  ⚠ Error creating promotion for {emp.employee_name}: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_promotions)} employee promotions")
    return created_promotions


def create_employee_transfers(company, company_abbr):
    """Create employee transfer records"""
    
    # Get employees who could be transferred
    employees = frappe.get_all(
        "Employee",
        filters={
            "company": company,
            "status": "Active",
            "designation": ["not like", "%Chief%"],
            "designation": ["not like", "%Director%"],
            "designation": ["not like", "%Head%"],
        },
        fields=["name", "employee_name", "designation", "department", "date_of_joining"],
        order_by="date_of_joining asc",
        limit=10
    )
    
    # Get available departments
    departments = frappe.get_all(
        "Department",
        filters={"company": company, "disabled": 0},
        fields=["name", "department_name"]
    )
    
    if not employees or len(departments) < 2:
        print("  ⚠ Not enough employees or departments for transfers")
        return []
    
    created_transfers = []
    
    # Create 1-2 transfers
    for emp in employees[:2]:
        try:
            # Find a different department
            current_dept = emp.department
            other_depts = [d for d in departments if d.name != current_dept]
            
            if not other_depts:
                continue
            
            new_dept = random.choice(other_depts)
            
            # Check if transfer already exists
            existing = frappe.get_all(
                "Employee Transfer",
                filters={"employee": emp.name, "docstatus": ["!=", 2]},
                limit=1
            )
            if existing:
                print(f"  ↻ Transfer already exists for: {emp.employee_name}")
                continue
            
            transfer_date = add_days(getdate(nowdate()), random.randint(-30, -7))
            
            doc = frappe.get_doc({
                "doctype": "Employee Transfer",
                "employee": emp.name,
                "transfer_date": transfer_date,
                "company": company,
                "transfer_details": [
                    {
                        "property": "Department",
                        "current": current_dept,
                        "new": new_dept.name,
                        "fieldname": "department"
                    }
                ]
            })
            doc.insert(ignore_permissions=True)
            doc.submit()
            
            created_transfers.append(doc.name)
            print(f"  ✓ Created transfer: {emp.employee_name} ({current_dept} → {new_dept.name})")
            
        except Exception as e:
            print(f"  ⚠ Error creating transfer for {emp.employee_name}: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_transfers)} employee transfers")
    return created_transfers


# ============================================================================
# SEPARATION MODULE
# ============================================================================

def create_separation_templates(company, company_abbr):
    """Create employee separation templates"""
    
    templates_data = [
        {
            "title": "Standard Separation",
            "activities": [
                {"activity_name": "Knowledge Transfer Documentation", "role": "HR Manager", "begin_on": 0, "duration": 14, "description": "Document all processes, projects, and knowledge for handover"},
                {"activity_name": "Return Company Assets", "role": "System Manager", "begin_on": 7, "duration": 7, "description": "Return laptop, access cards, keys, and other company property"},
                {"activity_name": "Revoke System Access", "role": "System Manager", "begin_on": 14, "duration": 1, "description": "Disable all system accounts and access credentials"},
                {"activity_name": "Exit Interview", "role": "HR Manager", "begin_on": 10, "duration": 1, "description": "Conduct exit interview to gather feedback"},
                {"activity_name": "Final Settlement Processing", "role": "HR Manager", "begin_on": 14, "duration": 7, "description": "Process final paycheck, benefits, and any pending reimbursements"},
                {"activity_name": "Handover to Replacement", "role": "HR Manager", "begin_on": 7, "duration": 7, "description": "Brief replacement employee on responsibilities and ongoing projects"},
            ]
        },
        {
            "title": "Executive Separation",
            "activities": [
                {"activity_name": "Board Notification", "role": "HR Manager", "begin_on": 0, "duration": 1, "description": "Notify board of directors and key stakeholders"},
                {"activity_name": "Strategic Knowledge Transfer", "role": "HR Manager", "begin_on": 1, "duration": 21, "description": "Comprehensive handover of strategic initiatives and relationships"},
                {"activity_name": "Client Transition Meetings", "role": "HR Manager", "begin_on": 7, "duration": 14, "description": "Introduce replacement to key clients and partners"},
                {"activity_name": "Return Company Assets", "role": "System Manager", "begin_on": 21, "duration": 3, "description": "Return all company property including any executive equipment"},
                {"activity_name": "Revoke All Access", "role": "System Manager", "begin_on": 28, "duration": 1, "description": "Revoke all system access, board access, and financial signing authority"},
                {"activity_name": "Exit Interview", "role": "HR Manager", "begin_on": 25, "duration": 1, "description": "Conduct confidential exit interview"},
                {"activity_name": "Final Settlement", "role": "HR Manager", "begin_on": 28, "duration": 14, "description": "Process executive compensation package and settlements"},
            ]
        },
    ]
    
    created_templates = []
    
    for template_data in templates_data:
        try:
            if frappe.db.exists("Employee Separation Template", {"title": template_data["title"]}):
                print(f"  ↻ Already exists: {template_data['title']}")
                existing = frappe.get_doc("Employee Separation Template", {"title": template_data["title"]})
                created_templates.append(existing.name)
                continue
            
            activities = []
            for activity in template_data["activities"]:
                activities.append({
                    "activity_name": activity["activity_name"],
                    "role": activity.get("role"),
                    "begin_on": activity.get("begin_on", 0),
                    "duration": activity.get("duration", 1),
                    "description": activity.get("description", "")
                })
            
            doc = frappe.get_doc({
                "doctype": "Employee Separation Template",
                "title": template_data["title"],
                "company": company,
                "activities": activities
            })
            doc.insert(ignore_permissions=True)
            created_templates.append(doc.name)
            print(f"  ✓ Created: {template_data['title']}")
            
        except Exception as e:
            print(f"  ⚠ Error creating template {template_data['title']}: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_templates)} separation templates")
    return created_templates


def create_employee_separations(company, separation_templates):
    """Create employee separation records"""
    
    # For demo purposes, we'll create a simulated separation scenario
    # In real usage, this would be for employees who are actually leaving
    
    created_separations = []
    
    # Get employees who could have separations (for demo - pick employees with recent join dates)
    # In production, this would be based on resignation_letter_date
    employees = frappe.get_all(
        "Employee",
        filters={
            "company": company,
            "status": "Active",
            "designation": ["not like", "%Chief%"],
        },
        fields=["name", "employee_name", "designation", "department"],
        order_by="date_of_joining desc",
        limit=5
    )
    
    if not employees or not separation_templates:
        print("  ⚠ No employees or templates available for separation")
        return created_separations
    
    # Create 3 sample separations with different statuses
    statuses = ["Pending", "In Process", "Completed"]
    
    for idx, emp in enumerate(employees[:3]):
        template = separation_templates[idx % len(separation_templates)] if separation_templates else None
        status = statuses[idx % len(statuses)]
        
        try:
            # Check if separation already exists
            existing = frappe.get_all(
                "Employee Separation",
                filters={"employee": emp.name, "docstatus": ["!=", 2]},
                limit=1
            )
            if existing:
                print(f"  ↻ Separation already exists for: {emp.employee_name}")
                continue
            
            # Vary the dates based on status
            if status == "Completed":
                boarding_begins = add_days(getdate(nowdate()), -45)
            elif status == "In Process":
                boarding_begins = add_days(getdate(nowdate()), -14)
            else:
                boarding_begins = add_days(getdate(nowdate()), 7)
            
            doc = frappe.get_doc({
                "doctype": "Employee Separation",
                "employee": emp.name,
                "employee_separation_template": template,
                "company": company,
                "boarding_begins_on": boarding_begins,
                "boarding_status": status,
                "notify_users_by_email": 0
            })
            doc.insert(ignore_permissions=True)
            
            # Submit for In Process and Completed statuses
            if status in ["In Process", "Completed"]:
                doc.submit()
            
            created_separations.append(doc.name)
            print(f"  ✓ Created separation for: {emp.employee_name} ({status})")
            
        except Exception as e:
            print(f"  ⚠ Error creating separation for {emp.employee_name}: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_separations)} employee separations")
    return created_separations


def create_exit_interviews(company, separations):
    """Create exit interview records"""
    
    created_interviews = []
    
    # Get HR managers who can conduct interviews
    hr_employees = frappe.get_all(
        "Employee",
        filters={
            "company": company,
            "status": "Active",
            "department": ["like", "%Human Resources%"]
        },
        fields=["name", "employee_name"]
    )
    
    # Interview summaries for variety
    interview_summaries = [
        """<p><strong>Reason for Leaving:</strong> Career advancement opportunity</p>
<p><strong>Experience at Company:</strong> Overall positive experience with great colleagues and learning opportunities.</p>
<p><strong>Suggestions for Improvement:</strong> More structured career development paths and regular feedback sessions would be beneficial.</p>
<p><strong>Would Recommend Company:</strong> Yes, would recommend to others looking for a collaborative work environment.</p>""",
        """<p><strong>Reason for Leaving:</strong> Relocation to another city</p>
<p><strong>Experience at Company:</strong> Enjoyed the work culture and team collaboration. Will miss the team.</p>
<p><strong>Suggestions for Improvement:</strong> Consider offering remote work options for certain roles.</p>
<p><strong>Would Recommend Company:</strong> Absolutely, great place to work and grow.</p>""",
        """<p><strong>Reason for Leaving:</strong> Pursuing further education</p>
<p><strong>Experience at Company:</strong> Learned a lot during my time here. Management was supportive.</p>
<p><strong>Suggestions for Improvement:</strong> More educational assistance programs would be appreciated.</p>
<p><strong>Would Recommend Company:</strong> Yes, especially for entry-level professionals.</p>""",
    ]
    
    # First, create exit interviews for separations
    for separation_name in separations:
        try:
            separation = frappe.get_doc("Employee Separation", separation_name)
            
            # Check if exit interview already exists
            existing = frappe.get_all(
                "Exit Interview",
                filters={"employee": separation.employee},
                limit=1
            )
            if existing:
                print(f"  ↻ Exit interview already exists for: {separation.employee_name}")
                continue
            
            interview_date = add_days(getdate(nowdate()), random.randint(-7, 0))
            
            # Get random HR interviewers
            interviewers = []
            if hr_employees:
                selected = random.sample(hr_employees, min(2, len(hr_employees)))
                for hr in selected:
                    interviewers.append({"employee": hr.name})
            
            doc = frappe.get_doc({
                "doctype": "Exit Interview",
                "employee": separation.employee,
                "company": company,
                "status": "Completed",
                "date": interview_date,
                "interviewers": interviewers,
                "interview_summary": random.choice(interview_summaries),
                "employee_status": "Exit Confirmed"
            })
            doc.insert(ignore_permissions=True)
            
            created_interviews.append(doc.name)
            print(f"  ✓ Created exit interview for: {separation.employee_name}")
            
        except Exception as e:
            print(f"  ⚠ Error creating exit interview for separation {separation_name}: {str(e)[:60]}")
    
    # Also create a few additional exit interviews for demo variety (scheduled/pending)
    # These represent employees who may be considering leaving or scheduled for interview
    employees = frappe.get_all(
        "Employee",
        filters={
            "company": company,
            "status": "Active",
            "designation": ["not like", "%Chief%"]
        },
        fields=["name", "employee_name"],
        limit=10
    )
    
    # Pick 2-3 random employees for additional exit interviews
    for emp in random.sample(employees, min(3, len(employees))):
        try:
            # Check if exit interview already exists
            existing = frappe.get_all(
                "Exit Interview",
                filters={"employee": emp.name},
                limit=1
            )
            if existing:
                continue
            
            interview_date = add_days(getdate(nowdate()), random.randint(1, 14))
            
            interviewers = []
            if hr_employees:
                selected = random.sample(hr_employees, min(2, len(hr_employees)))
                for hr in selected:
                    interviewers.append({"employee": hr.name})
            
            status = random.choice(["Pending", "Scheduled"])
            
            doc = frappe.get_doc({
                "doctype": "Exit Interview",
                "employee": emp.name,
                "company": company,
                "status": status,
                "date": interview_date if status == "Scheduled" else None,
                "interviewers": interviewers if status == "Scheduled" else [],
            })
            doc.insert(ignore_permissions=True)
            
            created_interviews.append(doc.name)
            print(f"  ✓ Created exit interview ({status}): {emp.employee_name}")
            
        except Exception as e:
            print(f"  ⚠ Error creating exit interview: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_interviews)} exit interviews")
    return created_interviews


def create_fnf_statements(company, separations):
    """Create full and final settlement statements"""
    
    created_statements = []
    
    # Create F&F for separations first
    for separation_name in separations:
        try:
            separation = frappe.get_doc("Employee Separation", separation_name)
            
            # Check if F&F already exists
            existing = frappe.get_all(
                "Full and Final Statement",
                filters={"employee": separation.employee},
                limit=1
            )
            if existing:
                print(f"  ↻ F&F statement already exists for: {separation.employee_name}")
                continue
            
            transaction_date = getdate(nowdate())
            
            # Create sample payables and receivables
            payables = [
                {
                    "component": "Final Salary",
                    "amount": random.randint(3000, 8000),
                    "status": "Unsettled"
                },
                {
                    "component": "Unused Leave Encashment",
                    "amount": random.randint(500, 2000),
                    "status": "Unsettled"
                },
                {
                    "component": "Pending Expense Reimbursement",
                    "amount": random.randint(100, 500),
                    "status": "Unsettled"
                }
            ]
            
            receivables = [
                {
                    "component": "Notice Period Shortfall",
                    "amount": random.randint(0, 1000),
                    "status": "Unsettled"
                },
                {
                    "component": "Training Bond Recovery",
                    "amount": 0,
                    "status": "Settled"
                }
            ]
            
            doc = frappe.get_doc({
                "doctype": "Full and Final Statement",
                "employee": separation.employee,
                "transaction_date": transaction_date,
                "company": company,
                "status": "Unpaid",
                "payables": payables,
                "receivables": receivables
            })
            doc.insert(ignore_permissions=True)
            
            created_statements.append(doc.name)
            print(f"  ✓ Created F&F statement for: {separation.employee_name}")
            
        except Exception as e:
            print(f"  ⚠ Error creating F&F for separation {separation_name}: {str(e)[:60]}")
    
    # Create additional F&F statements for demo (for employees not in separation)
    employees = frappe.get_all(
        "Employee",
        filters={
            "company": company,
            "status": "Active",
            "designation": ["not like", "%Chief%"]
        },
        fields=["name", "employee_name"],
        limit=10
    )
    
    for emp in random.sample(employees, min(3, len(employees))):
        try:
            # Check if F&F already exists
            existing = frappe.get_all(
                "Full and Final Statement",
                filters={"employee": emp.name},
                limit=1
            )
            if existing:
                continue
            
            transaction_date = add_days(getdate(nowdate()), random.randint(-30, 0))
            
            payables = [
                {
                    "component": "Final Salary",
                    "amount": random.randint(4000, 10000),
                    "status": random.choice(["Settled", "Unsettled"])
                },
                {
                    "component": "Unused Leave Encashment",
                    "amount": random.randint(800, 2500),
                    "status": random.choice(["Settled", "Unsettled"])
                },
                {
                    "component": "Bonus Payout",
                    "amount": random.randint(1000, 3000),
                    "status": "Unsettled"
                }
            ]
            
            receivables = [
                {
                    "component": "Equipment Recovery",
                    "amount": random.randint(0, 500),
                    "status": "Unsettled"
                }
            ]
            
            doc = frappe.get_doc({
                "doctype": "Full and Final Statement",
                "employee": emp.name,
                "transaction_date": transaction_date,
                "company": company,
                "status": "Unpaid",
                "payables": payables,
                "receivables": receivables
            })
            doc.insert(ignore_permissions=True)
            
            created_statements.append(doc.name)
            print(f"  ✓ Created F&F statement for: {emp.employee_name}")
            
        except Exception as e:
            print(f"  ⚠ Error creating F&F: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_statements)} F&F statements")
    return created_statements


# ============================================================================
# GRIEVANCE MODULE
# ============================================================================

def create_grievance_types():
    """Create grievance type master data"""
    
    grievance_types_data = [
        {"name": "Workplace Harassment", "description": "Reports of harassment, bullying, or hostile work environment"},
        {"name": "Discrimination", "description": "Reports of discrimination based on protected characteristics"},
        {"name": "Compensation Issues", "description": "Disputes related to salary, benefits, or compensation"},
        {"name": "Work Conditions", "description": "Concerns about workplace safety, facilities, or working conditions"},
        {"name": "Management Conflict", "description": "Issues with management decisions, treatment, or communication"},
        {"name": "Policy Violation", "description": "Reports of company policy violations by employees or management"},
        {"name": "Workload Issues", "description": "Concerns about excessive workload or unreasonable expectations"},
        {"name": "Career Development", "description": "Issues related to promotions, training opportunities, or career growth"},
    ]
    
    created_types = []
    
    for gtype in grievance_types_data:
        try:
            if frappe.db.exists("Grievance Type", gtype["name"]):
                created_types.append(gtype["name"])
                continue
            
            doc = frappe.get_doc({
                "doctype": "Grievance Type",
                "name": gtype["name"],
                "description": gtype["description"]
            })
            doc.insert(ignore_permissions=True)
            created_types.append(doc.name)
            
        except Exception as e:
            print(f"  ⚠ Error creating grievance type {gtype['name']}: {str(e)[:40]}")
    
    print(f"  ✓ Created/verified {len(created_types)} grievance types")
    return created_types


def create_employee_grievances(company, grievance_types):
    """Create employee grievance records"""
    
    # Get active employees
    employees = frappe.get_all(
        "Employee",
        filters={"company": company, "status": "Active"},
        fields=["name", "employee_name", "designation", "reports_to"]
    )
    
    if not employees or not grievance_types:
        print("  ⚠ No employees or grievance types available")
        return []
    
    grievances_data = [
        {
            "subject": "Excessive Workload in Q4",
            "grievance_type": "Workload Issues",
            "description": "The workload during Q4 was significantly higher than sustainable. Multiple team members worked overtime for weeks without adequate compensation or time off.",
            "status": "Resolved",
            "resolution_detail": "Approved additional headcount for the team and implemented workload monitoring. Provided comp time for affected employees."
        },
        {
            "subject": "Request for Career Development Discussion",
            "grievance_type": "Career Development",
            "description": "Despite multiple requests, I have not received clarity on my career progression path or opportunities for skill development training.",
            "status": "Investigated",
            "cause_of_grievance": "Lack of structured career development program and manager communication gaps."
        },
        {
            "subject": "Office Temperature Concerns",
            "grievance_type": "Work Conditions",
            "description": "The office temperature is consistently too cold, making it uncomfortable to work. Multiple colleagues have raised similar concerns.",
            "status": "Open"
        },
        {
            "subject": "Delayed Expense Reimbursement",
            "grievance_type": "Compensation Issues",
            "description": "Expense reimbursements submitted over 60 days ago are still pending. This has caused personal financial strain.",
            "status": "Resolved",
            "resolution_detail": "Expedited the pending reimbursements and streamlined the approval process to prevent future delays."
        },
        {
            "subject": "Unfair Performance Review",
            "grievance_type": "Management Conflict",
            "description": "I believe my recent performance review did not accurately reflect my contributions and achievements during the review period.",
            "status": "Open"
        },
    ]
    
    created_grievances = []
    
    # Get employees with managers for proper grievance structure
    employees_with_managers = [e for e in employees if e.reports_to]
    if not employees_with_managers:
        employees_with_managers = employees
    
    for idx, grievance_data in enumerate(grievances_data):
        try:
            # Select random employee (different one for each grievance if possible)
            emp_idx = idx % len(employees_with_managers)
            emp = employees_with_managers[emp_idx]
            
            grievance_type = grievance_data["grievance_type"]
            if grievance_type not in grievance_types:
                grievance_type = grievance_types[0] if grievance_types else None
            
            if not grievance_type:
                continue
            
            grievance_date = add_days(getdate(nowdate()), random.randint(-60, -7))
            
            # Grievance against party should be "Employee" (the DocType name)
            # and grievance_against should be an Employee record
            grievance_against = emp.reports_to if emp.reports_to else employees[0].name
            
            doc_data = {
                "doctype": "Employee Grievance",
                "subject": grievance_data["subject"],
                "raised_by": emp.name,
                "date": grievance_date,
                "grievance_type": grievance_type,
                "grievance_against_party": "Employee",  # This is the DocType name
                "grievance_against": grievance_against,
                "description": grievance_data["description"],
                "status": grievance_data["status"]
            }
            
            # Add resolution details for resolved grievances
            if grievance_data["status"] == "Resolved":
                doc_data["resolution_detail"] = grievance_data.get("resolution_detail", "Issue has been addressed.")
                doc_data["resolution_date"] = add_days(grievance_date, random.randint(7, 21))
                doc_data["cause_of_grievance"] = grievance_data.get("cause_of_grievance", "Identified root cause and addressed.")
                # Add resolved_by for resolved grievances
                hr_users = frappe.get_all("User", filters={"enabled": 1}, limit=1)
                if hr_users:
                    doc_data["resolved_by"] = hr_users[0].name
            elif grievance_data["status"] == "Investigated":
                doc_data["cause_of_grievance"] = grievance_data.get("cause_of_grievance", "Under investigation.")
            
            doc = frappe.get_doc(doc_data)
            doc.insert(ignore_permissions=True)
            
            # Don't submit grievances - they use workflow, just save them
            created_grievances.append(doc.name)
            print(f"  ✓ Created grievance: {grievance_data['subject'][:40]}...")
            
        except Exception as e:
            print(f"  ⚠ Error creating grievance: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_grievances)} employee grievances")
    return created_grievances


# ============================================================================
# DAILY WORK SUMMARY MODULE
# ============================================================================

def create_daily_work_summary_groups(company):
    """Create daily work summary groups"""
    
    # Get active employees grouped by department
    employees = frappe.get_all(
        "Employee",
        filters={"company": company, "status": "Active"},
        fields=["name", "employee_name", "user_id", "department"]
    )
    
    if not employees:
        print("  ⚠ No employees available for work summary groups")
        return []
    
    # Filter employees with user_id
    employees_with_users = [e for e in employees if e.user_id]
    
    if not employees_with_users:
        print("  ⚠ No employees with user accounts found for work summary groups")
        return []
    
    # Group employees by department
    dept_employees = {}
    for emp in employees_with_users:
        dept = (emp.department or "General").split(" - ")[0]
        if dept not in dept_employees:
            dept_employees[dept] = []
        dept_employees[dept].append(emp)
    
    groups_data = [
        {
            "group_name": "Engineering Daily Standup",
            "department": "Research & Development",
            "send_emails_at": "17:00",
            "subject": "What did you accomplish today?",
            "message": "<p>Please share your daily progress. Reply with:</p><ul><li>What you completed today</li><li>Any blockers</li><li>What you plan for tomorrow</li></ul>"
        },
        {
            "group_name": "Sales Daily Update",
            "department": "Sales",
            "send_emails_at": "18:00",
            "subject": "Daily Sales Activity Summary",
            "message": "<p>Please provide your daily sales activity summary:</p><ul><li>Calls made</li><li>Meetings held</li><li>Deals progressed</li><li>Revenue closed</li></ul>"
        },
        {
            "group_name": "HR Team Daily Summary",
            "department": "Human Resources",
            "send_emails_at": "17:30",
            "subject": "Daily HR Activities",
            "message": "<p>Please share today's HR activities:</p><ul><li>Interviews conducted</li><li>Onboarding tasks completed</li><li>Employee queries handled</li></ul>"
        },
    ]
    
    created_groups = []
    
    # Get holiday list
    holiday_list = frappe.db.get_value("Company", company, "default_holiday_list")
    
    for group_data in groups_data:
        try:
            group_name = group_data["group_name"]
            
            if frappe.db.exists("Daily Work Summary Group", group_name):
                print(f"  ↻ Already exists: {group_name}")
                created_groups.append(group_name)
                continue
            
            # Get users for this department
            users = []
            dept_name = group_data["department"]
            if dept_name in dept_employees:
                for emp in dept_employees[dept_name][:10]:  # Max 10 users per group
                    users.append({"user": emp.user_id})
            
            if not users:
                # Add some random users if department not found
                for emp in employees_with_users[:5]:
                    users.append({"user": emp.user_id})
            
            if not users:
                print(f"  ⚠ No users found for group: {group_name}")
                continue
            
            # For "Prompt" autoname, we need to set __newname
            doc = frappe.get_doc({
                "doctype": "Daily Work Summary Group",
                "__newname": group_name,
                "enabled": 1,
                "send_emails_at": group_data["send_emails_at"],
                "holiday_list": holiday_list,
                "subject": group_data["subject"],
                "message": group_data["message"],
                "users": users
            })
            doc.insert(ignore_permissions=True)
            created_groups.append(doc.name)
            print(f"  ✓ Created: {doc.name} ({len(users)} users)")
            
        except Exception as e:
            print(f"  ⚠ Error creating group {group_data['group_name']}: {str(e)[:80]}")
    
    print(f"  ✓ Created {len(created_groups)} daily work summary groups")
    return created_groups


def create_daily_work_summaries(summary_groups):
    """Create sample daily work summary records"""
    
    created_summaries = []
    
    if not summary_groups:
        print("  ⚠ No summary groups available")
        return created_summaries
    
    # Daily Work Summary is typically auto-generated by the system
    # For demo purposes, we'll create a few historical records
    
    for group_name in summary_groups:
        try:
            # Verify the group exists
            if not frappe.db.exists("Daily Work Summary Group", group_name):
                print(f"  ⚠ Group not found: {group_name}")
                continue
            
            # Create summaries for past 7 weekdays
            created_for_group = 0
            for days_ago in range(1, 10):
                summary_date = add_days(getdate(nowdate()), -days_ago)
                
                # Skip weekends
                if summary_date.weekday() >= 5:
                    continue
                
                # Check if we already have 5 summaries for this group
                if created_for_group >= 5:
                    break
                
                # Check if summary already exists for this group on this date
                existing = frappe.get_all(
                    "Daily Work Summary",
                    filters=[
                        ["daily_work_summary_group", "=", group_name],
                        ["creation", ">=", f"{summary_date} 00:00:00"],
                        ["creation", "<=", f"{summary_date} 23:59:59"]
                    ],
                    limit=1
                )
                if existing:
                    continue
                
                doc = frappe.get_doc({
                    "doctype": "Daily Work Summary",
                    "daily_work_summary_group": group_name,
                    "status": "Sent"
                })
                doc.insert(ignore_permissions=True)
                created_summaries.append(doc.name)
                created_for_group += 1
            
            if created_for_group > 0:
                print(f"  ✓ Created {created_for_group} summaries for: {group_name}")
            
        except Exception as e:
            print(f"  ⚠ Error creating summaries for {group_name}: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_summaries)} daily work summaries")
    return created_summaries


# ============================================================================
# CLEANUP FUNCTION
# ============================================================================

def clear_tenure_data(company="NovaSoft"):
    """
    Clear all tenure/lifecycle demo data created by this script.
    Use with caution - this will delete data!
    
    Usage:
        bench --site [sitename] execute hrms.demo_data.tenure_setup.clear_tenure_data
    """
    frappe.set_user("Administrator")
    
    print(f"\n{'='*60}")
    print(f"Clearing Tenure Data for Company: {company}")
    print(f"{'='*60}\n")
    
    # Order matters for deletion due to dependencies
    doctypes_to_clear = [
        # Cleanup in reverse order of creation
        ("Daily Work Summary", {}),
        ("Daily Work Summary Group", {}),
        ("Employee Grievance", {}),
        ("Grievance Type", {}),
        ("Full and Final Statement", {"company": company}),
        ("Exit Interview", {"company": company}),
        ("Employee Separation", {"company": company}),
        ("Employee Separation Template", {"company": company}),
        ("Employee Transfer", {"company": company}),
        ("Employee Promotion", {"company": company}),
        ("Employee Skill Map", {}),
        ("Skill", {}),
        ("Training Feedback", {}),
        ("Training Result", {}),
        ("Training Event", {"company": company}),
        ("Training Program", {"company": company}),
        ("Employee Onboarding", {"company": company}),
        ("Employee Onboarding Template", {"company": company}),
    ]
    
    for doctype, filters in doctypes_to_clear:
        try:
            # For submittable doctypes, cancel first
            meta = frappe.get_meta(doctype)
            
            docs = frappe.get_all(doctype, filters=filters, pluck="name")
            
            for doc_name in docs:
                try:
                    doc = frappe.get_doc(doctype, doc_name)
                    
                    if meta.is_submittable and doc.docstatus == 1:
                        doc.cancel()
                    
                    frappe.delete_doc(doctype, doc_name, force=True)
                except Exception as e:
                    print(f"  ⚠ Error deleting {doctype} {doc_name}: {str(e)[:40]}")
            
            if docs:
                print(f"  ✓ Deleted {len(docs)} {doctype} records")
            
        except Exception as e:
            print(f"  ⚠ Error clearing {doctype}: {str(e)[:60]}")
    
    frappe.db.commit()
    
    print(f"\n{'='*60}")
    print("✅ Tenure Data Cleared!")
    print(f"{'='*60}\n")

