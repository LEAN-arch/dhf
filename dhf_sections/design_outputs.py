# File: dhf_dashboard/dhf_sections/design_outputs.py

import streamlit as st
import pandas as pd
from utils.session_state_manager import SessionStateManager

def render_design_outputs(ssm: SessionStateManager):
    """
    Renders the Design Outputs section.
    """
    st.header("4. Design Outputs")
    st.markdown("""
    *As per 21 CFR 820.30(d).*

    Design outputs are the tangible results of the design process. For this smart-pill, they include not only
    device drawings and software code, but also specifications for drug-device interaction, such as:
    - Material specifications (biocompatibility, inertness to the drug)
    - Drug release profile specifications
    - Manufacturing procedures that address both device assembly and drug handling.
    
    **Each output must be traceable to a design input.**
    """)

    outputs_data = ssm.get_section_data("design_outputs")
    inputs_data = ssm.get_section_data("design_inputs")

    req_ids = [""] + [req.get('id', '') for req in inputs_data.get("requirements", [])]

    outputs_df = pd.DataFrame(outputs_data.get("documents", []))
    
    edited_df = st.data_editor(
        outputs_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "id": st.column_config.TextColumn("Output ID", required=True),
            "title": st.column_config.TextColumn("Output Title/Description", required=True),
            "file": st.column_config.TextColumn("File Name / Link"),
            "linked_input_id": st.column_config.SelectboxColumn(
                "Trace to Input ID",
                options=req_ids,
                required=True
            ),
        },
        key="design_outputs_editor"
    )
    
    outputs_data["documents"] = edited_df.to_dict('records')
    ssm.update_section_data("design_outputs", outputs_data)

    if st.button("Save Design Outputs Section"):
        st.success("Design Outputs data saved successfully!")
