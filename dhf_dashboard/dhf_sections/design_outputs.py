# File: dhf_dashboard/dhf_sections/design_outputs.py
# --- Enhanced Version ---
"""
Renders the Design Outputs section of the DHF dashboard.

This module provides the UI for documenting all tangible outputs of the design
process (e.g., drawings, specifications) and ensuring each one is traceably
linked to a design input, as required by 21 CFR 820.30(d).
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


def render_design_outputs(ssm: SessionStateManager) -> None:
    """
    Renders the UI for the Design Outputs section.

    This function displays an editable table for managing design outputs. Its
    key feature is a user-friendly, descriptive dropdown for enforcing the
    critical traceability link from each output back to a specific design input.

    Args:
        ssm (SessionStateManager): The session state manager to access DHF data.
    """
    st.header("5. Design Outputs")
    st.markdown("""
    *As per 21 CFR 820.30(d).*

    Design outputs are the tangible results of the design process, such as drawings, specifications,
    and manufacturing procedures. For this combination product, they must also address drug-device
    interaction requirements. **Crucially, each output must be traceable to a design input.**
    """)
    st.info("Changes made here are saved automatically. Every output must be linked to an input requirement.", icon="ℹ️")

    try:
        # --- 1. Load Data and Prepare Traceability Links ---
        outputs_data: List[Dict[str, Any]] = ssm.get_data("design_outputs", "documents")
        inputs_data: List[Dict[str, Any]] = ssm.get_data("design_inputs", "requirements")
        logger.info(f"Loaded {len(outputs_data)} design output records and {len(inputs_data)} input records.")

        if not inputs_data:
            st.warning(
                "⚠️ No Design Inputs found. Please add requirements in the '4. Design Inputs' section before creating outputs.",
                icon="❗"
            )
            req_options: List[str] = []
            req_map: Dict[str, str] = {}
        else:
            # UX Enhancement: Show "ID: Description" in the dropdown for clarity.
            req_options = [
                f"{req.get('id', '')}: {req.get('description', '')[:50]}..."
                if len(req.get('description', '')) > 50 else f"{req.get('id', '')}: {req.get('description', '')}"
                for req in inputs_data
            ]
            # Create a mapping from the descriptive string back to the raw ID for saving.
            req_map = {option: req.get('id', '') for option, req in zip(req_options, inputs_data)}
            logger.debug("Created descriptive requirement options for dropdown.")

        # --- 2. Display Data Editor ---
        st.subheader("Output Documents & Specifications")
        st.markdown("List all design outputs (e.g., drawings, specs, code) and link each one to a design input requirement.")

        outputs_df = pd.DataFrame(outputs_data)

        # Create a reverse map to convert stored IDs to the descriptive format for display in the editor.
        reverse_req_map = {v: k for k, v in req_map.items()}
        if 'linked_input_id' in outputs_df.columns:
            outputs_df['linked_input_descriptive'] = outputs_df['linked_input_id'].map(reverse_req_map)
        else:
             # Ensure the column exists even if there's no data
            outputs_df['linked_input_descriptive'] = pd.Series(dtype=str)

        edited_df = st.data_editor(
            outputs_df,
            num_rows="dynamic",
            use_container_width=True,
            key="design_outputs_editor",
            column_config={
                "id": st.column_config.TextColumn(
                    "Output ID",
                    help="Unique identifier for the output (e.g., DWG-101, SPEC-002)",
                    required=True
                ),
                "title": st.column_config.TextColumn(
                    "Output Title/Description",
                    width="large",
                    required=True
                ),
                "linked_input_descriptive": st.column_config.SelectboxColumn(
                    "Traces to Input Requirement",
                    help="Select the Design Input this output satisfies. This is a required compliance link.",
                    options=req_options,
                    required=True
                ),
                # Hide the raw ID column and other irrelevant columns from the user in this view.
                "linked_input_id": None,
                "phase": None,
                "status": None,
            },
            hide_index=True
        )

        # --- 3. Process and Persist Data ---
        # Convert the user-friendly descriptive selection back to the raw ID for storage.
        if 'linked_input_descriptive' in edited_df.columns:
            valid_rows = edited_df['linked_input_descriptive'].notna()
            edited_df.loc[valid_rows, 'linked_input_id'] = edited_df.loc[valid_rows, 'linked_input_descriptive'].map(req_map)

        # Drop the temporary descriptive column before saving
        if 'linked_input_descriptive' in edited_df.columns:
            edited_df.drop(columns=['linked_input_descriptive'], inplace=True)

        updated_records = edited_df.to_dict('records')

        if updated_records != outputs_data:
            ssm.update_data(updated_records, "design_outputs", "documents")
            logger.info("Design outputs data updated in session state.")
            st.toast("Design outputs saved!", icon="✅")

    except Exception as e:
        st.error("An error occurred while displaying the Design Outputs section. The data may be malformed.")
        logger.error(f"Failed to render design outputs: {e}", exc_info=True)
