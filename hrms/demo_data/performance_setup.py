"""
Performance Management Setup - Demo Data Generator for HRMS Performance Activities

This script initializes performance management activities including:
- Employee Feedback Criteria (rating criteria for evaluations)
- KRAs (Key Result Areas)
- Appraisal Templates (with KRAs and rating criteria)
- Appraisal Cycles (with appraisees)
- Goals (individual employee goals linked to KRAs)
- Appraisals (employee appraisal documents)
- Employee Performance Feedback (feedback from managers/peers)

Usage: 
    bench --site [sitename] execute hrms.demo_data.performance_setup.create_performance_data
    Or with company:
    bench --site [sitename] execute hrms.demo_data.performance_setup.create_performance_data --kwargs '{"company": "NovaSoft"}'

Author: Generated for HRMS Demo
Version: 1.0.0
"""

import frappe
from frappe.utils import getdate, add_days, add_months, nowdate, nowtime
import random


def create_performance_data(company="NovaSoft"):
    """
    Create comprehensive performance management demo data for HRMS testing.
    Should be run AFTER company_setup.py has been executed.
    """
    frappe.set_user("Administrator")
    
    print(f"\n{'='*60}")
    print(f"Creating Performance Management Data for Company: {company}")
    print(f"{'='*60}\n")
    
    # Verify company exists
    if not frappe.db.exists("Company", company):
        print(f"❌ Company '{company}' not found. Please run company_setup.py first.")
        return
    
    # Get company abbreviation
    company_abbr = frappe.db.get_value("Company", company, "abbr")
    
    # 1. Create Employee Feedback Criteria
    print("📊 Creating Employee Feedback Criteria...")
    feedback_criteria = create_feedback_criteria()
    frappe.db.commit()
    
    # 2. Create KRAs (Key Result Areas)
    print("🎯 Creating KRAs (Key Result Areas)...")
    kras = create_kras()
    frappe.db.commit()
    
    # 3. Create Appraisal Templates
    print("📋 Creating Appraisal Templates...")
    appraisal_templates = create_appraisal_templates(kras, feedback_criteria)
    frappe.db.commit()
    
    # 4. Create Appraisal Cycles
    print("🔄 Creating Appraisal Cycles...")
    appraisal_cycles = create_appraisal_cycles(company, company_abbr, appraisal_templates)
    frappe.db.commit()
    
    # 5. Create Goals for Employees
    print("🎯 Creating Employee Goals...")
    goals = create_employee_goals(company, appraisal_cycles, kras)
    frappe.db.commit()
    
    # 6. Create Appraisals
    print("📝 Creating Appraisals...")
    appraisals = create_appraisals(company, appraisal_cycles, appraisal_templates, kras)
    frappe.db.commit()
    
    # 7. Create Employee Performance Feedback
    print("💬 Creating Employee Performance Feedback...")
    feedbacks = create_performance_feedback(company, appraisals, feedback_criteria)
    frappe.db.commit()
    
    print(f"\n{'='*60}")
    print("✅ Performance Management Data Creation Complete!")
    print(f"{'='*60}")
    print(f"\nCreated:")
    print(f"  - {len(feedback_criteria)} Feedback Criteria")
    print(f"  - {len(kras)} KRAs (Key Result Areas)")
    print(f"  - {len(appraisal_templates)} Appraisal Templates")
    print(f"  - {len(appraisal_cycles)} Appraisal Cycles")
    print(f"  - {len(goals)} Employee Goals")
    print(f"  - {len(appraisals)} Appraisals")
    print(f"  - {len(feedbacks)} Performance Feedback Records")
    print(f"\n{'='*60}\n")


# ============================================================================
# EMPLOYEE FEEDBACK CRITERIA
# ============================================================================

def create_feedback_criteria():
    """Create feedback criteria for performance evaluations"""
    criteria_list = [
        # Technical Competencies
        "Technical Skills",
        "Problem Solving",
        "Code Quality",
        "System Design",
        "Innovation & Creativity",
        # Soft Skills
        "Communication",
        "Teamwork & Collaboration",
        "Leadership",
        "Time Management",
        "Adaptability",
        # Work Quality
        "Quality of Work",
        "Productivity",
        "Attention to Detail",
        "Initiative",
        # Professional Growth
        "Learning Agility",
        "Professional Development",
        "Mentorship & Coaching",
        # Customer & Business Focus
        "Customer Focus",
        "Business Acumen",
        "Results Orientation",
    ]
    
    created_criteria = []
    for criteria in criteria_list:
        try:
            if frappe.db.exists("Employee Feedback Criteria", criteria):
                created_criteria.append(criteria)
                continue
            
            doc = frappe.get_doc({
                "doctype": "Employee Feedback Criteria",
                "criteria": criteria
            })
            doc.insert(ignore_permissions=True)
            created_criteria.append(criteria)
        except Exception as e:
            print(f"  ⚠ Error creating criteria {criteria}: {str(e)[:50]}")
    
    print(f"  ✓ Created/verified {len(created_criteria)} feedback criteria")
    return created_criteria


# ============================================================================
# KRAs (KEY RESULT AREAS)
# ============================================================================

def create_kras():
    """Create Key Result Areas for performance appraisals"""
    kras_data = [
        # Engineering KRAs
        {
            "title": "Technical Excellence",
            "description": "Deliver high-quality, well-tested, and maintainable code. Continuously improve technical skills and apply best practices."
        },
        {
            "title": "Project Delivery",
            "description": "Complete assigned projects on time with high quality. Meet sprint commitments and project milestones."
        },
        {
            "title": "System Reliability",
            "description": "Ensure system uptime, performance, and reliability. Reduce bugs and technical debt."
        },
        {
            "title": "Code Review & Quality",
            "description": "Participate actively in code reviews. Maintain high code quality standards and documentation."
        },
        {
            "title": "Architecture & Design",
            "description": "Contribute to system architecture decisions. Design scalable and maintainable solutions."
        },
        # Leadership KRAs
        {
            "title": "Team Leadership",
            "description": "Lead and mentor team members. Foster collaboration and create a positive work environment."
        },
        {
            "title": "Strategic Planning",
            "description": "Develop and execute strategic plans. Align team goals with company objectives."
        },
        {
            "title": "Stakeholder Management",
            "description": "Effectively communicate with stakeholders. Manage expectations and build strong relationships."
        },
        # Product/Design KRAs
        {
            "title": "Product Innovation",
            "description": "Drive product innovation and improvements. Identify new features and opportunities."
        },
        {
            "title": "User Experience",
            "description": "Ensure excellent user experience. Conduct user research and implement improvements."
        },
        # Sales/Marketing KRAs
        {
            "title": "Revenue Growth",
            "description": "Meet or exceed sales targets. Identify and pursue new revenue opportunities."
        },
        {
            "title": "Customer Acquisition",
            "description": "Acquire new customers and expand market reach. Build and maintain sales pipeline."
        },
        {
            "title": "Brand Development",
            "description": "Build and strengthen company brand. Execute effective marketing campaigns."
        },
        # HR/Operations KRAs
        {
            "title": "Talent Development",
            "description": "Support employee growth and development. Implement training and development programs."
        },
        {
            "title": "Process Improvement",
            "description": "Identify and implement process improvements. Increase operational efficiency."
        },
        {
            "title": "Employee Engagement",
            "description": "Foster employee engagement and satisfaction. Build a positive workplace culture."
        },
        # Customer Success KRAs
        {
            "title": "Customer Satisfaction",
            "description": "Maintain high customer satisfaction scores. Resolve customer issues effectively."
        },
        {
            "title": "Customer Retention",
            "description": "Retain existing customers and reduce churn. Build long-term customer relationships."
        },
        # General KRAs
        {
            "title": "Communication & Collaboration",
            "description": "Communicate effectively across teams. Collaborate with cross-functional stakeholders."
        },
        {
            "title": "Professional Growth",
            "description": "Continuously develop skills and knowledge. Pursue learning and certifications."
        },
    ]
    
    created_kras = []
    for kra_data in kras_data:
        try:
            if frappe.db.exists("KRA", kra_data["title"]):
                created_kras.append(kra_data["title"])
                continue
            
            kra = frappe.get_doc({
                "doctype": "KRA",
                "title": kra_data["title"],
                "description": kra_data["description"]
            })
            kra.insert(ignore_permissions=True)
            created_kras.append(kra_data["title"])
        except Exception as e:
            print(f"  ⚠ Error creating KRA {kra_data['title']}: {str(e)[:50]}")
    
    print(f"  ✓ Created/verified {len(created_kras)} KRAs")
    return created_kras


# ============================================================================
# APPRAISAL TEMPLATES
# ============================================================================

def create_appraisal_templates(kras, feedback_criteria):
    """Create appraisal templates for different role types"""
    
    templates_data = [
        {
            "template_title": "Engineering Individual Contributor",
            "description": "Appraisal template for Software Engineers, DevOps Engineers, and QA Engineers",
            "goals": [
                {"key_result_area": "Technical Excellence", "per_weightage": 35},
                {"key_result_area": "Project Delivery", "per_weightage": 25},
                {"key_result_area": "Code Review & Quality", "per_weightage": 20},
                {"key_result_area": "Professional Growth", "per_weightage": 10},
                {"key_result_area": "Communication & Collaboration", "per_weightage": 10},
            ],
            "rating_criteria": [
                {"criteria": "Technical Skills", "per_weightage": 30},
                {"criteria": "Problem Solving", "per_weightage": 20},
                {"criteria": "Quality of Work", "per_weightage": 20},
                {"criteria": "Teamwork & Collaboration", "per_weightage": 15},
                {"criteria": "Communication", "per_weightage": 15},
            ]
        },
        {
            "template_title": "Senior Engineer / Tech Lead",
            "description": "Appraisal template for Senior Engineers and Technical Leads",
            "goals": [
                {"key_result_area": "Technical Excellence", "per_weightage": 25},
                {"key_result_area": "Architecture & Design", "per_weightage": 20},
                {"key_result_area": "Team Leadership", "per_weightage": 20},
                {"key_result_area": "Code Review & Quality", "per_weightage": 15},
                {"key_result_area": "Professional Growth", "per_weightage": 10},
                {"key_result_area": "Communication & Collaboration", "per_weightage": 10},
            ],
            "rating_criteria": [
                {"criteria": "Technical Skills", "per_weightage": 25},
                {"criteria": "Leadership", "per_weightage": 20},
                {"criteria": "Problem Solving", "per_weightage": 20},
                {"criteria": "Mentorship & Coaching", "per_weightage": 15},
                {"criteria": "Communication", "per_weightage": 10},
                {"criteria": "Initiative", "per_weightage": 10},
            ]
        },
        {
            "template_title": "Engineering Manager",
            "description": "Appraisal template for Engineering Managers and Directors",
            "goals": [
                {"key_result_area": "Team Leadership", "per_weightage": 30},
                {"key_result_area": "Strategic Planning", "per_weightage": 20},
                {"key_result_area": "Project Delivery", "per_weightage": 20},
                {"key_result_area": "Talent Development", "per_weightage": 15},
                {"key_result_area": "Stakeholder Management", "per_weightage": 15},
            ],
            "rating_criteria": [
                {"criteria": "Leadership", "per_weightage": 30},
                {"criteria": "Communication", "per_weightage": 20},
                {"criteria": "Results Orientation", "per_weightage": 20},
                {"criteria": "Mentorship & Coaching", "per_weightage": 15},
                {"criteria": "Business Acumen", "per_weightage": 15},
            ]
        },
        {
            "template_title": "Product Manager",
            "description": "Appraisal template for Product Managers",
            "goals": [
                {"key_result_area": "Product Innovation", "per_weightage": 30},
                {"key_result_area": "User Experience", "per_weightage": 25},
                {"key_result_area": "Strategic Planning", "per_weightage": 20},
                {"key_result_area": "Stakeholder Management", "per_weightage": 15},
                {"key_result_area": "Communication & Collaboration", "per_weightage": 10},
            ],
            "rating_criteria": [
                {"criteria": "Business Acumen", "per_weightage": 25},
                {"criteria": "Communication", "per_weightage": 20},
                {"criteria": "Customer Focus", "per_weightage": 20},
                {"criteria": "Innovation & Creativity", "per_weightage": 20},
                {"criteria": "Results Orientation", "per_weightage": 15},
            ]
        },
        {
            "template_title": "UX/UI Designer",
            "description": "Appraisal template for UX/UI Designers",
            "goals": [
                {"key_result_area": "User Experience", "per_weightage": 35},
                {"key_result_area": "Product Innovation", "per_weightage": 25},
                {"key_result_area": "Communication & Collaboration", "per_weightage": 20},
                {"key_result_area": "Professional Growth", "per_weightage": 20},
            ],
            "rating_criteria": [
                {"criteria": "Innovation & Creativity", "per_weightage": 30},
                {"criteria": "Quality of Work", "per_weightage": 25},
                {"criteria": "Customer Focus", "per_weightage": 20},
                {"criteria": "Teamwork & Collaboration", "per_weightage": 15},
                {"criteria": "Communication", "per_weightage": 10},
            ]
        },
        {
            "template_title": "Data Scientist",
            "description": "Appraisal template for Data Scientists and Analysts",
            "goals": [
                {"key_result_area": "Technical Excellence", "per_weightage": 30},
                {"key_result_area": "Product Innovation", "per_weightage": 25},
                {"key_result_area": "Project Delivery", "per_weightage": 25},
                {"key_result_area": "Professional Growth", "per_weightage": 10},
                {"key_result_area": "Communication & Collaboration", "per_weightage": 10},
            ],
            "rating_criteria": [
                {"criteria": "Technical Skills", "per_weightage": 30},
                {"criteria": "Problem Solving", "per_weightage": 25},
                {"criteria": "Innovation & Creativity", "per_weightage": 20},
                {"criteria": "Communication", "per_weightage": 15},
                {"criteria": "Quality of Work", "per_weightage": 10},
            ]
        },
        {
            "template_title": "Sales Representative",
            "description": "Appraisal template for Account Executives and SDRs",
            "goals": [
                {"key_result_area": "Revenue Growth", "per_weightage": 40},
                {"key_result_area": "Customer Acquisition", "per_weightage": 30},
                {"key_result_area": "Customer Satisfaction", "per_weightage": 15},
                {"key_result_area": "Communication & Collaboration", "per_weightage": 15},
            ],
            "rating_criteria": [
                {"criteria": "Results Orientation", "per_weightage": 35},
                {"criteria": "Communication", "per_weightage": 25},
                {"criteria": "Customer Focus", "per_weightage": 20},
                {"criteria": "Initiative", "per_weightage": 10},
                {"criteria": "Adaptability", "per_weightage": 10},
            ]
        },
        {
            "template_title": "Marketing Professional",
            "description": "Appraisal template for Marketing team members",
            "goals": [
                {"key_result_area": "Brand Development", "per_weightage": 30},
                {"key_result_area": "Customer Acquisition", "per_weightage": 30},
                {"key_result_area": "Product Innovation", "per_weightage": 20},
                {"key_result_area": "Communication & Collaboration", "per_weightage": 20},
            ],
            "rating_criteria": [
                {"criteria": "Innovation & Creativity", "per_weightage": 30},
                {"criteria": "Results Orientation", "per_weightage": 25},
                {"criteria": "Communication", "per_weightage": 20},
                {"criteria": "Customer Focus", "per_weightage": 15},
                {"criteria": "Quality of Work", "per_weightage": 10},
            ]
        },
        {
            "template_title": "Customer Success Manager",
            "description": "Appraisal template for Customer Success team",
            "goals": [
                {"key_result_area": "Customer Satisfaction", "per_weightage": 35},
                {"key_result_area": "Customer Retention", "per_weightage": 30},
                {"key_result_area": "Process Improvement", "per_weightage": 20},
                {"key_result_area": "Communication & Collaboration", "per_weightage": 15},
            ],
            "rating_criteria": [
                {"criteria": "Customer Focus", "per_weightage": 35},
                {"criteria": "Communication", "per_weightage": 25},
                {"criteria": "Problem Solving", "per_weightage": 20},
                {"criteria": "Adaptability", "per_weightage": 10},
                {"criteria": "Teamwork & Collaboration", "per_weightage": 10},
            ]
        },
        {
            "template_title": "HR Professional",
            "description": "Appraisal template for HR team members",
            "goals": [
                {"key_result_area": "Talent Development", "per_weightage": 30},
                {"key_result_area": "Employee Engagement", "per_weightage": 25},
                {"key_result_area": "Process Improvement", "per_weightage": 25},
                {"key_result_area": "Communication & Collaboration", "per_weightage": 20},
            ],
            "rating_criteria": [
                {"criteria": "Communication", "per_weightage": 25},
                {"criteria": "Teamwork & Collaboration", "per_weightage": 25},
                {"criteria": "Results Orientation", "per_weightage": 20},
                {"criteria": "Attention to Detail", "per_weightage": 15},
                {"criteria": "Adaptability", "per_weightage": 15},
            ]
        },
        {
            "template_title": "Executive Leadership",
            "description": "Appraisal template for C-level and VP positions",
            "goals": [
                {"key_result_area": "Strategic Planning", "per_weightage": 30},
                {"key_result_area": "Team Leadership", "per_weightage": 25},
                {"key_result_area": "Revenue Growth", "per_weightage": 25},
                {"key_result_area": "Stakeholder Management", "per_weightage": 20},
            ],
            "rating_criteria": [
                {"criteria": "Leadership", "per_weightage": 30},
                {"criteria": "Business Acumen", "per_weightage": 25},
                {"criteria": "Results Orientation", "per_weightage": 20},
                {"criteria": "Communication", "per_weightage": 15},
                {"criteria": "Innovation & Creativity", "per_weightage": 10},
            ]
        },
    ]
    
    created_templates = []
    for template_data in templates_data:
        try:
            if frappe.db.exists("Appraisal Template", template_data["template_title"]):
                created_templates.append(template_data["template_title"])
                print(f"  ↻ Already exists: {template_data['template_title']}")
                continue
            
            # Filter valid goals (KRAs)
            valid_goals = []
            for goal in template_data["goals"]:
                if goal["key_result_area"] in kras:
                    valid_goals.append(goal)
            
            # Filter valid rating criteria
            valid_criteria = []
            for criteria in template_data["rating_criteria"]:
                if criteria["criteria"] in feedback_criteria:
                    valid_criteria.append(criteria)
            
            if not valid_goals:
                print(f"  ⚠ No valid KRAs for template: {template_data['template_title']}")
                continue
            
            template = frappe.get_doc({
                "doctype": "Appraisal Template",
                "template_title": template_data["template_title"],
                "description": template_data["description"],
                "goals": valid_goals,
                "rating_criteria": valid_criteria
            })
            template.insert(ignore_permissions=True)
            created_templates.append(template.name)
            print(f"  ✓ Created: {template_data['template_title']}")
        except Exception as e:
            print(f"  ⚠ Error creating template {template_data['template_title']}: {str(e)[:60]}")
    
    print(f"  ✓ Created/verified {len(created_templates)} appraisal templates")
    return created_templates


# ============================================================================
# APPRAISAL CYCLES
# ============================================================================

def create_appraisal_cycles(company, company_abbr, appraisal_templates):
    """Create appraisal cycles with appraisees"""
    
    current_year = getdate().year
    
    # Map departments to templates
    dept_template_map = {
        "Research & Development": "Engineering Individual Contributor",
        "Sales": "Sales Representative",
        "Marketing": "Marketing Professional",
        "Customer Service": "Customer Success Manager",
        "Human Resources": "HR Professional",
        "Accounts": "HR Professional",  # Use HR template for finance
        "Operations": "HR Professional",
        "Quality Management": "Engineering Individual Contributor",
        "Management": "Executive Leadership",
        "Legal": "Executive Leadership",
        "Purchase": "HR Professional",
    }
    
    # Designation-specific template overrides
    designation_template_map = {
        # C-Level Executives
        "Chief Executive Officer (CEO)": "Executive Leadership",
        "Chief Operating Officer (COO)": "Executive Leadership",
        "Chief Technology Officer (CTO)": "Executive Leadership",
        "Chief Financial Officer (CFO)": "Executive Leadership",
        "Chief People Officer (CPO)": "Executive Leadership",
        "Chief Revenue Officer (CRO)": "Executive Leadership",
        "General Counsel (GC)": "Executive Leadership",
        # VPs and Directors (leadership level)
        "VP Engineering": "Executive Leadership",
        "Director of Product": "Executive Leadership",
        "Marketing Director": "Executive Leadership",
        # Department Heads
        "Head of Sales": "Executive Leadership",
        "Head of Design": "Executive Leadership",
        "Head of Data": "Executive Leadership",
        "Head of Talent Acquisition": "Executive Leadership",
        "Head of Customer Success": "Executive Leadership",
        # Engineering Management
        "Engineering Manager (Backend)": "Engineering Manager",
        "Engineering Manager (Frontend)": "Engineering Manager",
        "Engineering Manager (Platform/Infra)": "Engineering Manager",
        # Senior Engineers / Tech Leads
        "Senior Backend Engineer": "Senior Engineer / Tech Lead",
        "Senior Frontend Engineer": "Senior Engineer / Tech Lead",
        # Product & Design
        "Product Manager": "Product Manager",
        "UX/UI Designer": "UX/UI Designer",
        # Data
        "Data Scientist": "Data Scientist",
        "Data Analyst": "Data Scientist",
        # HR Management
        "HR Operations Manager": "Executive Leadership",
        # Customer Success (explicit)
        "Customer Success Manager": "Customer Success Manager",
    }
    
    cycles_data = [
        {
            "cycle_name": f"Annual Performance Review {current_year}",
            "start_date": f"{current_year}-01-01",
            "end_date": f"{current_year}-12-31",
            "status": "In Progress",
            "kra_evaluation_method": "Automated Based on Goal Progress",
            "description": f"Annual performance review cycle for {current_year}. All employees participate in goal setting, self-assessment, and manager feedback.",
            # Uses default formula: average of Goal Score, Feedback Score, and Self Appraisal Score
            "calculate_final_score_based_on_formula": 0,
            "final_score_formula": "",
        },
        {
            "cycle_name": f"Q1 Performance Check-in {current_year}",
            "start_date": f"{current_year}-01-01",
            "end_date": f"{current_year}-03-31",
            "status": "Completed",
            "kra_evaluation_method": "Automated Based on Goal Progress",
            "description": f"Q1 performance check-in for {current_year}. Focus on quarterly goals and initial feedback.",
            "calculate_final_score_based_on_formula": 0,
            "final_score_formula": "",
        },
        {
            "cycle_name": f"Mid-Year Review {current_year}",
            "start_date": f"{current_year}-01-01",
            "end_date": f"{current_year}-06-30",
            "status": "Completed",
            "kra_evaluation_method": "Automated Based on Goal Progress",
            "description": f"Mid-year performance review for {current_year}. Comprehensive progress check and goal adjustments.",
            # Custom formula: 50% goal score, 30% feedback score, 20% self score
            "calculate_final_score_based_on_formula": 1,
            "final_score_formula": "(goal_score * 0.5) + (avg_feedback_score * 0.3) + (self_score * 0.2)",
        },
    ]
    
    created_cycles = []
    for cycle_data in cycles_data:
        try:
            if frappe.db.exists("Appraisal Cycle", cycle_data["cycle_name"]):
                created_cycles.append(cycle_data["cycle_name"])
                print(f"  ↻ Already exists: {cycle_data['cycle_name']}")
                continue
            
            # Get employees for this cycle
            employees = frappe.get_all(
                "Employee",
                filters={"company": company, "status": "Active"},
                fields=["name", "employee_name", "department", "designation"]
            )
            
            # Build appraisees list with appropriate templates
            appraisees = []
            for emp in employees:
                # Get template based on designation first, then department
                template = None
                if emp.designation:
                    template = designation_template_map.get(emp.designation)
                
                if not template and emp.department:
                    # Extract department name without company suffix
                    dept_name = emp.department.replace(f" - {company_abbr}", "")
                    template = dept_template_map.get(dept_name)
                
                # Default template
                if not template:
                    template = "Engineering Individual Contributor"
                
                # Check if template exists
                if template not in appraisal_templates:
                    template = appraisal_templates[0] if appraisal_templates else None
                
                appraisees.append({
                    "employee": emp.name,
                    "appraisal_template": template
                })
            
            cycle_doc_data = {
                "doctype": "Appraisal Cycle",
                "cycle_name": cycle_data["cycle_name"],
                "company": company,
                "start_date": cycle_data["start_date"],
                "end_date": cycle_data["end_date"],
                "status": cycle_data["status"],
                "kra_evaluation_method": cycle_data["kra_evaluation_method"],
                "description": cycle_data["description"],
                "appraisees": appraisees
            }
            
            # Add formula-based final score calculation if configured
            if cycle_data.get("calculate_final_score_based_on_formula"):
                cycle_doc_data["calculate_final_score_based_on_formula"] = 1
                cycle_doc_data["final_score_formula"] = cycle_data.get("final_score_formula", "")
            
            cycle = frappe.get_doc(cycle_doc_data)
            cycle.insert(ignore_permissions=True)
            created_cycles.append(cycle.name)
            print(f"  ✓ Created: {cycle_data['cycle_name']} ({len(appraisees)} appraisees)")
        except Exception as e:
            print(f"  ⚠ Error creating cycle {cycle_data['cycle_name']}: {str(e)[:60]}")
    
    print(f"  ✓ Created/verified {len(created_cycles)} appraisal cycles")
    return created_cycles


# ============================================================================
# EMPLOYEE GOALS
# ============================================================================

def create_employee_goals(company, appraisal_cycles, kras):
    """Create individual goals and sub-goals for employees (tree structure)"""
    
    # Goal templates by role category
    # Each goal can have optional sub-goals for hierarchical tracking
    engineering_goals = [
        {
            "goal_name": "Complete major feature development", 
            "kra": "Project Delivery", 
            "progress": 75,
            "sub_goals": [
                {"goal_name": "Design feature architecture", "progress": 100},
                {"goal_name": "Implement core functionality", "progress": 80},
                {"goal_name": "Write unit and integration tests", "progress": 60},
                {"goal_name": "Complete code review and merge", "progress": 50},
            ]
        },
        {"goal_name": "Reduce bug count by 30%", "kra": "System Reliability", "progress": 60},
        {"goal_name": "Improve code test coverage to 80%", "kra": "Code Review & Quality", "progress": 85},
        {"goal_name": "Learn and implement new technology stack", "kra": "Professional Growth", "progress": 50},
        {"goal_name": "Conduct weekly code reviews", "kra": "Code Review & Quality", "progress": 90},
        {"goal_name": "Refactor legacy codebase module", "kra": "Technical Excellence", "progress": 40},
        {"goal_name": "Mentor junior developers", "kra": "Team Leadership", "progress": 70},
        {"goal_name": "Design microservices architecture", "kra": "Architecture & Design", "progress": 55},
    ]
    
    sales_goals = [
        {"goal_name": "Achieve quarterly sales quota", "kra": "Revenue Growth", "progress": 80},
        {"goal_name": "Close 10 new enterprise accounts", "kra": "Customer Acquisition", "progress": 60},
        {"goal_name": "Expand existing account revenue by 20%", "kra": "Revenue Growth", "progress": 45},
        {"goal_name": "Maintain 95% customer satisfaction score", "kra": "Customer Satisfaction", "progress": 92},
        {"goal_name": "Build pipeline of 50 qualified leads", "kra": "Customer Acquisition", "progress": 70},
    ]
    
    marketing_goals = [
        {"goal_name": "Launch 3 marketing campaigns", "kra": "Brand Development", "progress": 66},
        {"goal_name": "Increase website traffic by 40%", "kra": "Customer Acquisition", "progress": 55},
        {"goal_name": "Improve brand awareness score", "kra": "Brand Development", "progress": 70},
        {"goal_name": "Generate 500 MQLs monthly", "kra": "Customer Acquisition", "progress": 80},
        {"goal_name": "Develop new product positioning", "kra": "Product Innovation", "progress": 50},
    ]
    
    customer_success_goals = [
        {"goal_name": "Achieve 90% customer retention rate", "kra": "Customer Retention", "progress": 88},
        {"goal_name": "Reduce average response time to 2 hours", "kra": "Customer Satisfaction", "progress": 75},
        {"goal_name": "Complete 50 customer health checks", "kra": "Customer Satisfaction", "progress": 60},
        {"goal_name": "Identify 10 upsell opportunities", "kra": "Revenue Growth", "progress": 40},
        {"goal_name": "Improve NPS score to 50+", "kra": "Customer Satisfaction", "progress": 65},
    ]
    
    hr_goals = [
        {"goal_name": "Reduce time-to-hire to 30 days", "kra": "Process Improvement", "progress": 70},
        {"goal_name": "Achieve 85% employee engagement score", "kra": "Employee Engagement", "progress": 82},
        {"goal_name": "Complete training program rollout", "kra": "Talent Development", "progress": 90},
        {"goal_name": "Implement new onboarding process", "kra": "Process Improvement", "progress": 100},
        {"goal_name": "Conduct quarterly employee surveys", "kra": "Employee Engagement", "progress": 75},
    ]
    
    leadership_goals = [
        {
            "goal_name": "Develop and execute team roadmap", 
            "kra": "Strategic Planning", 
            "progress": 65,
            "sub_goals": [
                {"goal_name": "Define Q1-Q2 team objectives", "progress": 100},
                {"goal_name": "Align roadmap with company strategy", "progress": 90},
                {"goal_name": "Communicate roadmap to stakeholders", "progress": 80},
                {"goal_name": "Track and report roadmap progress", "progress": 50},
            ]
        },
        {"goal_name": "Grow team by 5 new hires", "kra": "Team Leadership", "progress": 80},
        {"goal_name": "Improve team velocity by 20%", "kra": "Project Delivery", "progress": 55},
        {"goal_name": "Establish cross-team collaboration process", "kra": "Stakeholder Management", "progress": 70},
        {"goal_name": "Reduce team attrition to below 10%", "kra": "Employee Engagement", "progress": 90},
    ]
    
    # Get annual appraisal cycle
    annual_cycle = None
    for cycle in appraisal_cycles:
        if "Annual" in cycle:
            annual_cycle = cycle
            break
    
    if not annual_cycle:
        annual_cycle = appraisal_cycles[0] if appraisal_cycles else None
    
    if not annual_cycle:
        print("  ⚠ No appraisal cycle found, skipping goals creation")
        return []
    
    # Get cycle dates
    cycle_doc = frappe.get_doc("Appraisal Cycle", annual_cycle)
    start_date = cycle_doc.start_date
    end_date = cycle_doc.end_date
    
    # Select sample employees for goals
    employees = frappe.get_all(
        "Employee",
        filters={"company": company, "status": "Active"},
        fields=["name", "employee_name", "department", "designation"],
        limit=50  # Create goals for first 50 employees
    )
    
    created_goals = []
    for emp in employees:
        try:
            # Determine goal set based on department/designation
            dept_name = emp.department.split(" - ")[0] if emp.department else ""
            
            if "Engineering" in (emp.designation or "") or dept_name == "Research & Development":
                if "Manager" in (emp.designation or "") or "VP" in (emp.designation or "") or "Lead" in (emp.designation or ""):
                    goals_template = leadership_goals[:3] + engineering_goals[:2]
                else:
                    goals_template = engineering_goals[:4]
            elif dept_name == "Sales":
                goals_template = sales_goals[:3]
            elif dept_name == "Marketing":
                goals_template = marketing_goals[:3]
            elif dept_name == "Customer Service":
                goals_template = customer_success_goals[:3]
            elif dept_name == "Human Resources":
                goals_template = hr_goals[:3]
            else:
                goals_template = engineering_goals[:2] + hr_goals[:1]
            
            for goal_data in goals_template:
                # Check if KRA exists
                if goal_data["kra"] not in kras:
                    continue
                
                # Check if similar goal already exists
                existing = frappe.db.exists("Goal", {
                    "employee": emp.name,
                    "goal_name": goal_data["goal_name"],
                    "appraisal_cycle": annual_cycle
                })
                
                if existing:
                    continue
                
                # Randomize progress slightly
                progress = min(100, max(0, goal_data["progress"] + random.randint(-10, 10)))
                
                # Determine status based on progress
                if progress >= 100:
                    status = "Completed"
                elif progress > 0:
                    status = "In Progress"
                else:
                    status = "Pending"
                
                # Check if this goal has sub-goals (is a group/parent goal)
                has_sub_goals = "sub_goals" in goal_data and goal_data["sub_goals"]
                
                goal = frappe.get_doc({
                    "doctype": "Goal",
                    "goal_name": goal_data["goal_name"],
                    "employee": emp.name,
                    "kra": goal_data["kra"],
                    "appraisal_cycle": annual_cycle,
                    "start_date": start_date,
                    "end_date": end_date,
                    "progress": progress,
                    "status": status,
                    "is_group": 1 if has_sub_goals else 0,
                    "description": f"<p>{goal_data['goal_name']} for {emp.employee_name}</p>"
                })
                goal.flags.ignore_mandatory = True
                goal.insert(ignore_permissions=True)
                created_goals.append(goal.name)
                
                # Create sub-goals if they exist (tree structure)
                if has_sub_goals:
                    for sub_goal_data in goal_data["sub_goals"]:
                        sub_progress = min(100, max(0, sub_goal_data["progress"] + random.randint(-10, 10)))
                        if sub_progress >= 100:
                            sub_status = "Completed"
                        elif sub_progress > 0:
                            sub_status = "In Progress"
                        else:
                            sub_status = "Pending"
                        
                        sub_goal = frappe.get_doc({
                            "doctype": "Goal",
                            "goal_name": sub_goal_data["goal_name"],
                            "employee": emp.name,
                            "parent_goal": goal.name,  # Link to parent goal
                            # KRA is inherited from parent goal
                            "appraisal_cycle": annual_cycle,
                            "start_date": start_date,
                            "end_date": end_date,
                            "progress": sub_progress,
                            "status": sub_status,
                            "is_group": 0,
                            "description": f"<p>Sub-goal: {sub_goal_data['goal_name']}</p>"
                        })
                        sub_goal.flags.ignore_mandatory = True
                        sub_goal.insert(ignore_permissions=True)
                        created_goals.append(sub_goal.name)
        except Exception as e:
            print(f"  ⚠ Error creating goals for {emp.employee_name}: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_goals)} employee goals")
    return created_goals


# ============================================================================
# APPRAISALS
# ============================================================================

def create_appraisals(company, appraisal_cycles, appraisal_templates, kras):
    """Create appraisal documents for employees"""
    
    # Get annual cycle
    annual_cycle = None
    for cycle in appraisal_cycles:
        if "Annual" in cycle:
            annual_cycle = cycle
            break
    
    if not annual_cycle:
        annual_cycle = appraisal_cycles[0] if appraisal_cycles else None
    
    if not annual_cycle:
        print("  ⚠ No appraisal cycle found, skipping appraisals creation")
        return []
    
    # Get cycle document
    cycle_doc = frappe.get_doc("Appraisal Cycle", annual_cycle)
    
    # Select employees for appraisals (limit to subset for demo)
    employees = frappe.get_all(
        "Employee",
        filters={"company": company, "status": "Active"},
        fields=["name", "employee_name", "department", "designation"],
        limit=30  # Create appraisals for first 30 employees
    )
    
    created_appraisals = []
    for emp in employees:
        try:
            # Check if appraisal already exists
            existing = frappe.db.exists("Appraisal", {
                "employee": emp.name,
                "appraisal_cycle": annual_cycle
            })
            
            if existing:
                created_appraisals.append(existing)
                continue
            
            # Find appraisee record to get template
            appraisee = None
            for a in cycle_doc.appraisees:
                if a.employee == emp.name:
                    appraisee = a
                    break
            
            template = appraisee.appraisal_template if appraisee else None
            if not template or template not in appraisal_templates:
                template = appraisal_templates[0] if appraisal_templates else None
            
            if not template:
                continue
            
            # Get template document
            template_doc = frappe.get_doc("Appraisal Template", template)
            
            # Build appraisal KRAs from template
            appraisal_kras = []
            for goal in template_doc.goals:
                if goal.key_result_area in kras:
                    # Calculate random goal completion
                    goal_completion = random.uniform(50, 95)
                    goal_score = (goal_completion * goal.per_weightage) / 100
                    
                    appraisal_kras.append({
                        "kra": goal.key_result_area,
                        "per_weightage": goal.per_weightage,
                        "goal_completion": round(goal_completion, 2),
                        "goal_score": round(goal_score, 2)
                    })
            
            # Build self ratings from template rating criteria
            self_ratings = []
            for criteria in template_doc.rating_criteria:
                self_ratings.append({
                    "criteria": criteria.criteria,
                    "per_weightage": criteria.per_weightage,
                    "rating": random.uniform(0.6, 1.0)  # Random rating between 3-5 stars
                })
            
            appraisal = frappe.get_doc({
                "doctype": "Appraisal",
                "employee": emp.name,
                "company": company,
                "appraisal_cycle": annual_cycle,
                "appraisal_template": template,
                "start_date": cycle_doc.start_date,
                "end_date": cycle_doc.end_date,
                "appraisal_kra": appraisal_kras,
                "self_ratings": self_ratings,
                "rate_goals_manually": 0,
                "reflections": f"<p>{emp.employee_name}'s self-reflection for the appraisal period. "
                              f"Overall, I have made significant progress on my goals and contributed "
                              f"to team success through collaboration and continuous learning.</p>"
            })
            appraisal.flags.ignore_mandatory = True
            appraisal.insert(ignore_permissions=True)
            created_appraisals.append(appraisal.name)
            print(f"  ✓ Created appraisal for {emp.employee_name}")
        except Exception as e:
            print(f"  ⚠ Error creating appraisal for {emp.employee_name}: {str(e)[:60]}")
    
    print(f"  ✓ Created/verified {len(created_appraisals)} appraisals")
    return created_appraisals


# ============================================================================
# EMPLOYEE PERFORMANCE FEEDBACK
# ============================================================================

def create_performance_feedback(company, appraisals, feedback_criteria):
    """Create performance feedback from managers for employees"""
    
    feedback_comments = [
        "Consistently delivers high-quality work and exceeds expectations. A valuable team member who takes initiative and collaborates effectively with others.",
        "Demonstrates strong technical skills and problem-solving abilities. Has shown significant growth this review period and continues to develop leadership qualities.",
        "Excellent communicator who keeps stakeholders informed. Proactively identifies issues and proposes solutions. A positive influence on team morale.",
        "Reliable and dependable team member. Meets deadlines consistently and maintains high standards of work quality. Could benefit from taking on more challenging projects.",
        "Shows great potential and eagerness to learn. Has made notable progress in technical competency. Recommend focusing on improving time management skills.",
        "Outstanding performance this quarter. Led several key initiatives and mentored junior team members effectively. A strong candidate for advancement.",
        "Solid contributor who consistently meets expectations. Works well within the team and adapts to changing priorities. Encouraged to be more vocal in team discussions.",
        "Exceptional problem solver who tackles complex challenges. Demonstrates strong ownership and accountability. Continue developing cross-functional collaboration skills.",
    ]
    
    # Get managers who can give feedback
    managers = frappe.get_all(
        "Employee",
        filters={
            "company": company,
            "status": "Active",
            "designation": ["like", "%Manager%"]
        },
        fields=["name", "employee_name"],
        limit=20
    )
    
    if not managers:
        # Fallback to any senior employees
        managers = frappe.get_all(
            "Employee",
            filters={
                "company": company,
                "status": "Active",
                "designation": ["like", "%Senior%"]
            },
            fields=["name", "employee_name"],
            limit=10
        )
    
    if not managers:
        print("  ⚠ No managers found for feedback, skipping")
        return []
    
    created_feedbacks = []
    for appraisal_name in appraisals[:20]:  # Limit to first 20 appraisals
        try:
            # Get appraisal document
            if isinstance(appraisal_name, str):
                appraisal = frappe.get_doc("Appraisal", appraisal_name)
            else:
                continue
            
            # Get employee's manager
            employee_doc = frappe.get_doc("Employee", appraisal.employee)
            reviewer = None
            
            if employee_doc.reports_to:
                reviewer = employee_doc.reports_to
            else:
                # Assign a random manager
                reviewer = random.choice(managers).name
            
            # Skip if reviewer is the same as employee
            if reviewer == appraisal.employee:
                continue
            
            # Check if feedback already exists
            existing = frappe.db.exists("Employee Performance Feedback", {
                "appraisal": appraisal_name,
                "reviewer": reviewer
            })
            
            if existing:
                created_feedbacks.append(existing)
                continue
            
            # Build feedback ratings
            feedback_ratings = []
            # Get rating criteria from appraisal template
            if appraisal.appraisal_template:
                template_doc = frappe.get_doc("Appraisal Template", appraisal.appraisal_template)
                for criteria in template_doc.rating_criteria:
                    if criteria.criteria in feedback_criteria:
                        feedback_ratings.append({
                            "criteria": criteria.criteria,
                            "per_weightage": criteria.per_weightage,
                            "rating": random.uniform(0.6, 1.0)
                        })
            
            feedback = frappe.get_doc({
                "doctype": "Employee Performance Feedback",
                "employee": appraisal.employee,
                "reviewer": reviewer,
                "appraisal": appraisal_name,
                "company": company,
                "added_on": nowdate(),
                "feedback": random.choice(feedback_comments),
                "feedback_ratings": feedback_ratings
            })
            feedback.flags.ignore_mandatory = True
            feedback.insert(ignore_permissions=True)
            
            # Submit the feedback
            try:
                feedback.submit()
            except:
                pass
            
            created_feedbacks.append(feedback.name)
        except Exception as e:
            print(f"  ⚠ Error creating feedback: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_feedbacks)} performance feedback records")
    return created_feedbacks


# ============================================================================
# CLEAR FUNCTIONS (for cleanup/testing)
# ============================================================================

def clear_performance_data(company="NovaSoft"):
    """
    Clear all performance management demo data.
    USE WITH CAUTION - This will delete data!
    
    Usage: bench --site [sitename] execute hrms.demo_data.performance_setup.clear_performance_data
    """
    frappe.set_user("Administrator")
    
    print(f"\n{'='*60}")
    print(f"⚠️  Clearing Performance Data for Company: {company}")
    print(f"{'='*60}\n")
    
    # Delete in reverse dependency order
    doctypes = [
        ("Employee Performance Feedback", {"company": company}),
        ("Appraisal", {"company": company}),
        ("Goal", {"company": company}),
        ("Appraisal Cycle", {"company": company}),
    ]
    
    for doctype, filters in doctypes:
        try:
            docs = frappe.get_all(doctype, filters=filters)
            count = 0
            for doc in docs:
                try:
                    d = frappe.get_doc(doctype, doc.name)
                    if d.docstatus == 1:
                        d.cancel()
                    frappe.delete_doc(doctype, doc.name, force=True)
                    count += 1
                except Exception as e:
                    pass
            print(f"  ✓ Deleted {count} {doctype} records")
        except Exception as e:
            print(f"  ⚠ Error deleting {doctype}: {str(e)[:50]}")
    
    frappe.db.commit()
    print(f"\n{'='*60}")
    print("✅ Performance Data Deletion Complete!")
    print(f"{'='*60}\n")

