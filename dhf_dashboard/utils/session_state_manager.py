# File: dhf_dashboard/utils/session_state_manager.py

import streamlit as st
from datetime import date, timedelta

class SessionStateManager:
    """Manages session state with added structures for advanced analytics and compliance."""
    def __init__(self):
        # SME Note: Versioning the data ensures that when we update the mock data structure,
        # the app automatically reloads it, preventing bugs from stale session state.
        CURRENT_DATA_VERSION = 3 # Incremented to force a refresh of stale data

        if ('dhf_data' not in st.session_state or 
            st.session_state.dhf_data.get('data_version') != CURRENT_DATA_VERSION):
            
            st.toast(f"Initializing fresh mock data (v{CURRENT_DATA_VERSION})...")
            
            # Base date set to 2025 as requested
            base_date = date(2025, 1, 15)

            st.session_state.dhf_data = {
                "data_version": CURRENT_DATA_VERSION,
                "design_plan": {
                    "project_name": "Smart-Pill Drug Delivery System",
                    "scope": "This project covers the design and development of a new combination product, the 'Smart-Pill', which integrates an electronic sensor with a drug delivery mechanism. The scope includes the pill itself, the associated firmware, and the user interface for patient monitoring.",
                    "team_members": [
                        {"id": "TM-01", "name": "Dr. Alice Weber", "role": "Project Lead"},
                        {"id": "TM-02", "name": "Bob Chen", "role": "Software Engineer"},
                        {"id": "TM-03", "name": "Carol Davis", "role": "QA/RA Specialist"},
                        {"id": "TM-04", "name": "David Evans", "role": "Human Factors Engineer"},
                    ],
                    "applicable_cgmp": "21 CFR Part 210/211, 21 CFR Part 820",
                    "risk_management_plan_ref": "RMP-001",
                    "software_level_of_concern": "Moderate"
                },
                "risk_management_file": {
                    "hazards": [
                        {"id": "HAZ-001", "description": "Incorrect drug dosage delivered", "cause": "Firmware calculation error", "initial_severity": 5, "initial_probability": 3, "initial_risk": "High", "mitigation": "Implement redundant calculation checks; rigorous unit testing (VER-002).", "final_severity": 5, "final_probability": 1, "final_risk": "Low", "residual_risk_accepted": True},
                        {"id": "HAZ-002", "description": "Battery failure during use", "cause": "Component end-of-life", "initial_severity": 4, "initial_probability": 2, "initial_risk": "Medium", "mitigation": "Use medical-grade battery with known lifecycle; software low-battery warning.", "final_severity": 4, "final_probability": 1, "final_risk": "Low", "residual_risk_accepted": True},
                        {"id": "HAZ-003", "description": "Patient data transmission intercepted (Cybersecurity)", "cause": "Unencrypted data channel", "initial_severity": 3, "initial_probability": 4, "initial_risk": "High", "mitigation": "Implement AES-256 encryption for all data transmissions.", "final_severity": 3, "final_probability": 1, "final_risk": "Low", "residual_risk_accepted": True},
                        {"id": "HAZ-004", "description": "Pill casing cracks during swallowing", "cause": "Material stress failure", "initial_severity": 4, "initial_probability": 3, "initial_risk": "High", "mitigation": "Change material to medical-grade polymer X.", "final_severity": 2, "final_probability": 1, "final_risk": "Low", "residual_risk_accepted": False},
                    ],
                    "overall_risk_benefit_analysis": "Initial analysis shows a positive risk-benefit profile. The identified high-risk hazards have feasible mitigations that significantly reduce the overall risk. This analysis will be finalized upon completion of all verification and validation activities."
                },
                "design_inputs": {
                    "requirements": [
                        {"id": "UN-01", "description": "The patient must be able to swallow the pill easily.", "source_type": "User Need", "source_ref": "Focus Group A"},
                        {"id": "UN-02", "description": "The system must reliably deliver the prescribed 10mg dose of Drug-X.", "source_type": "User Need", "source_ref": "Clinical Protocol"},
                        {"id": "SR-01", "description": "The pill dimensions shall not exceed 8mm in diameter and 20mm in length.", "source_type": "System Requirement", "source_ref": "UN-01"},
                        {"id": "SR-02", "description": "The pill shall use Bluetooth Low Energy (BLE) for communication.", "source_type": "System Requirement", "source_ref": "Technical Specification"},
                        {"id": "REG-01", "description": "Patient data must be handled in compliance with HIPAA.", "source_type": "Regulatory Requirement", "source_ref": "21 CFR 820"},
                    ]
                },
                "design_outputs": {
                    "documents": [
                        {"id": "DO-001", "title": "Pill Casing Mechanical Drawing", "type": "CAD File", "linked_input_id": "SR-01"},
                        {"id": "DO-002", "title": "Firmware Module - Dose Calculation", "type": "Source Code", "linked_input_id": "UN-02"},
                        {"id": "DO-003", "title": "BLE Communication Protocol Specification", "type": "Specification", "linked_input_id": "SR-02"},
                    ]
                },
                "design_reviews": {
                    "reviews": [
                        { "id": "DR-01", "date": base_date + timedelta(days=60), "attendees": "A. Weber, B. Chen, C. Davis", "notes": "Concept review completed. Feasibility approved. Key risks identified.",
                            "action_items": [
                                {"id": "AI-DR1-01", "description": "Finalize battery selection", "owner": "A. Weber", "due_date": base_date + timedelta(days=75), "status": "Completed"},
                                {"id": "AI-DR1-02", "description": "Draft initial software architecture", "owner": "B. Chen", "due_date": base_date + timedelta(days=90), "status": "In Progress"},
                                {"id": "AI-DR1-03", "description": "Source alternative polymer for casing", "owner": "A. Weber", "due_date": base_date + timedelta(days=90), "status": "In Progress"},
                            ]
                        },
                        { "id": "DR-02", "date": base_date + timedelta(days=120), "attendees": "A. Weber, B. Chen, C. Davis, D. Evans", "notes": "Design review for first prototype. Casing dimensions are acceptable. Firmware needs further testing.",
                            "action_items": [
                                {"id": "AI-DR2-01", "description": "Investigate alternative casing material", "owner": "D. Evans", "due_date": date(2025, 3, 1), "status": "Overdue"},
                            ]
                        }
                    ]
                },
                "design_verification": {
                    "tests": [
                        {"id": "VER-001", "description": "Dimensional analysis of 100 pill casings", "output_verified": "DO-001", "result": "Passed"},
                        {"id": "VER-002", "description": "Unit test for dose calculation algorithm (1000 iterations)", "output_verified": "DO-002", "result": "Passed"},
                    ]
                },
                "design_validation": {
                    "studies": [
                        {"id": "VAL-001", "description": "Usability study with 20 representative users", "user_need_validated": "UN-01", "result": "Passed"},
                    ]
                },
                "human_factors": { "use_scenarios": [] },
                "design_transfer": { "activities": [] },
                "design_changes": { "changes": [] },
                "project_management": {
                    "tasks": [
                        {"id": "PLAN", "name": "1. Design Planning", "start_date": base_date, "end_date": base_date + timedelta(days=14), "status": "Completed", "completion_pct": 100, "dependencies": ""},
                        {"id": "RISK", "name": "2. Risk Management (ISO 14971)", "start_date": base_date + timedelta(days=7), "end_date": base_date + timedelta(days=30), "status": "Completed", "completion_pct": 100, "dependencies": "PLAN"},
                        {"id": "HF", "name": "3. Human Factors (IEC 62366)", "start_date": base_date + timedelta(days=20), "end_date": base_date + timedelta(days=50), "status": "In Progress", "completion_pct": 75, "dependencies": "PLAN"},
                        {"id": "INPUTS", "name": "4. Define Design Inputs", "start_date": base_date + timedelta(days=25), "end_date": base_date + timedelta(days=55), "status": "In Progress", "completion_pct": 90, "dependencies": "PLAN,RISK,HF"},
                        {"id": "OUTPUTS", "name": "5. Develop Design Outputs", "start_date": base_date + timedelta(days=56), "end_date": base_date + timedelta(days=120), "status": "At Risk", "completion_pct": 40, "dependencies": "INPUTS"},
                        {"id": "VERIFY", "name": "6. Design Verification", "start_date": base_date + timedelta(days=121), "end_date": base_date + timedelta(days=150), "status": "Not Started", "completion_pct": 0, "dependencies": "OUTPUTS"},
                        {"id": "VALIDATE", "name": "7. Design Validation", "start_date": base_date + timedelta(days=151), "end_date": base_date + timedelta(days=180), "status": "Not Started", "completion_pct": 0, "dependencies": "VERIFY"},
                        {"id": "TRANSFER", "name": "8. Design Transfer", "start_date": base_date + timedelta(days=181), "end_date": base_date + timedelta(days=200), "status": "Not Started", "completion_pct": 0, "dependencies": "VALIDATE"},
                    ]
                }
            }

    def get_data(self, primary_key, secondary_key=None):
        if secondary_key:
            return st.session_state.dhf_data.get(primary_key, {}).get(secondary_key, [])
        return st.session_state.dhf_data.get(primary_key, {})

    def update_data(self, data, primary_key, secondary_key=None):
        if secondary_key:
            st.session_state.dhf_data[primary_key][secondary_key] = data
        else:
            st.session_state.dhf_data[primary_key] = data
