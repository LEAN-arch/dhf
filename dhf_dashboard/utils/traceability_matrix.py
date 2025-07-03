# File: dhf_dashboard/analytics/traceability_matrix.py

import streamlit as st
import pandas as pd

def render_traceability_matrix(ssm):
    """
    Generates and displays a full traceability matrix, linking requirements from cradle to grave.
    This is a critical view for ensuring design control compliance.
    """
    st.header("Live Traceability Matrix")
    st.info("""
    This matrix provides end-to-end traceability from User Needs and Design Inputs to Design Outputs, Verification, and Validation.
    - ✅: A direct link exists between the items.
    - ❌: A link is missing, representing a potential compliance gap that must be addressed.
    """)

    # 1. Gather all relevant data from the session state manager
    inputs = pd.DataFrame(ssm.get_data("design_inputs", "requirements"))
    outputs = pd.DataFrame(ssm.get_data("design_outputs", "documents"))
    verifications = pd.DataFrame(ssm.get_data("design_verification", "tests"))
    validations = pd.DataFrame(ssm.get_data("design_validation", "studies"))

    if inputs.empty:
        st.warning("No Design Inputs found. Please add requirements in the 'DHF Section Details' tab to build the matrix.")
        return

    # 2. Create the base matrix from inputs, which is the spine of the DHF
    trace_matrix = inputs[['id', 'description', 'source_type']].copy()
    trace_matrix.set_index('id', inplace=True)

    # 3. Map Design Outputs to Inputs
    if not outputs.empty and 'linked_input_id' in outputs.columns and 'id' in outputs.columns:
        output_map = outputs.groupby('linked_input_id')['id'].apply(lambda ids: '✅ (' + ', '.join(ids.astype(str)) + ')')
        trace_matrix['Design Output'] = trace_matrix.index.map(output_map)
    trace_matrix['Design Output'] = trace_matrix.get('Design Output', pd.Series(index=trace_matrix.index)).fillna("❌")

    # 4. Map Verification to Inputs (a multi-step process)
    if not verifications.empty and not outputs.empty and 'output_verified' in verifications.columns:
        # Step A: Map verification tests to the output IDs they verify
        ver_map = verifications.groupby('output_verified')['id'].apply(lambda ids: ', '.join(ids.astype(str)))
        
        # Step B: Create a map from output ID back to its original input ID
        output_to_input_map = outputs.set_index('id')['linked_input_id']
        
        # Step C: Use the two maps to link verifications all the way back to inputs
        input_to_ver_map = {}
        for output_id, ver_ids in ver_map.items():
            if output_id in output_to_input_map:
                input_id = output_to_input_map[output_id]
                if input_id not in input_to_ver_map:
                    input_to_ver_map[input_id] = []
                input_to_ver_map[input_id].append(ver_ids)
        
        # Step D: Apply the final map to the trace matrix
        final_ver_map = {k: '✅ (' + ', '.join(v) + ')' for k, v in input_to_ver_map.items()}
        trace_matrix['Design Verification'] = trace_matrix.index.map(final_ver_map)
    trace_matrix['Design Verification'] = trace_matrix.get('Design Verification', pd.Series(index=trace_matrix.index)).fillna("❌")
        
    # 5. Map Validation to User Needs (the highest level of testing)
    if not validations.empty and 'user_need_validated' in validations.columns:
        val_map = validations.groupby('user_need_validated')['id'].apply(lambda ids: '✅ (' + ', '.join(ids.astype(str)) + ')')
        # Only apply this map to rows that are User Needs
        is_user_need = trace_matrix['source_type'] == 'User Need'
        trace_matrix.loc[is_user_need, 'Design Validation'] = trace_matrix[is_user_need].index.map(val_map)
    trace_matrix['Design Validation'] = trace_matrix.get('Design Validation', pd.Series(index=trace_matrix.index)).fillna("❌")

    # 6. Style the matrix for visual clarity
    def style_matrix(cell_value):
        return 'color: #d62728; font-weight: bold;' if '❌' in str(cell_value) else 'color: #2ca02c;'

    # Display the final, styled DataFrame
    st.dataframe(
        trace_matrix.style.map(style_matrix, subset=['Design Output', 'Design Verification', 'Design Validation']), 
        use_container_width=True
    )
    
    # 7. Add an export button for compliance documentation
    csv = trace_matrix.to_csv().encode('utf-8')
    st.download_button("Export Matrix to CSV", csv, "traceability_matrix.csv", "text/csv", key='export_trace_matrix')
