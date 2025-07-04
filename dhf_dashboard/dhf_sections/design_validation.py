# File: dhf_dashboard/dhf_sections/design_validation.py
# --- Enhanced Version ---
"""
Renders the Design Validation section of the DHF dashboard.

This module provides the UI for documenting design validation activities, which
confirm that the final product meets user needs and intended uses, as required
by 21 CFR 820.30(g).
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


def render_design_validation(ssm: SessionStateManager) -> None:
    """
    Renders the UI for the Design Validation section.

    This function displays an editable table for managing validation studies.
    It enforces the critical compliance rule that validation must trace
    specifically to a 'User Need' type of requirement.

    Args:
        ssm (SessionStateManager): The session state manager to access DHF data.
    """
    st.header("8. Design Validation")
    st.markdown("""
    *As per 21 CFR 820.30(g) and ISO 14971.*

    Validation ensures the final product meets **user needs** and intended uses under actual or
    simulated conditions. It also serves as a final check on the effectiveness of risk controls.
    It answers the question: **"Did we build the right product?"**
    """)
    st.info("Changes made here are saved automatically. Each validation study must be linked to a specific User Need.", icon="ℹ️")

    try:
        # --- 1. Load Data and Prepare Traceability Links ---
        validation_data: List[Dict[str, Any]] = ssm.get_data("design_validation", "studies")
        inputs_data: List[Dict[str, Any]] = ssm.get_data("design_inputs", "requirements")
        logger.info(f"Loaded {len(validation_data)} validation studies and {len(inputs_data)} input records.")

        # --- SME Enhancement: Only allow linking to User Needs ---
        user_needs = [req for req in inputs_data if req.get('source_type') == 'User Need']

        if not user_needs:
            st.warning(
                "⚠️ No 'User Need' requirements found. Please add them in the '4. Design Inputs' section before documenting validation.",
                icon="❗"
            )
            user_need_options: List[str] = []
            user_need_map: Dict[str, str] = {}
        else:
            # Create descriptive options for the dropdown
            user_need_options = [f"{un.get('id', '')}: {un.get('description', '')}" for un in user_needs]
            # Map descriptive options back to raw IDs for saving
            user_need_map = {option: un.get('id', '') for option, un in zip(user_need_options, user_needs)}
            logger.debug(f"Created {len(user_need_options)} user need options for dropdown.")

        # --- 2. Display Data Editor ---
        st.subheader("Validation Studies & Results")
        st.markdown("Document each validation study (e.g., usability study, clinical trial) and link it to the User Need it confirms.")

        studies_df = pd.DataFrame(validation_data)
        # Create a reverse map to convert stored IDs to descriptive format for display
        reverse_user_need_map = {v: k for k, v in user_need_map.items()}
        if 'user_need_validated' in studies_df.columns:
            studies_df['user_need_validated_descriptive'] = studies_df['user_need_validated'].map(reverse_user_need_map)
        else:
            studies_df['user_need_validated_descriptive'] = pd.Series(dtype=str)

        edited_df = st.data_editor(
            studies_df,
            num_rows="dynamic",
            use_container_width=True,
            key="design_validation_editor",
            column_config={
                "id": st.column_config.TextColumn("Study ID", help="Unique ID for the study protocol (e.g., VAL-001).", required=True),
                "study_name": st.column_config.TextColumn("Study/Protocol Name", width="large", required=True),
                "user_need_validated_descriptive": st.column_config.SelectboxColumn(
                    "User Need Validated",
                    options=user_need_options,
                    help="Select the User Need that this study confirms. This link is mandatory.",
                    required=True
                ),
                "risk_control_effectiveness": st.column_config.CheckboxColumn(
                    "Confirms Risk Control?",
                    help="Did this study also confirm that risk controls are effective in the hands of the user?",
                    default=False
                ),
                "result": st.column_config.SelectboxColumn("Result", options=["Not Started", "In Progress", "Pass", "Fail"], required=True),
                "report_file": st.column_config.TextColumn("Link to Validation Report", help="Filename or link to the final study report."),
                # Hide the raw ID column from the user
                "user_need_validated": None,
            },
            hide_index=True
        )

        # --- 3. Process and Persist Data ---
        if 'user_need_validated_descriptive' in edited_df.columns:
            valid_rows = edited_df['user_need_validated_descriptive'].notna()
            edited_df.loc[valid_rows, 'user_need_validated'] = edited_df.loc[valid_rows, 'user_need_validated_descriptive'].map(user_need_map)
        
        if 'user_need_validated_descriptive' in edited_df.columns:
            edited_df.drop(columns=['user_need_validated_descriptive'], inplace=True)

        updated_records = edited_df.to_dict('records')

        if updated_records != validation_data:
            ssm.update_data(updated_records, "design_validation", "studies")
            logger.info("Design validation data updated in session state.")
            st.toast("Design validation studies saved!", icon="✅")

    except Exception as e:
        st.error("An error occurred while displaying the Design Validation section. The data may be malformed.")
        logger.error(f"Failed to render design validation: {e}", exc_info=True)
