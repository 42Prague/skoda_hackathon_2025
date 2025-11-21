import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

from srcs.data_loader import DataLoader
from srcs.processing import DataProcessor
from srcs.ai_service import AIService

# Load environment variables
load_dotenv()

# Page Config
st.set_page_config(
    page_title="AI Skill Coach - Skoda Auto",
    page_icon="🚗",
    layout="wide"
)

# Initialize Services
@st.cache_resource
def init_services():
    loader = DataLoader()
    data = loader.load_all()
    processor = DataProcessor(data)
    ai_service = AIService()
    return loader, processor, ai_service, data

loader, processor, ai_service, raw_data = init_services()

# --- Sidebar ---
st.sidebar.image("https://storage.dealers-uat.bluehosting.cz/sdmedia/sharedmedia/skodadealers/files/skoda_logo_header_fi_e7f2cba9.png?guid=420397f5-24c8-474c-8bc0-928eb8cf8e06&ext=.png", width=150)
st.sidebar.title("AI Skill Coach")

# User Selection
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None
if "employee_self_id" not in st.session_state:
    st.session_state["employee_self_id"] = ""
if "employee_locked" not in st.session_state:
    st.session_state["employee_locked"] = False

employees_df = raw_data.get('employees', pd.DataFrame())
if not employees_df.empty and 'personal_number' in employees_df.columns:
    employees_df['personal_number'] = employees_df['personal_number'].astype(str).str.strip()
    employee_choices = [val for val in employees_df['personal_number'].dropna().unique() if val]
    if not employee_choices:
        st.error("No employee identifiers available after normalization.")
        st.stop()

    def _format_employee(value: str) -> str:
        name_col = 'name' if 'name' in employees_df.columns else None
        if name_col:
            match = employees_df.loc[employees_df['personal_number'] == value, name_col]
            if not match.empty:
                return f"{value} - {match.iloc[0]}"
        return str(value)
else:
    st.error("Employee dataset is missing required columns or data. Please check your data.")
    st.stop()

role = st.session_state.get("user_role")
locked_employee = st.session_state.get("employee_locked", False)

if role is None:
    st.sidebar.markdown("### Access Mode")
    mode_col_manager, mode_col_employee = st.sidebar.columns(2)
    if mode_col_manager.button("Manager", use_container_width=True):
        st.session_state["user_role"] = "manager"
        st.session_state["employee_locked"] = False
        st.session_state["employee_self_id"] = ""
        st.rerun()
    if mode_col_employee.button("Employee", use_container_width=True):
        st.session_state["user_role"] = "employee"
        st.rerun()
    st.sidebar.info("Select Manager or Employee to continue.")
    st.stop()

selected_emp_id = None

if role == "manager":
    st.sidebar.caption("Manager mode: switch between employees freely.")
    selected_emp_id = st.sidebar.selectbox(
        "Select Employee",
        employee_choices,
        format_func=_format_employee
    )
elif role == "employee":
    if not locked_employee:
        st.sidebar.caption("Employee mode: view locked to your own profile.")
        employee_id_input = st.sidebar.text_input(
            "Enter your personal number",
            value=st.session_state.get("employee_self_id", ""),
        ).strip()
        st.session_state["employee_self_id"] = employee_id_input

        if st.sidebar.button(
            "Access My Profile",
            key="employee_lock_button",
            use_container_width=True,
        ):
            if not employee_id_input:
                st.sidebar.warning("Please enter your personal number before continuing.")
                st.stop()
            if employee_id_input not in employee_choices:
                st.sidebar.error("Personal number not found. Please contact your manager.")
                st.stop()
            st.session_state["employee_locked"] = True
            locked_employee = True
            st.rerun()

    if not st.session_state.get("employee_locked"):
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Log out", use_container_width=True):
            st.session_state["user_role"] = None
            st.session_state["employee_locked"] = False
            st.session_state["employee_self_id"] = ""
            st.rerun()
        st.sidebar.info("Enter your personal number and press 'Access My Profile' to continue.")
        st.stop()

    selected_emp_id = st.session_state.get("employee_self_id")
    if not selected_emp_id or selected_emp_id not in employee_choices:
        st.error("Employee record unavailable. Please reach out to HR.")
        st.stop()
    
    personal_number_display = st.session_state.get("employee_self_id", "—")
    st.sidebar.success(f"Logged in as personal number {personal_number_display}.")# Navigation
page = st.sidebar.radio("Navigation", ["My Profile", "Skill Gaps", "AI Coach Recommendations", "Team Dashboard"])

# Get current employee data
emp_profile = processor.get_employee_profile(selected_emp_id)
gap_analysis = processor.analyze_gaps(selected_emp_id)

# --- Main Content ---

if page == "My Profile":
    # -----------------------------
    # Profile Header
    # -----------------------------
    personal_number = emp_profile.get("personal_number") or selected_emp_id
    st.title("👤 Employee profile")
    st.subheader(f"Personal number: {personal_number}")

    # -----------------------------
    # Role Information
    # -----------------------------
    current_profession = (
        emp_profile.get("current_profession_name")
        or emp_profile.get("current_profession")
        or emp_profile.get("profession_name")
    )
    planned_profession = (
        emp_profile.get("planned_profession_name")
        or emp_profile.get("planned_profession")
        or emp_profile.get("position_name")
    )
    planned_position = (emp_profile.get("planned_position_name") or "—")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**Current profession:**\n{current_profession}")
    with col2:
        st.info(f"**Planned profession:**\n{planned_profession}")
    with col3:
        st.info(f"**Planned position:**\n{planned_position}")

    st.markdown("---")

    # -----------------------------
    # Education Profile
    # -----------------------------
    st.markdown("### 🎓 Education profile")

    col_ed1, col_ed2, col_ed3 = st.columns(3)
    with col_ed1:
        st.info(
            "**Basic branch of education:**\n"
            f"{emp_profile.get('basic_branch_of_education_name') or '—'}"
        )
    with col_ed2:
        st.info(
            "**Education category:**\n"
            f"{emp_profile.get('education_category_name') or '—'}"
        )
    with col_ed3:
        st.info(
            "**Field of study:**\n"
            f"{emp_profile.get('field_of_study_name') or '—'}"
        )

    st.markdown("---")

    # -----------------------------
    # ERP Classification (OB1 / OB2 / OB3 / OB5 / OB8)
    # -----------------------------
    st.markdown("### 🧾 ERP classification (OB1 / OB2 / OB3 / OB5 / OB8)")

    def format_ob(code_key: str, label_key: str) -> str:
        code = emp_profile.get(code_key)
        label = emp_profile.get(label_key)
        if code is None and not label:
            return "—"
        code_str = "" if code is None else str(code).strip()
        if label:
            return f"{code_str} — {label}"
        return code_str or "—"

    col_left, col_right = st.columns(2)
    with col_left:
        st.write(f"**OB1:** {format_ob('ob1', 'ob1_label')}")
        st.write(f"**OB2:** {format_ob('ob2', 'ob2_label')}")
        st.write(f"**OB3:** {format_ob('ob3', 'ob3_label')}")
    with col_right:
        st.write(f"**OB5:** {format_ob('ob5', 'ob5_label')}")
        st.write(f"**OB8:** {format_ob('ob8', 'ob8_label')}")

    st.markdown("---")

    # -----------------------------
    # Skill Overview
    # -----------------------------
    st.markdown("### 📊 Skill overview")

    skills = emp_profile.get("skills_detailed") or emp_profile.get("skills") or []
    if skills:
        skills_df = pd.DataFrame(skills)
        if "category" in skills_df.columns:
            cat_counts = (
                skills_df["category"]
                .fillna("Uncategorized")
                .value_counts()
                .reset_index()
            )
            cat_counts.columns = ["Category", "Count"]
            st.bar_chart(
                cat_counts.set_index("Category")["Count"],
                height=250,
            )

        st.markdown("#### Skills details")
        display_cols = [c for c in ["skill", "category", "source", "source_name", "date"] if c in skills_df.columns]
        st.dataframe(
            skills_df[display_cols].sort_values(by=["category", "skill"]),
            use_container_width=True,
        )
    else:
        st.info("No skills found for this employee.")

    # -----------------------------
    # Degreed learning overview
    # -----------------------------
    st.markdown("---")
    st.markdown("### 🎓 Degreed learning history")

    degreed_table = processor.get_degreed_learning_table(selected_emp_id)

    with st.expander("📚 Completed Degreed content", expanded=False):
        if degreed_table is None or degreed_table.empty:
            st.info("No Degreed completions found for this employee in Degreed.")
        else:
            view_df = degreed_table.copy()
            if "completed_date" in view_df.columns:
                view_df["completed_date"] = pd.to_datetime(
                    view_df["completed_date"], errors="coerce"
                ).dt.date

            rename_map = {
                "completed_date": "Completed",
                "title": "Title",
                "provider": "Provider",
                "content_type": "Type",
                "minutes": "Minutes (est.)",
                "categories": "Categories",
                "url": "URL",
            }
            existing = {k: v for k, v in rename_map.items() if k in view_df.columns}
            view_df = view_df.rename(columns=existing)
            st.dataframe(view_df, use_container_width=True)


elif page == "Skill Gaps":
    st.title("🎯 Skill Gap Analysis")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        score = gap_analysis.get('completeness_score', 0)
        st.metric("Role Readiness", f"{score}%")
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Completeness"},
            gauge = {'axis': {'range': [None, 100]},
                     'bar': {'color': "green" if score > 80 else "orange" if score > 50 else "red"}}
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader(f"Requirements for {gap_analysis.get('position_name')}")
        
        tab_missing, tab_met = st.tabs(["❌ Missing Requirements", "✅ Met Requirements"])
        
        with tab_missing:
            gaps = gap_analysis.get('gaps', [])
            if gaps:
                for gap in gaps:
                    priority = "🔴 Mandatory" if gap['mandatory'] else "🟡 Optional"
                    st.warning(f"**{gap['name']}** ({priority})")
            else:
                st.success("🎉 No gaps found! You are fully qualified for this role.")

        with tab_met:
            met = gap_analysis.get('met', [])
            if met:
                for item in met:
                    st.success(f"**{item['name']}**")
            else:
                st.info("No requirements met yet.")


elif page == "AI Coach Recommendations":
    st.title("🤖 AI Skill Coach")
    st.markdown(
        "Generate a personalized learning plan based on your current gaps and career goals."
    )
    st.caption(f"AI backend active: {ai_service.is_active}")

    if "dev_plan_text" not in st.session_state:
        st.session_state["dev_plan_text"] = ""
    
    if "dev_plan_courses" not in st.session_state:
        st.session_state["dev_plan_courses"] = []

    if not emp_profile:
        st.warning("No employee profile loaded.")
    elif not gap_analysis:
        st.warning("No gap analysis available.")
    else:
        if st.button("🚀 Generate My Development Plan"):
            with st.spinner("Consulting AI Coach..."):
                text_result, courses_result = ai_service.generate_learning_plan(emp_profile, gap_analysis)
                
                st.session_state["dev_plan_text"] = text_result
                st.session_state["dev_plan_courses"] = courses_result

        if st.session_state.get("dev_plan_text"):
            st.markdown("---")
            st.markdown("### Your Personal Growth Strategy")
            st.markdown("---")
            st.markdown(st.session_state["dev_plan_text"])
            
            st.download_button(
                label="📥 Download Full Plan ",
                data=st.session_state["dev_plan_text"],
                file_name=f"Growth_Plan_{emp_profile.get('personal_number')}.md",
                mime="text/markdown",
            )

elif page == "Team Dashboard":
    st.title("👥 Team Overview")
    
    stats = processor.get_team_stats()
    
    # --- Top Metrics ---
    c1, c2 = st.columns(2)
    c1.metric("Total Employees", stats.get('total_employees', 0))
    c2.metric("Unique Positions", len(stats.get('positions', {})))
    
    st.markdown("---")
    st.subheader("💼 Roles Distribution")
    
    pos_data = stats.get('positions', {})
    if pos_data:
        pos_df = pd.DataFrame(list(pos_data.items()), columns=['Position', 'Count'])
        # Filter out 'Unknown'
        pos_df = pos_df[pos_df['Position'] != 'Unknown']
        # Top 15
        pos_df = pos_df.sort_values('Count', ascending=False).head(15)
        
        fig = px.bar(
            pos_df, 
            x='Count', 
            y='Position', 
            orientation='h',
            color='Count',
            color_continuous_scale='Purples'
        )
        fig.update_layout(
            yaxis={'categoryorder':'total ascending'},
            height=400,
            margin=dict(t=0, b=0, l=0, r=0)
        )
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Log out", key="logout_main", use_container_width=True):
    st.session_state["user_role"] = None
    st.session_state["employee_locked"] = False
    st.session_state["employee_self_id"] = ""
    st.rerun()
st.sidebar.caption("Hackathon 2025 | Secure Environment")