# File: dhf_dashboard/dhf_sections/design_reviews.py

import streamlit as st
import pandas as pd
from utils.session_state_manager import SessionStateManager
import datetime

def render_design_reviews(ssm: SessionStateManager):
    """
    Renders the Design Reviews section.
    """
    st.header("5. Design Reviews")
    st.markdown("""
    *As per 21 CFR 820.30(e).*
    
    Formal, documented reviews of the design results. For a combination product, attendees
    must include individuals with expertise in both the device and drug constituent parts.
    The review must also assess the status of risk management activities.
    """)
    
    reviews_data = ssm.get_section_data("design_reviews")
    
    st.info("Record each formal design review. Ensure attendees represent all relevant functions (device, drug, quality, regulatory).")

    reviews_df = pd.DataFrame(reviews_data.get("reviews", []))

    edited_df = st.data_editor(
        reviews_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "date": st.column_config.DateColumn("Review Date", required=True, default=datetime.date.today()),
            "attendees": st.column_config.TextColumn("Attendees", help="List names and roles (e.g., J. Doe - Device Eng, A. Smith - Pharma)", required=True),
            "notes": st.column_config.TextColumn("Minutes / Notes Summary (incl. risk review)"),
            "action_items": st.column_config.TextColumn("Action Items (ID, Description, Owner)"),
        },
        key="design_reviews_editor"
    )

    reviews_data["reviews"] = edited_df.to_dict('records')
    ssm.update_section_data("design_reviews", reviews_data)

    if st.button("Save Design Reviews Section"):
        st.success("Design Reviews data saved successfully!")
