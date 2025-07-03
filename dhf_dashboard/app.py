# File: dhf_dashboard/app.py
# SME Note: This is the definitive, all-inclusive, and untruncated version. It includes the robust
# path correction block, the professional-grade QE dashboard, all educational content in its full
# unabridged form, and all bug fixes and feature enhancements, including the AI & Statistics hub.

import sys
import os
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from scipy import stats

# --- ROBUST PATH CORRECTION BLOCK ---
try:
    current_file_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file_path)
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except Exception as e:
    st.error(f"Error adjusting system path: {e}")
# --- END OF PATH CORRECTION BLOCK ---


# --- MODULAR IMPORTS ---
from dhf_dashboard.utils.session_state_manager import SessionStateManager
from dhf_dashboard.utils.critical_path_utils import find_critical_path
from dhf_dashboard.utils.plot_utils import create_progress_donut, create_action_item_chart
from dhf_dashboard.analytics.traceability_matrix import render_traceability_matrix
from dhf_dashboard.analytics.action_item_tracker import render_action_item_tracker
from dhf_dashboard.dhf_sections import (
    design_plan, design_risk_management, human_factors, design_inputs,
    design_outputs, design_reviews, design_verification, design_validation,
    design_transfer, design_changes
)

# --- DASHBOARD COMPONENT FUNCTIONS ---

def render_dhr_completeness_panel(ssm, tasks_df):
    st.subheader("1. DHF Completeness & Gate Readiness")
    st.markdown("Monitor the flow of Design Controls from inputs to outputs, including cross-functional sign-offs and DHF document status.")
    
    tasks_raw = ssm.get_data("project_management", "tasks")
    docs = pd.DataFrame(ssm.get_data("design_outputs", "documents"))

    for task in tasks_raw:
        with st.expander(f"**{task.get('name', 'N/A')}** (Status: {task.get('status', 'N/A')} - {task.get('completion_pct', 0)}%)"):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown("**Associated DHF Documents:**")
                phase_docs = docs[docs['phase'] == task.get('name')]
                if not phase_docs.empty:
                    st.dataframe(phase_docs[['id', 'title', 'status']], use_container_width=True, hide_index=True)
                else:
                    st.caption("No documents for this phase yet.")
            with col2:
                st.markdown("**Cross-Functional Sign-offs:**")
                sign_offs = task.get('sign_offs', {})
                if isinstance(sign_offs, dict):
                    for team, status in sign_offs.items():
                        color = "green" if status == "✅" else "orange" if status == "In Progress" else "grey"
                        st.markdown(f"- **{team}:** <span style='color:{color};'>{status}</span>", unsafe_allow_html=True)
                else:
                    st.caption("Sign-off data is not in the correct format.")
    
    st.markdown("---")
    st.markdown("##### Project Phase Timeline (Gantt Chart)")
    if not tasks_df.empty:
        gantt_fig = go.Figure(px.timeline(
            tasks_df, x_start="start_date", x_end="end_date", y="name",
            color="color", color_discrete_map="identity"
        ))
        gantt_fig.update_traces(
            text=tasks_df['display_text'], textposition='inside', insidetextanchor='middle',
            marker_line_color=tasks_df['line_color'], marker_line_width=tasks_df['line_width']
        )
        gantt_fig.update_layout(
            showlegend=False, title_x=0.5, xaxis_title="Date", yaxis_title="DHF Phase", height=400,
            yaxis_categoryorder='array', yaxis_categoryarray=tasks_df.sort_values("start_date", ascending=False)["name"].tolist()
        )
        st.plotly_chart(gantt_fig, use_container_width=True)
        legend_html = """
        <div style="padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-top: 15px; font-size: 0.9em;">
        <b>Legend:</b>
        <ul style="list-style-type: none; padding-left: 0; margin-top: 5px; column-count: 2;">
            <li style="margin-bottom: 5px;"><span style="display:inline-block; width:15px; height:15px; background-color:#2ca02c; margin-right: 8px; vertical-align: middle;"></span> Completed</li>
            <li style="margin-bottom: 5px;"><span style="display:inline-block; width:15px; height:15px; background-color:#1f77b4; margin-right: 8px; vertical-align: middle;"></span> In Progress</li>
            <li style="margin-bottom: 5px;"><span style="display:inline-block; width:15px; height:15px; background-color:#d62728; margin-right: 8px; vertical-align: middle;"></span> At Risk</li>
            <li style="margin-bottom: 5px;"><span style="display:inline-block; width:15px; height:15px; background-color:#7f7f7f; margin-right: 8px; vertical-align: middle;"></span> Not Started</li>
            <li style="margin-bottom: 5px;"><span style="display:inline-block; width:11px; height:11px; border: 2px solid red; margin-right: 8px; vertical-align: middle;"></span> Task on Critical Path</li>
        </ul></div>
        """
        st.markdown(legend_html, unsafe_allow_html=True)

def render_risk_and_fmea_dashboard(ssm):
    st.subheader("2. DHF Risk Artifacts (ISO 14971, FMEA)")
    st.markdown("Analyze the project's risk profile via the Risk Mitigation Flow and Failure Mode and Effects Analysis (FMEA) highlights.")
    
    risk_tabs = st.tabs(["Risk Mitigation Flow (System Level)", "dFMEA Highlights", "pFMEA Highlights"])
    
    with risk_tabs[0]:
        hazards_data = ssm.get_data("risk_management_file", "hazards")
        if not hazards_data:
            st.warning("No hazard analysis data available.")
        else:
            df = pd.DataFrame(hazards_data)
            risk_config = {
                'levels': { (1,1):'Low', (1,2):'Low', (1,3):'Medium', (1,4):'Medium', (1,5):'High', (2,1):'Low', (2,2):'Low', (2,3):'Medium', (2,4):'High', (2,5):'High', (3,1):'Medium', (3,2):'Medium', (3,3):'High', (3,4):'High', (3,5):'Unacceptable', (4,1):'Medium', (4,2):'High', (4,3):'High', (4,4):'Unacceptable', (4,5):'Unacceptable', (5,1):'High', (5,2):'High', (5,3):'Unacceptable', (5,4):'Unacceptable', (5,5):'Unacceptable' },
                'colors': { 'Unacceptable': 'rgba(139, 0, 0, 0.8)', 'High': 'rgba(214, 39, 40, 0.8)', 'Medium': 'rgba(255, 127, 14, 0.8)', 'Low': 'rgba(44, 160, 44, 0.8)' }
            }
            def get_level(s, o): return risk_config['levels'].get((s, o), 'High')
            df['initial_level'] = df.apply(lambda x: get_level(x['initial_S'], x['initial_O']), axis=1)
            df['final_level'] = df.apply(lambda x: get_level(x['final_S'], x['final_O']), axis=1)
            
            all_nodes = [f"Initial {level}" for level in ['Unacceptable', 'High', 'Medium', 'Low']] + [f"Residual {level}" for level in ['Unacceptable', 'High', 'Medium', 'Low']]
            node_map = {name: i for i, name in enumerate(all_nodes)}
            links = df.groupby(['initial_level', 'final_level', 'hazard_id']).size().reset_index(name='count')
            sankey_data = links.groupby(['initial_level', 'final_level']).agg(count=('count', 'sum'), hazards=('hazard_id', lambda x: ', '.join(x))).reset_index()
            source_nodes = [node_map.get(f"Initial {row['initial_level']}") for _, row in sankey_data.iterrows()]
            target_nodes = [node_map.get(f"Residual {row['final_level']}") for _, row in sankey_data.iterrows()]
            values = [row['count'] for _, row in sankey_data.iterrows()]
            link_colors = [risk_config['colors'][row['final_level']] for _, row in sankey_data.iterrows()]
            hover_text = [f"<b>{row['count']} risk(s)</b> moved from {row['initial_level']} to {row['final_level']}:<br>{row['hazards']}" for _, row in sankey_data.iterrows()]
            
            fig = go.Figure(data=[go.Sankey(
                node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5), label=all_nodes, color=[risk_config['colors'][name.split(' ')[1]] for name in all_nodes]),
                link=dict(source=source_nodes, target=target_nodes, value=values, color=link_colors, customdata=hover_text, hovertemplate='%{customdata}<extra></extra>')
            )])
            fig.update_layout(title_text="Risk Mitigation Flow: Initial State vs. Residual State", font_size=12, height=500)
            st.plotly_chart(fig, use_container_width=True)

    def render_fmea_highlights(fmea_data, title):
        if not fmea_data:
            st.warning(f"No {title} data available.")
            return
        df = pd.DataFrame(fmea_data)
        df['RPN'] = df['S'] * df['O'] * df['D']
        top_items = df.sort_values('RPN', ascending=False).head(5)
        
        fig = px.bar(top_items, x='RPN', y='failure_mode', orientation='h', title=f"Top 5 {title} Items by RPN", labels={'failure_mode': 'Failure Mode'}, text='RPN')
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

    with risk_tabs[1]:
        render_fmea_highlights(ssm.get_data("risk_management_file", "dfmea"), "dFMEA")
    with risk_tabs[2]:
        render_fmea_highlights(ssm.get_data("risk_management_file", "pfmea"), "pFMEA")

def render_qbd_and_cgmp_panel(ssm):
    st.subheader("3. DHF to Manufacturing Readiness")
    st.markdown("This section tracks key activities that bridge the design with a robust, manufacturable product, including Quality by Design (QbD) and CGMP compliance.")
    qbd_tabs = st.tabs(["Quality by Design (QbD) Linkages", "CGMP Readiness"])
    with qbd_tabs[0]:
        qbd_elements = ssm.get_data("quality_by_design", "elements")
        if not qbd_elements:
            st.warning("No Quality by Design elements have been defined.")
        else:
            for element in qbd_elements:
                with st.expander(f"**CQA:** {element.get('cqa', 'N/A')} (links to Requirement: {element.get('links_to_req', 'N/A')})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Critical Material Attributes (CMAs)**")
                        for cma in element.get('cm_attributes', []):
                            st.markdown(f"- {cma}")
                    with col2:
                        st.markdown("**Critical Process Parameters (CPPs)**")
                        for cpp in element.get('cp_parameters', []):
                            st.markdown(f"- {cpp}")
        st.info("💡 FTR (First-Time-Right) initiatives are driven by deeply understanding and controlling the CMAs and CPPs that affect the product's CQAs.", icon="💡")
    with qbd_tabs[1]:
        cgmp_data = ssm.get_data("quality_system", "cgmp_compliance")
        if not cgmp_data:
            st.warning("No CGMP compliance data available.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Pilot Batch Record Review**")
                brr = cgmp_data.get('batch_record_review', {})
                total, passed = brr.get('total', 0), brr.get('passed', 0)
                pass_rate = (passed / total) * 100 if total > 0 else 0
                st.metric(f"Batch Pass Rate: {pass_rate:.1f}%", f"{passed}/{total} Passed")
            with col2:
                st.markdown("**Drug-Device Stability Studies**")
                stability = pd.DataFrame(cgmp_data.get('stability_studies', []))
                if not stability.empty:
                    st.dataframe(stability, use_container_width=True, hide_index=True)
        st.info("💡 For combination products, successful Design Transfer is contingent on passing stability studies and demonstrating a capable manufacturing process under CGMP.", icon="💡")

def render_audit_and_improvement_dashboard(ssm):
    st.subheader("4. Audit & Continuous Improvement Readiness")
    st.markdown("A high-level assessment of QMS health and process efficiency to gauge readiness for audits and track improvement initiatives.")
    audit_tabs = st.tabs(["Audit Readiness Scorecard", "FTR & COPQ Dashboard"])
    with audit_tabs[0]:
        docs = pd.DataFrame(ssm.get_data("design_outputs", "documents"))
        approved_docs = docs[docs['status'] == 'Approved']
        doc_readiness = (len(approved_docs) / len(docs)) * 100 if not docs.empty else 0

        capas = pd.DataFrame(ssm.get_data("quality_system", "capa_records"))
        open_capas = len(capas[capas['status'] == 'Open'])

        suppliers = pd.DataFrame(ssm.get_data("quality_system", "supplier_audits"))
        supplier_pass_rate = (len(suppliers[suppliers['status'] == 'Pass']) / len(suppliers)) * 100 if not suppliers.empty else 100

        def get_light(score):
            if score >= 90: return "🟢"
            if score >= 70: return "🟡"
            return "🔴"

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(f"DHF Document Readiness {get_light(doc_readiness)}", f"{doc_readiness:.1f}% Approved")
        with col2:
            st.metric(f"Open CAPAs {get_light(100 - open_capas*20)}", f"{open_capas} Item(s)")
        with col3:
            st.metric(f"Supplier Audit Pass Rate {get_light(supplier_pass_rate)}", f"{supplier_pass_rate:.1f}%")
        st.success("Bonus: Next mock internal audit scheduled for Q4 2025.")
    with audit_tabs[1]:
        improvements = pd.DataFrame(ssm.get_data("quality_system", "continuous_improvement"))
        st.info("This dashboard tracks First-Time-Right (FTR) rates and the associated Cost of Poor Quality (COPQ), demonstrating a commitment to proactive quality.")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**FTR & COPQ Trends**")
            if not improvements.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=improvements['date'], y=improvements['ftr_rate'], name='FTR Rate (%)', yaxis='y1'))
                fig.add_trace(go.Scatter(x=improvements['date'], y=improvements['copq_cost'], name='COPQ ($)', yaxis='y2', line=dict(color='red')))
                fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10), yaxis=dict(title='FTR Rate (%)'), yaxis2=dict(title='COPQ ($)', overlaying='y', side='right'))
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.markdown("**Mocked Statistical Output**")
            st.metric("Process Capability (Cpk)", "1.67", delta="0.34", help="A Cpk > 1.33 indicates a capable process.")
            st.caption("Increased Cpk from process optimization (DOE) directly reduces COPQ.")

# --- PAGE CONFIGURATION AND MAIN LAYOUT ---
st.set_page_config(layout="wide", page_title="DHF Command Center", page_icon="🚀")
ssm = SessionStateManager()

tasks_df_processed = pd.DataFrame(ssm.get_data("project_management", "tasks"))
if not tasks_df_processed.empty:
    tasks_df_processed['start_date'] = pd.to_datetime(tasks_df_processed['start_date'], errors='coerce')
    tasks_df_processed['end_date'] = pd.to_datetime(tasks_df_processed['end_date'], errors='coerce')
    tasks_df_processed.dropna(subset=['start_date', 'end_date'], inplace=True)
    critical_path_ids = find_critical_path(tasks_df_processed.copy())
    status_colors = {"Completed": "#2ca02c", "In Progress": "#1f77b4", "Not Started": "#7f7f7f", "At Risk": "#d62728"}
    tasks_df_processed['color'] = tasks_df_processed['status'].map(status_colors).fillna('#7f7f7f')
    tasks_df_processed['is_critical'] = tasks_df_processed['id'].isin(critical_path_ids)
    tasks_df_processed['line_color'] = tasks_df_processed.apply(lambda r: 'red' if r['is_critical'] else '#FFFFFF', axis=1)
    tasks_df_processed['line_width'] = tasks_df_processed.apply(lambda r: 4 if r['is_critical'] else 0, axis=1)
    tasks_df_processed['display_text'] = tasks_df_processed.apply(lambda r: f"<b>{r['name']}</b> ({r.get('completion_pct', 0)}%)", axis=1)

st.title("🚀 DHF Command Center")
project_name = ssm.get_data("design_plan", "project_name")
st.caption(f"Live monitoring for the **{project_name}** project.")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 **DHF Health Dashboard**", "🗂️ **DHF Sections Explorer**", "🔬 **Advanced Analytics**", "🤖 **AI & Statistical Tools**", "🏛️ **QE & Compliance Guide**"
])

# ==============================================================================
# TAB 1: DHF HEALTH DASHBOARD
# ==============================================================================
with tab1:
    st.header("Project Health At-a-Glance")
    col1, col2, col3 = st.columns(3)
    with col1:
        completion_pct = tasks_df_processed['completion_pct'].mean() if not tasks_df_processed.empty else 0
        st.plotly_chart(create_progress_donut(completion_pct), use_container_width=True)
    with col2:
        st.markdown("#### Overall Risk Profile")
        st.caption("Based on Initial vs. Final RPN")
        hazards_df = pd.DataFrame(ssm.get_data("risk_management_file", "hazards"))
        hazards_df['initial_rpn'] = hazards_df['initial_S'] * hazards_df['initial_O'] * hazards_df['initial_D']
        hazards_df['final_rpn'] = hazards_df['final_S'] * hazards_df['final_O'] * hazards_df['final_D']
        st.metric("Initial Total RPN", f"{hazards_df['initial_rpn'].sum():,}")
        st.metric("Current Residual RPN", f"{hazards_df['final_rpn'].sum():,}", delta=f"{(hazards_df['final_rpn'].sum() - hazards_df['initial_rpn'].sum()):,}")
    with col3:
        reviews = ssm.get_data("design_reviews", "reviews")
        actions = [item for r in reviews for item in r.get("action_items", [])]
        actions_df = pd.DataFrame(actions)
        st.plotly_chart(create_action_item_chart(actions_df), use_container_width=True)
    st.divider()
    render_dhr_completeness_panel(ssm, tasks_df_processed)
    st.divider()
    render_risk_and_fmea_dashboard(ssm)
    st.divider()
    render_qbd_and_cgmp_panel(ssm)
    st.divider()
    render_audit_and_improvement_dashboard(ssm)

# ==============================================================================
# TAB 2: DHF SECTIONS EXPLORER
# ==============================================================================
with tab2:
    st.header("Design History File Explorer")
    st.markdown("Select a DHF section from the sidebar to view or edit its contents.")
    with st.sidebar:
        st.header("DHF Section Navigation")
        PAGES = {"1. Design Plan": design_plan.render_design_plan, "2. Risk Management": design_risk_management.render_design_risk_management, "3. Human Factors": human_factors.render_human_factors, "4. Design Inputs": design_inputs.render_design_inputs, "5. Design Outputs": design_outputs.render_design_outputs, "6. Design Reviews": design_reviews.render_design_reviews, "7. Design Verification": design_verification.render_design_verification, "8. Design Validation": design_validation.render_design_validation, "9. Design Transfer": design_transfer.render_design_transfer, "10. Design Changes": design_changes.render_design_changes}
        dhf_selection = st.radio("Select a section to edit:", PAGES.keys(), key="sidebar_dhf_selection")
    st.divider()
    page_function = PAGES[dhf_selection]
    page_function(ssm)

# ==============================================================================
# TAB 3: ADVANCED ANALYTICS
# ==============================================================================
with tab3:
    st.header("Advanced Compliance & Project Analytics")
    analytics_tabs = st.tabs(["Traceability Matrix", "Action Item Tracker", "Project Task Editor"])
    with analytics_tabs[0]: render_traceability_matrix(ssm)
    with analytics_tabs[1]: render_action_item_tracker(ssm)
    with analytics_tabs[2]:
        st.subheader("Project Timeline and Task Editor")
        st.warning("Directly edit project timelines, statuses, and dependencies. Changes are saved automatically.", icon="⚠️")
        tasks_df_to_edit = pd.DataFrame(ssm.get_data("project_management", "tasks"))
        edited_df = st.data_editor(tasks_df_to_edit, key="main_task_editor", num_rows="dynamic", use_container_width=True, column_config={"start_date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD"), "end_date": st.column_config.DateColumn("End Date", format="YYYY-MM-DD")})
        if not tasks_df_to_edit.equals(edited_df):
            ssm.update_data(edited_df.to_dict('records'), "project_management", "tasks")
            st.toast("Project tasks updated! Rerunning...")
            st.rerun()

# ==============================================================================
# TAB 4: AI & STATISTICAL TOOLS
# ==============================================================================
with tab4:
    st.header("🤖 AI & Statistical Tools")
    st.info("Leverage advanced statistical methods and predictive models to proactively manage quality and project timelines.")
    tool_tabs = st.tabs(["Process Control (SPC)", "Hypothesis Testing (A/B Test)", "Pareto Analysis (FMEA)", "Design of Experiments (DOE)", "Predictive Analytics"])
    with tool_tabs[0]:
        st.subheader("Statistical Process Control (SPC) Chart")
        st.markdown("This chart monitors the stability of a critical process parameter (e.g., pill casing diameter) over time. It helps detect shifts or trends before they result in out-of-specification products.")
        spc_data = ssm.get_data("quality_system", "spc_data")
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=spc_data['measurements'], name='Measurements', mode='lines+markers'))
        fig.add_hline(y=spc_data['target'], line_dash="dash", line_color="green", annotation_text="Target")
        fig.add_hline(y=spc_data['usl'], line_dash="dot", line_color="red", annotation_text="USL")
        fig.add_hline(y=spc_data['lsl'], line_dash="dot", line_color="red", annotation_text="LSL")
        st.plotly_chart(fig, use_container_width=True)
    with tool_tabs[1]:
        st.subheader("Hypothesis Testing: Process Comparison")
        st.markdown("This analysis uses a two-sample t-test to determine if there is a *statistically significant* difference between two manufacturing lines or suppliers. This moves decisions from anecdotal to data-driven.")
        ht_data = ssm.get_data("quality_system", "hypothesis_testing_data")
        line_a, line_b = ht_data['line_a'], ht_data['line_b']
        t_stat, p_value = stats.ttest_ind(line_a, line_b)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Test Results:**")
            st.metric("T-statistic", f"{t_stat:.3f}")
            st.metric("P-value", f"{p_value:.3f}")
            if p_value < 0.05:
                st.success("**Conclusion:** The p-value is less than 0.05. We reject the null hypothesis. There is a statistically significant difference between the two lines.")
            else:
                st.warning("**Conclusion:** The p-value is greater than 0.05. We fail to reject the null hypothesis. There is no statistically significant difference.")
        with col2:
            df_a = pd.DataFrame({'value': line_a, 'line': 'Line A'})
            df_b = pd.DataFrame({'value': line_b, 'line': 'Line B'})
            df_ht = pd.concat([df_a, df_b])
            fig = px.box(df_ht, x='line', y='value', title="Distribution Comparison", points="all")
            st.plotly_chart(fig, use_container_width=True)
    with tool_tabs[2]:
        st.subheader("Pareto Analysis of FMEA Risk")
        st.markdown("This chart applies the 80/20 rule to FMEA data, identifying the 'vital few' failure modes that contribute to the majority of the risk (by RPN). This allows for focused mitigation efforts.")
        fmea_df = pd.concat([pd.DataFrame(ssm.get_data("risk_management_file", "dfmea")), pd.DataFrame(ssm.get_data("risk_management_file", "pfmea"))])
        fmea_df['RPN'] = fmea_df['S'] * fmea_df['O'] * fmea_df['D']
        fmea_df = fmea_df.sort_values('RPN', ascending=False)
        fmea_df['cumulative_pct'] = (fmea_df['RPN'].cumsum() / fmea_df['RPN'].sum()) * 100
        fig = go.Figure()
        fig.add_trace(go.Bar(x=fmea_df['failure_mode'], y=fmea_df['RPN'], name='RPN'))
        fig.add_trace(go.Scatter(x=fmea_df['failure_mode'], y=fmea_df['cumulative_pct'], name='Cumulative %', yaxis='y2', line=dict(color='red')))
        fig.update_layout(title="FMEA Pareto Chart", yaxis=dict(title='RPN'), yaxis2=dict(title='Cumulative %', overlaying='y', side='right', range=[0, 105]))
        st.plotly_chart(fig, use_container_width=True)
    with tool_tabs[3]:
        st.subheader("Design of Experiments (DOE) Analysis")
        st.markdown("DOE is a powerful tool to understand which process inputs (factors) affect the output (response). This example analyzes the effect of **Molding Temperature** and **Nozzle Pressure** on the **Pill Casing's Seal Strength**.")
        doe_df = pd.DataFrame(ssm.get_data("quality_system", "doe_data"))
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Main Effects Plot**")
            st.caption("Shows the average change in Seal Strength for each factor. A steeper line indicates a more significant effect.")
            main_effects = {}
            for factor in ['temperature', 'pressure']:
                main_effects[factor] = doe_df.groupby(factor)['seal_strength'].mean()
            fig = go.Figure()
            for factor, effects in main_effects.items():
                fig.add_trace(go.Scatter(x=effects.index, y=effects.values, mode='lines+markers', name=factor))
            fig.update_layout(xaxis_title="Factor Level (-1: Low, 1: High)", yaxis_title="Mean Seal Strength")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.markdown("**Contour Plot**")
            st.caption("Visualizes the 'response surface' to find the optimal settings for Temperature and Pressure.")
            model = np.poly1d(np.polyfit(doe_df['temperature'], doe_df['seal_strength'], 2)) # Simplified model for viz
            t_range = np.linspace(-1.5, 1.5, 20)
            p_range = np.linspace(-1.5, 1.5, 20)
            t_grid, p_grid = np.meshgrid(t_range, p_range)
            strength_grid = model(t_grid) + (p_grid * 2) # Adding pressure effect
            fig = go.Figure(data=[go.Contour(z=strength_grid, x=t_range, y=p_range, colorscale='Viridis'), go.Scatter(x=doe_df['temperature'], y=doe_df['pressure'], mode='markers', marker=dict(color='red', size=10), name='Actual Runs')])
            fig.update_layout(xaxis_title="Temperature", yaxis_title="Pressure", title="Seal Strength vs. Factors")
            st.plotly_chart(fig, use_container_width=True)
    with tool_tabs[4]:
        st.subheader("Predictive Analytics: Project Completion Forecast")
        st.markdown("This simple predictive model uses the average velocity of completed phases to forecast the project's completion date.")
        tasks = ssm.get_data("project_management", "tasks")
        completed_tasks = [t for t in tasks if t['status'] == 'Completed' and t.get('days_taken')]
        if completed_tasks:
            total_pct_done = sum(t['completion_pct'] for t in completed_tasks)
            total_days_taken = sum(t['days_taken'] for t in completed_tasks)
            velocity = total_days_taken / total_pct_done if total_pct_done > 0 else 0
            if velocity > 0:
                projected_days_remaining = velocity * (len(tasks)*100 - total_pct_done)
                last_end_date = pd.to_datetime(completed_tasks[-1]['end_date'])
                projected_end_date = last_end_date + timedelta(days=int(projected_days_remaining))
                st.metric("Projected Completion Date", f"{projected_end_date.strftime('%Y-%m-%d')}")
                st.info(f"Based on a current velocity of **{velocity:.2f} days per percent complete**, the project is forecast to need another **{int(projected_days_remaining)} days**.")
            else:
                st.warning("Cannot calculate velocity with available data.")
        else:
            st.warning("Not enough completed task data to generate a forecast.")

# ==============================================================================
# TAB 5: QE & COMPLIANCE GUIDE (UNTRUNCATED AND EXPANDED)
# ==============================================================================
with tab5:
    st.header("A Guide to Design Controls & the Regulatory Landscape")
    st.markdown("This section provides a high-level overview of the Design Controls methodology and the key regulations and standards governing medical device development.")
    st.subheader("Navigating the Regulatory Maze for Combination Products")
    st.info("A 'Combination Product' like the Smart-Pill contains both device and drug components, so it must comply with regulations for both.")
    with st.expander("▶️ **21 CFR Part 4: The 'Rulebook for Rulebooks'**"):
        st.markdown("""
        Part 4 governs combination products. It doesn't add new requirements, but instead tells you **which existing regulations to apply**. For the Smart-Pill, this means:
        - The **device aspects** (casing, electronics, software) must follow the **Quality System Regulation (QSR) for devices**.
        - The **drug aspects** (formulation, stability, purity) must follow the **Current Good Manufacturing Practices (cGMP) for drugs**.
        - Design Controls (part of the QSR) must consider the entire system, including how the device and drug interact.
        """)
    with st.expander("▶️ **21 CFR Part 820: The Quality System Regulation (QSR) for Devices**"):
        st.markdown("""
        This is the FDA's rulebook for medical device manufacturing and design. The Design Controls section (`820.30`) is the foundation of this entire application. It mandates a systematic approach to design to ensure the final product is safe and effective.
        - **Applies to:** The physical pill, its electronics, the embedded software, and the companion mobile app.
        - **Key Principle:** You must document everything to prove you designed the device in a state of control. The DHF is that proof.
        """)
    with st.expander("▶️ **21 CFR Parts 210/211 & CGMP in a Design Context**"):
        st.markdown("""
        This is the FDA's rulebook for pharmaceutical products. While this app focuses on the DHF (a device concept), design decisions for the device constituent part must be made with CGMP in mind. The goal is to ensure the final, combined product can be manufactured reliably, safely, and consistently.
        - **Material Compatibility:** The pill casing cannot contaminate or react with the drug. This is a design choice verified during V&V.
        - **Stability:** The device cannot cause the drug to degrade over its shelf life. This is confirmed via **Stability Studies**, a key CGMP activity.
        - **Sterilizability:** The design materials and construction must be compatible with the chosen sterilization method (e.g., EtO, gamma) without damaging the device or the drug.
        - **Aseptic Processing:** If applicable, the device must be designed to be assembled and filled in a sterile environment without introducing contamination.
        """)
    with st.expander("▶️ **ISO 13485:2016: Quality Management Systems (International Standard)**"):
        st.markdown("""
        ISO 13485 is the internationally recognized standard for a medical device Quality Management System (QMS). It is very similar to the FDA's QSR but is required for market access in many other regions, including Europe (as part of MDR), Canada, and Australia.
        - **Relationship to QSR:** Following the QSR gets you very close to ISO 13485 compliance. The key difference is that ISO 13485 places a stronger emphasis on **risk management** throughout the entire QMS.
        - **Why it matters:** A DHF built to QSR standards is easily adaptable for ISO 13485 audits, enabling global market strategies.
        """)
    with st.expander("▶️ **ISO 14971:2019: Risk Management for Medical Devices (International Standard)**"):
        st.markdown("""
        This is the global "how-to" guide for risk management. Both the FDA and international regulators consider it the state-of-the-art process for ensuring device safety.
        - **Process:** It defines a lifecycle approach: identify hazards, estimate and evaluate risks, implement controls, and monitor the effectiveness of those controls.
        - **Role in this App:** The **'2. Risk Management'** section of the DHF Explorer is a direct implementation of the documentation required by ISO 14971.
        """)
    st.divider()
    st.subheader("The Role of a Design Assurance Quality Engineer")
    st.markdown("A Design Assurance QE is the steward of the DHF, ensuring compliance, quality, and safety are designed into the product from day one. This tool is designed to be their primary workspace. Key responsibilities within this framework include:")
    with st.expander("✅ **Owning the Design History File (DHF)**"):
        st.markdown("The QE is responsible for the **creation, remediation, and maintenance** of the DHF. It's not just a repository; it's a living document that tells the story of the product's development. \n- This application serves as the DHF's active workspace.\n- **Key QE Goal:** Ensure the DHF is complete, coherent, and audit-ready at all times. The Traceability Matrix is the QE's primary tool for identifying gaps.")
    with st.expander("✅ **Driving Verification & Validation (V&V) Strategy**"):
        st.markdown("The QE doesn't just witness tests; they help architect the entire V&V strategy.\n- **V&V Master Plan:** This is a high-level document, referenced in the Design Plan, that outlines the scope, methods, and acceptance criteria for all V&V activities.\n- **Protocol & Report Review:** The QE reviews and approves all test protocols (to ensure they are adequate) and reports (to ensure they are accurate and complete). The 'Design Verification' and 'Design Validation' sections track these deliverables.")
    with st.expander("✅ **Advanced Quality Engineering Concepts**"):
        st.markdown("""Beyond foundational Design Controls, a Senior QE leverages advanced methodologies to ensure quality is built into the product proactively, not inspected in later. This is the core of **First-Time-Right (FTR)** initiatives, which aim to reduce the **Cost of Poor Quality (COPQ)**—the significant expenses associated with scrap, rework, complaints, and recalls.
- **Quality by Design (QbD):** A systematic approach that begins with predefined objectives and emphasizes product and process understanding and control. The key is to identify **Critical Quality Attributes (CQAs)**—the physical, chemical, or biological characteristics that must be within a specific limit to ensure the desired product quality. These CQAs are then linked to the **Critical Material Attributes (CMAs)** of the raw materials and the **Critical Process Parameters (CPPs)** of the manufacturing process. The **QbD Tracker** on the main dashboard visualizes these crucial linkages.
- **Failure Mode and Effects Analysis (FMEA):** A bottom-up, systematic tool for analyzing potential failure modes in a system. It is a core part of the risk management process.
    - **Design FMEA (dFMEA):** Focuses on failures that can result from the **design** of the product (e.g., incorrect material choice, software bug).
    - **Process FMEA (pFMEA):** Focuses on failures that can result from the **manufacturing process** (e.g., incorrect machine setting, operator error).
    - The **Risk & FMEA Dashboard** shows highlights from both.
- **Fault Tree Analysis (FTA):** A top-down, deductive failure analysis where a high-level system failure (e.g., "Patient receives no therapy") is traced back to all the potential root causes. It's a powerful risk management tool used to understand complex failure modes, complementing the bottom-up FMEA. The project's `FTA-001` document would be part of the Risk Management File.
- **Design of Experiments (DOE):** A statistical tool used to systematically determine the relationship between inputs (factors) and outputs of a process. Instead of testing one factor at a time, DOE allows for efficient exploration of the **design space**. It is used to identify the most critical CPPs and optimize their settings to ensure the process robustly produces products that meet their CQAs. The **DOE Analysis** tool in the `AI & Statistical Tools` tab provides a practical example.
- **Statistical Process Control (SPC):** A method of quality control which employs statistical methods to monitor and control a process. This helps to ensure that the process operates efficiently, producing more specification-conforming product with less waste. The **SPC Chart** in the `AI & Statistical Tools` tab is a practical implementation.
- **Hypothesis Testing:** A statistical method used to make decisions using data. For example, a t-test can determine if a new supplier's material is significantly stronger than the old one. The **Hypothesis Testing** tool in the `AI & Statistical Tools` tab demonstrates this.
- **Process Capability (Cpk):** A statistical measure of a process's ability to produce output within specification limits. A Cpk value of **1.33 is considered capable**, while **1.67 is considered highly capable (6-sigma level)**. The 'Audit & Continuous Improvement' dashboard tracks this metric.
- **Process Validation (IQ/OQ/PQ):** A cornerstone of CGMP and Design Transfer. It provides documented evidence that a process will consistently produce a product meeting its predetermined specifications.
    - **Installation Qualification (IQ):** Confirms that the equipment has been installed correctly.
    - **Operational Qualification (OQ):** Confirms that the equipment operates correctly across its entire operational range.
    - **Performance Qualification (PQ):** Confirms that the equipment, under normal operating conditions, consistently produces product that meets all specifications. The 'DHF Sections Explorer' tracks these activities.""")
    st.divider()
    st.subheader("Visualizing the Process: The V-Model")
    st.markdown("The V-Model is a powerful way to visualize the Design Controls process, emphasizing the critical link between design (left side) and testing (right side).")
    v_model_image_path = os.path.join(os.path.dirname(__file__), "v_model_diagram.png")
    if os.path.exists(v_model_image_path): _, img_col, _ = st.columns([1, 2, 1]); img_col.image(v_model_image_path, caption="The V-Model illustrates the relationship between design decomposition and integration/testing.", width=600)
    else: st.error(f"Image Not Found: Ensure `v_model_diagram.png` is in the same directory as this script.", icon="🚨")
    col1, col2 = st.columns(2)
    with col1: st.subheader("Left Side: Decomposition & Design"); st.markdown("- **User Needs & Intended Use:** What problem does the user need to solve?\n- **Design Inputs (Requirements):** How must the device perform to meet those needs? This includes technical, functional, and safety requirements.\n- **System & Architectural Design:** How will the components be structured to meet the requirements?\n- **Detailed Design (Outputs):** At the lowest level, these are the final drawings, code, and specifications that are used to build the device.")
    with col2: st.subheader("Right Side: Integration & Testing"); st.markdown("- **Unit/Component Verification:** Does each individual part meet its detailed design specification?\n- **Integration & System Verification:** Do the assembled parts work together as defined in the architectural design?\n- **Design Validation:** Does the final, complete device meet the high-level User Needs? This is the ultimate test.")
    st.success("""#### The Core Principle: Verification vs. Validation
- **Verification (Horizontal Arrows):** Answers the question, **"Are we building the product right?"** It is the process of confirming that a design output meets its specified input requirements (e.g., does the code correctly implement the detailed design?).
- **Validation (Top-Level Arrow):** Answers the question, **"Are we building the right product?"** It is the process of confirming that the final, finished product meets the user's actual needs and its intended use.""")
