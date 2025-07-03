# File: dhf_dashboard/utils/session_state_manager.py

import streamlit as st
from datetime import date, timedelta

class SessionStateManager:
    """
    Manages session state with a robust, interconnected mock dataset.
    This structured data is essential for advanced analytics and compliance views.
    """
    def __init__(self):
        # SME NOTE: Versioning is critical. Incrementing it forces a one-time
        # data refresh, clearing old/corrupted data from the user's session.
        CURRENT_DATA_VERSION = 5

        if ('dhf_data' not in st.session_state or
            st.session_state.dhf_data.get('data_version') != CURRENT_DATA_VERSION):

            st.toast(f"SME Fix: Initializing robust mock data (v{CURRENT_DATA_VERSION})...")

            base_date = date(2025, 1, 15)

            st.session_state.dhf_data = {
                "data_version": CURRENT_DATA_VERSION,
                "design_plan": {
                    "project_name": "Smart-Pill Drug Delivery System",
                    "scope": "This project covers the design and development of a new combination product, the 'Smart-Pill', intended for the targeted oral delivery of drug XYZ for treating chronic condition ABC. The system comprises a swallowable electronic capsule (device) containing a payload of drug XYZ (drug).",
                    "team_members": [
                        {"role": "Project Lead", "name": "Dr. Alice Weber", "responsibility": "Overall project oversight and final DHF approval."},
                        {"role": "Device Engineer", "name": "Bob Chen", "responsibility": "Hardware design, material selection, and manufacturing process."},
                        {"role": "Software Engineer", "name": "Charlie Day", "responsibility": "Embedded software, mobile app, and data security."},
                        {"role": "Pharma Scientist", "name": "Diana Evans", "responsibility": "Drug formulation, stability, and release profile."},
                        {"role": "Quality/Regulatory", "name": "Frank Green", "responsibility": "Ensuring compliance with QSR, cGMP, and ISO standards."}
                    ],
                    "applicable_cgmp": "21 CFR Parts 210, 211",
                    "risk_management_plan_ref": "RMP-001",
                    "software_level_of_concern": "Moderate"
                },
                "risk_management_file": {
                    "hazards": [
                        {"hazard_id": "H-001", "hazard_description": "Incorrect drug dosage delivered (over/under)", "potential_harm": "Ineffective therapy or toxic overdose.", "initial_severity": 5, "initial_probability": 3, "risk_control_req_id": "RC-001", "residual_severity": 5, "residual_probability": 1, "risk_acceptability": "Acceptable"},
                        {"hazard_id": "H-002", "hazard_description": "Battery failure during use", "potential_harm": "Pill fails to deliver drug.", "initial_severity": 4, "initial_probability": 2, "risk_control_req_id": "RC-002", "residual_severity": 2, "residual_probability": 1, "risk_acceptability": "Acceptable"},
                        {"hazard_id": "H-003", "hazard_description": "Patient data transmission intercepted", "potential_harm": "Breach of patient privacy.", "initial_severity": 3, "initial_probability": 3, "risk_control_req_id": "RC-003", "residual_severity": 3, "residual_probability": 1, "risk_acceptability": "Acceptable"},
                    ],
                    "overall_risk_benefit_analysis": "The overall residual risk of the Smart-Pill System is judged to be acceptable, as the benefits of accurate and timely drug delivery for the specified patient population outweigh the identified and mitigated residual risks. Final analysis is pending completion of all verification and validation activities."
                },
                "human_factors": {
                    "use_scenarios": [
                        {"use_scenario": "Patient takes daily pill", "user_task": "Swallows pill with water", "potential_use_error": "Takes pill without water", "potential_harm": "Pill lodges in esophagus", "related_hazard_id": "H-004"}
                    ]
                },
                "design_inputs": {
                    "requirements": [
                        {"id": "UN-001", "source_type": "User Need", "description": "The system must be easy for an elderly patient to use daily without assistance.", "is_risk_control": False, "related_hazard_id": ""},
                        {"id": "UN-002", "source_type": "User Need", "description": "The patient needs to feel confident the dose was delivered.", "is_risk_control": False, "related_hazard_id": ""},
                        {"id": "DEV-001", "source_type": "QSR (Device)", "description": "The pill casing shall have a diameter less than 8mm.", "is_risk_control": False, "related_hazard_id": ""},
                        {"id": "DRG-001", "source_type": "cGMP (Drug Interface)", "description": "The pill shall deliver a 10mg +/- 0.5mg dose of drug XYZ.", "is_risk_control": False, "related_hazard_id": ""},
                        {"id": "SW-001", "source_type": "QSR (Device)", "description": "The companion mobile app shall confirm dose delivery via Bluetooth.", "is_risk_control": False, "related_hazard_id": ""},
                        {"id": "RC-001", "source_type": "Risk Control", "description": "The release mechanism shall be tested to a 6-sigma reliability for dose accuracy.", "is_risk_control": True, "related_hazard_id": "H-001"},
                        {"id": "RC-002", "source_type": "Risk Control", "description": "The device shall use a certified medical-grade battery with >99.9% reliability.", "is_risk_control": True, "related_hazard_id": "H-002"},
                        {"id": "RC-003", "source_type": "Risk Control", "description": "All patient data transmission shall be encrypted using AES-256.", "is_risk_control": True, "related_hazard_id": "H-003"},
                    ]
                },
                "design_outputs": {
                    "documents": [
                        {"id": "DO-001", "title": "Pill Casing Final CAD Model", "file": "CAD-Casing-v3.dwg", "linked_input_id": "DEV-001"},
                        {"id": "DO-002", "title": "Dose Release Mechanism Specification", "file": "SPEC-Release-v1.pdf", "linked_input_id": "DRG-001"},
                        {"id": "DO-003", "title": "Software Architecture Document", "file": "SW-Arch-v2.docx", "linked_input_id": "SW-001"},
                        {"id": "DO-004", "title": "Manufacturing Procedure for Dose Accuracy", "file": "SOP-MFG-101.pdf", "linked_input_id": "RC-001"},
                        {"id": "DO-005", "title": "Bill of Materials - Final", "file": "BOM-Final.xlsx", "linked_input_id": "RC-002"},
                        {"id": "DO-006", "title": "Security Protocol Specification", "file": "SEC-Proto-v1.pdf", "linked_input_id": "RC-003"},
                    ]
                },
                "design_reviews": {
                    "reviews": [
                        {"date": base_date + timedelta(days=60), "attendees": "A. Weber, B. Chen, D. Evans", "notes": "Phase 1 review complete. Inputs approved. Proceed to detailed design.", "is_gate_review": True, "action_items": [
                            {"id": "AI-DR1-01", "description": "Finalize material selection for casing based on biocompatibility report.", "owner": "B. Chen", "due_date": base_date + timedelta(days=75), "status": "Completed"},
                            {"id": "AI-DR1-02", "description": "Investigate alternative battery supplier for cost reduction.", "owner": "D. Evans", "due_date": base_date + timedelta(days=90), "status": "In Progress"}
                        ]}
                    ]
                },
                "design_verification": {
                    "tests": [
                        {"id": "VER-001", "test_name": "Pill Diameter Measurement Test", "output_verified": "DO-001", "risk_control_verified_id": "", "result": "Pass", "report_file": "Test-RPT-001.pdf"},
                        {"id": "VER-002", "test_name": "Dose Accuracy Assay (n=1000)", "output_verified": "DO-004", "risk_control_verified_id": "RC-001", "result": "In Progress", "report_file": ""},
                        {"id": "VER-003", "test_name": "Penetration Test for Data Security", "output_verified": "DO-006", "risk_control_verified_id": "RC-003", "result": "Pass", "report_file": "Test-RPT-003.pdf"}
                    ]
                },
                "design_validation": {
                    "studies": [
                        {"id": "VAL-001", "study_name": "Simulated Use Usability Study (n=30)", "user_need_validated": "UN-001", "risk_control_effectiveness": True, "result": "Pass", "report_file": "VAL-RPT-001.pdf"},
                        {"id": "VAL-002", "study_name": "Patient Confidence Survey (Post-Use)", "user_need_validated": "UN-002", "risk_control_effectiveness": False, "result": "In Progress", "report_file": ""}
                    ]
                },
                "design_transfer": {"activities": []},
                "design_changes": {"changes": []},
                "project_management": {
                    "tasks": [
                        {"id": "PLAN", "name": "1. Design Planning", "start_date": base_date, "end_date": base_date + timedelta(days=14), "status": "Completed", "completion_pct": 100, "dependencies": ""},
                        {"id": "RISK", "name": "2. Risk Management", "start_date": base_date + timedelta(days=7), "end_date": base_date + timedelta(days=30), "status": "Completed", "completion_pct": 100, "dependencies": "PLAN"},
                        {"id": "HF", "name": "3. Human Factors", "start_date": base_date + timedelta(days=20), "end_date": base_date + timedelta(days=50), "status": "In Progress", "completion_pct": 75, "dependencies": "PLAN"},
                        {"id": "INPUTS", "name": "4. Define Design Inputs", "start_date": base_date + timedelta(days=25), "end_date": base_date + timedelta(days=55), "status": "Completed", "completion_pct": 100, "dependencies": "PLAN,RISK,HF"},
                        {"id": "OUTPUTS", "name": "5. Develop Design Outputs", "start_date": base_date + timedelta(days=56), "end_date": base_date + timedelta(days=120), "status": "In Progress", "completion_pct": 60, "dependencies": "INPUTS"},
                        {"id": "VERIFY", "name": "6. Design Verification", "start_date": base_date + timedelta(days=121), "end_date": base_date + timedelta(days=180), "status": "In Progress", "completion_pct": 20, "dependencies": "OUTPUTS"},
                        {"id": "VALIDATE", "name": "7. Design Validation", "start_date": base_date + timedelta(days=181), "end_date": base_date + timedelta(days=240), "status": "Not Started", "completion_pct": 0, "dependencies": "VERIFY"},
                        {"id": "TRANSFER", "name": "8. Design Transfer", "start_date": base_date + timedelta(days=241), "end_date": base_date + timedelta(days=270), "status": "Not Started", "completion_pct": 0, "dependencies": "VALIDATE"},
                    ]
                }
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
