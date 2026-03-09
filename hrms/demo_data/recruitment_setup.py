"""
Recruitment Setup - Demo Data Generator for HRMS Recruitment Activities

This script initializes recruitment activities including:
- Staffing Plans
- Job Requisitions
- Job Openings
- Job Applicants (with Employee Referrals)
- Interviews and Interview Feedback
- Job Offers
- Offer Terms and Job Offer Term Templates
- Appointment Letter Templates and Appointment Letters

Usage: 
    bench --site [sitename] execute demo_data.recruitment_setup.create_recruitment_data
    Or with company:
    bench --site [sitename] execute demo_data.recruitment_setup.create_recruitment_data --kwargs '{"company": "NovaSoft"}'

Author: hjian42
Version: 1.0.0
"""

import frappe
from frappe.utils import getdate, add_days, nowdate, nowtime


def create_recruitment_data(company="NovaSoft"):
    """
    Create comprehensive recruitment demo data for HRMS testing.
    Should be run AFTER company_setup.py has been executed.
    """
    frappe.set_user("Administrator")
    
    print(f"\n{'='*60}")
    print(f"Creating Recruitment Data for Company: {company}")
    print(f"{'='*60}\n")
    
    # Verify company exists
    if not frappe.db.exists("Company", company):
        print(f"❌ Company '{company}' not found. Please run company_setup.py first.")
        return
    
    # Get company abbreviation
    company_abbr = frappe.db.get_value("Company", company, "abbr")
    
    # 1. Create Skills (for interview rounds)
    print("🎯 Creating Skills...")
    skills = create_skills()
    frappe.db.commit()
    
    # 2. Create Interview Types
    print("📋 Creating Interview Types...")
    interview_types = create_interview_types()
    frappe.db.commit()
    
    # 3. Create Job Applicant Sources
    print("📌 Creating Job Applicant Sources...")
    create_job_applicant_sources()
    frappe.db.commit()
    
    # 4. Create Staffing Plans
    print("📊 Creating Staffing Plans...")
    staffing_plans = create_staffing_plans(company, company_abbr)
    frappe.db.commit()
    
    # 5. Create Job Requisitions
    print("📝 Creating Job Requisitions...")
    job_requisitions = create_job_requisitions(company, company_abbr)
    frappe.db.commit()
    
    # 6. Create Job Openings
    print("📢 Creating Job Openings...")
    job_openings = create_job_openings(company, company_abbr, job_requisitions)
    frappe.db.commit()
    
    # 7. Create Employee Referrals
    print("🤝 Creating Employee Referrals...")
    employee_referrals = create_employee_referrals(company)
    frappe.db.commit()
    
    # 8. Create Job Applicants
    print("👤 Creating Job Applicants...")
    job_applicants = create_job_applicants(job_openings, employee_referrals)
    frappe.db.commit()
    
    # 9. Create Interview Rounds
    print("🔄 Creating Interview Rounds...")
    interview_rounds = create_interview_rounds(skills, interview_types)
    frappe.db.commit()
    
    # 10. Setup Interviewers (assign Interviewer role)
    print("👥 Setting up Interviewers...")
    interviewers = setup_interviewers(company)
    frappe.db.commit()
    
    # 11. Create Interviews
    print("🎤 Creating Interviews...")
    interviews = create_interviews(job_applicants, interview_rounds, interviewers)
    frappe.db.commit()
    
    # 12. Create Interview Feedback
    print("📝 Creating Interview Feedback...")
    create_interview_feedback(interviews, interviewers, skills)
    frappe.db.commit()
    
    # 13. Create Offer Terms (master data for job offers)
    print("📋 Creating Offer Terms...")
    offer_terms = create_offer_terms()
    frappe.db.commit()
    
    # 14. Create Job Offer Term Templates
    print("📄 Creating Job Offer Term Templates...")
    offer_templates = create_job_offer_term_templates(offer_terms)
    frappe.db.commit()
    
    # 15. Create Job Offers (with offer terms)
    print("💼 Creating Job Offers...")
    job_offers = create_job_offers(job_applicants, company, offer_templates)
    frappe.db.commit()
    
    # 16. Create Appointment Letter Templates
    print("📜 Creating Appointment Letter Templates...")
    appointment_templates = create_appointment_letter_templates()
    frappe.db.commit()
    
    # 17. Create Appointment Letters (for accepted offers)
    print("✉️ Creating Appointment Letters...")
    appointment_letters = create_appointment_letters(job_offers, company, appointment_templates)
    frappe.db.commit()
    
    print(f"\n{'='*60}")
    print("✅ Recruitment Data Creation Complete!")
    print(f"{'='*60}")
    print(f"\nCreated:")
    print(f"  - {len(skills)} Skills")
    print(f"  - {len(interview_types)} Interview Types")
    print(f"  - {len(staffing_plans)} Staffing Plans")
    print(f"  - {len(job_requisitions)} Job Requisitions")
    print(f"  - {len(job_openings)} Job Openings")
    print(f"  - {len(employee_referrals)} Employee Referrals")
    print(f"  - {len(job_applicants)} Job Applicants")
    print(f"  - {len(interview_rounds)} Interview Rounds")
    print(f"  - {len(interviews)} Interviews")
    print(f"  - Interview Feedback records")
    print(f"  - {len(offer_terms)} Offer Terms")
    print(f"  - {len(offer_templates)} Job Offer Term Templates")
    print(f"  - {len(job_offers)} Job Offers")
    print(f"  - {len(appointment_templates)} Appointment Letter Templates")
    print(f"  - {len(appointment_letters)} Appointment Letters")
    print(f"\n{'='*60}\n")


# ============================================================================
# SKILLS
# ============================================================================

def create_skills():
    """Create skills for interview assessments"""
    skill_names = [
        # Technical Skills
        "Python",
        "JavaScript",
        "TypeScript",
        "React",
        "Node.js",
        "SQL",
        "AWS",
        "Docker",
        "Kubernetes",
        "System Design",
        "Data Structures",
        "Algorithms",
        "Machine Learning",
        "Data Analysis",
        # Soft Skills
        "Communication",
        "Problem Solving",
        "Leadership",
        "Teamwork",
        "Time Management",
        "Presentation Skills",
        # Role-specific Skills
        "Sales Techniques",
        "Negotiation",
        "Customer Success",
        "Marketing Strategy",
        "Content Writing",
        "SEO",
        "Product Management",
        "UX Design",
        "UI Design",
        "Project Management",
    ]
    
    created_skills = []
    for skill_name in skill_names:
        try:
            if frappe.db.exists("Skill", skill_name):
                created_skills.append(skill_name)
                continue
            
            skill = frappe.get_doc({
                "doctype": "Skill",
                "skill_name": skill_name
            })
            skill.insert(ignore_permissions=True)
            created_skills.append(skill.name)
        except Exception as e:
            print(f"  ⚠ Error creating skill {skill_name}: {str(e)[:50]}")
    
    print(f"  ✓ Created/verified {len(created_skills)} skills")
    return created_skills


# ============================================================================
# INTERVIEW TYPES
# ============================================================================

def create_interview_types():
    """Create interview types"""
    types_data = [
        {"name": "Technical Interview", "description": "Technical skills assessment including coding and system design"},
        {"name": "HR Interview", "description": "Human Resources interview for cultural fit and company values"},
        {"name": "Behavioral Interview", "description": "Behavioral questions to assess past experiences and decision-making"},
        {"name": "Case Study", "description": "Problem-solving exercise with a business case"},
        {"name": "Panel Interview", "description": "Interview with multiple team members"},
        {"name": "Phone Screen", "description": "Initial phone screening call"},
        {"name": "Final Round", "description": "Final interview with leadership"},
    ]
    
    created_types = []
    for type_data in types_data:
        try:
            if frappe.db.exists("Interview Type", type_data["name"]):
                created_types.append(type_data["name"])
                continue
            
            interview_type = frappe.get_doc({
                "doctype": "Interview Type",
                "name": type_data["name"],
                "description": type_data["description"]
            })
            interview_type.insert(ignore_permissions=True)
            created_types.append(interview_type.name)
        except Exception as e:
            print(f"  ⚠ Error creating interview type {type_data['name']}: {str(e)[:50]}")
    
    print(f"  ✓ Created/verified {len(created_types)} interview types")
    return created_types


# ============================================================================
# JOB APPLICANT SOURCES
# ============================================================================

def create_job_applicant_sources():
    """Create job applicant sources"""
    sources = [
        "LinkedIn",
        "Indeed",
        "Company Website",
        "Employee Referral",
        "Glassdoor",
        "Campus Recruitment",
        "Recruiting Agency",
        "Job Fair",
        "Direct Application",
    ]
    
    count = 0
    for source in sources:
        try:
            if frappe.db.exists("Job Applicant Source", source):
                continue
            
            doc = frappe.get_doc({
                "doctype": "Job Applicant Source",
                "source_name": source
            })
            doc.insert(ignore_permissions=True)
            count += 1
        except Exception as e:
            pass
    
    print(f"  ✓ Created {count} new job applicant sources")


# ============================================================================
# STAFFING PLANS
# ============================================================================

def create_staffing_plans(company, company_abbr):
    """Create comprehensive staffing plans with emphasis on engineering"""
    
    current_year = getdate().year
    from_date = f"{current_year}-01-01"
    to_date = f"{current_year}-12-31"
    
    # Get R&D department
    rd_dept = f"Research & Development - {company_abbr}"
    sales_dept = f"Sales - {company_abbr}"
    marketing_dept = f"Marketing - {company_abbr}"
    cs_dept = f"Customer Service - {company_abbr}"
    
    staffing_plans_data = [
        {
            "name": f"Engineering Backend Hiring {current_year}",
            "department": rd_dept,
            "staffing_details": [
                {"designation": "Backend Engineer", "vacancies": 3, "estimated_cost_per_position": 95000},
                {"designation": "Senior Backend Engineer", "vacancies": 2, "estimated_cost_per_position": 130000},
            ]
        },
        {
            "name": f"Engineering Frontend Hiring {current_year}",
            "department": rd_dept,
            "staffing_details": [
                {"designation": "Frontend Engineer", "vacancies": 3, "estimated_cost_per_position": 90000},
                {"designation": "Senior Frontend Engineer", "vacancies": 1, "estimated_cost_per_position": 125000},
            ]
        },
        {
            "name": f"Platform Infrastructure Hiring {current_year}",
            "department": rd_dept,
            "staffing_details": [
                {"designation": "DevOps Engineer", "vacancies": 2, "estimated_cost_per_position": 110000},
                {"designation": "Site Reliability Engineer (SRE)", "vacancies": 1, "estimated_cost_per_position": 120000},
                {"designation": "Security Engineer", "vacancies": 1, "estimated_cost_per_position": 115000},
            ]
        },
        {
            "name": f"Data Team Hiring {current_year}",
            "department": rd_dept,
            "staffing_details": [
                {"designation": "Data Scientist", "vacancies": 2, "estimated_cost_per_position": 125000},
                {"designation": "Data Analyst", "vacancies": 1, "estimated_cost_per_position": 85000},
            ]
        },
        {
            "name": f"Product Design Hiring {current_year}",
            "department": rd_dept,
            "staffing_details": [
                {"designation": "Product Manager", "vacancies": 2, "estimated_cost_per_position": 120000},
                {"designation": "UX/UI Designer", "vacancies": 2, "estimated_cost_per_position": 95000},
            ]
        },
        {
            "name": f"Sales Team Expansion {current_year}",
            "department": sales_dept,
            "staffing_details": [
                {"designation": "Account Executive", "vacancies": 3, "estimated_cost_per_position": 85000},
                {"designation": "SDR (Sales Development Representative)", "vacancies": 2, "estimated_cost_per_position": 60000},
            ]
        },
        {
            "name": f"Marketing Growth Hiring {current_year}",
            "department": marketing_dept,
            "staffing_details": [
                {"designation": "Growth Marketer", "vacancies": 1, "estimated_cost_per_position": 90000},
                {"designation": "Brand/Content Marketer", "vacancies": 1, "estimated_cost_per_position": 80000},
                {"designation": "SEO Specialist", "vacancies": 1, "estimated_cost_per_position": 75000},
            ]
        },
        {
            "name": f"Customer Success Hiring {current_year}",
            "department": cs_dept,
            "staffing_details": [
                {"designation": "Customer Success Manager", "vacancies": 2, "estimated_cost_per_position": 85000},
                {"designation": "Customer Support Specialist", "vacancies": 2, "estimated_cost_per_position": 55000},
            ]
        },
    ]
    
    created_plans = []
    for plan_data in staffing_plans_data:
        try:
            if frappe.db.exists("Staffing Plan", plan_data["name"]):
                print(f"  ↻ Already exists: {plan_data['name']}")
                created_plans.append(plan_data["name"])
                continue
            
            # Verify department exists
            if not frappe.db.exists("Department", plan_data["department"]):
                print(f"  ⚠ Department not found: {plan_data['department']}")
                continue
            
            # Filter valid designations
            valid_details = []
            for detail in plan_data["staffing_details"]:
                if frappe.db.exists("Designation", detail["designation"]):
                    valid_details.append(detail)
                else:
                    print(f"  ⚠ Designation not found: {detail['designation']}")
            
            if not valid_details:
                continue
            
            staffing_plan = frappe.get_doc({
                "doctype": "Staffing Plan",
                "name": plan_data["name"],
                "company": company,
                "department": plan_data["department"],
                "from_date": from_date,
                "to_date": to_date,
                "staffing_details": valid_details
            })
            staffing_plan.insert(ignore_permissions=True)
            staffing_plan.submit()
            created_plans.append(staffing_plan.name)
            print(f"  ✓ Created: {plan_data['name']}")
        except Exception as e:
            print(f"  ⚠ Error creating staffing plan {plan_data['name']}: {str(e)[:60]}")
    
    return created_plans


# ============================================================================
# JOB REQUISITIONS
# ============================================================================

def create_job_requisitions(company, company_abbr):
    """Create job requisitions from hiring managers"""
    
    # Get hiring managers from roster
    hiring_managers = {
        "Victor James Lin": "VP Engineering",
        "David Wong": "Engineering Manager (Backend)",
        "Hannah Lee": "Engineering Manager (Frontend)",
        "Samuel Ortiz": "Engineering Manager (Platform/Infra)",
        "Oscar Reyes": "Head of Sales",
        "Vera Johansson": "Marketing Director",
        "Rebecca Shaw": "Head of Talent Acquisition",
    }
    
    rd_dept = f"Research & Development - {company_abbr}"
    sales_dept = f"Sales - {company_abbr}"
    marketing_dept = f"Marketing - {company_abbr}"
    
    requisitions_data = [
        {
            "designation": "Backend Engineer",
            "department": rd_dept,
            "no_of_positions": 2,
            "expected_compensation": 95000,
            "requested_by_name": "David Wong",
            "description": "We are looking for talented Backend Engineers to join our growing team.",
            "reason_for_requesting": "Team expansion to support new product features",
            "expected_by_days": 45,
        },
        {
            "designation": "Senior Backend Engineer",
            "department": rd_dept,
            "no_of_positions": 1,
            "expected_compensation": 130000,
            "requested_by_name": "David Wong",
            "description": "Senior Backend Engineer to lead complex backend initiatives.",
            "reason_for_requesting": "Need senior leadership for backend architecture",
            "expected_by_days": 60,
        },
        {
            "designation": "Frontend Engineer",
            "department": rd_dept,
            "no_of_positions": 2,
            "expected_compensation": 90000,
            "requested_by_name": "Hannah Lee",
            "description": "Frontend Engineers to build amazing user experiences.",
            "reason_for_requesting": "New product UI development",
            "expected_by_days": 30,
        },
        {
            "designation": "DevOps Engineer",
            "department": rd_dept,
            "no_of_positions": 1,
            "expected_compensation": 110000,
            "requested_by_name": "Samuel Ortiz",
            "description": "DevOps Engineer to improve our CI/CD and infrastructure.",
            "reason_for_requesting": "Infrastructure scaling requirements",
            "expected_by_days": 45,
        },
        {
            "designation": "Data Scientist",
            "department": rd_dept,
            "no_of_positions": 1,
            "expected_compensation": 125000,
            "requested_by_name": "Victor James Lin",
            "description": "Data Scientist to drive data-driven product decisions.",
            "reason_for_requesting": "Building out ML capabilities",
            "expected_by_days": 60,
        },
        {
            "designation": "Account Executive",
            "department": sales_dept,
            "no_of_positions": 2,
            "expected_compensation": 85000,
            "requested_by_name": "Oscar Reyes",
            "description": "Account Executives to drive enterprise sales.",
            "reason_for_requesting": "Sales team expansion for Q3/Q4 targets",
            "expected_by_days": 30,
        },
        {
            "designation": "Growth Marketer",
            "department": marketing_dept,
            "no_of_positions": 1,
            "expected_compensation": 90000,
            "requested_by_name": "Vera Johansson",
            "description": "Growth Marketer to scale our acquisition channels.",
            "reason_for_requesting": "Need to 3x growth in next quarter",
            "expected_by_days": 45,
        },
    ]
    
    created_requisitions = []
    for req_data in requisitions_data:
        try:
            # Find the employee who is requesting
            requested_by = frappe.db.get_value(
                "Employee",
                {"employee_name": req_data["requested_by_name"], "company": company},
                "name"
            )
            
            if not requested_by:
                print(f"  ⚠ Requester not found: {req_data['requested_by_name']}")
                continue
            
            # Check if designation exists
            if not frappe.db.exists("Designation", req_data["designation"]):
                print(f"  ⚠ Designation not found: {req_data['designation']}")
                continue
            
            job_req = frappe.get_doc({
                "doctype": "Job Requisition",
                "designation": req_data["designation"],
                "department": req_data["department"],
                "no_of_positions": req_data["no_of_positions"],
                "expected_compensation": req_data["expected_compensation"],
                "company": company,
                "status": "Open & Approved",
                "requested_by": requested_by,
                "posting_date": nowdate(),
                "expected_by": add_days(getdate(), req_data["expected_by_days"]),
                "description": req_data["description"],
                "reason_for_requesting": req_data["reason_for_requesting"],
            })
            job_req.insert(ignore_permissions=True)
            created_requisitions.append(job_req)
            print(f"  ✓ Created: {req_data['designation']} ({req_data['no_of_positions']} positions)")
        except Exception as e:
            print(f"  ⚠ Error creating requisition for {req_data['designation']}: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_requisitions)} job requisitions")
    return created_requisitions


# ============================================================================
# JOB OPENINGS
# ============================================================================

def create_job_openings(company, company_abbr, job_requisitions):
    """Create job openings with descriptions"""
    
    rd_dept = f"Research & Development - {company_abbr}"
    sales_dept = f"Sales - {company_abbr}"
    marketing_dept = f"Marketing - {company_abbr}"
    cs_dept = f"Customer Service - {company_abbr}"
    
    # Job descriptions templates
    job_descriptions = {
        "Backend Engineer": """
<h3>About the Role</h3>
<p>We're looking for a Backend Engineer to help build scalable, reliable backend systems that power our platform.</p>

<h3>Responsibilities</h3>
<ul>
<li>Design and implement RESTful APIs and microservices</li>
<li>Write clean, maintainable, and well-tested code</li>
<li>Collaborate with frontend engineers and product managers</li>
<li>Participate in code reviews and technical discussions</li>
<li>Troubleshoot and debug production issues</li>
</ul>

<h3>Requirements</h3>
<ul>
<li>2+ years of experience in backend development</li>
<li>Proficiency in Python, Node.js, or similar languages</li>
<li>Experience with SQL and NoSQL databases</li>
<li>Understanding of RESTful API design principles</li>
<li>Familiarity with cloud services (AWS, GCP, or Azure)</li>
</ul>
""",
        "Senior Backend Engineer": """
<h3>About the Role</h3>
<p>We're seeking a Senior Backend Engineer to lead complex technical initiatives and mentor junior engineers.</p>

<h3>Responsibilities</h3>
<ul>
<li>Lead the design and architecture of backend systems</li>
<li>Mentor and guide junior engineers</li>
<li>Drive technical decisions and best practices</li>
<li>Optimize system performance and scalability</li>
<li>Collaborate cross-functionally with product and design</li>
</ul>

<h3>Requirements</h3>
<ul>
<li>5+ years of backend development experience</li>
<li>Strong system design and architecture skills</li>
<li>Experience with distributed systems</li>
<li>Track record of delivering complex projects</li>
<li>Excellent communication and leadership skills</li>
</ul>
""",
        "Frontend Engineer": """
<h3>About the Role</h3>
<p>Join our frontend team to build beautiful, responsive user interfaces that delight our customers.</p>

<h3>Responsibilities</h3>
<ul>
<li>Build responsive web applications using React</li>
<li>Implement pixel-perfect designs from Figma</li>
<li>Write unit and integration tests</li>
<li>Optimize application performance</li>
<li>Collaborate with designers and backend engineers</li>
</ul>

<h3>Requirements</h3>
<ul>
<li>2+ years of frontend development experience</li>
<li>Proficiency in JavaScript/TypeScript and React</li>
<li>Strong HTML/CSS skills</li>
<li>Experience with state management (Redux, MobX, etc.)</li>
<li>Eye for design and attention to detail</li>
</ul>
""",
        "DevOps Engineer": """
<h3>About the Role</h3>
<p>We're looking for a DevOps Engineer to help us build and maintain our cloud infrastructure.</p>

<h3>Responsibilities</h3>
<ul>
<li>Design and maintain CI/CD pipelines</li>
<li>Manage cloud infrastructure (AWS/GCP)</li>
<li>Implement monitoring and alerting solutions</li>
<li>Automate deployment and operations tasks</li>
<li>Ensure system reliability and security</li>
</ul>

<h3>Requirements</h3>
<ul>
<li>3+ years of DevOps/SRE experience</li>
<li>Strong experience with Docker and Kubernetes</li>
<li>Proficiency in infrastructure as code (Terraform, CloudFormation)</li>
<li>Experience with CI/CD tools (Jenkins, GitLab CI, GitHub Actions)</li>
<li>Strong Linux administration skills</li>
</ul>
""",
        "Data Scientist": """
<h3>About the Role</h3>
<p>Join our data team to drive insights and build ML models that power our product.</p>

<h3>Responsibilities</h3>
<ul>
<li>Develop and deploy machine learning models</li>
<li>Analyze large datasets to extract insights</li>
<li>Collaborate with product teams on data-driven features</li>
<li>Build and maintain data pipelines</li>
<li>Present findings to stakeholders</li>
</ul>

<h3>Requirements</h3>
<ul>
<li>3+ years of data science experience</li>
<li>Strong Python skills and ML frameworks (scikit-learn, TensorFlow, PyTorch)</li>
<li>Experience with SQL and data visualization</li>
<li>Statistical analysis and experimentation experience</li>
<li>Excellent communication skills</li>
</ul>
""",
        "Account Executive": """
<h3>About the Role</h3>
<p>We're looking for driven Account Executives to grow our enterprise customer base.</p>

<h3>Responsibilities</h3>
<ul>
<li>Manage full sales cycle from prospecting to close</li>
<li>Build relationships with enterprise decision-makers</li>
<li>Conduct product demos and presentations</li>
<li>Negotiate contracts and close deals</li>
<li>Collaborate with customer success for smooth handoffs</li>
</ul>

<h3>Requirements</h3>
<ul>
<li>3+ years of B2B SaaS sales experience</li>
<li>Track record of meeting or exceeding quota</li>
<li>Experience with enterprise sales cycles</li>
<li>Strong presentation and negotiation skills</li>
<li>CRM experience (Salesforce preferred)</li>
</ul>
""",
        "Growth Marketer": """
<h3>About the Role</h3>
<p>We're seeking a Growth Marketer to scale our acquisition channels and drive user growth.</p>

<h3>Responsibilities</h3>
<ul>
<li>Develop and execute growth strategies</li>
<li>Manage paid acquisition channels</li>
<li>Run A/B tests and optimize conversion funnels</li>
<li>Analyze metrics and report on performance</li>
<li>Collaborate with product on growth features</li>
</ul>

<h3>Requirements</h3>
<ul>
<li>3+ years of growth marketing experience</li>
<li>Experience with paid ads (Google, Facebook, LinkedIn)</li>
<li>Strong analytical skills and data-driven mindset</li>
<li>Experience with marketing automation tools</li>
<li>Track record of driving measurable growth</li>
</ul>
""",
        "UX/UI Designer": """
<h3>About the Role</h3>
<p>Join our design team to create intuitive and beautiful user experiences.</p>

<h3>Responsibilities</h3>
<ul>
<li>Design user interfaces for web and mobile applications</li>
<li>Conduct user research and usability testing</li>
<li>Create wireframes, prototypes, and high-fidelity designs</li>
<li>Maintain and evolve our design system</li>
<li>Collaborate with engineers on implementation</li>
</ul>

<h3>Requirements</h3>
<ul>
<li>3+ years of UX/UI design experience</li>
<li>Proficiency in Figma or similar design tools</li>
<li>Strong portfolio demonstrating UX process</li>
<li>Understanding of design systems</li>
<li>Experience with user research methods</li>
</ul>
""",
        "Customer Success Manager": """
<h3>About the Role</h3>
<p>We're looking for a Customer Success Manager to ensure our customers achieve their goals.</p>

<h3>Responsibilities</h3>
<ul>
<li>Manage a portfolio of enterprise customers</li>
<li>Drive product adoption and customer satisfaction</li>
<li>Conduct business reviews and health checks</li>
<li>Identify upsell and expansion opportunities</li>
<li>Advocate for customer needs internally</li>
</ul>

<h3>Requirements</h3>
<ul>
<li>3+ years of customer success or account management experience</li>
<li>Experience with SaaS products</li>
<li>Strong relationship-building skills</li>
<li>Data-driven approach to customer health</li>
<li>Excellent communication and presentation skills</li>
</ul>
""",
        "SDR (Sales Development Representative)": """
<h3>About the Role</h3>
<p>We're looking for motivated SDRs to generate qualified leads for our sales team.</p>

<h3>Responsibilities</h3>
<ul>
<li>Prospect and qualify inbound and outbound leads</li>
<li>Conduct initial discovery calls</li>
<li>Schedule meetings for Account Executives</li>
<li>Maintain accurate records in CRM</li>
<li>Meet and exceed activity and meeting targets</li>
</ul>

<h3>Requirements</h3>
<ul>
<li>1+ years of SDR or sales experience</li>
<li>Excellent communication skills</li>
<li>Self-motivated and goal-oriented</li>
<li>Experience with sales tools and CRM</li>
<li>Coachable and eager to learn</li>
</ul>
""",
    }
    
    # Create openings from requisitions first
    created_openings = []
    for req in job_requisitions:
        try:
            designation = req.designation
            description = job_descriptions.get(designation, f"<p>We are hiring for {designation}. Apply now!</p>")
            
            job_opening = frappe.get_doc({
                "doctype": "Job Opening",
                "job_title": f"{designation} - {company}",
                "designation": designation,
                "company": company,
                "department": req.department,
                "status": "Open",
                "job_requisition": req.name,
                "description": description,
                "currency": "USD",
                "lower_range": int(req.expected_compensation * 0.9),
                "upper_range": int(req.expected_compensation * 1.15),
                "salary_per": "Year",
            })
            job_opening.insert(ignore_permissions=True)
            created_openings.append(job_opening)
            print(f"  ✓ Created: {job_opening.job_title}")
        except Exception as e:
            print(f"  ⚠ Error creating job opening for {req.designation}: {str(e)[:60]}")
    
    # Create additional standalone openings
    additional_openings = [
        {"designation": "UX/UI Designer", "department": rd_dept, "lower_range": 85000, "upper_range": 110000},
        {"designation": "Customer Success Manager", "department": cs_dept, "lower_range": 75000, "upper_range": 95000},
        {"designation": "SDR (Sales Development Representative)", "department": sales_dept, "lower_range": 50000, "upper_range": 70000},
    ]
    
    for opening_data in additional_openings:
        try:
            if not frappe.db.exists("Designation", opening_data["designation"]):
                continue
            
            description = job_descriptions.get(opening_data["designation"], f"<p>We are hiring for {opening_data['designation']}. Apply now!</p>")
            
            job_opening = frappe.get_doc({
                "doctype": "Job Opening",
                "job_title": f"{opening_data['designation']} - {company}",
                "designation": opening_data["designation"],
                "company": company,
                "department": opening_data["department"],
                "status": "Open",
                "description": description,
                "currency": "USD",
                "lower_range": opening_data["lower_range"],
                "upper_range": opening_data["upper_range"],
                "salary_per": "Year",
            })
            job_opening.insert(ignore_permissions=True)
            created_openings.append(job_opening)
            print(f"  ✓ Created: {job_opening.job_title}")
        except Exception as e:
            print(f"  ⚠ Error creating job opening for {opening_data['designation']}: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_openings)} job openings")
    return created_openings


# ============================================================================
# EMPLOYEE REFERRALS
# ============================================================================

def create_employee_referrals(company):
    """Create employee referrals from existing employees"""
    
    referrals_data = [
        {
            "first_name": "Marcus",
            "last_name": "Thompson",
            "email": "marcus.thompson@gmail.com",
            "contact_no": "+1 (415) 555-8901",
            "for_designation": "Backend Engineer",
            "referrer_name": "Emily Zhang",  # Senior Backend Engineer
            "current_employer": "TechCorp Inc",
            "current_job_title": "Software Developer",
            "qualification_reason": "Former colleague with strong Python skills and system design experience.",
        },
        {
            "first_name": "Priya",
            "last_name": "Sharma",
            "email": "priya.sharma.dev@gmail.com",
            "contact_no": "+1 (415) 555-8902",
            "for_designation": "Frontend Engineer",
            "referrer_name": "Ivan Petrov",  # Senior Frontend Engineer
            "current_employer": "WebSolutions LLC",
            "current_job_title": "React Developer",
            "qualification_reason": "Met at a React conference, impressive portfolio and passion for UI/UX.",
        },
        {
            "first_name": "James",
            "last_name": "O'Brien",
            "email": "james.obrien@outlook.com",
            "contact_no": "+1 (415) 555-8903",
            "for_designation": "DevOps Engineer",
            "referrer_name": "Leonardo Silva",  # DevOps Engineer
            "current_employer": "CloudFirst",
            "current_job_title": "Infrastructure Engineer",
            "qualification_reason": "University classmate with excellent AWS and Kubernetes skills.",
        },
        {
            "first_name": "Sarah",
            "last_name": "Kim",
            "email": "sarah.kim.design@gmail.com",
            "contact_no": "+1 (415) 555-8904",
            "for_designation": "UX/UI Designer",
            "referrer_name": "Grace Liu",  # UX/UI Designer
            "current_employer": "DesignStudio",
            "current_job_title": "Product Designer",
            "qualification_reason": "Worked together on a freelance project, excellent design thinking skills.",
        },
        {
            "first_name": "David",
            "last_name": "Chen",
            "email": "david.chen.sales@gmail.com",
            "contact_no": "+1 (415) 555-8905",
            "for_designation": "Account Executive",
            "referrer_name": "Priya Nair",  # Account Executive
            "current_employer": "SalesForce Solutions",
            "current_job_title": "Sales Representative",
            "qualification_reason": "Former sales partner, consistently exceeded targets.",
        },
    ]
    
    created_referrals = []
    for ref_data in referrals_data:
        try:
            # Check if already exists
            if frappe.db.exists("Employee Referral", {"email": ref_data["email"]}):
                print(f"  ↻ Already exists: {ref_data['first_name']} {ref_data['last_name']}")
                continue
            
            # Find the referrer employee
            referrer = frappe.db.get_value(
                "Employee",
                {"employee_name": ref_data["referrer_name"], "company": company},
                "name"
            )
            
            if not referrer:
                print(f"  ⚠ Referrer not found: {ref_data['referrer_name']}")
                continue
            
            # Check if designation exists
            if not frappe.db.exists("Designation", ref_data["for_designation"]):
                print(f"  ⚠ Designation not found: {ref_data['for_designation']}")
                continue
            
            emp_referral = frappe.get_doc({
                "doctype": "Employee Referral",
                "first_name": ref_data["first_name"],
                "last_name": ref_data["last_name"],
                "email": ref_data["email"],
                "contact_no": ref_data["contact_no"],
                "date": nowdate(),
                "for_designation": ref_data["for_designation"],
                "referrer": referrer,
                "current_employer": ref_data["current_employer"],
                "current_job_title": ref_data["current_job_title"],
                "qualification_reason": ref_data["qualification_reason"],
                "is_applicable_for_referral_bonus": 1,
            })
            emp_referral.insert(ignore_permissions=True)
            emp_referral.submit()
            created_referrals.append(emp_referral)
            print(f"  ✓ Created referral: {ref_data['first_name']} {ref_data['last_name']} (referred by {ref_data['referrer_name']})")
        except Exception as e:
            print(f"  ⚠ Error creating referral for {ref_data['first_name']}: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_referrals)} employee referrals")
    return created_referrals


# ============================================================================
# JOB APPLICANTS
# ============================================================================

def create_job_applicants(job_openings, employee_referrals):
    """Create job applicants with realistic profiles"""
    
    # External applicants (not from referrals)
    external_applicants = [
        {
            "applicant_name": "Alex Johnson",
            "email_id": "alex.johnson.dev@gmail.com",
            "phone_number": "+1 (415) 555-7001",
            "designation": "Backend Engineer",
            "source": "LinkedIn",
            "cover_letter": "I am excited to apply for the Backend Engineer position. With 3 years of experience in Python and Django, I believe I would be a great fit for your team.",
            "status": "Open",
        },
        {
            "applicant_name": "Emily Rodriguez",
            "email_id": "emily.rodriguez@outlook.com",
            "phone_number": "+1 (415) 555-7002",
            "designation": "Backend Engineer",
            "source": "Indeed",
            "cover_letter": "I'm a passionate backend developer with experience in microservices architecture. I'd love to contribute to your engineering team.",
            "status": "Replied",
        },
        {
            "applicant_name": "Michael Park",
            "email_id": "michael.park.eng@gmail.com",
            "phone_number": "+1 (415) 555-7003",
            "designation": "Senior Backend Engineer",
            "source": "Company Website",
            "cover_letter": "With 6 years of experience building scalable systems at tech companies, I'm looking for my next challenge.",
            "status": "Open",
        },
        {
            "applicant_name": "Jessica Liu",
            "email_id": "jessica.liu.frontend@gmail.com",
            "phone_number": "+1 (415) 555-7004",
            "designation": "Frontend Engineer",
            "source": "LinkedIn",
            "cover_letter": "I'm a React specialist with a keen eye for design. I've built several production applications and am excited about this opportunity.",
            "status": "Open",
        },
        {
            "applicant_name": "Ryan Mitchell",
            "email_id": "ryan.mitchell@yahoo.com",
            "phone_number": "+1 (415) 555-7005",
            "designation": "Frontend Engineer",
            "source": "Glassdoor",
            "cover_letter": "Frontend developer with 4 years of experience. Strong in TypeScript and modern CSS frameworks.",
            "status": "Replied",
        },
        {
            "applicant_name": "Sophia Williams",
            "email_id": "sophia.williams.devops@gmail.com",
            "phone_number": "+1 (415) 555-7006",
            "designation": "DevOps Engineer",
            "source": "LinkedIn",
            "cover_letter": "DevOps engineer with expertise in Kubernetes and CI/CD pipelines. Passionate about automation and reliability.",
            "status": "Open",
        },
        {
            "applicant_name": "Daniel Kim",
            "email_id": "daniel.kim.data@gmail.com",
            "phone_number": "+1 (415) 555-7007",
            "designation": "Data Scientist",
            "source": "Indeed",
            "cover_letter": "PhD in Machine Learning with 4 years of industry experience. Excited about applying ML to real-world problems.",
            "status": "Open",
        },
        {
            "applicant_name": "Amanda Foster",
            "email_id": "amanda.foster.sales@gmail.com",
            "phone_number": "+1 (415) 555-7008",
            "designation": "Account Executive",
            "source": "LinkedIn",
            "cover_letter": "Top-performing AE with 5 years of B2B SaaS experience. Consistently exceeded quota by 120%.",
            "status": "Open",
        },
        {
            "applicant_name": "Christopher Brown",
            "email_id": "chris.brown.sales@outlook.com",
            "phone_number": "+1 (415) 555-7009",
            "designation": "Account Executive",
            "source": "Recruiting Agency",
            "cover_letter": "Enterprise sales professional with deep experience in software sales. Looking to join a fast-growing company.",
            "status": "Replied",
        },
        {
            "applicant_name": "Olivia Martinez",
            "email_id": "olivia.martinez.growth@gmail.com",
            "phone_number": "+1 (415) 555-7010",
            "designation": "Growth Marketer",
            "source": "LinkedIn",
            "cover_letter": "Growth marketer with expertise in paid acquisition and conversion optimization. Ready to scale your marketing efforts.",
            "status": "Open",
        },
        {
            "applicant_name": "Nathan Cooper",
            "email_id": "nathan.cooper.ux@gmail.com",
            "phone_number": "+1 (415) 555-7011",
            "designation": "UX/UI Designer",
            "source": "Company Website",
            "cover_letter": "UX designer with a background in psychology. I create user-centered designs backed by research.",
            "status": "Open",
        },
        {
            "applicant_name": "Rachel Adams",
            "email_id": "rachel.adams.cs@gmail.com",
            "phone_number": "+1 (415) 555-7012",
            "designation": "Customer Success Manager",
            "source": "Indeed",
            "cover_letter": "Customer success professional with 5 years of experience. Passionate about helping customers achieve their goals.",
            "status": "Open",
        },
        {
            "applicant_name": "Kevin Zhang",
            "email_id": "kevin.zhang.sdr@gmail.com",
            "phone_number": "+1 (415) 555-7013",
            "designation": "SDR (Sales Development Representative)",
            "source": "Campus Recruitment",
            "cover_letter": "Recent graduate with internship experience in sales. Eager to start my career in tech sales.",
            "status": "Open",
        },
        {
            "applicant_name": "Michelle Torres",
            "email_id": "michelle.torres.be@gmail.com",
            "phone_number": "+1 (415) 555-7014",
            "designation": "Backend Engineer",
            "source": "Job Fair",
            "cover_letter": "Backend engineer with experience in Go and Python. Interested in building distributed systems.",
            "status": "Rejected",
        },
        {
            "applicant_name": "Brandon Lee",
            "email_id": "brandon.lee.fe@gmail.com",
            "phone_number": "+1 (415) 555-7015",
            "designation": "Frontend Engineer",
            "source": "Direct Application",
            "cover_letter": "Self-taught developer with a strong portfolio. Transitioned from graphic design to frontend development.",
            "status": "Hold",
        },
    ]
    
    # Map job openings by designation for linking
    openings_by_designation = {}
    for opening in job_openings:
        if opening.designation not in openings_by_designation:
            openings_by_designation[opening.designation] = opening.name
    
    created_applicants = []
    
    # First, create applicants from referrals
    for referral in employee_referrals:
        try:
            # Check if applicant already exists
            if frappe.db.exists("Job Applicant", {"email_id": referral.email}):
                print(f"  ↻ Already exists: {referral.full_name}")
                continue
            
            job_opening = openings_by_designation.get(referral.for_designation)
            
            applicant = frappe.get_doc({
                "doctype": "Job Applicant",
                "applicant_name": referral.full_name,
                "email_id": referral.email,
                "phone_number": referral.contact_no,
                "job_title": job_opening,
                "designation": referral.for_designation,
                "status": "Open",
                "source": "Employee Referral",
                "employee_referral": referral.name,
                "cover_letter": f"Referred by a current employee. {referral.qualification_reason}",
            })
            applicant.insert(ignore_permissions=True)
            created_applicants.append(applicant)
            print(f"  ✓ Created (referral): {referral.full_name}")
        except Exception as e:
            print(f"  ⚠ Error creating applicant from referral {referral.full_name}: {str(e)[:60]}")
    
    # Then create external applicants
    for app_data in external_applicants:
        try:
            # Check if applicant already exists
            if frappe.db.exists("Job Applicant", {"email_id": app_data["email_id"]}):
                print(f"  ↻ Already exists: {app_data['applicant_name']}")
                continue
            
            job_opening = openings_by_designation.get(app_data["designation"])
            
            # Check if source exists
            source = app_data["source"] if frappe.db.exists("Job Applicant Source", app_data["source"]) else None
            
            applicant = frappe.get_doc({
                "doctype": "Job Applicant",
                "applicant_name": app_data["applicant_name"],
                "email_id": app_data["email_id"],
                "phone_number": app_data["phone_number"],
                "job_title": job_opening,
                "designation": app_data["designation"],
                "status": app_data["status"],
                "source": source,
                "cover_letter": app_data["cover_letter"],
            })
            applicant.insert(ignore_permissions=True)
            created_applicants.append(applicant)
            print(f"  ✓ Created: {app_data['applicant_name']}")
        except Exception as e:
            print(f"  ⚠ Error creating applicant {app_data['applicant_name']}: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_applicants)} job applicants")
    return created_applicants


# ============================================================================
# INTERVIEW ROUNDS
# ============================================================================

def create_interview_rounds(skills, interview_types):
    """Create interview rounds with expected skill sets"""
    
    rounds_data = [
        {
            "round_name": "Technical Phone Screen",
            "interview_type": "Phone Screen",
            "expected_average_rating": 0.6,
            "skills": ["Python", "Data Structures", "Problem Solving"],
        },
        {
            "round_name": "Backend Technical Interview",
            "interview_type": "Technical Interview",
            "expected_average_rating": 0.7,
            "skills": ["Python", "SQL", "System Design", "Data Structures", "Algorithms"],
        },
        {
            "round_name": "Frontend Technical Interview",
            "interview_type": "Technical Interview",
            "expected_average_rating": 0.7,
            "skills": ["JavaScript", "React", "TypeScript", "Problem Solving"],
        },
        {
            "round_name": "DevOps Technical Interview",
            "interview_type": "Technical Interview",
            "expected_average_rating": 0.7,
            "skills": ["AWS", "Docker", "Kubernetes", "Problem Solving"],
        },
        {
            "round_name": "System Design Interview",
            "interview_type": "Technical Interview",
            "expected_average_rating": 0.75,
            "skills": ["System Design", "Problem Solving", "Communication"],
        },
        {
            "round_name": "HR Screening",
            "interview_type": "HR Interview",
            "expected_average_rating": 0.6,
            "skills": ["Communication", "Teamwork", "Leadership"],
        },
        {
            "round_name": "Behavioral Interview",
            "interview_type": "Behavioral Interview",
            "expected_average_rating": 0.7,
            "skills": ["Communication", "Problem Solving", "Leadership", "Teamwork"],
        },
        {
            "round_name": "Sales Role Play",
            "interview_type": "Case Study",
            "expected_average_rating": 0.7,
            "skills": ["Sales Techniques", "Negotiation", "Communication", "Presentation Skills"],
        },
        {
            "round_name": "Design Review",
            "interview_type": "Panel Interview",
            "expected_average_rating": 0.7,
            "skills": ["UX Design", "UI Design", "Communication", "Problem Solving"],
        },
        {
            "round_name": "Final Round - Leadership",
            "interview_type": "Final Round",
            "expected_average_rating": 0.8,
            "skills": ["Communication", "Leadership", "Problem Solving"],
        },
    ]
    
    created_rounds = []
    for round_data in rounds_data:
        try:
            if frappe.db.exists("Interview Round", round_data["round_name"]):
                created_rounds.append(round_data["round_name"])
                print(f"  ↻ Already exists: {round_data['round_name']}")
                continue
            
            # Check interview type exists
            interview_type = round_data["interview_type"] if frappe.db.exists("Interview Type", round_data["interview_type"]) else None
            
            interview_round = frappe.new_doc("Interview Round")
            interview_round.round_name = round_data["round_name"]
            interview_round.interview_type = interview_type
            interview_round.expected_average_rating = round_data["expected_average_rating"]
            
            # Add expected skill set
            for skill in round_data["skills"]:
                if skill in skills:
                    interview_round.append("expected_skill_set", {"skill": skill})
            
            interview_round.insert(ignore_permissions=True)
            created_rounds.append(interview_round.name)
            print(f"  ✓ Created: {round_data['round_name']}")
        except Exception as e:
            print(f"  ⚠ Error creating interview round {round_data['round_name']}: {str(e)[:60]}")
    
    print(f"  ✓ Created/verified {len(created_rounds)} interview rounds")
    return created_rounds


# ============================================================================
# INTERVIEWERS SETUP
# ============================================================================

def setup_interviewers(company):
    """Setup employees as interviewers by assigning Interviewer role"""
    
    # Select employees to be interviewers (senior engineers, managers, HR)
    interviewer_names = [
        "Victor James Lin",      # VP Engineering
        "David Wong",            # Engineering Manager (Backend)
        "Hannah Lee",            # Engineering Manager (Frontend)
        "Emily Zhang",           # Senior Backend Engineer
        "Hiroshi Tanaka",        # Senior Backend Engineer
        "Ivan Petrov",           # Senior Frontend Engineer
        "Michelle Wang",         # Senior Frontend Engineer
        "Samuel Ortiz",          # Engineering Manager (Platform/Infra)
        "Rebecca Shaw",          # Head of Talent Acquisition
        "Samuel Lee",            # HR Operations Manager
        "Oscar Reyes",           # Head of Sales
        "Vera Johansson",        # Marketing Director
        "Natalie Park",          # Head of Design
    ]
    
    interviewers = []
    for name in interviewer_names:
        try:
            # Find employee
            employee = frappe.db.get_value(
                "Employee",
                {"employee_name": name, "company": company},
                ["name", "user_id"],
                as_dict=True
            )
            
            if not employee or not employee.user_id:
                continue
            
            # Check if Interviewer role exists
            if not frappe.db.exists("Role", "Interviewer"):
                frappe.get_doc({
                    "doctype": "Role",
                    "role_name": "Interviewer"
                }).insert(ignore_permissions=True)
            
            # Add Interviewer role to user
            if not frappe.db.exists("Has Role", {"parent": employee.user_id, "role": "Interviewer"}):
                frappe.get_doc({
                    "doctype": "Has Role",
                    "parent": employee.user_id,
                    "parenttype": "User",
                    "parentfield": "roles",
                    "role": "Interviewer"
                }).db_insert()
            
            interviewers.append(employee.user_id)
        except Exception as e:
            print(f"  ⚠ Error setting up interviewer {name}: {str(e)[:50]}")
    
    frappe.db.commit()
    print(f"  ✓ Set up {len(interviewers)} interviewers")
    return interviewers


# ============================================================================
# INTERVIEWS
# ============================================================================

def create_interviews(job_applicants, interview_rounds, interviewers):
    """Create interviews for job applicants"""
    
    if not interviewers:
        print("  ⚠ No interviewers available, skipping interviews")
        return []
    
    # Select applicants for interviews (those with Open or Replied status)
    interview_candidates = [
        app for app in job_applicants 
        if app.status in ["Open", "Replied"]
    ][:12]  # Limit to 12 interviews
    
    # Map rounds to designations
    round_mapping = {
        "Backend Engineer": ["Technical Phone Screen", "Backend Technical Interview", "Behavioral Interview"],
        "Senior Backend Engineer": ["Backend Technical Interview", "System Design Interview", "Final Round - Leadership"],
        "Frontend Engineer": ["Technical Phone Screen", "Frontend Technical Interview", "Behavioral Interview"],
        "DevOps Engineer": ["DevOps Technical Interview", "System Design Interview", "Behavioral Interview"],
        "Data Scientist": ["Technical Phone Screen", "System Design Interview", "Behavioral Interview"],
        "Account Executive": ["HR Screening", "Sales Role Play", "Final Round - Leadership"],
        "Growth Marketer": ["HR Screening", "Behavioral Interview", "Final Round - Leadership"],
        "UX/UI Designer": ["HR Screening", "Design Review", "Final Round - Leadership"],
        "Customer Success Manager": ["HR Screening", "Behavioral Interview", "Final Round - Leadership"],
        "SDR (Sales Development Representative)": ["HR Screening", "Sales Role Play"],
    }
    
    statuses = ["Pending", "Pending", "Under Review", "Cleared", "Rejected"]
    
    created_interviews = []
    for i, applicant in enumerate(interview_candidates):
        try:
            designation = applicant.designation or "Backend Engineer"
            rounds_for_role = round_mapping.get(designation, ["HR Screening", "Behavioral Interview"])
            
            # Pick a round for this interview
            round_name = rounds_for_role[i % len(rounds_for_role)]
            
            if round_name not in interview_rounds:
                round_name = interview_rounds[0] if interview_rounds else None
            
            if not round_name:
                continue
            
            # Schedule interview in the future
            scheduled_date = add_days(getdate(), 3 + i)
            status = statuses[i % len(statuses)]
            
            # If status is Cleared or Rejected, schedule in the past
            if status in ["Cleared", "Rejected", "Under Review"]:
                scheduled_date = add_days(getdate(), -(i + 1))
            
            interview = frappe.new_doc("Interview")
            interview.job_applicant = applicant.name
            interview.interview_round = round_name
            interview.scheduled_on = scheduled_date
            interview.from_time = "10:00:00"
            interview.to_time = "11:00:00"
            interview.status = status
            
            # Add interviewers
            for j in range(min(2, len(interviewers))):
                interviewer_idx = (i + j) % len(interviewers)
                interview.append("interview_details", {
                    "interviewer": interviewers[interviewer_idx]
                })
            
            interview.flags.ignore_mandatory = True
            interview.insert(ignore_permissions=True)
            
            # Submit if status is Cleared or Rejected
            if status in ["Cleared", "Rejected"]:
                try:
                    interview.submit()
                except:
                    pass
            
            created_interviews.append(interview)
            print(f"  ✓ Created interview for {applicant.applicant_name} ({status})")
        except Exception as e:
            print(f"  ⚠ Error creating interview for {applicant.applicant_name}: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_interviews)} interviews")
    return created_interviews


# ============================================================================
# INTERVIEW FEEDBACK
# ============================================================================

def create_interview_feedback(interviews, interviewers, skills):
    """Create interview feedback for completed interviews"""
    
    # Only create feedback for interviews that are Under Review or completed
    feedback_candidates = [
        intv for intv in interviews 
        if intv.status in ["Under Review", "Cleared", "Rejected"]
    ]
    
    feedback_texts = [
        "Strong technical skills demonstrated. Good problem-solving approach.",
        "Excellent communication and clear thinking. Would be a great addition to the team.",
        "Solid fundamentals but needs more experience with our tech stack.",
        "Good cultural fit. Showed enthusiasm and asked thoughtful questions.",
        "Struggled with some technical questions but showed willingness to learn.",
        "Outstanding candidate. Highly recommend for next round.",
        "Average performance. Some concerns about pace of delivery.",
        "Strong leadership potential. Good at explaining complex concepts.",
    ]
    
    results = ["Cleared", "Cleared", "Cleared", "Rejected"]
    
    count = 0
    for i, interview in enumerate(feedback_candidates):
        try:
            # Get skills for this interview round
            round_skills = frappe.get_all(
                "Expected Skill Set",
                filters={"parent": interview.interview_round},
                fields=["skill"]
            )
            
            if not round_skills:
                round_skills = [{"skill": "Communication"}, {"skill": "Problem Solving"}]
            
            # Get interviewers for this interview
            interview_details = frappe.get_all(
                "Interview Detail",
                filters={"parent": interview.name},
                fields=["interviewer"]
            )
            
            for j, detail in enumerate(interview_details[:1]):  # One feedback per interview for demo
                interviewer = detail.interviewer
                
                # Check if feedback already exists
                if frappe.db.exists("Interview Feedback", {
                    "interview": interview.name,
                    "interviewer": interviewer
                }):
                    continue
                
                result = results[(i + j) % len(results)]
                
                feedback = frappe.new_doc("Interview Feedback")
                feedback.interview = interview.name
                feedback.interviewer = interviewer
                feedback.result = result
                feedback.feedback = feedback_texts[(i + j) % len(feedback_texts)]
                
                # Add skill assessments
                for skill_data in round_skills[:4]:  # Max 4 skills
                    rating = 0.6 + (0.3 * ((i + j) % 3) / 2)  # Ratings between 0.6 and 0.9
                    feedback.append("skill_assessment", {
                        "skill": skill_data["skill"],
                        "rating": rating
                    })
                
                feedback.flags.ignore_mandatory = True
                feedback.insert(ignore_permissions=True)
                
                # Submit feedback for past interviews
                try:
                    feedback.submit()
                except:
                    pass
                
                count += 1
        except Exception as e:
            print(f"  ⚠ Error creating feedback: {str(e)[:60]}")
    
    print(f"  ✓ Created {count} interview feedback records")


# ============================================================================
# OFFER TERMS (Master Data)
# ============================================================================

def create_offer_terms():
    """Create offer terms for job offers"""
    
    terms = [
        "Base Salary",
        "Signing Bonus",
        "Annual Bonus",
        "Stock Options",
        "Equity Grant",
        "Health Insurance",
        "Dental Insurance",
        "Vision Insurance",
        "401(k) Match",
        "Paid Time Off",
        "Remote Work",
        "Relocation Assistance",
        "Professional Development",
        "Gym Membership",
        "Commuter Benefits",
        "Start Date",
        "Probation Period",
        "Notice Period",
    ]
    
    created_terms = []
    for term in terms:
        try:
            if frappe.db.exists("Offer Term", term):
                created_terms.append(term)
                continue
            
            doc = frappe.get_doc({
                "doctype": "Offer Term",
                "offer_term": term
            })
            doc.insert(ignore_permissions=True)
            created_terms.append(term)
        except Exception as e:
            print(f"  ⚠ Error creating offer term {term}: {str(e)[:50]}")
    
    print(f"  ✓ Created/verified {len(created_terms)} offer terms")
    return created_terms


# ============================================================================
# JOB OFFER TERM TEMPLATES
# ============================================================================

def create_job_offer_term_templates(offer_terms):
    """Create job offer term templates for different role types"""
    
    templates_data = [
        {
            "title": "Standard Engineering Offer",
            "terms": [
                {"offer_term": "Base Salary", "value": "$[SALARY] per year"},
                {"offer_term": "Signing Bonus", "value": "$10,000 one-time payment"},
                {"offer_term": "Annual Bonus", "value": "Up to 15% of base salary based on performance"},
                {"offer_term": "Stock Options", "value": "[SHARES] shares vesting over 4 years with 1-year cliff"},
                {"offer_term": "Health Insurance", "value": "Comprehensive medical, dental, and vision coverage"},
                {"offer_term": "401(k) Match", "value": "100% match up to 4% of salary"},
                {"offer_term": "Paid Time Off", "value": "20 days PTO plus company holidays"},
                {"offer_term": "Remote Work", "value": "Hybrid work arrangement (3 days office, 2 days remote)"},
                {"offer_term": "Start Date", "value": "To be mutually agreed upon"},
            ]
        },
        {
            "title": "Senior Engineering Offer",
            "terms": [
                {"offer_term": "Base Salary", "value": "$[SALARY] per year"},
                {"offer_term": "Signing Bonus", "value": "$25,000 one-time payment"},
                {"offer_term": "Annual Bonus", "value": "Up to 20% of base salary based on performance"},
                {"offer_term": "Equity Grant", "value": "[SHARES] RSUs vesting over 4 years"},
                {"offer_term": "Health Insurance", "value": "Premium medical, dental, and vision coverage for employee and dependents"},
                {"offer_term": "401(k) Match", "value": "100% match up to 6% of salary"},
                {"offer_term": "Paid Time Off", "value": "25 days PTO plus company holidays"},
                {"offer_term": "Remote Work", "value": "Flexible work arrangement"},
                {"offer_term": "Professional Development", "value": "$5,000 annual learning budget"},
                {"offer_term": "Start Date", "value": "To be mutually agreed upon"},
            ]
        },
        {
            "title": "Sales Offer",
            "terms": [
                {"offer_term": "Base Salary", "value": "$[SALARY] per year"},
                {"offer_term": "Annual Bonus", "value": "On-Target Earnings (OTE) of $[OTE] including commissions"},
                {"offer_term": "Stock Options", "value": "[SHARES] shares vesting over 4 years"},
                {"offer_term": "Health Insurance", "value": "Comprehensive medical, dental, and vision coverage"},
                {"offer_term": "401(k) Match", "value": "100% match up to 4% of salary"},
                {"offer_term": "Paid Time Off", "value": "15 days PTO plus company holidays"},
                {"offer_term": "Commuter Benefits", "value": "Pre-tax commuter benefits up to IRS limits"},
                {"offer_term": "Start Date", "value": "To be mutually agreed upon"},
            ]
        },
        {
            "title": "Marketing Offer",
            "terms": [
                {"offer_term": "Base Salary", "value": "$[SALARY] per year"},
                {"offer_term": "Annual Bonus", "value": "Up to 15% of base salary based on performance"},
                {"offer_term": "Stock Options", "value": "[SHARES] shares vesting over 4 years"},
                {"offer_term": "Health Insurance", "value": "Comprehensive medical, dental, and vision coverage"},
                {"offer_term": "401(k) Match", "value": "100% match up to 4% of salary"},
                {"offer_term": "Paid Time Off", "value": "20 days PTO plus company holidays"},
                {"offer_term": "Remote Work", "value": "Hybrid work arrangement"},
                {"offer_term": "Professional Development", "value": "$2,500 annual learning budget"},
                {"offer_term": "Start Date", "value": "To be mutually agreed upon"},
            ]
        },
        {
            "title": "Customer Success Offer",
            "terms": [
                {"offer_term": "Base Salary", "value": "$[SALARY] per year"},
                {"offer_term": "Annual Bonus", "value": "Up to 10% of base salary based on performance"},
                {"offer_term": "Health Insurance", "value": "Comprehensive medical, dental, and vision coverage"},
                {"offer_term": "401(k) Match", "value": "100% match up to 4% of salary"},
                {"offer_term": "Paid Time Off", "value": "15 days PTO plus company holidays"},
                {"offer_term": "Start Date", "value": "To be mutually agreed upon"},
            ]
        },
    ]
    
    created_templates = []
    for template_data in templates_data:
        try:
            if frappe.db.exists("Job Offer Term Template", template_data["title"]):
                created_templates.append(template_data["title"])
                print(f"  ↻ Already exists: {template_data['title']}")
                continue
            
            # Filter valid terms
            valid_terms = []
            for term in template_data["terms"]:
                if term["offer_term"] in offer_terms:
                    valid_terms.append(term)
            
            if not valid_terms:
                continue
            
            template = frappe.get_doc({
                "doctype": "Job Offer Term Template",
                "title": template_data["title"],
                "offer_terms": valid_terms
            })
            template.insert(ignore_permissions=True)
            created_templates.append(template.name)
            print(f"  ✓ Created: {template_data['title']}")
        except Exception as e:
            print(f"  ⚠ Error creating template {template_data['title']}: {str(e)[:60]}")
    
    print(f"  ✓ Created/verified {len(created_templates)} job offer term templates")
    return created_templates


# ============================================================================
# JOB OFFERS
# ============================================================================

def create_job_offers(job_applicants, company, offer_templates=None):
    """Create job offers for qualified applicants"""
    
    # Select applicants who would receive offers (simulating successful candidates)
    # In reality, these would be candidates who cleared interviews
    offer_candidates = [
        app for app in job_applicants
        if app.status in ["Open", "Replied"] and "referral" not in app.email_id.lower()
    ][:4]
    
    # Add some referral candidates
    referral_candidates = [
        app for app in job_applicants
        if app.employee_referral
    ][:2]
    
    offer_candidates.extend(referral_candidates)
    
    statuses = ["Awaiting Response", "Awaiting Response", "Accepted", "Accepted", "Rejected"]
    
    # Map designations to templates
    template_mapping = {
        "Backend Engineer": "Standard Engineering Offer",
        "Senior Backend Engineer": "Senior Engineering Offer",
        "Frontend Engineer": "Standard Engineering Offer",
        "DevOps Engineer": "Standard Engineering Offer",
        "Data Scientist": "Senior Engineering Offer",
        "Account Executive": "Sales Offer",
        "SDR (Sales Development Representative)": "Sales Offer",
        "Growth Marketer": "Marketing Offer",
        "UX/UI Designer": "Standard Engineering Offer",
        "Customer Success Manager": "Customer Success Offer",
    }
    
    created_offers = []
    for i, applicant in enumerate(offer_candidates):
        try:
            # Check if offer already exists
            if frappe.db.exists("Job Offer", {"job_applicant": applicant.name}):
                print(f"  ↻ Offer already exists for: {applicant.applicant_name}")
                continue
            
            status = statuses[i % len(statuses)]
            
            # Get appropriate template
            template_name = template_mapping.get(applicant.designation, "Standard Engineering Offer")
            template = template_name if template_name in (offer_templates or []) else None
            
            job_offer = frappe.get_doc({
                "doctype": "Job Offer",
                "job_applicant": applicant.name,
                "designation": applicant.designation,
                "company": company,
                "offer_date": add_days(getdate(), -(i + 1)),
                "status": status,
                "job_offer_term_template": template,
            })
            
            # Add offer terms from template or manually
            if template and frappe.db.exists("Job Offer Term Template", template):
                template_doc = frappe.get_doc("Job Offer Term Template", template)
                for term in template_doc.offer_terms:
                    job_offer.append("offer_terms", {
                        "offer_term": term.offer_term,
                        "value": term.value
                    })
            
            job_offer.flags.ignore_mandatory = True
            job_offer.insert(ignore_permissions=True)
            
            # Submit accepted offers
            if status == "Accepted":
                try:
                    job_offer.submit()
                except:
                    pass
            
            created_offers.append(job_offer)
            print(f"  ✓ Created offer for {applicant.applicant_name} ({status})")
        except Exception as e:
            print(f"  ⚠ Error creating offer for {applicant.applicant_name}: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_offers)} job offers")
    return created_offers


# ============================================================================
# APPOINTMENT LETTER TEMPLATES
# ============================================================================

def create_appointment_letter_templates():
    """Create appointment letter templates"""
    
    templates_data = [
        {
            "template_name": "Standard Employment Letter",
            "introduction": """Dear {applicant_name},

We are pleased to offer you the position of {designation} at {company}. We were impressed with your background and experience, and we believe you will be a valuable addition to our team.

This letter outlines the terms and conditions of your employment with us.""",
            "terms": [
                {
                    "title": "Position and Responsibilities",
                    "description": "You will be employed as {designation} and will report to your designated manager. Your responsibilities will include duties as outlined in the job description and any additional tasks as assigned."
                },
                {
                    "title": "Compensation",
                    "description": "Your annual base salary will be as discussed during the offer process. Salary will be paid on a bi-weekly basis via direct deposit."
                },
                {
                    "title": "Start Date",
                    "description": "Your employment will commence on the date specified in your offer letter, subject to successful completion of background verification."
                },
                {
                    "title": "Benefits",
                    "description": "You will be eligible for our comprehensive benefits package including health insurance, dental, vision, 401(k) with company match, and paid time off, subject to the terms of each plan."
                },
                {
                    "title": "At-Will Employment",
                    "description": "Your employment with the company is at-will, meaning either you or the company may terminate the employment relationship at any time, with or without cause, and with or without notice."
                },
            ],
            "closing_notes": """We are excited to welcome you to our team. Please sign and return this letter by {acceptance_date} to confirm your acceptance of this offer.

If you have any questions, please don't hesitate to reach out to our HR team.

Sincerely,
Human Resources
{company}"""
        },
        {
            "template_name": "Engineering Appointment Letter",
            "introduction": """Dear {applicant_name},

Congratulations! We are thrilled to extend an offer for the position of {designation} at {company}.

Your technical skills and experience align perfectly with what we're looking for, and we believe you'll make significant contributions to our engineering team.""",
            "terms": [
                {
                    "title": "Position",
                    "description": "You will join our engineering team as {designation}. You will be working on cutting-edge technology projects and collaborating with talented engineers."
                },
                {
                    "title": "Compensation Package",
                    "description": "Your total compensation includes base salary, equity/stock options, and performance bonuses as detailed in your offer letter."
                },
                {
                    "title": "Work Arrangement",
                    "description": "We offer a flexible hybrid work environment. You will be expected to be in the office for team collaboration days as per company policy."
                },
                {
                    "title": "Equipment",
                    "description": "You will be provided with a company laptop and necessary equipment to perform your duties. Additional equipment requests can be made through IT."
                },
                {
                    "title": "Professional Development",
                    "description": "We invest in our engineers' growth. You will have access to learning resources, conference attendance, and a professional development budget."
                },
                {
                    "title": "Intellectual Property",
                    "description": "Work products created during your employment will be the property of the company as outlined in the Employee Agreement you will sign on your first day."
                },
            ],
            "closing_notes": """We can't wait to have you on board! Please review and sign this letter to confirm your acceptance.

Welcome to the team!

Best regards,
Engineering Leadership
{company}"""
        },
        {
            "template_name": "Sales Appointment Letter",
            "introduction": """Dear {applicant_name},

We are excited to offer you the position of {designation} at {company}!

Your sales experience and track record of success make you an excellent fit for our growing sales team. We look forward to your contributions in driving revenue growth.""",
            "terms": [
                {
                    "title": "Position",
                    "description": "You will join as {designation} reporting to the Head of Sales. Your territory and accounts will be assigned during your first week."
                },
                {
                    "title": "Compensation",
                    "description": "Your compensation includes a base salary plus uncapped commission. On-Target Earnings (OTE) is as discussed in your offer. Commission structure details will be provided during onboarding."
                },
                {
                    "title": "Quota and Performance",
                    "description": "You will be assigned a sales quota aligned with company revenue targets. Performance will be reviewed quarterly."
                },
                {
                    "title": "Tools and Resources",
                    "description": "You will have access to our CRM, sales enablement tools, and marketing resources to support your success."
                },
                {
                    "title": "Travel",
                    "description": "This role may require travel to meet with clients and attend industry events. Travel expenses will be reimbursed per company policy."
                },
            ],
            "closing_notes": """We believe you're going to crush it here! Please sign below to accept this offer.

Looking forward to closing deals together!

Best,
Sales Leadership
{company}"""
        },
    ]
    
    created_templates = []
    for template_data in templates_data:
        try:
            if frappe.db.exists("Appointment Letter Template", template_data["template_name"]):
                created_templates.append(template_data["template_name"])
                print(f"  ↻ Already exists: {template_data['template_name']}")
                continue
            
            template = frappe.get_doc({
                "doctype": "Appointment Letter Template",
                "template_name": template_data["template_name"],
                "introduction": template_data["introduction"],
                "closing_notes": template_data["closing_notes"],
                "terms": [
                    {"title": term["title"], "description": term["description"]}
                    for term in template_data["terms"]
                ]
            })
            template.insert(ignore_permissions=True)
            created_templates.append(template.name)
            print(f"  ✓ Created: {template_data['template_name']}")
        except Exception as e:
            print(f"  ⚠ Error creating template {template_data['template_name']}: {str(e)[:60]}")
    
    print(f"  ✓ Created/verified {len(created_templates)} appointment letter templates")
    return created_templates


# ============================================================================
# APPOINTMENT LETTERS
# ============================================================================

def create_appointment_letters(job_offers, company, appointment_templates):
    """Create appointment letters for accepted job offers"""
    
    # Only create appointment letters for accepted offers
    accepted_offers = [
        offer for offer in job_offers
        if offer.status == "Accepted"
    ]
    
    # Map designations to templates
    template_mapping = {
        "Backend Engineer": "Engineering Appointment Letter",
        "Senior Backend Engineer": "Engineering Appointment Letter",
        "Frontend Engineer": "Engineering Appointment Letter",
        "DevOps Engineer": "Engineering Appointment Letter",
        "Data Scientist": "Engineering Appointment Letter",
        "Account Executive": "Sales Appointment Letter",
        "SDR (Sales Development Representative)": "Sales Appointment Letter",
        "Growth Marketer": "Standard Employment Letter",
        "UX/UI Designer": "Engineering Appointment Letter",
        "Customer Success Manager": "Standard Employment Letter",
    }
    
    created_letters = []
    for i, offer in enumerate(accepted_offers):
        try:
            # Check if letter already exists
            if frappe.db.exists("Appointment Letter", {"job_applicant": offer.job_applicant}):
                print(f"  ↻ Letter already exists for: {offer.applicant_name}")
                continue
            
            # Get appropriate template
            template_name = template_mapping.get(offer.designation, "Standard Employment Letter")
            
            if template_name not in appointment_templates:
                template_name = appointment_templates[0] if appointment_templates else None
            
            if not template_name:
                print(f"  ⚠ No template found for: {offer.applicant_name}")
                continue
            
            # Get template details
            template = frappe.get_doc("Appointment Letter Template", template_name)
            
            # Create appointment letter
            appointment_letter = frappe.get_doc({
                "doctype": "Appointment Letter",
                "job_applicant": offer.job_applicant,
                "company": company,
                "appointment_date": add_days(getdate(), 14 + i),  # Start date 2+ weeks from now
                "appointment_letter_template": template_name,
                "introduction": template.introduction,
                "closing_notes": template.closing_notes,
                "terms": [
                    {"title": term.title, "description": term.description}
                    for term in template.terms
                ]
            })
            appointment_letter.flags.ignore_mandatory = True
            appointment_letter.insert(ignore_permissions=True)
            
            created_letters.append(appointment_letter)
            print(f"  ✓ Created letter for {offer.applicant_name}")
        except Exception as e:
            print(f"  ⚠ Error creating letter for {offer.applicant_name}: {str(e)[:60]}")
    
    print(f"  ✓ Created {len(created_letters)} appointment letters")
    return created_letters

def clear_recruitment_data(company="NovaSoft"):
    """
    Clear all recruitment demo data created by this script.
    USE WITH CAUTION - This will delete data!

    Usage:
        bench --site [sitename] execute hrms.demo_data.recruitment_setup.clear_recruitment_data
        Or with company:
        bench --site [sitename] execute hrms.demo_data.recruitment_setup.clear_recruitment_data --kwargs '{"company": "NovaSoft"}'
    """
    frappe.set_user("Administrator")

    print(f"\n{'='*60}")
    print(f"⚠️  Clearing Recruitment Data for Company: {company}")
    print(f"{'='*60}\n")

    # Delete in reverse dependency order (opposite of creation)
    doctypes_to_clear = [
        # Most dependent first
        ("Appointment Letter", {"company": company}),
        ("Job Offer", {"company": company}),
        ("Interview Feedback", {}),
        ("Interview", {}),  # No direct company field, linked through Job Applicant
        ("Job Applicant", {}),  # No direct company field, linked through Job Opening
        ("Employee Referral", {}),  # No direct company field
        ("Job Opening", {"company": company}),
        ("Job Requisition", {"company": company}),
        ("Staffing Plan", {"company": company}),
        # Master data (be careful with these)
        ("Job Offer Term Template", {}),
        ("Offer Term", {}),
        ("Appointment Letter Template", {}),
        ("Interview Round", {}),
        ("Job Applicant Source", {}),
        ("Interview Type", {}),
        # Skills might be used elsewhere, so skip or handle carefully
        # ("Skill", {}),
    ]

    total_deleted = 0
    # Disable foreign key constraints for deletion
    frappe.db.sql("SET FOREIGN_KEY_CHECKS=0")

    # Special handling for Job Offer - use raw SQL to avoid validation issues
    frappe.db.sql("SET FOREIGN_KEY_CHECKS=0")
    job_offers = frappe.db.sql(f"SELECT name FROM `tabJob Offer` WHERE company = %s", (company,), as_list=True)
    job_offer_deleted = 0
    for offer in job_offers:
        offer_name = offer[0]
        try:
            frappe.db.sql(f"DELETE FROM `tabJob Offer Term` WHERE parent = %s", (offer_name,))
            frappe.db.sql(f"DELETE FROM `tabJob Offer` WHERE name = %s", (offer_name,))
            job_offer_deleted += 1
        except:
            pass
    frappe.db.sql("SET FOREIGN_KEY_CHECKS=1")
    if job_offer_deleted > 0:
        print(f"  ✓ Deleted {job_offer_deleted} Job Offer records")
    total_deleted += job_offer_deleted

    # Process remaining doctypes
    for doctype, filters in doctypes_to_clear:
        # Skip Job Offer since we already handled it
        if doctype == "Job Offer":
            continue

        try:
            # Get meta to check if submittable
            meta = frappe.get_meta(doctype)

            # For doctypes without company field, use raw SQL to avoid filter issues
            if doctype in ["Interview", "Job Applicant", "Employee Referral"]:
                # Use raw SQL for these as they don't have company field
                frappe.db.sql("SET FOREIGN_KEY_CHECKS=0")
                doc_names = frappe.db.sql(f"SELECT name FROM `tab{doctype}`", as_list=True)
                doc_names = [row[0] for row in doc_names]
                frappe.db.sql("SET FOREIGN_KEY_CHECKS=1")
            else:
                # Get all documents matching filters
                docs = frappe.get_all(doctype, filters=filters, pluck="name")
                doc_names = docs

            deleted_count = 0
            for doc_name in doc_names:
                try:
                    # Check docstatus first without loading the full document
                    docstatus = frappe.db.get_value(doctype, doc_name, "docstatus")

                    # For cancelled documents, use direct SQL deletion
                    if meta.is_submittable and docstatus == 2:
                        frappe.db.sql(f"DELETE FROM `tab{doctype}` WHERE name = %s", (doc_name,))
                    else:
                        doc = frappe.get_doc(doctype, doc_name)
                        # Cancel if submitted
                        if meta.is_submittable and doc.docstatus == 1:
                            doc.cancel()
                        # Delete the document
                        frappe.delete_doc(doctype, doc_name, force=True)
                    deleted_count += 1

                except Exception as e:
                    print(f"  ⚠ Error deleting {doctype} {doc_name}: {str(e)[:100]}")

            if deleted_count > 0:
                print(f"  ✓ Deleted {deleted_count} {doctype} records")
                total_deleted += deleted_count
        except Exception as e:
            print(f"  ⚠ Error processing {doctype}: {str(e)[:100]}")

    # Re-enable foreign key constraints
    frappe.db.sql("SET FOREIGN_KEY_CHECKS=1")

    frappe.db.commit()

    print(f"\n{'='*60}")
    print(f"✅ Recruitment Data Deletion Complete!")
    print(f"{'='*60}")
    print(f"\n  Total records deleted: {total_deleted}")
    print(f"\n{'='*60}\n")
    return {"total_deleted": total_deleted}
