# File: dhf_dashboard/utils/session_state_manager.py

import streamlit as st
from datetime import date, timedelta

class SessionStateManager:
    """Manages session state with added structures for advanced analytics and compliance."""
    def __init__(self):
        # SME NOTE: This versioning is critical. Incrementing it forces a one-time
        # data refresh, clearing any old or corrupted data from the user's session.
        CURRENT_DATA_VERSION = 4

        if ('dhf_data' not in st.session_state or 
            st.session_state.dhf_data.get('data_version') != CURRENT_DATA_VERSION):
            
            st.toast(f"SME Fix: Initializing fresh mock data (v{CURRENT_DATA_VERSION})...")
            
            base_date = date(2025, 1, 15)

            st.session_state.dhf_data = {
                "data_version": CURRENT_DATA_VERSION,
                # The rest of the mock data structure remains the same as the last correct version
                "design_plan": {
                    "project_name": "Smart-Pill Drug Delivery System",
                    "scope": "This project covers the design and development of a new combination product, the 'Smart-Pill'...",
                    "team_members": [
                        {"id": "TM-01", "name": "Dr. Alice Weber", "role": "Project Lead"},
                        {"id": "TM-02", "name": "Bob Chen", "role": "Software Engineer"},
                    ],
                    "applicable_cgmp": "21 CFR Part 820",
                    "risk_management_plan_ref": "RMP-001",
                    "software_level_of_concern": "Moderate"
                },
                "risk_management_file": {
                    "hazards": [
                        {"id": "HAZ-001", "description": "Incorrect drug dosage delivered", "initial_risk": "High", "final_risk": "Low", "residual_risk_accepted": True},
                        {"id": "HAZ-002", "description": "Battery failure during use", "initial_risk": "Medium", "final_risk": "Low", "residual_risk_accepted": True},
                        {"id": "HAZ-003", "description": "Patient data transmission intercepted", "initial_risk": "High", "final_risk": "Low", "residual_risk_accepted": True},
                        {"id": "HAZ-004", "description": "Pill casing cracks", "initial_risk": "High", "final_risk": "Low", "residual_risk_accepted": False},
                    ],
                    "overall_risk_benefit_analysis": "Pending final verification."
                },
                "design_inputs": {"requirements": [{"id": "UN-01", "description": "Pill must be easy to swallow.", "source_type": "User Need"}, {"id": "SR-01", "description": "Pill shall be < 8mm diameter.", "source_type": "System Requirement"}]},
                "design_outputs": {"documents": [{"id": "DO-001", "title": "Pill Casing CAD", "type": "CAD File", "linked_input_id": "SR-01"}]},
                "design_reviews": {"reviews": [{"id": "DR-01", "date": base_date + timedelta(days=60), "action_items": [{"id": "AI-DR1-02", "owner": "B. Chen", "status": "In Progress"}, {"id": "AI-DR2-01", "owner": "D. Evans", "status": "Overdue"}]}]},
                "design_verification": {"tests": []}, "design_validation": {"studies": []}, "human_factors": {"use_scenarios": []}, "design_transfer": {"activities": []}, "design_changes": {"changes": []},
                "project_management": {
                    "tasks": [
                        {"id": "PLAN", "name": "1. Design Planning", "start_date": base_date, "end_date": base_date + timedelta(days=14), "status": "Completed", "completion_pct": 100, "dependencies": ""},
                        {"id": "RISK", "name": "2. Risk Management (ISO 14971)", "start_date": base_date + timedelta(days=7), "end_date": base_date + timedelta(days=30), "status": "Completed", "completion_pct": 100, "dependencies": "PLAN"},
                        {"id": "HF", "name": "3. Human Factors (IEC 62366)", "start_date": base_date + timedelta(days=20), "end_date": base_date + timedelta(days=50), "status": "In Progress", "completion_pct": 75, "dependencies": "PLAN"},
                        {"id": "INPUTS", "name": "4. Define Design Inputs", "start_date": base_date + timedelta(days=25), "end_date": base_date + timedelta(days=55), "status": "In Progress", "completion_pct": 90, "dependencies": "PLAN,RISK,HF"},
                        {"id": "OUTPUTS", "name": "5. Develop Design Outputs", "start_date": base_date + timedelta(days=56), "end_date": base_date + timedelta(days=120), "status": "At Risk", "completion_pct": 40, "dependencies": "INPUTS"},
                        {"id": "VERIFY", "name": "6. Design Verification", "start_date": base_date + timedelta(days=121), "end_date": base_date + timedelta(days=150), "status": "Not Started", "completion_pct": 0, "dependencies": "OUTPUTS"},
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
