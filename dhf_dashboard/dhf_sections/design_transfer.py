# --- Definitive, Corrected, and Unabridged Optimized Version ---
"""
Module for rendering the Design Transfer section of the DHF Explorer.

This component provides an interface to view and manage activities related to
transferring the device design from R&D to manufacturing, ensuring the product
can be reliably and consistently produced.
"""

# --- Standard Library Imports ---
import logging

# --- Third-party Imports ---
import pandas as pd
import streamlit as st

# --- Local Application Imports ---
from dhf_dashboard.utils.session_state_manager import SessionStateManager

# --- Setup Logging ---
logger = logging.getLogger(__name__)

def render_design_transfer(ssm: SessionStateManager):
    """
    Renders an editable table of design transfer activities.
    
    This function displays key Design Transfer tasks, such as process validation
    (IQ/OQ/PQ), and allows for real-time editing of their status and details.
    """
    st.header("9. Design Transfer")
    st.markdown("This section documents the activities that ensure the developed device design is correctly translated into production specifications. This is a critical bridge between R&D and Manufacturing.")
    st.info("💡 **Best Practice:** Design Transfer is not a single event but a continuous process. It should begin early, with Manufacturing Engineering involved in Design Reviews to ensure 'Design for Manufacturability' (DFM).", icon="💡")
    st.divider()

    try:
        activities_data = ssm.get_data("design_transfer", "activities")
        if not activities_data:
            st.warning("No design transfer activities have been recorded yet.")
            # Provide a way to add the first activity if the list is empty
            if st.button("Add First Design Transfer Activity"):
                # Define a default new activity
                new_activity = {
                    "activity": "New Activity",
                    "responsible_party": "Mfg. Eng.",
                    "status": "Not Started",
                    "completion_date": None,
                    "evidence_link": ""
                }
                ssm.update_data([new_activity], "design_transfer", "activities")
                st.rerun()
            return

        activities_df = pd.DataFrame(activities_data)
        
        # Ensure data consistency for the editor
        activities_df['completion_date'] = pd.to_datetime(activities_df['completion_date'], errors='coerce')
        
        # Define valid options for dropdowns to ensure data integrity
        status_options = ["Not Started", "In Progress", "Completed", "Blocked"]
        owner_options = ["Mfg. Eng.", "Quality Eng.", "R&D", "Validation Team"]
        
        # Sort to bring active items to the top
        activities_df['status'] = pd.Categorical(activities_df['status'], categories=status_options, ordered=True)
        activities_df = activities_df.sort_values(by=['status', 'activity'])

        st.subheader("Process Validation & Transfer Activities")
        
        # Use a unique key for the data editor
        editor_key = "design_transfer_editor"
        
        edited_df = st.data_editor(
            activities_df,
            key=editor_key,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "activity": st.column_config.TextColumn("Activity / Deliverable", width="large", required=True),
                "responsible_party": st.column_config.SelectboxColumn(
                    "Responsible Party",
                    options=owner_options,
                    required=True
                ),
                "status": st.column_config.SelectboxColumn(
                    "Status",
                    options=status_options,
                    required=True
                ),
                "completion_date": st.column_config.DateColumn(
                    "Completion Date",
                    format="YYYY-MM-DD"
                ),
                "evidence_link": st.column_config.LinkColumn(
                    "Evidence Link",
                    help="Link to the report or document in the QMS (e.g., IQ-RPT-01.pdf)",
                    display_text="View Document"
                )
            },
            hide_index=True,
        )

        # Check if the data has been changed by the user
        if not activities_df.equals(edited_df):
            # Convert datetime objects back to strings for JSON compatibility
            df_to_save = edited_df.copy()
            # Handle the date column carefully to allow for empty dates (None)
            df_to_save['completion_date'] = df_to_save['completion_date'].dt.strftime('%Y-%m-%d').replace({pd.NaT: None})
            
            # Update the session state
            ssm.update_data(df_to_save.to_dict('records'), "design_transfer", "activities")
            st.toast("Design Transfer activities updated!", icon="✅")
            st.rerun()

    except Exception as e:
        st.error("An error occurred while displaying the Design Transfer section. The data may be malformed.")
        logger.error(f"Error in render_design_transfer: {e}", exc_info=True)
