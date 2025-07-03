# File: dhf_dashboard/utils/session_state_manager.py
# SME Note: This version provides the definitive fix for all KeyError issues by ensuring
# the mock data model contains all keys required by the application's analytics,
# specifically restoring 'output_verified' to the design_verification tests.

import streamlit as st
from datetime import date, timedelta

class SessionStateManager:
    """
    Manages session state with a robust, interconnected mock dataset designed for a
    professional-grade Design Assurance dashboard.
    """
    def __init__(self):
        # Incrementing the version to 8 to guarantee a fresh data load for all users.
        CURRENT_DATA_VERSION = 8

        if ('dhf_data' not in st.session_state or
            st.session_state.dhf_data.get('data_version') != CURRENT_DATA_VERSION):

            st.toast(f"Data Model Fix: Initializing definitive mock data (v{CURRENT_DATA_VERSION})...")

            base_date = date(2024, 1, 15)

            st.session_state.dhf_data = {
                "data_version": CURRENT_DATA_VERSION,
                "design_plan": {
                    "project_name": "Smart-Pill Drug Delivery System (SP-DDS)",
                    "scope": "This project covers the design and development of a new combination product, the 'Smart-Pill', intended for the targeted oral delivery of drug XYZ for treating chronic condition ABC. The system comprises a swallowable electronic capsule (device) containing a payload of drug XYZ (drug).",
                    "team_members": [
                        {"role": "Project Lead", "name": "Dr. Alice Weber", "responsibility": "Overall project oversight."},
                        {"role": "Device Engineer", "name": "Bob Chen", "responsibility": "Hardware design, material selection."},
                        {"role": "Software Engineer", "name": "Charlie Day", "responsibility": "Embedded software, mobile app."},
                        {"role": "Pharma Scientist", "name": "Diana Evans", "responsibility": "Drug formulation, stability."},
                        {"role": "Quality Engineer", "name": "Frank Green", "responsibility": "DHF owner, V&V strategy, Risk Mgmt."}
                    ],
                },
                "risk_management_file": {
                    "hazards": [
                        {"hazard_id": "H-001", "description": "Incorrect drug dosage delivered (overdose)", "initial_S": 5, "initial_O": 3, "initial_D": 4, "final_S": 5, "final_O": 1, "final_D": 2},
                        {"hazard_id": "H-002", "description": "Biocompatibility failure (material leaching)", "initial_S": 5, "initial_O": 2, "initial_D": 3, "final_S": 5, "final_O": 1, "final_D": 1},
                        {"hazard_id": "H-003", "description": "Battery failure during use (no therapy)", "initial_S": 4, "initial_O": 2, "initial_D": 5, "final_S": 2, "final_O": 1, "final_D": 2},
                        {"hazard_id": "H-004", "description": "Loss of data integrity (cybersecurity breach)", "initial_S": 3, "initial_O": 3, "initial_D": 2, "final_S": 3, "final_O": 1, "final_D": 1},
                        {"hazard_id": "H-005", "description": "Pill casing cracks (choking hazard)", "initial_S": 5, "initial_O": 1, "initial_D": 2, "final_S": 5, "final_O": 1, "final_D": 1},
                    ],
                    "historical_rpn": [
                        {"date": "2024-02-01", "total_rpn": 350},
                        {"date": "2024-04-01", "total_rpn": 210},
                        {"date": "2024-06-01", "total_rpn": 95},
                    ]
                },
                "design_inputs": {
                    "requirements": [
                        {"id": "UN-001", "description": "The system must be easy for an elderly patient to use daily without assistance."},
                        {"id": "SR-001", "description": "The pill casing shall have a diameter less than 8mm."},
                        {"id": "RC-001", "description": "The release mechanism shall be tested to a 6-sigma reliability for dose accuracy."},
                        {"id": "RC-002", "description": "Casing material must pass all ISO 10993 biocompatibility tests."},
                    ]
                },
                "design_outputs": {
                    "documents": [
                        {"id": "DO-001", "title": "User Needs Document", "phase": "User Needs", "status": "Approved", "linked_input_id": "UN-001"},
                        {"id": "DO-002", "title": "System Requirements Spec", "phase": "Design Inputs", "status": "Approved", "linked_input_id": "UN-001"},
                        {"id": "DO-003", "title": "Risk Management Plan", "phase": "Design Inputs", "status": "Approved", "linked_input_id": "UN-001"},
                        {"id": "DO-004", "title": "Pill Casing Final CAD Model", "phase": "Design Outputs", "status": "In Review", "linked_input_id": "SR-001"},
                        {"id": "DO-005", "title": "Dose Release Mechanism Spec", "phase": "Design Outputs", "status": "Draft", "linked_input_id": "RC-001"},
                        {"id": "DO-006", "title": "Biocompatibility Test Protocol", "phase": "V&V", "status": "Draft", "linked_input_id": "RC-002"},
                    ]
                },
                "design_verification": {
                    "tests": [
                        # --- FIX IS HERE: Restored 'output_verified' and corrected 'risk_control' to 'risk_control_verified_id' ---
                        {"id": "VER-001", "name": "Pill Diameter Test", "status": "Completed", "tmv_status": "N/A", "output_verified": "DO-004", "risk_control_verified_id": "SR-001"},
                        {"id": "VER-002", "name": "Dose Accuracy Assay", "status": "In Progress", "tmv_status": "Required", "output_verified": "DO-005", "risk_control_verified_id": "RC-001"},
                        {"id": "VER-003", "name": "ISO 10993 Biocompatibility Study", "status": "Not Started", "tmv_status": "Completed", "output_verified": "DO-006", "risk_control_verified_id": "RC-002"},
                    ]
                },
                "quality_system": {
                    "capa_records": [
                        {"id": "CAPA-01", "status": "Closed", "source": "Internal Audit"},
                        {"id": "CAPA-02", "status": "Open", "source": "Supplier Corrective Action"},
                        {"id": "CAPA-03", "status": "Open", "source": "Complaint Investigation"},
                    ],
                    "supplier_audits": [
                        {"supplier": "PillCasing Inc.", "status": "Pass", "date": "2024-03-15"},
                        {"supplier": "BatteryCorp", "status": "Pass with Observations", "date": "2024-04-20"},
                    ],
                    "continuous_improvement": [
                        {"date": "2024-03-10", "area": "Documentation", "impact": 15},
                        {"date": "2024-05-20", "area": "Testing", "impact": 10},
                    ]
                },
                "project_management": {
                    "tasks": [
                        {"id": "NEEDS", "name": "User Needs", "start_date": base_date, "end_date": base_date + timedelta(days=14), "status": "Completed", "completion_pct": 100, "sign_offs": {"R&D": "✅", "Quality": "✅", "Marketing": "✅"}},
                        {"id": "INPUTS", "name": "Design Inputs", "start_date": base_date + timedelta(days=15), "end_date": base_date + timedelta(days=30), "status": "Completed", "completion_pct": 100, "sign_offs": {"R&D": "✅", "Quality": "✅", "Regulatory": "✅"}},
                        {"id": "OUTPUTS", "name": "Design Outputs", "start_date": base_date + timedelta(days=31), "end_date": base_date + timedelta(days=90), "status": "In Progress", "completion_pct": 60, "sign_offs": {"R&D": "In Progress", "Quality": "Pending", "Regulatory": "Pending"}},
                        {"id": "V&V", "name": "Verification & Validation", "start_date": base_date + timedelta(days=91), "end_date": base_date + timedelta(days=180), "status": "Not Started", "completion_pct": 10, "sign_offs": {"R&D": "Pending", "Quality": "Pending", "Regulatory": "Pending"}},
                        {"id": "TRANSFER", "name": "Design Transfer", "start_date": base_date + timedelta(days=181), "end_date": base_date + timedelta(days=210), "status": "Not Started", "completion_pct": 0, "sign_offs": {"Manufacturing": "Pending", "Quality": "Pending"}},
                    ]
                },
                "design_reviews": {"reviews":[]}, "human_factors":{"use_scenarios":[]}, "design_validation":{"studies":[]}, "design_transfer":{"activities":[]}, "design_changes":{"changes":[]}
            }

    def get_data(self, primary_key, secondary_key=None):
        """Safely retrieves data from the session state."""
        if secondary_key:
            return st.session_state.dhf_data.get(primary_key, {}).get(secondary_key, [])
        return st.session_state.dhf_data.get(primary_key, {})

    def update_data(self, data, primary_key, secondary_key=None):
        """Updates data in the session state."""
        if secondary_key:
            if primary_key not in st.session_state.dhf_data:
                st.session_state.dhf_data[primary_key] = {}
            st.session_state.dhf_data[primary_key][secondary_key] = data
        else:
            st.session_state.dhf_data[primary_key] = data
