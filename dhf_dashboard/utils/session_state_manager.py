# File: dhf_dashboard/utils/session_state_manager.py
# SME Note: This is the definitive, fully populated data model. It adds mock data
# for all empty sections (Reviews, Validation, Transfer, Changes) and ensures all
# data types and keys are correct to prevent any errors.

import streamlit as st
from datetime import date, timedelta

class SessionStateManager:
    """
    Manages session state with a robust, interconnected mock dataset designed for a
    professional-grade Design Assurance dashboard.
    """
    def __init__(self):
        # Incrementing version to 9 to guarantee a fresh, fully populated data load.
        CURRENT_DATA_VERSION = 9

        if ('dhf_data' not in st.session_state or
            st.session_state.dhf_data.get('data_version') != CURRENT_DATA_VERSION):

            st.toast(f"Definitive Data Load: Initializing complete mock data (v{CURRENT_DATA_VERSION})...")

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
                    "historical_rpn": [{"date": "2024-02-01", "total_rpn": 350}, {"date": "2024-04-01", "total_rpn": 210}, {"date": "2024-06-01", "total_rpn": 95}],
                },
                "human_factors": {
                    "use_scenarios": [{"use_scenario": "Patient takes daily pill", "user_task": "Swallows pill with water", "potential_use_error": "Takes pill without water", "potential_harm": "Pill lodges in esophagus", "related_hazard_id": "H-005"}]
                },
                "design_inputs": {
                    "requirements": [
                        {"id": "UN-001", "description": "The system must be easy for an elderly patient to use daily without assistance.", "source_type": "User Need", "is_risk_control": False},
                        {"id": "UN-002", "description": "The pill must be comfortable to swallow.", "source_type": "User Need", "is_risk_control": False},
                        {"id": "SR-001", "description": "The pill casing shall have a diameter less than 8mm.", "source_type": "QSR (Device)", "is_risk_control": False},
                        {"id": "RC-001", "description": "The release mechanism shall be tested to a 6-sigma reliability for dose accuracy.", "source_type": "Risk Control", "is_risk_control": True, "related_hazard_id": "H-001"},
                        {"id": "RC-002", "description": "Casing material must pass all ISO 10993 biocompatibility tests.", "source_type": "Risk Control", "is_risk_control": True, "related_hazard_id": "H-002"},
                    ]
                },
                "design_outputs": {
                    "documents": [
                        {"id": "DO-001", "title": "User Needs Document", "phase": "User Needs", "status": "Approved", "linked_input_id": "UN-001"},
                        {"id": "DO-002", "title": "System Requirements Spec", "phase": "Design Inputs", "status": "Approved", "linked_input_id": "UN-002"},
                        {"id": "DO-003", "title": "Risk Management Plan", "phase": "Design Inputs", "status": "Approved", "linked_input_id": "UN-001"},
                        {"id": "DO-004", "title": "Pill Casing Final CAD Model", "phase": "Design Outputs", "status": "In Review", "linked_input_id": "SR-001"},
                        {"id": "DO-005", "title": "Dose Release Mechanism Spec", "phase": "Design Outputs", "status": "Draft", "linked_input_id": "RC-001"},
                        {"id": "DO-006", "title": "Biocompatibility Test Protocol", "phase": "V&V", "status": "Draft", "linked_input_id": "RC-002"},
                    ]
                },
                "design_reviews": { # POPULATED SECTION
                    "reviews":[
                        {"date": date(2024, 5, 10), "attendees": "A. Weber, B. Chen, F. Green", "notes": "Phase 1 Gate Review completed. Approved to proceed to detailed design. Key action items on material sourcing.", "is_gate_review": True, "action_items": [
                            {"id": "AI-DR1-01", "description": "Finalize biocompatible polymer selection from approved supplier list.", "owner": "B. Chen", "due_date": date(2024, 5, 24), "status": "Completed"},
                            {"id": "AI-DR1-02", "description": "Update Risk Management File with outputs from this review.", "owner": "F. Green", "due_date": date(2024, 5, 17), "status": "In Progress"}
                        ]}
                    ]
                },
                "design_verification": {
                    "tests": [
                        {"id": "VER-001", "name": "Pill Diameter Test", "status": "Completed", "tmv_status": "N/A", "output_verified": "DO-004", "risk_control_verified_id": "SR-001"},
                        {"id": "VER-002", "name": "Dose Accuracy Assay", "status": "In Progress", "tmv_status": "Required", "output_verified": "DO-005", "risk_control_verified_id": "RC-001"},
                        {"id": "VER-003", "name": "ISO 10993 Biocompatibility Study", "status": "Not Started", "tmv_status": "Completed", "output_verified": "DO-006", "risk_control_verified_id": "RC-002"},
                    ]
                },
                "design_validation": { # POPULATED SECTION
                    "studies": [
                        {"id": "VAL-001", "study_name": "Simulated Use Human Factors Study (n=15)", "user_need_validated": "UN-001", "risk_control_effectiveness": True, "result": "In Progress", "report_file": ""}
                    ]
                },
                "design_transfer": { # POPULATED SECTION
                    "activities": [
                        {"activity": "Finalize Device Master Record (DMR)", "responsible_party": "Quality Eng.", "status": "In Progress", "completion_date": None, "evidence_link": ""},
                        {"activity": "Validate Automated Assembly Line (IQ/OQ)", "responsible_party": "Mfg. Eng.", "status": "Not Started", "completion_date": None, "evidence_link": ""}
                    ]
                },
                "design_changes": { # POPULATED SECTION
                    "changes": [
                        {"id": "DCR-001", "description": "Change battery supplier from BatteryCorp to PowerPlus for improved cycle life.", "reason": "Improved reliability based on new test data.", "impact_analysis": "Minimal impact. PowerPlus battery is form-fit-function equivalent. Requires regression testing of power management software.", "approval_status": "Pending", "approval_date": None}
                    ]
                },
                "quality_system": {
                    "capa_records": [{"id": "CAPA-01", "status": "Closed", "source": "Internal Audit"}, {"id": "CAPA-02", "status": "Open", "source": "Supplier Corrective Action"}, {"id": "CAPA-03", "status": "Open", "source": "Complaint Investigation"}],
                    "supplier_audits": [{"supplier": "PillCasing Inc.", "status": "Pass", "date": "2024-03-15"}, {"supplier": "BatteryCorp", "status": "Pass with Observations", "date": "2024-04-20"}],
                    "continuous_improvement": [{"date": "2024-03-10", "area": "Documentation", "impact": 15}, {"date": "2024-05-20", "area": "Testing", "impact": 10}],
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
            }

    def get_data(self, primary_key, secondary_key=None):
        if secondary_key:
            return st.session_state.dhf_data.get(primary_key, {}).get(secondary_key, [])
        return st.session_state.dhf_data.get(primary_key, {})

    def update_data(self, data, primary_key, secondary_key=None):
        if secondary_key:
            if primary_key not in st.session_state.dhf_data:
                st.session_state.dhf_data[primary_key] = {}
            st.session_state.dhf_data[primary_key][secondary_key] = data
        else:
            st.session_state.dhf_data[primary_key] = data
