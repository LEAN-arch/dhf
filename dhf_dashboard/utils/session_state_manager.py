# File: dhf_dashboard/utils/session_state_manager.py

import streamlit as st
from datetime import date, timedelta

class SessionStateManager:
    """Manages session state with added structures for advanced analytics and compliance."""
    def __init__(self):
        if 'dhf_data' not in st.session_state:
            st.session_state.dhf_data = {
                "design_plan": {
                    "project_name": "Smart-Pill Drug Delivery System",
                    "scope": "", "team_members": [], "applicable_cgmp": "21 CFR Part 210/211",
                    "risk_management_plan_ref": "",
                    "software_level_of_concern": "Moderate" # NEW: For IEC 62304
                },
                "risk_management_file": {
                    "hazards": [],
                    # NEW: Formal conclusion for the Risk Management Report
                    "overall_risk_benefit_analysis": "Analysis pending completion of verification and validation activities."
                },
                "design_inputs": {"requirements": []},
                "design_outputs": {"documents": []},
                "design_reviews": {
                    # MODIFIED: Action items are now a structured list
                    "reviews": [] # dict: {date, attendees, notes, action_items: [{id, desc, owner, due, status}]}
                },
                "design_verification": {"tests": []},
                "design_validation": {"studies": []},
                # --- NEW SECTION for IEC 62366 ---
                "human_factors": {
                    "use_scenarios": [] # List of dicts for Use-Related Risk Analysis
                },
                "design_transfer": {"activities": []},
                "design_changes": {"changes": []},
                "project_management": {
                    # ... (task structure remains the same) ...
                    "tasks": [
                        {"id": "PLAN", "name": "1. Design Planning", "start_date": date.today(), "end_date": date.today() + timedelta(days=14), "status": "In Progress", "completion_pct": 10, "dependencies": ""},
                        {"id": "RISK", "name": "2. Risk Management (ISO 14971)", "start_date": date.today() + timedelta(days=7), "end_date": date.today() + timedelta(days=30), "status": "Not Started", "completion_pct": 0, "dependencies": "PLAN"},
                        {"id": "HF", "name": "3. Human Factors (IEC 62366)", "start_date": date.today() + timedelta(days=20), "end_date": date.today() + timedelta(days=50), "status": "Not Started", "completion_pct": 0, "dependencies": "PLAN"},
                        {"id": "INPUTS", "name": "4. Define Design Inputs", "start_date": date.today() + timedelta(days=25), "end_date": date.today() + timedelta(days=55), "status": "Not Started", "completion_pct": 0, "dependencies": "PLAN,RISK,HF"},
                        {"id": "OUTPUTS", "name": "5. Develop Design Outputs", "start_date": date.today() + timedelta(days=56), "end_date": date.today() + timedelta(days=90), "status": "Not Started", "completion_pct": 0, "dependencies": "INPUTS"},
                        {"id": "VERIFY", "name": "6. Design Verification", "start_date": date.today() + timedelta(days=91), "end_date": date.today() + timedelta(days=120), "status": "Not Started", "completion_pct": 0, "dependencies": "OUTPUTS"},
                        {"id": "VALIDATE", "name": "7. Design Validation", "start_date": date.today() + timedelta(days=121), "end_date": date.today() + timedelta(days=150), "status": "Not Started", "completion_pct": 0, "dependencies": "VERIFY"},
                        {"id": "TRANSFER", "name": "8. Design Transfer", "start_date": date.today() + timedelta(days=151), "end_date": date.today() + timedelta(days=180), "status": "Not Started", "completion_pct": 0, "dependencies": "VALIDATE"},
                    ]
                }
            }

    def get_data(self, primary_key, secondary_key=None):
        # ... (no changes to getter/setter) ...
        if secondary_key:
            return st.session_state.dhf_data.get(primary_key, {}).get(secondary_key, [])
        return st.session_state.dhf_data.get(primary_key, {})

    def update_data(self, data, primary_key, secondary_key=None):
        if secondary_key:
            st.session_state.dhf_data[primary_key][secondary_key] = data
        else:
            st.session_state.dhf_data[primary_key] = data
