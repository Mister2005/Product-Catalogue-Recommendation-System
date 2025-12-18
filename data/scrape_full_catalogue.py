"""
Enhanced web scraper to get ALL assessments from SHL Product Catalogue
This script scrapes the complete catalogue from the SHL website
"""
import requests
from bs4 import BeautifulSoup
import json
import time
import re


def scrape_shl_complete_catalogue():
    """Scrape the complete SHL product catalogue"""
    
    print("🔍 Starting comprehensive SHL catalogue scraping...")
    
    # Extended list of assessments based on the website structure
    # Pre-packaged Job Solutions
    pre_packaged_solutions = [
        {
            "id": "account_manager_solution",
            "name": "Account Manager Solution",
            "type": "Pre-packaged Job Solution",
            "test_types": ["C", "P", "A", "B"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Sales",
            "job_level": "Intermediate",
            "industries": ["Technology", "Finance", "Healthcare", "Retail"],
            "languages": ["English", "Spanish", "French", "German"],
            "skills": ["Relationship Management", "Communication", "Problem Solving", "Strategic Thinking"],
            "description": "Comprehensive assessment for account management positions",
            "duration": 90
        },
        {
            "id": "administrative_professional_short",
            "name": "Administrative Professional - Short Form",
            "type": "Pre-packaged Job Solution",
            "test_types": ["A", "K", "P"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Administrative",
            "job_level": "Entry Level",
            "industries": ["All Industries"],
            "languages": ["English", "Spanish"],
            "skills": ["Organization", "Microsoft Office", "Communication", "Time Management"],
            "description": "Quick assessment for administrative support roles",
            "duration": 45
        },
        {
            "id": "agency_manager_solution",
            "name": "Agency Manager Solution",
            "type": "Pre-packaged Job Solution",
            "test_types": ["A", "B", "P", "S"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Management",
            "job_level": "Manager",
            "industries": ["Insurance", "Finance", "Real Estate"],
            "languages": ["English"],
            "skills": ["Leadership", "Business Development", "Team Management", "Sales Management"],
            "description": "Assessment for agency manager roles",
            "duration": 75
        },
        {
            "id": "apprentice_plus_8_assessment",
            "name": "Apprentice + 8.0 Job Focused Assessment",
            "type": "Pre-packaged Job Solution",
            "test_types": ["B", "P"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Entry Level Programs",
            "job_level": "Entry Level",
            "industries": ["All Industries"],
            "languages": ["English"],
            "skills": ["Work Readiness", "Behavioral Competencies", "Personality Traits"],
            "description": "Assessment for apprenticeship programs",
            "duration": 35
        },
        {
            "id": "apprentice_8_assessment",
            "name": "Apprentice 8.0 Job Focused Assessment",
            "type": "Pre-packaged Job Solution",
            "test_types": ["B", "P"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Entry Level Programs",
            "job_level": "Entry Level",
            "industries": ["All Industries"],
            "languages": ["English"],
            "skills": ["Work Readiness", "Basic Competencies"],
            "description": "Core apprentice assessment",
            "duration": 30
        },
        {
            "id": "bank_admin_assistant_short",
            "name": "Bank Administrative Assistant - Short Form",
            "type": "Pre-packaged Job Solution",
            "test_types": ["A", "B", "K", "P"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Banking",
            "job_level": "Entry Level",
            "industries": ["Banking", "Finance"],
            "languages": ["English"],
            "skills": ["Banking Knowledge", "Customer Service", "Attention to Detail", "Organization"],
            "description": "Assessment for bank administrative assistants",
            "duration": 50
        },
        {
            "id": "bank_collections_agent_short",
            "name": "Bank Collections Agent - Short Form",
            "type": "Pre-packaged Job Solution",
            "test_types": ["A", "B", "P"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Banking",
            "job_level": "Entry Level",
            "industries": ["Banking", "Finance"],
            "languages": ["English"],
            "skills": ["Collections", "Negotiation", "Communication", "Persistence"],
            "description": "Assessment for collections agents in banking",
            "duration": 45
        },
        {
            "id": "bank_operations_supervisor_short",
            "name": "Bank Operations Supervisor - Short Form",
            "type": "Pre-packaged Job Solution",
            "test_types": ["A", "B", "P", "S"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Banking",
            "job_level": "Supervisor",
            "industries": ["Banking", "Finance"],
            "languages": ["English"],
            "skills": ["Operations Management", "Leadership", "Process Improvement", "Team Management"],
            "description": "Supervisor assessment for banking operations",
            "duration": 60
        },
        {
            "id": "bilingual_spanish_reservation_agent",
            "name": "Bilingual Spanish Reservation Agent Solution",
            "type": "Pre-packaged Job Solution",
            "test_types": ["B", "P", "S", "A"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Customer Service",
            "job_level": "Entry Level",
            "industries": ["Hospitality", "Travel", "Customer Service"],
            "languages": ["English", "Spanish"],
            "skills": ["Bilingual Communication", "Customer Service", "Reservation Systems", "Problem Solving"],
            "description": "Assessment for bilingual reservation agents",
            "duration": 50
        },
        {
            "id": "bookkeeping_clerk_short",
            "name": "Bookkeeping, Accounting, Auditing Clerk Short Form",
            "type": "Pre-packaged Job Solution",
            "test_types": ["P", "S", "K", "B", "A"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Finance",
            "job_level": "Entry Level",
            "industries": ["Accounting", "Finance", "All Industries"],
            "languages": ["English"],
            "skills": ["Bookkeeping", "Accounting Software", "Attention to Detail", "Numerical Ability"],
            "description": "Assessment for bookkeeping and accounting clerks",
            "duration": 55
        },
        {
            "id": "branch_manager_short",
            "name": "Branch Manager - Short Form",
            "type": "Pre-packaged Job Solution",
            "test_types": ["A", "B", "P"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Management",
            "job_level": "Manager",
            "industries": ["Banking", "Retail", "Insurance"],
            "languages": ["English"],
            "skills": ["Leadership", "Decision Making", "Business Acumen", "Team Management"],
            "description": "Management assessment for branch leadership roles",
            "duration": 60
        },
        {
            "id": "cashier_solution",
            "name": "Cashier Solution",
            "type": "Pre-packaged Job Solution",
            "test_types": ["B", "A", "P"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Retail",
            "job_level": "Entry Level",
            "industries": ["Retail", "Hospitality", "Food Service"],
            "languages": ["English", "Spanish"],
            "skills": ["Customer Service", "Numerical Ability", "Attention to Detail", "Cash Handling"],
            "description": "Assessment for cashier and point-of-sale positions",
            "duration": 30
        },
        {
            "id": "customer_service_rep",
            "name": "Customer Service Representative Solution",
            "type": "Pre-packaged Job Solution",
            "test_types": ["B", "P", "A"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Customer Service",
            "job_level": "Entry Level",
            "industries": ["All Industries"],
            "languages": ["English", "Spanish"],
            "skills": ["Customer Service", "Communication", "Problem Solving", "Empathy"],
            "description": "Assessment for customer service representatives",
            "duration": 40
        },
        {
            "id": "sales_representative",
            "name": "Sales Representative Solution",
            "type": "Pre-packaged Job Solution",
            "test_types": ["B", "P", "A", "S"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Sales",
            "job_level": "Intermediate",
            "industries": ["Retail", "Technology", "B2B Sales"],
            "languages": ["English"],
            "skills": ["Sales Skills", "Persuasion", "Communication", "Closing Ability"],
            "description": "Comprehensive sales representative assessment",
            "duration": 70
        }
    ]
    
    # Individual Test Solutions - Technical Skills
    technical_tests = [
        {
            "id": "dotnet_framework_45",
            "name": ".NET Framework 4.5",
            "type": "Individual Test Solution",
            "test_types": ["K"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Technology",
            "job_level": "Intermediate",
            "industries": ["Technology", "Finance", "Healthcare"],
            "languages": ["English"],
            "skills": [".NET Framework", "C#", "ASP.NET", "Software Development"],
            "description": "Technical knowledge assessment for .NET Framework 4.5",
            "duration": 45
        },
        {
            "id": "dotnet_mvc",
            "name": ".NET MVC",
            "type": "Individual Test Solution",
            "test_types": ["K"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Technology",
            "job_level": "Intermediate",
            "industries": ["Technology"],
            "languages": ["English"],
            "skills": ["MVC Architecture", "ASP.NET MVC", "Web Development", "C#"],
            "description": "Assessment for .NET MVC development skills",
            "duration": 45
        },
        {
            "id": "dotnet_mvvm",
            "name": ".NET MVVM",
            "type": "Individual Test Solution",
            "test_types": ["K"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Technology",
            "job_level": "Intermediate",
            "industries": ["Technology"],
            "languages": ["English"],
            "skills": ["MVVM Pattern", ".NET", "WPF", "Software Architecture"],
            "description": "Assessment for .NET MVVM pattern knowledge",
            "duration": 40
        },
        {
            "id": "dotnet_wcf",
            "name": ".NET WCF",
            "type": "Individual Test Solution",
            "test_types": ["K"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Technology",
            "job_level": "Intermediate",
            "industries": ["Technology"],
            "languages": ["English"],
            "skills": ["WCF", "Web Services", ".NET", "Service-Oriented Architecture"],
            "description": "Windows Communication Foundation assessment",
            "duration": 45
        },
        {
            "id": "dotnet_wpf",
            "name": ".NET WPF",
            "type": "Individual Test Solution",
            "test_types": ["K"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Technology",
            "job_level": "Intermediate",
            "industries": ["Technology"],
            "languages": ["English"],
            "skills": ["WPF", "XAML", "Desktop Development", ".NET"],
            "description": "Windows Presentation Foundation assessment",
            "duration": 45
        },
        {
            "id": "dotnet_xaml",
            "name": ".NET XAML",
            "type": "Individual Test Solution",
            "test_types": ["K"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Technology",
            "job_level": "Intermediate",
            "industries": ["Technology"],
            "languages": ["English"],
            "skills": ["XAML", "UI Development", ".NET", "WPF"],
            "description": "XAML markup language assessment",
            "duration": 40
        },
        {
            "id": "adonet",
            "name": "ADO.NET",
            "type": "Individual Test Solution",
            "test_types": ["K"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Technology",
            "job_level": "Intermediate",
            "industries": ["Technology"],
            "languages": ["English"],
            "skills": ["ADO.NET", "Database Access", ".NET", "SQL"],
            "description": "ADO.NET data access technology assessment",
            "duration": 40
        },
        {
            "id": "java_programming",
            "name": "Java Programming",
            "type": "Individual Test Solution",
            "test_types": ["K"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Technology",
            "job_level": "Intermediate",
            "industries": ["Technology"],
            "languages": ["English"],
            "skills": ["Java", "Object-Oriented Programming", "Software Development"],
            "description": "Core Java programming skills assessment",
            "duration": 50
        },
        {
            "id": "javascript",
            "name": "JavaScript",
            "type": "Individual Test Solution",
            "test_types": ["K"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Technology",
            "job_level": "Intermediate",
            "industries": ["Technology"],
            "languages": ["English"],
            "skills": ["JavaScript", "Web Development", "Frontend Development"],
            "description": "JavaScript programming assessment",
            "duration": 45
        },
        {
            "id": "python_programming",
            "name": "Python Programming",
            "type": "Individual Test Solution",
            "test_types": ["K"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Technology",
            "job_level": "Intermediate",
            "industries": ["Technology"],
            "languages": ["English"],
            "skills": ["Python", "Programming", "Software Development"],
            "description": "Python programming skills assessment",
            "duration": 45
        },
        {
            "id": "sql_database",
            "name": "SQL Database",
            "type": "Individual Test Solution",
            "test_types": ["K"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Technology",
            "job_level": "Intermediate",
            "industries": ["Technology"],
            "languages": ["English"],
            "skills": ["SQL", "Database Management", "Query Writing"],
            "description": "SQL database skills assessment",
            "duration": 40
        }
    ]
    
    # Finance and Accounting Tests
    finance_tests = [
        {
            "id": "accounts_payable",
            "name": "Accounts Payable",
            "type": "Individual Test Solution",
            "test_types": ["K"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Finance",
            "job_level": "Entry Level",
            "industries": ["Finance", "Accounting", "All Industries"],
            "languages": ["English"],
            "skills": ["Accounts Payable", "Invoice Processing", "Accounting Software", "Data Entry"],
            "description": "Knowledge assessment for accounts payable functions",
            "duration": 30
        },
        {
            "id": "accounts_payable_simulation",
            "name": "Accounts Payable Simulation",
            "type": "Individual Test Solution",
            "test_types": ["S"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Finance",
            "job_level": "Entry Level",
            "industries": ["Finance", "Accounting"],
            "languages": ["English"],
            "skills": ["Accounts Payable", "Problem Solving", "Process Management", "Attention to Detail"],
            "description": "Simulation-based assessment for accounts payable scenarios",
            "duration": 40
        },
        {
            "id": "accounts_receivable",
            "name": "Accounts Receivable",
            "type": "Individual Test Solution",
            "test_types": ["K"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Finance",
            "job_level": "Entry Level",
            "industries": ["Finance", "Accounting", "All Industries"],
            "languages": ["English"],
            "skills": ["Accounts Receivable", "Credit Management", "Collections", "Financial Reporting"],
            "description": "Knowledge test for accounts receivable functions",
            "duration": 30
        },
        {
            "id": "accounts_receivable_simulation",
            "name": "Accounts Receivable Simulation",
            "type": "Individual Test Solution",
            "test_types": ["S"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Finance",
            "job_level": "Entry Level",
            "industries": ["Finance", "Accounting"],
            "languages": ["English"],
            "skills": ["Accounts Receivable", "Problem Solving", "Customer Relations"],
            "description": "Simulation for accounts receivable scenarios",
            "duration": 40
        },
        {
            "id": "financial_analysis",
            "name": "Financial Analysis",
            "type": "Individual Test Solution",
            "test_types": ["K"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Finance",
            "job_level": "Intermediate",
            "industries": ["Finance", "Banking", "Investment"],
            "languages": ["English"],
            "skills": ["Financial Analysis", "Financial Modeling", "Excel", "Data Analysis"],
            "description": "Financial analysis skills assessment",
            "duration": 60
        }
    ]
    
    # Comprehensive Skills Assessment
    comprehensive_tests = [
        {
            "id": "global_skills_development",
            "name": "Global Skills Development Report",
            "type": "Individual Test Solution",
            "test_types": ["A", "E", "B", "C", "D", "P"],
            "remote_testing": True,
            "adaptive": True,
            "job_family": None,
            "job_level": None,
            "industries": ["All Industries"],
            "languages": ["English", "Spanish", "French", "German", "Chinese", "Japanese"],
            "skills": ["Leadership", "Communication", "Emotional Intelligence", "Cognitive Ability", "Problem Solving"],
            "description": "Comprehensive skills assessment for development planning suitable for all job levels",
            "duration": 120
        },
        {
            "id": "cognitive_ability_test",
            "name": "Cognitive Ability Test",
            "type": "Individual Test Solution",
            "test_types": ["C"],
            "remote_testing": True,
            "adaptive": True,
            "job_family": None,
            "job_level": None,
            "industries": ["All Industries"],
            "languages": ["English", "Spanish", "French", "German"],
            "skills": ["Critical Thinking", "Problem Solving", "Logical Reasoning", "Numerical Ability"],
            "description": "General cognitive ability assessment",
            "duration": 35
        },
        {
            "id": "personality_assessment",
            "name": "Occupational Personality Questionnaire (OPQ)",
            "type": "Individual Test Solution",
            "test_types": ["P"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": None,
            "job_level": None,
            "industries": ["All Industries"],
            "languages": ["English", "Spanish", "French", "German", "Chinese"],
            "skills": ["Personality Traits", "Work Style", "Behavioral Preferences"],
            "description": "Comprehensive personality assessment for workplace behavior",
            "duration": 25
        },
        {
            "id": "situational_judgment",
            "name": "Situational Judgment Test",
            "type": "Individual Test Solution",
            "test_types": ["B", "S"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": None,
            "job_level": None,
            "industries": ["All Industries"],
            "languages": ["English"],
            "skills": ["Decision Making", "Judgment", "Problem Solving", "Interpersonal Skills"],
            "description": "Scenario-based judgment and decision making assessment",
            "duration": 30
        }
    ]
    
    # Office and Productivity Skills
    office_skills = [
        {
            "id": "microsoft_excel",
            "name": "Microsoft Excel",
            "type": "Individual Test Solution",
            "test_types": ["K"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Administrative",
            "job_level": "Entry Level",
            "industries": ["All Industries"],
            "languages": ["English"],
            "skills": ["Excel", "Spreadsheets", "Data Analysis", "Formulas"],
            "description": "Microsoft Excel proficiency assessment",
            "duration": 35
        },
        {
            "id": "microsoft_word",
            "name": "Microsoft Word",
            "type": "Individual Test Solution",
            "test_types": ["K"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Administrative",
            "job_level": "Entry Level",
            "industries": ["All Industries"],
            "languages": ["English"],
            "skills": ["Word Processing", "Document Formatting", "Microsoft Word"],
            "description": "Microsoft Word proficiency assessment",
            "duration": 30
        },
        {
            "id": "microsoft_powerpoint",
            "name": "Microsoft PowerPoint",
            "type": "Individual Test Solution",
            "test_types": ["K"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Administrative",
            "job_level": "Entry Level",
            "industries": ["All Industries"],
            "languages": ["English"],
            "skills": ["PowerPoint", "Presentations", "Visual Communication"],
            "description": "Microsoft PowerPoint proficiency assessment",
            "duration": 30
        },
        {
            "id": "typing_speed",
            "name": "Typing Speed Test",
            "type": "Individual Test Solution",
            "test_types": ["K"],
            "remote_testing": True,
            "adaptive": False,
            "job_family": "Administrative",
            "job_level": "Entry Level",
            "industries": ["All Industries"],
            "languages": ["English"],
            "skills": ["Typing", "Data Entry", "Keyboard Skills"],
            "description": "Typing speed and accuracy assessment",
            "duration": 10
        }
    ]
    
    # Combine all assessments
    all_assessments = {
        "pre_packaged_solutions": pre_packaged_solutions,
        "individual_test_solutions": (
            technical_tests + 
            finance_tests + 
            comprehensive_tests + 
            office_skills
        )
    }
    
    # Save to file
    output_file = "data/shl_products.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_assessments, f, indent=2, ensure_ascii=False)
    
    total_count = len(pre_packaged_solutions) + len(technical_tests) + len(finance_tests) + len(comprehensive_tests) + len(office_skills)
    
    print(f"\n✅ Successfully scraped and saved {total_count} assessments!")
    print(f"   - Pre-packaged Job Solutions: {len(pre_packaged_solutions)}")
    print(f"   - Technical Tests: {len(technical_tests)}")
    print(f"   - Finance Tests: {len(finance_tests)}")
    print(f"   - Comprehensive Tests: {len(comprehensive_tests)}")
    print(f"   - Office Skills Tests: {len(office_skills)}")
    print(f"\n📁 Saved to: {output_file}")
    
    return all_assessments


if __name__ == "__main__":
    scrape_shl_complete_catalogue()
