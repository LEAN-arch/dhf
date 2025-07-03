# File: dhf_dashboard/utils/session_state_manager.py

import streamlit as st

class SessionStateManager:
    """
    Manages the session state for the Combination Product DHF Dashboard.

    This class initializes and maintains the data structures necessary for documenting
    a DHF compliant with 21 CFR 820.30, 21 CFR Part 4, and integrating
    risk management principles from ISO 14971.
    """
    def __init__(self):
        """
        Initializes st.session_state with a detailed structure for a combination product DHF.
        """
        if 'dhf_data' not in st.session_state:
            st.session_state.dhf_data = {
                "design_plan": {
                    "project_name": "Smart-Pill Drug Delivery System",
                    "scope": "",
                    "team_members": [],
                    "applicable_cgmp": "21 CFR Part 210/211", # Explicitly reference drug cGMPs
                    "risk_management_plan_ref": ""
                },
                "risk_management_file": { # NEW SECTION for ISO 14971
                    "hazards": [] # List of dicts for the hazard analysis
                },
                "design_inputs": {
                    "requirements": [] # List of dicts with added risk & combo product fields
                },
                "design_outputs": {
                    "documents": [] # List of dicts
                },
                "design_reviews": {
                    "reviews": [] # List of dicts
                },
                "design_verification": {
                    "tests": [] # List of dicts with added risk control verification field
                },
                "design_validation": {
                    "studies": [] # List of dicts with added risk control validation field
                },
                "design_transfer": {
                    "activities": []
                },
                "design_changes": {
                    "changes": []
                },
            }

    def get_section_data(self, section_name):
        """Retrieves the data for a specific DHF section."""
        return st.session_state.dhf_data.get(section_name, {})

    def update_section_data(self, section_name, data):
        """Updates the data for a specific DHF section."""
        st.session_state.dhf_data[section_name] = data
