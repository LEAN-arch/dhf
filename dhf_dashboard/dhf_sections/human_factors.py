# File: dhf_dashboard/dhf_sections/human_factors.py

import streamlit as st
import pandas as pd
from ..utils.session_state_manager import SessionStateManager

def render_human_factors(ssm: SessionStateManager):
    """
    Renders the Human Factors & Usability Engineering section.
    """
    st.header("3. Human Factors & Usability Engineering (IEC 62366)")
    st.markdown("""
    This section documents the usability engineering process to ensure the smart-pill can be used safely and effectively by the intended users in the intended use environment.
    We identify tasks users perform, analyze potential use errors, and link them to clinical hazards documented in the Risk Management File.
    """)
    st.info("Changes made here are saved automatically.", icon="ℹ️")

    hf_data = ssm.get_data("human_factors", "use_scenarios")
    rmf_data = ssm.get_data("risk_management_file")

    # --- SME Enhancement: Live link to Risk Management File ---
    # Fetch all Hazard IDs from the RMF to populate the dropdown.
    # This creates a direct, auditable link from a use error to the system hazard it can cause.
    hazard_ids = [""] + [h.get('hazard_id', '') for h in rmf_data.get("hazards", [])]

    st.subheader("Use-Related Risk Analysis (URRA)")
    st.markdown("For each critical user task, identify things that could go wrong (use errors) and the potential harm that could result.")

    edited_df = st.data_editor(
        pd.DataFrame(hf_data),
        num_rows="dynamic",
        use_container_width=True,
        key="hf_editor",
        column_config={
            "use_scenario": st.column_config.TextColumn(
                "Use Scenario",
                help="Describe the high-level situation, e.g., 'Patient taking the pill for the first time', 'Pharmacist dispensing the prescription'.",
                required=True,
                width="large"
            ),
            "user_task": st.column_config.TextColumn(
                "Critical User Task",
                help="The specific, essential action the user must perform, e.g., 'Swallows pill with water', 'Checks app for dose confirmation'.",
                required=True,
                width="large"
            ),
            "potential_use_error": st.column_config.TextColumn(
                "Potential Use Error",
                help="How could the user perform the task incorrectly? e.g., 'Forgets to take pill', 'Takes double dose', 'Misinterprets app notification'.",
                width="large"
            ),
            "potential_harm": st.column_config.TextColumn(
                "Resulting Potential Harm",
                help="What is the clinical consequence of the use error? e.g., 'Ineffective therapy', 'Overdose event', 'Delayed treatment'.",
                width="large"
            ),
            "related_hazard_id": st.column_config.SelectboxColumn(
                "Links to System Hazard ID",
                options=hazard_ids,
                help="Link this use error to a formal system hazard from the Risk Management File."
            ),
        },
    )

    # Persist the updated data back to the session state
    ssm.update_data(edited_df.to_dict('records'), "human_factors", "use_scenarios")
