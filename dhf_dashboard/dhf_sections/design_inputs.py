# File: dhf_dashboard/dhf_sections/design_inputs.py
# --- Enhanced Version ---
"""
Renders the Design Inputs section of the DHF dashboard.

This module provides the UI for managing all product requirements, which serve
as the foundation for the Design History File. It integrates user needs,
technical requirements, and risk controls as required by 21 CFR 820.30(c).
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


def render_design_inputs(ssm: SessionStateManager) -> None:
    """
    Renders the UI for the Design Inputs section.

    This function displays an editable table for managing all project
    requirements. It provides traceability features by allowing risk control
    requirements to be linked directly to hazards from the Risk Management File.
    It also includes logic to enforce data consistency.

    Args:
        ssm (SessionStateManager): The session state manager to access DHF data.
    """
    st.header("4. Design Inputs")
    st.markdown("""
    *As per 21 CFR 820.30(c), accounting for 21 CFR Part 4 and ISO 14971.*

    This section captures all requirements for the product. This includes user needs, device requirements (QSR),
    drug interface requirements (cGMP), and requirements derived from risk analysis (Risk Controls).
    Each requirement must be unambiguous, verifiable, and traceable.
    """)
    st.info("Changes made here are saved automatically. Checking 'Is a Risk Control?' will auto-set the Source/Type and enable the Hazard ID link.", icon="ℹ️")

    try:
        # --- 1. Load Data and Prepare Traceability Links ---
        inputs_data: List[Dict[str, Any]] = ssm.get_data("design_inputs", "requirements")
        rmf_data: Dict[str, Any] = ssm.get_data("risk_management_file")
        logger.info(f"Loaded {len(inputs_data)} design input records.")

        # Fetch all Hazard IDs from the Risk Management File to populate the dropdown.
        # This creates a direct, auditable link from a risk control requirement to the hazard it mitigates.
        hazards: List[Dict[str, Any]] = rmf_data.get("hazards", [])
        hazard_ids: List[str] = [""] + [h.get('hazard_id', '') for h in hazards if h.get('hazard_id')]
        logger.debug(f"Populated hazard ID dropdown with: {hazard_ids}")

        # --- 2. Display Data Editor ---
        st.subheader("Requirements and Needs")
        st.markdown("Use this table to manage all project requirements. If a requirement is a risk control, check the box and link it to a Hazard ID.")

        requirements_df = pd.DataFrame(inputs_data)

        edited_df = st.data_editor(
            requirements_df,
            num_rows="dynamic",
            use_container_width=True,
            key="design_inputs_editor",
            column_config={
                "id": st.column_config.TextColumn(
                    "Req. ID",
                    help="Unique ID (e.g., UN-001, SR-001, RC-001)",
                    required=True
                ),
                "source_type": st.column_config.SelectboxColumn(
                    "Source / Type",
                    options=["User Need", "QSR (Device)", "cGMP (Drug Interface)", "Standard", "Risk Control"],
                    help="Categorize the requirement. Will be set to 'Risk Control' automatically if the checkbox is ticked.",
                    required=True
                ),
                "description": st.column_config.TextColumn(
                    "Requirement Description",
                    width="large",
                    required=True
                ),
                "is_risk_control": st.column_config.CheckboxColumn(
                    "Is a Risk Control?",
                    help="Check if this requirement's purpose is to mitigate a hazard.",
                    default=False
                ),
                "related_hazard_id": st.column_config.SelectboxColumn(
                    "Mitigates Hazard ID",
                    options=hazard_ids,
                    help="If this is a risk control, which hazard from the RMF does it mitigate? (Enabled when 'Is a Risk Control?' is checked)"
                ),
            },
            hide_index=True
        )

        # --- 3. Apply Smart UI Logic and Persist Data ---
        # This logic enforces data consistency automatically.
        if 'is_risk_control' in edited_df.columns:
            # Create a boolean mask for rows where the state changed
            original_df_reindexed = requirements_df.reindex(edited_df.index)
            state_changed = (edited_df['is_risk_control'] != original_df_reindexed['is_risk_control'])
            
            if state_changed.any():
                # Automatically set 'source_type' to 'Risk Control' when checkbox is checked.
                edited_df.loc[edited_df['is_risk_control'] == True, 'source_type'] = 'Risk Control'
                # Clear the hazard link if it's no longer a risk control to prevent dangling references.
                edited_df.loc[edited_df['is_risk_control'] == False, 'related_hazard_id'] = ""
                logger.info("Applied automatic updates to 'source_type' and 'related_hazard_id' based on 'is_risk_control' checkbox.")

        updated_records = edited_df.to_dict('records')
        
        # Only update if there has been a change
        if updated_records != inputs_data:
            ssm.update_data(updated_records, "design_inputs", "requirements")
            logger.info("Design inputs data updated in session state.")
            st.toast("Design inputs saved!", icon="✅")

    except Exception as e:
        st.error("An error occurred while displaying the Design Inputs section. The data may be malformed.")
        logger.error(f"Failed to render design inputs: {e}", exc_info=True)
