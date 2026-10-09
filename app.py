import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Student Performance Analyzer",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 Student Performance Analyzer")
st.write(
    "Analyze student marks, attendance, and academic performance "
    "using interactive charts and personalized recommendations."
)

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.title("🎓 Student Analytics")
    st.write("Upload, analyze, and explore student results.")
    st.divider()
    st.caption("Student Performance Analyzer")
    st.caption("Version 1.0")

# --------------------------------------------------
# SAMPLE DATA
# --------------------------------------------------

sample_data = {
    "Student": [
        "Aditi", "Rahul", "Priya", "Aman",
        "Neha", "Rohan", "Sneha", "Karan"
    ],
    "Math": [85, 45, 92, 60, 35, 76, 88, 28],
    "Science": [78, 52, 95, 55, 42, 82, 91, 32],
    "English": [90, 48, 88, 64, 50, 70, 86, 40],
    "Attendance": [92, 65, 98, 75, 58, 85, 95, 55]
}

SUBJECTS = ["Math", "Science", "English"]

# --------------------------------------------------
# DATA UPLOAD
# --------------------------------------------------

st.header("📂 Upload Student Dataset")

uploaded_file = st.file_uploader(
    "Upload a CSV file containing student marks and attendance",
    type=["csv"]
)

if uploaded_file is not None:
    try:
        original_df = pd.read_csv(uploaded_file)
    except Exception as error:
        st.error(f"Unable to read the uploaded file: {error}")
        st.stop()
else:
    original_df = pd.DataFrame(sample_data)
    st.info("Showing sample student data. Upload your own CSV to analyze it.")

# --------------------------------------------------
# DATA VALIDATION AND PREPARATION
# --------------------------------------------------

required_columns = ["Student", "Math", "Science", "English", "Attendance"]

missing_columns = [
    column for column in required_columns
    if column not in original_df.columns
]

if missing_columns:
    st.error(
        "Your CSV is missing these required columns: "
        + ", ".join(missing_columns)
    )
    st.info(
        "Required columns: Student, Math, Science, English, Attendance"
    )
    st.stop()

df = original_df.copy()

df["Student"] = df["Student"].fillna("").astype(str).str.strip()

for column in SUBJECTS + ["Attendance"]:
    df[column] = pd.to_numeric(df[column], errors="coerce")

df = df.dropna(
    subset=["Student"] + SUBJECTS + ["Attendance"]
)

df = df[df["Student"] != ""]

if df.empty:
    st.warning("No valid student records were found in the dataset.")
    st.stop()

# Validate the expected score ranges
invalid_scores = (
    (df[SUBJECTS] < 0).any(axis=1)
    | (df[SUBJECTS] > 100).any(axis=1)
    | (df["Attendance"] < 0)
    | (df["Attendance"] > 100)
)

if invalid_scores.any():
    st.warning(
        "Rows containing marks or attendance outside the 0–100 range "
        "have been excluded."
    )
    df = df.loc[~invalid_scores].copy()

if df.empty:
    st.warning("No valid records remain after checking score ranges.")
    st.stop()

# Calculate student averages and results
df["Average"] = df[SUBJECTS].mean(axis=1)

df["Result"] = df[SUBJECTS].apply(
    lambda row: "Pass" if (row >= 35).all() else "Needs Improvement",
    axis=1
)

df["Category"] = df["Average"].apply(
    lambda average: (
        "Excellent" if average >= 85
        else "Good" if average >= 70
        else "Average" if average >= 50
        else "Needs Improvement"
    )
)

# --------------------------------------------------
# KEY PERFORMANCE METRICS
# --------------------------------------------------

st.divider()
st.header("📊 Overall Performance")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Students", len(df))
col2.metric("Class Average", f"{df['Average'].mean():.1f}%")
col3.metric("Average Attendance", f"{df['Attendance'].mean():.1f}%")
col4.metric(
    "Students Passing",
    f"{(df['Result'] == 'Pass').sum()} / {len(df)}"
)

# --------------------------------------------------
# PERFORMANCE CHARTS
# --------------------------------------------------

st.divider()
st.header("📈 Performance Dashboard")

chart1, chart2 = st.columns(2)

with chart1:
    subject_averages = pd.DataFrame({
        "Subject": SUBJECTS,
        "Average Marks": [df[subject].mean() for subject in SUBJECTS]
    })

    fig_subjects = px.bar(
        subject_averages,
        x="Subject",
        y="Average Marks",
        color="Subject",
        range_y=[0, 100],
        title="Average Marks by Subject",
        text_auto=".1f"
    )

    st.plotly_chart(fig_subjects, use_container_width=True)

with chart2:
    category_counts = (
        df["Category"]
        .value_counts()
        .rename_axis("Category")
        .reset_index(name="Students")
    )

    fig_categories = px.pie(
        category_counts,
        names="Category",
        values="Students",
        title="Student Performance Categories",
        hole=0.4
    )

    st.plotly_chart(fig_categories, use_container_width=True)

# --------------------------------------------------
# STUDENT COMPARISON
# --------------------------------------------------

st.subheader("📚 Compare Student Performance")

comparison_chart = px.bar(
    df,
    x="Student",
    y="Average",
    color="Category",
    range_y=[0, 100],
    title="Average Marks by Student",
    labels={"Average": "Average Marks"}
)

st.plotly_chart(comparison_chart, use_container_width=True)

# --------------------------------------------------
# KEY INSIGHTS
# --------------------------------------------------

st.divider()
st.header("🔍 Key Insights")

best_student = df.loc[df["Average"].idxmax()]
lowest_student = df.loc[df["Average"].idxmin()]
best_subject = df[SUBJECTS].mean().idxmax()
weakest_subject = df[SUBJECTS].mean().idxmin()

insight1, insight2 = st.columns(2)

with insight1:
    st.success(
        f"🏆 **Top Performer:** {best_student['Student']} "
        f"with an average of {best_student['Average']:.1f}%."
    )

    st.info(
        f"📘 **Strongest Subject:** {best_subject}, "
        f"with an average of {df[best_subject].mean():.1f}%."
    )

with insight2:
    st.warning(
        f"📉 **Needs Support:** {lowest_student['Student']} "
        f"has the lowest average of {lowest_student['Average']:.1f}%."
    )

    st.info(
        f"📖 **Subject to Focus On:** {weakest_subject}, "
        f"with an average of {df[weakest_subject].mean():.1f}%."
    )

# ==================================================
# NEW FEATURE 1: INDIVIDUAL STUDENT REPORT
# ==================================================

st.divider()
st.header("👤 Individual Student Report")

student_names = df["Student"].tolist()

selected_student = st.selectbox(
    "Select a student to view their report",
    options=student_names,
    key="individual_student"
)

student = df[
    df["Student"] == selected_student
].iloc[0]

st.subheader(f"Report for {selected_student}")

report_col1, report_col2, report_col3 = st.columns(3)

report_col1.metric(
    "Average Marks",
    f"{student['Average']:.1f}%"
)

report_col2.metric(
    "Attendance",
    f"{student['Attendance']:.1f}%"
)

report_col3.metric(
    "Result",
    student["Result"]
)

st.caption(f"Performance Category: {student['Category']}")

student_marks = pd.DataFrame({
    "Subject": SUBJECTS,
    "Marks": [student[subject] for subject in SUBJECTS]
})

report_chart = px.bar(
    student_marks,
    x="Subject",
    y="Marks",
    color="Subject",
    range_y=[0, 100],
    title=f"{selected_student}'s Subject-wise Marks",
    text_auto=".1f"
)

st.plotly_chart(
    report_chart,
    use_container_width=True
)

# Download an individual student's report
report_csv = pd.DataFrame([student]).to_csv(index=False)

st.download_button(
    label="📥 Download Individual Student Report",
    data=report_csv,
    file_name=f"{selected_student}_report.csv",
    mime="text/csv"
)

# ==================================================
# NEW FEATURE 2: PERSONALIZED RECOMMENDATIONS
# ==================================================

st.divider()
st.header("💡 Personalized Recommendations")

st.write(
    f"Suggestions based on the current marks and attendance "
    f"record for **{selected_student}**:"
)

recommendations = []

for subject in SUBJECTS:
    marks = student[subject]

    if marks < 35:
        recommendations.append(
            f"⚠️ **{subject}:** Marks are below 35. "
            "Prioritize revision and seek additional academic support."
        )
    elif marks < 60:
        recommendations.append(
            f"📚 **{subject}:** Practice more questions and revise "
            "the topics you find difficult."
        )

if student["Attendance"] < 75:
    recommendations.append(
        "📅 **Attendance:** Attendance is below 75%. "
        "Improve class attendance where possible."
    )

if student["Average"] >= 85 and student["Attendance"] >= 90:
    recommendations.append(
        "🌟 **Excellent progress:** Maintain your study routine "
        "and challenge yourself with more advanced topics."
    )

if not recommendations:
    recommendations.append(
        "✅ **Keep it up!** Continue your current study routine "
        "and review your subjects regularly."
    )

for recommendation in recommendations:
    st.markdown(f"- {recommendation}")

# --------------------------------------------------
# STUDENT RECORDS: SEARCH AND FILTER
# --------------------------------------------------

st.divider()
st.header("📋 Student Records")

search = st.text_input(
    "🔍 Search student by name",
    placeholder="Enter a student name..."
)

filtered = df.copy()

if search:
    filtered = filtered[
        filtered["Student"].str.contains(
            search,
            case=False,
            na=False,
            regex=False
        )
    ]

categories = sorted(df["Category"].unique().tolist())

selected_categories = st.multiselect(
    "Filter by performance category",
    options=categories,
    default=categories
)

filtered = filtered[
    filtered["Category"].isin(selected_categories)
]

st.write(f"Showing **{len(filtered)}** student record(s).")

st.dataframe(
    filtered[
        [
            "Student",
            "Math",
            "Science",
            "English",
            "Average",
            "Attendance",
            "Result",
            "Category"
        ]
    ].round(1),
    use_container_width=True,
    hide_index=True
)

# Download filtered records
filtered_csv = filtered.to_csv(index=False)

st.download_button(
    label="📥 Download Filtered Student Records",
    data=filtered_csv,
    file_name="filtered_student_records.csv",
    mime="text/csv"
)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()
st.caption(
    "Student Performance Analyzer | Built with Python, "
    "Streamlit, Pandas, and Plotly"
)
