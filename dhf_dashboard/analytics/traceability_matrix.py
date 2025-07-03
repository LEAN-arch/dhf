# File: dhf_dashboard/analytics/traceability_matrix.py

import streamlit as st
import pandas as pd

def render_traceability_matrix(ssm):
    """
    Generates and displays a full traceability matrix, linking requirements from cradle to grave.
    This is a critical view for ensuring design control compliance.
    """
    st.header("🔬 Live Traceability Matrix")
    st.info("""
    This matrix provides end-to-end traceability from User Needs and Design Inputs to Design Outputs, Verification, and Validation.
    - ✅: A direct link exists. Hover over the checkmark to see the linked item ID(s).
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
    trace_matrix = inputs[['id', 'description']].copy()
    trace_matrix.set_index('id', inplace=True)

    # --- SME Enhancement: Simplified and robust mapping logic ---

    # 3. Map Design Outputs to Inputs
    if not outputs.empty:
        output_map = outputs.groupby('linked_input_id')['id'].apply(lambda ids: f"✅ ({', '.join(ids)})")
        trace_matrix['Output'] = trace_matrix.index.map(output_map)
    trace_matrix['Output'] = trace_matrix.get('Output', pd.Series(dtype=str)).fillna("❌")

    # 4. Map Verification to Inputs (Multi-step: Verification -> Output -> Input)
    if not verifications.empty and not outputs.empty:
        # Merge verifications with outputs to link them directly to an input ID
        ver_to_out = pd.merge(
            verifications[['id', 'output_verified']],
            outputs[['id', 'linked_input_id']],
            left_on='output_verified',
            right_on='id',
            suffixes=('_ver', '_out')
        )
        ver_map = ver_to_out.groupby('linked_input_id')['id_ver'].apply(lambda ids: f"✅ ({', '.join(ids)})")
        trace_matrix['Verification'] = trace_matrix.index.map(ver_map)
    trace_matrix['Verification'] = trace_matrix.get('Verification', pd.Series(dtype=str)).fillna("❌")

    # 5. Map Validation to User Needs
    if not validations.empty:
        # Filter for User Needs only for this mapping
        is_user_need = inputs['source_type'] == 'User Need'
        user_need_ids = inputs[is_user_need]['id']

        val_map = validations.groupby('user_need_validated')['id'].apply(lambda ids: f"✅ ({', '.join(ids)})")
        trace_matrix['Validation'] = trace_matrix.index.map(val_map)
    # For non-User-Need rows, validation is not applicable. For User Needs without validation, it's a gap.
    trace_matrix['Validation'] = trace_matrix.get('Validation', pd.Series(dtype=str)).fillna("❌")


    # 6. Style the matrix for visual clarity
    def style_cell(cell_value):
        color = '#d62728' if '❌' in str(cell_value) else '#2ca02c' if '✅' in str(cell_value) else 'inherit'
        return f'color: {color}; font-weight: bold; text-align: center;'

    # --- UX Enhancement: Use st.column_config to add tooltips ---
    st.dataframe(
        trace_matrix.reset_index(), # Reset index to display the 'id' column
        use_container_width=True,
        column_config={
            "id": st.column_config.TextColumn("Requirement ID", width="small"),
            "description": st.column_config.TextColumn("Requirement Description", width="large"),
            "Output": st.column_config.TextColumn("Trace to Output", help="Does a Design Output satisfy this input?"),
            "Verification": st.column_config.TextColumn("Trace to Verification", help="Is there a test verifying the output that satisfies this input?"),
            "Validation": st.column_config.TextColumn("Trace to Validation", help="Is there a study validating this User Need? (N/A for other reqs)"),
        },
        # Apply styling after configuring columns
    )

    # Apply CSS styling for alignment and color via a separate markdown call
    st.markdown(f"""
        <style>
            /* Center the traceability columns */
            div[data-testid="stDataFrame"] table td:nth-child(n+3) {{
                text-align: center;
                font-weight: bold;
            }}
            /* Color the cells based on content */
            {trace_matrix.style.map(style_cell, subset=['Output', 'Verification', 'Validation']).to_html()}
        </style>
    """, unsafe_allow_html=True)


    # 7. Add an export button for compliance documentation
    csv_export_df = trace_matrix.copy()
    for col in ['Output', 'Verification', 'Validation']:
        csv_export_df[col] = csv_export_df[col].str.replace("✅", "Linked:").str.replace("❌", "Missing")

    csv = csv_export_df.to_csv().encode('utf-8')
    st.download_button(
        "📥 Export Matrix to CSV",
        csv,
        "traceability_matrix.csv",
        "text/csv",
        key='export_trace_matrix'
    )
