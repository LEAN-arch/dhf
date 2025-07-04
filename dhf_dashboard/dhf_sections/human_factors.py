# File: dhf_dashboard/dhf_sections/human_factors.py
# --- Enhanced Version ---
"""
Renders the Human Factors & Usability Engineering section of the DHF dashboard.

This module provides the UI for documenting the Use-Related Risk Analysis (URRA)
in alignment with usability engineering standards like IEC 62366.
"""

# --- Standard Library Imports ---
import logging
from typing import Any, Dict, List

# --- Third-party Imports ---
import pandas as pd
import streamlit as st

# --- Local Application Imports ---
from ..utils.session_state_manager import SessionStateManager

# --- Setup Logging ---
logger = logging.getLogger(__name__)


def render_human_factors(ssm: SessionStateManager) -> None:
    """
    Renders the UI for the Human Factors & Usability Engineering section.

    This function displays an editable table for performing a Use-Related Risk
    Analysis (URRA). It allows users to document use scenarios, tasks, potential
    use errors, and link them directly to system hazards from the Risk
    Management File.

    Args:
        ssm (SessionStateManager): The session state manager to access DHF data.
    """
    st.header("3. Human Factors & Usability Engineering (IEC 62366)")
    st.markdown("""
    This section documents the usability engineering process to ensure the smart-pill can be used safely and effectively by the intended users in the intended use environment.
    We identify tasks users perform, analyze potential use errors, and link them to clinical hazards documented in the Risk Management File.
    """)
    st.info("Changes made here are saved automatically. Link use errors to system hazards to complete the risk analysis chain.", icon="ℹ️")

    try:
        # --- 1. Load Data and Prepare Traceability Links ---
        hf_data: List[Dict[str, Any]] = ssm.get_data("human_factors", "use_scenarios")
        rmf_data: Dict[str, Any] = ssm.get_data("risk_management_file")
        logger.info(f"Loaded {len(hf_data)} human factors records.")

        # Fetch all Hazard IDs from the RMF to populate the dropdown.
        # This creates a direct, auditable link from a use error to the system hazard it can cause.
        hazards: List[Dict[str, Any]] = rmf_data.get("hazards", [])
        hazard_ids: List[str] = [""] + [h.get('hazard_id', '') for h in hazards if h.get('hazard_id')]
        logger.debug(f"Populated hazard ID dropdown with: {hazard_ids}")

        # --- 2. Display Data Editor ---
        st.subheader("Use-Related Risk Analysis (URRA)")
        st.markdown("For each critical user task, identify things that could go wrong (use errors) and the potential harm that could result.")

        hf_df = pd.DataFrame(hf_data)

        edited_df = st.data_editor(
            hf_df,
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
            hide_index=True
        )

        # --- 3. Persist Updated Data ---
        updated_records = edited_df.to_dict('records')

        if updated_records != hf_data:
            ssm.update_data(updated_records, "human_factors", "use_scenarios")
            logger.info("Human factors data updated in session state.")
            st.toast("Human factors analysis saved!", icon="✅")

    except Exception as e:
        st.error("An error occurred while displaying the Human Factors section. The data may be malformed.")
        logger.error(f"Failed to render human factors: {e}", exc_info=True)
