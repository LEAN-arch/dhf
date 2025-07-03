# File: dhf_dashboard/analytics/traceability_matrix.py

import streamlit as st
import pandas as pd

def render_traceability_matrix(ssm):
    """Generates and displays a full traceability matrix."""
    st.header("Live Traceability Matrix")
    st.info("""
    This matrix provides end-to-end traceability from User Needs and Design Inputs to Design Outputs, Verification, and Validation.
    - ✅: A direct link exists.
    - ❌: A link is missing, representing a potential compliance gap.
    """)

    # 1. Gather all relevant data
    inputs = pd.DataFrame(ssm.get_data("design_inputs", "requirements"))
    outputs = pd.DataFrame(ssm.get_data("design_outputs", "documents"))
    verifications = pd.DataFrame(ssm.get_data("design_verification", "tests"))
    validations = pd.DataFrame(ssm.get_data("design_validation", "studies"))

    if inputs.empty:
        st.warning("No Design Inputs found. Please add requirements in the 'DHF Section Details' tab.")
        return

    # 2. Create the base matrix from inputs
    trace_matrix = inputs[['id', 'description', 'source_type']].copy()
    trace_matrix.set_index('id', inplace=True)

    # 3. Map Outputs to Inputs
    if not outputs.empty and 'linked_input_id' in outputs.columns and 'id' in outputs.columns:
        # --- FIX IS HERE ---
        # Simplified the groupby and separated the logic into a robust two-step process.
        
        # Step 3.1: Create a map of Input ID -> list of Output IDs
        output_map = outputs.groupby('linked_input_id')['id'].apply(lambda x: ', '.join(x.astype(str)))
        
        # Step 3.2: Map the values to the matrix and fill missing links.
        trace_matrix['Design Output'] = trace_matrix.index.map(output_map)
        trace_matrix['Design Output'].fillna("❌", inplace=True)
        # --- END OF FIX ---
    else:
        trace_matrix['Design Output'] = "❌"

    # 4. Map Verification to Outputs (and by extension, to Inputs)
    if not verifications.empty and not outputs.empty and 'output_verified' in verifications.columns and 'linked_input_id' in outputs.columns:
        ver_map = verifications.groupby('output_verified')['id'].apply(list).apply(lambda x: ', '.join(x))
        output_to_input_map = outputs.set_index('id')['linked_input_id']
        input_to_ver_map = {}
        for output_id, ver_ids in ver_map.items():
            if output_id in output_to_input_map:
                input_id = output_to_input_map[output_id]
                if input_id not in input_to_ver_map:
                    input_to_ver_map[input_id] = []
                input_to_ver_map[input_id].append(ver_ids)
        trace_matrix['Verification'] = pd.Series(input_to_ver_map).apply(lambda x: ', '.join(x)).fillna("❌")
    else:
        trace_matrix['Verification'] = "❌"
        
    # 5. Map Validation to User Needs
    if not validations.empty and 'user_need_validated' in validations.columns:
        val_map = validations.groupby('user_need_validated')['id'].apply(list).apply(lambda x: ', '.join(x))
        is_user_need = trace_matrix['source_type'] == 'User Need'
        trace_matrix.loc[is_user_need, 'Validation'] = trace_matrix[is_user_need].index.map(val_map)
        trace_matrix['Validation'].fillna("❌", inplace=True)
    else:
        trace_matrix['Validation'] = "❌"

    # 6. Style the matrix for visual clarity
    def style_matrix(cell):
        return 'color: #d62728; font-weight: bold;' if cell == "❌" else 'color: #2ca02c;'

    st.dataframe(trace_matrix.style.map(style_matrix, subset=['Design Output', 'Verification', 'Validation']), use_container_width=True)
    
    # Add an export button
    csv = trace_matrix.to_csv().encode('utf-8')
    st.download_button("Export Matrix to CSV", csv, "traceability_matrix.csv", "text/csv")
