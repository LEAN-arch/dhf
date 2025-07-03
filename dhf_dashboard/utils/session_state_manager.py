# File: dhf_dashboard/utils/session_state_manager.py
# SME Note: This is the definitive, fully populated data model. It names
# JOSE BAUTISTA as the main Quality Lead and assigns relevant tasks and
# responsibilities to him for a personalized experience.

import streamlit as st
from datetime import date, timedelta

class SessionStateManager:
    """
    Manages session state with a robust, interconnected mock dataset designed for a
    professional-grade Design Assurance dashboard.
    """
    def __init__(self):
        # Incrementing version to 15 to load the personalized data.
        CURRENT_DATA_VERSION = 15

        if ('dhf_data' not in st.session_state or
            st.session_state.dhf_data.get('data_version') != CURRENT_DATA_VERSION):

            st.toast(f"Loading Personalized Data Model (v{CURRENT_DATA_VERSION})...")

            base_date = date(2024, 1, 15)
            current_date = date.today()

            st.session_state.dhf_data = {
                "data_version": CURRENT_DATA_VERSION,
                "design_plan": {
                    "project_name": "Smart-Pill Drug Delivery System (SP-DDS)",
                    "scope": "This project covers the design and development of a new combination product, the 'Smart-Pill', intended for the targeted oral delivery of drug XYZ for treating chronic condition ABC. The system comprises a swallowable electronic capsule (device) containing a payload of drug XYZ (drug), a companion mobile application for monitoring, and a cloud-based data backend.",
                    "team_members": [
                        {"role": "Project Lead", "name": "Dr. Alice Weber", "responsibility": "Overall project oversight and final DHF approval."},
                        {"role": "Senior Device Engineer", "name": "Bob Chen", "responsibility": "Hardware design, material selection, and mechanical testing."},
                        {"role": "Software Engineer", "name": "Charlie Day", "responsibility": "Embedded firmware, mobile app development, and cybersecurity."},
                        {"role": "Pharma Scientist", "name": "Dr. Diana Evans", "responsibility": "Drug formulation, stability studies, and release profile analysis."},
                        {"role": "Sr. Quality Engineer Lead", "name": "JOSE BAUTISTA", "responsibility": "DHF owner, V&V strategy, Risk Management, and regulatory compliance."}
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
                    "fta_document_ref": "FTA-001 - System Safety Analysis",
                    "dfmea": [
                        {"id": "DFMEA-01", "failure_mode": "Pill casing seal failure", "potential_effect": "Drug leakage, incorrect dose", "S": 5, "O": 2, "D": 2, "mitigation": "Redesigned seal geometry, add seal integrity test."},
                        {"id": "DFMEA-02", "failure_mode": "Battery shorts circuit", "potential_effect": "Device failure, potential thermal event", "S": 5, "O": 1, "D": 3, "mitigation": "Use medically certified battery with short-circuit protection."},
                        {"id": "DFMEA-03", "failure_mode": "Software algorithm miscalculates release time", "potential_effect": "Incorrect dose timing", "S": 4, "O": 3, "D": 2, "mitigation": "Add checksums, implement robust unit testing, code reviews."},
                    ],
                    "pfmea": [
                        {"id": "PFMEA-01", "failure_mode": "Incorrect polymer mixing ratio", "potential_effect": "Casing brittle, fails biocompatibility", "S": 5, "O": 2, "D": 4, "mitigation": "Automated mixing system with ratio alarms."},
                        {"id": "PFMEA-02", "failure_mode": "Contamination during drug filling", "potential_effect": "Adverse patient reaction", "S": 5, "O": 2, "D": 3, "mitigation": "Perform filling in certified cleanroom, regular environmental monitoring."},
                        {"id": "PFMEA-03", "failure_mode": "Incorrect torque on sealing machine", "potential_effect": "Improper seal, drug leakage", "S": 4, "O": 3, "D": 3, "mitigation": "Use calibrated torque wrench, regular calibration schedule."},
                    ]
                },
                "human_factors": {"use_scenarios": [{"use_scenario": "Patient takes daily pill", "user_task": "Swallows pill with water", "potential_use_error": "Takes pill without water", "potential_harm": "Pill lodges in esophagus", "related_hazard_id": "H-005"}]},
                "design_inputs": {
                    "requirements": [
                        {"id": "UN-001", "source_type": "User Need", "description": "The system must be easy for an elderly patient to use daily without assistance.", "is_risk_control": False, "related_hazard_id": ""},
                        {"id": "UN-002", "source_type": "User Need", "description": "The pill must be comfortable to swallow.", "is_risk_control": False, "related_hazard_id": ""},
                        {"id": "SR-001", "source_type": "QSR (Device)", "description": "The pill casing shall have a diameter less than 8mm.", "is_risk_control": False, "related_hazard_id": ""},
                        {"id": "SR-002", "source_type": "QSR (Device)", "description": "Device must be compatible with EtO sterilization.", "is_risk_control": False, "related_hazard_id": ""},
                        {"id": "RC-001", "source_type": "Risk Control", "description": "The release mechanism shall be tested to a 6-sigma reliability for dose accuracy.", "is_risk_control": True, "related_hazard_id": "H-001"},
                        {"id": "RC-002", "source_type": "Risk Control", "description": "Casing material must pass all ISO 10993 biocompatibility tests.", "is_risk_control": True, "related_hazard_id": "H-002"},
                    ]
                },
                "design_outputs": {
                    "documents": [
                        {"id": "DO-001", "title": "User Needs Document", "phase": "User Needs", "status": "Approved", "linked_input_id": "UN-001"},
                        {"id": "DO-002", "title": "System Requirements Spec", "phase": "Design Inputs", "status": "Approved", "linked_input_id": "UN-002"},
                        {"id": "RPT-001", "title": "DOE Report for Molding Parameters", "phase": "Design Outputs", "status": "Approved", "linked_input_id": "SR-001"},
                        {"id": "SPEC-001", "title": "EtO Sterilization Cycle Specification", "phase": "Design Outputs", "status": "Approved", "linked_input_id": "SR-002"},
                        {"id": "DO-004", "title": "Pill Casing Final CAD Model", "phase": "Design Outputs", "status": "In Review", "linked_input_id": "SR-001"},
                        {"id": "DO-005", "title": "Dose Release Mechanism Spec", "phase": "Design Outputs", "status": "Draft", "linked_input_id": "RC-001"},
                        {"id": "DO-006", "title": "Biocompatibility Test Protocol", "phase": "V&V", "status": "Draft", "linked_input_id": "RC-002"},
                    ]
                },
                "design_reviews": {
                    "reviews":[
                        {"date": date(2024, 5, 10), "attendees": "A. Weber, B. Chen, JOSE BAUTISTA, C. Day, D. Evans", "notes": "Phase 1 Gate Review completed. Approved to proceed to detailed design. Key action items on material sourcing and software architecture.", "is_gate_review": True,
                         "action_items": [
                            {"id": "AI-DR1-01", "description": "Finalize biocompatible polymer selection from approved supplier list.", "owner": "B. Chen", "due_date": date(2024, 5, 24), "status": "Completed"},
                            {"id": "AI-DR1-02", "description": "Update Risk Management File with outputs from this review.", "owner": "JOSE BAUTISTA", "due_date": current_date - timedelta(days=20), "status": "In Progress"},
                            {"id": "AI-DR1-03", "description": "Create detailed CAD models for manufacturing molds.", "owner": "B. Chen", "due_date": current_date + timedelta(days=30), "status": "In Progress"},
                            {"id": "AI-DR1-04", "description": "Develop initial firmware for Bluetooth communication handshake.", "owner": "C. Day", "due_date": current_date + timedelta(days=45), "status": "Open"},
                            {"id": "AI-DR1-05", "description": "Finalize drug stability protocol for combination testing.", "owner": "D. Evans", "due_date": current_date - timedelta(days=10), "status": "Open"},
                            {"id": "AI-DR1-06", "description": "Draft V&V Master Plan.", "owner": "JOSE BAUTISTA", "due_date": current_date + timedelta(days=15), "status": "In Progress"}
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
                "design_validation": {"studies": [{"id": "VAL-001", "study_name": "Simulated Use Human Factors Study (n=15)", "user_need_validated": "UN-001", "risk_control_effectiveness": True, "result": "In Progress", "report_file": ""}]},
                "design_transfer": {
                    "activities": [
                        {"activity": "Installation Qualification (IQ) - Assembly Line A", "responsible_party": "Mfg. Eng.", "status": "Completed", "completion_date": date(2024, 6, 1), "evidence_link": "IQ-RPT-01.pdf"},
                        {"activity": "Operational Qualification (OQ) - Assembly Line A", "responsible_party": "Mfg. Eng.", "status": "In Progress", "completion_date": None, "evidence_link": ""},
                        {"activity": "Performance Qualification (PQ) - Assembly Line A", "responsible_party": "JOSE BAUTISTA", "status": "Not Started", "completion_date": None, "evidence_link": ""},
                        {"activity": "Finalize Device Master Record (DMR)", "responsible_party": "JOSE BAUTISTA", "status": "In Progress", "completion_date": None, "evidence_link": ""}
                    ]
                },
                "design_changes": {"changes": [{"id": "DCR-001", "description": "Change battery supplier from BatteryCorp to PowerPlus for improved cycle life.", "reason": "Improved reliability based on new test data.", "impact_analysis": "Minimal impact. PowerPlus battery is form-fit-function equivalent. Requires regression testing of power management software.", "approval_status": "Pending", "approval_date": None}]},
                "quality_system": {
                    "capa_records": [{"id": "CAPA-01", "status": "Closed", "source": "Internal Audit"}, {"id": "CAPA-02", "status": "Open", "source": "Supplier Corrective Action"}],
                    "supplier_audits": [{"supplier": "PillCasing Inc.", "status": "Pass", "date": "2024-03-15"}, {"supplier": "BatteryCorp", "status": "Pass with Observations", "date": "2024-04-20"}],
                    "continuous_improvement": [{"date": "2024-03-10", "area": "Documentation", "impact": 15}, {"date": "2024-05-20", "area": "Testing", "impact": 10}],
                    "cgmp_compliance": {
                        "stability_studies": [
                            {"id": "STAB-01", "duration": "3 Months", "condition": "Accelerated", "status": "Completed - Pass"},
                            {"id": "STAB-02", "duration": "6 Months", "condition": "Real-Time", "status": "In Progress"}
                        ],
                        "batch_record_review": {"total": 5, "passed": 4, "failed": 1}
                    }
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
                "quality_by_design": {
                    "elements": [
                        {"cqa": "Accurate Drug Dosage (10mg ± 0.5mg)", "links_to_req": "RC-001", "cm_attributes": ["Drug Particle Size Distribution", "Polymer Viscosity"], "cp_parameters": ["Molding Temperature", "Nozzle Pressure", "Mixing Speed"]},
                        {"cqa": "Casing Biocompatibility", "links_to_req": "RC-002", "cm_attributes": ["Polymer Grade Purity", "Absence of Leachables/Extractables"], "cp_parameters": ["Curing Time", "Sterilization Cycle Parameters"]}
                    ]
                }
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
