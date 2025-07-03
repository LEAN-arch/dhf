# File: dhf_dashboard/dhf_sections/design_outputs.py

import streamlit as st
import pandas as pd
from ..utils.session_state_manager import SessionStateManager

def render_design_outputs(ssm: SessionStateManager):
    """
    Renders the Design Outputs section. This section documents all the tangible
    outputs of the design process and ensures they trace to a design input.
    """
    st.header("5. Design Outputs")
    st.markdown("""
    *As per 21 CFR 820.30(d).*

    Design outputs are the tangible results of the design process, such as drawings, specifications,
    and manufacturing procedures. For this combination product, they must also address drug-device
    interaction requirements. **Crucially, each output must be traceable to a design input.**
    """)
    st.info("Changes made here are saved automatically. Every output must be linked to an input requirement.", icon="ℹ️")


    outputs_data = ssm.get_data("design_outputs", "documents")
    inputs_data = ssm.get_data("design_inputs", "requirements")

    # --- SME Enhancement: Live and descriptive traceability link ---
    if not inputs_data:
        st.warning("⚠️ No Design Inputs found. Please add requirements in the '4. Design Inputs' section before creating outputs.", icon="❗")
        req_options = []
        req_map = {}
    else:
        # UX Enhancement: Show ID and description in dropdown for clarity
        req_options = [f"{req.get('id', '')}: {req.get('description', '')}" for req in inputs_data]
        # Create a mapping from the descriptive string back to the ID for saving
        req_map = {f"{req.get('id', '')}: {req.get('description', '')}": req.get('id') for req in inputs_data}


    st.subheader("Output Documents & Specifications")
    st.markdown("List all design outputs (e.g., drawings, specs, code) and link them to a design input requirement.")

    outputs_df = pd.DataFrame(outputs_data)
    # Convert saved IDs to the descriptive format for display in the editor
    reverse_req_map = {v: k for k, v in req_map.items()}
    if 'linked_input_id' in outputs_df.columns:
        outputs_df['linked_input_descriptive'] = outputs_df['linked_input_id'].map(reverse_req_map)


    edited_df = st.data_editor(
        outputs_df,
        num_rows="dynamic",
        use_container_width=True,
        key="design_outputs_editor",
        column_config={
            "id": st.column_config.TextColumn("Output ID", help="Unique identifier for the output (e.g., DWG-101, SPEC-002)", required=True),
            "title": st.column_config.TextColumn("Output Title/Description", width="large", required=True),
            "file": st.column_config.TextColumn("File Name / Link", help="e.g., 'CAD-Assembly-Final.zip' or a link to a document repository"),
            "linked_input_descriptive": st.column_config.SelectboxColumn(
                "Traces to Input Requirement",
                help="Select the Design Input this output satisfies. This is a required link.",
                options=req_options,
                required=True # Design Control SME: This enforces traceability
            ),
            # Hide the raw ID column from the user
            "linked_input_id": None,
        },
    )

    # Convert the user-friendly descriptive selection back to the raw ID for storage
    if 'linked_input_descriptive' in edited_df.columns:
        edited_df['linked_input_id'] = edited_df['linked_input_descriptive'].map(req_map)

    # Persist the updated data back to the session state
    ssm.update_data(edited_df.to_dict('records'), "design_outputs", "documents")
