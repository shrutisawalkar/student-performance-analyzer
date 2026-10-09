
import re
import pandas as pd
import plotly.express as px
import streamlit as st

# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Student Performance Analyzer",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 Student Performance Analyzer")
st.write(
    "Analyze student results, compare subjects, and generate "
    "individual reports with personalized recommendations."
)

# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:
    st.title("🎓 Student Analytics")
    st.write("Upload, analyze, and explore student results.")
    st.divider()
    st.caption("Student Performance Analyzer")
    st.caption("Version 3.0")

# ==================================================
# EXAM SETTINGS
# ==================================================

st.divider()
st.header("📝 Exam Settings")

exam_type = st.radio(
    "Select the exam type",
    options=["60-Mark Exam", "20-Mark Exam"],
    horizontal=True,
    key="exam_type"
)

if exam_type == "60-Mark Exam":
    MAX_MARKS = 60
    PASS_MARKS = 24
else:
    MAX_MARKS = 20
    PASS_MARKS = 8

st.info(
    f"Maximum marks per subject: {MAX_MARKS} | "
    f"Passing marks: {PASS_MARKS} | "
    f"Passing percentage: 40%"
)

# ==================================================
# SAMPLE DATA
# ==================================================

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

# ==================================================
# HELPER FUNCTIONS
# ==================================================

def normalize_name(name):
    name = str(name).strip().lower()
    name = re.sub(r"%", " percent ", name)
    name = re.sub(r"[^a-z0-9]+", " ", name)
    return " ".join(name.split())


def detect_column(columns, aliases):
    normalized = {
        column: normalize_name(column)
        for column in columns
    }

    # Exact matches first
    for alias in aliases:
        target = normalize_name(alias)
        for column, name in normalized.items():
            if name == target:
                return column

    # Then look for a complete alias phrase in the column name
    for alias in aliases:
        target = normalize_name(alias)
        for column, name in normalized.items():
            if target and target in name:
                return column

    return None


STUDENT_ALIASES = [
    "student", "student name", "name", "full name",
    "learner", "learner name", "candidate name",
    "pupil", "pupil name"
]

ATTENDANCE_ALIASES = [
    "attendance", "attendance percent",
    "attendance percentage", "attendance rate",
    "present percent", "present percentage",
    "presence rate"
]

NON_SUBJECT_ALIASES = [
    "id", "student id", "roll number", "roll no",
    "registration number", "serial number", "sr no",
    "index number", "age", "class", "grade", "year",
    "semester", "phone", "email", "attendance",
    "attendance percent", "attendance percentage",
    "attendance rate", "present percent",
    "present percentage", "presence rate"
]

# ==================================================
# UPLOAD DATA
# ==================================================

st.divider()
st.header("📂 Upload Student Dataset")

uploaded_file = st.file_uploader(
    "Upload your CSV file",
    type=["csv"]
)

if uploaded_file is not None:
    try:
        original_df = pd.read_csv(uploaded_file)
    except Exception as error:
        st.error(f"Could not read your CSV file: {error}")
        st.stop()
else:
    original_df = pd.DataFrame(sample_data)
    st.info(
        "Showing sample data. Upload your own CSV to analyze it."
    )

if original_df.empty:
    st.warning("Your CSV file is empty.")
    st.stop()

original_df.columns = [
    str(column).strip() for column in original_df.columns
]

if any(not column for column in original_df.columns):
    st.error("Every CSV column must have a name.")
    st.stop()

if original_df.columns.duplicated().any():
    st.error(
        "Duplicate column names were found. Rename them so each "
        "column has a unique name."
    )
    st.stop()

columns = original_df.columns.tolist()

# ==================================================
# AUTOMATIC COLUMN DETECTION
# ==================================================

detected_student = detect_column(columns, STUDENT_ALIASES)

if detected_student is None:
    detected_student = columns[0]

detected_attendance = detect_column(
    columns, ATTENDANCE_ALIASES
)

detected_subjects = []

for column in columns:
    if column == detected_student or column == detected_attendance:
        continue

    normalized = normalize_name(column)

    if any(
        normalize_name(alias) == normalized
        for alias in NON_SUBJECT_ALIASES
    ):
        continue

    numeric_values = pd.to_numeric(
        original_df[column], errors="coerce"
    )

    if numeric_values.notna().any():
        detected_subjects.append(column)

# ==================================================
# MANUAL COLUMN MAPPING
# ==================================================

st.divider()
st.header("🧩 Configure Your Columns")

st.write(
    "Check the automatically detected columns below. You can "
    "change them to match your own CSV."
)

with st.container(border=True):
    student_column = st.selectbox(
        "Student name column",
        options=columns,
        index=columns.index(detected_student),
        key="student_column"
    )

    attendance_options = ["— No attendance column —"] + columns

    attendance_default = (
        detected_attendance
        if detected_attendance in columns
        else "— No attendance column —"
    )

    attendance_column = st.selectbox(
        "Attendance column (optional)",
        options=attendance_options,
        index=attendance_options.index(attendance_default),
        key="attendance_column"
    )

    subject_candidates = [
        column for column in columns
        if column != student_column
        and column != attendance_column
        and column != "— No attendance column —"
    ]

    valid_detected_subjects = [
        subject for subject in detected_subjects
        if subject in subject_candidates
    ]

    selected_subjects = st.multiselect(
        "Subject marks columns",
        options=subject_candidates,
        default=valid_detected_subjects,
        help="Select every column containing subject marks.",
        key="subject_columns"
    )

if not selected_subjects:
    st.warning("Select at least one subject marks column.")
    st.stop()

if len(selected_subjects) != len(set(selected_subjects)):
    st.error("A subject column cannot be selected more than once.")
    st.stop()

if student_column in selected_subjects:
    st.error("The student name column cannot be a subject.")
    st.stop()

if attendance_column in selected_subjects:
    st.error("The attendance column cannot be a subject.")
    st.stop()

has_attendance = (
    attendance_column != "— No attendance column —"
)

subjects = selected_subjects

# ==================================================
# PREPARE DATA
# ==================================================

df = pd.DataFrame()

df["Student"] = (
    original_df[student_column]
    .fillna("")
    .astype(str)
    .str.strip()
)

for subject in subjects:
    df[subject] = pd.to_numeric(
        original_df[subject], errors="coerce"
    )

if has_attendance:
    df["Attendance"] = pd.to_numeric(
        original_df[attendance_column], errors="coerce"
    )

# Scale the built-in demonstration data to the selected exam.
# Uploaded CSV marks must already use the selected exam's scale.
if uploaded_file is None:
    for subject in subjects:
        df[subject] = (
            df[subject] * MAX_MARKS / 100
        ).round(1)

required_columns = ["Student"] + subjects

if has_attendance:
    required_columns.append("Attendance")

valid_rows = df[required_columns].notna().all(axis=1)
valid_rows &= df["Student"].ne("")

invalid_count = int((~valid_rows).sum())

if invalid_count:
    st.warning(
        f"{invalid_count} row(s) were excluded because a name or "
        "required numeric value was missing or invalid."
    )

df = df.loc[valid_rows].copy()

if df.empty:
    st.error(
        "No valid records remain. Check your column mapping and "
        "ensure your marks contain numeric values."
    )
    st.stop()

# ==================================================
# VALIDATE MARKS AND ATTENDANCE
# ==================================================

out_of_range = (
    (df[subjects] < 0).any(axis=1)
    | (df[subjects] > MAX_MARKS).any(axis=1)
)

if has_attendance:
    out_of_range |= (
        (df["Attendance"] < 0)
        | (df["Attendance"] > 100)
    )

range_error_count = int(out_of_range.sum())

if range_error_count:
    st.warning(
        f"{range_error_count} row(s) were excluded because marks "
        f"must be between 0 and {MAX_MARKS}"
        + (
            " and attendance must be between 0 and 100."
            if has_attendance else "."
        )
    )
    df = df.loc[~out_of_range].copy()

if df.empty:
    st.error(
        "No valid records remain. Check the selected exam type "
        "and the maximum marks in your CSV."
    )
    st.stop()

# ==================================================
# CALCULATE RESULTS
# ==================================================

# Normalize the average to a percentage so categories are comparable
# across 20-mark and 60-mark exams.
df["Average"] = (
    df[subjects].mean(axis=1) / MAX_MARKS * 100
)

# Passing requires the student to reach the passing mark
# in every selected subject.
df["Result"] = df[subjects].ge(PASS_MARKS).all(axis=1).map(
    {True: "Pass", False: "Needs Improvement"}
)

df["Category"] = df["Average"].apply(
    lambda value: (
        "Excellent" if value >= 85
        else "Good" if value >= 70
        else "Average" if value >= 50
        else "Needs Improvement"
    )
)

# Subject averages are also percentages
subject_averages = pd.DataFrame({
    "Subject": subjects,
    "Average Percentage": [
        df[subject].mean() / MAX_MARKS * 100
        for subject in subjects
    ]
})

# ==================================================
# OVERALL DASHBOARD
# ==================================================

st.divider()
st.header("📊 Overall Performance")

if has_attendance:
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Students", len(df))
    c2.metric("Class Average", f"{df['Average'].mean():.1f}%")
    c3.metric(
        "Average Attendance",
        f"{df['Attendance'].mean():.1f}%"
    )
    c4.metric(
        "Students Passing",
        f"{(df['Result'] == 'Pass').sum()} / {len(df)}"
    )
else:
    c1, c2, c3 = st.columns(3)

    c1.metric("Total Students", len(df))
    c2.metric("Class Average", f"{df['Average'].mean():.1f}%")
    c3.metric(
        "Students Passing",
        f"{(df['Result'] == 'Pass').sum()} / {len(df)}"
    )

# ==================================================
# CHARTS
# ==================================================

st.divider()
st.header("📈 Performance Dashboard")

chart1, chart2 = st.columns(2)

with chart1:
    fig_subjects = px.bar(
        subject_averages,
        x="Subject",
        y="Average Percentage",
        color="Subject",
        range_y=[0, 100],
        title="Average Percentage by Subject",
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

# ==================================================
# STUDENT COMPARISON
# ==================================================

st.subheader("📚 Compare Student Performance")

fig_comparison = px.bar(
    df,
    x="Student",
    y="Average",
    color="Category",
    range_y=[0, 100],
    title="Average Percentage by Student",
    labels={"Average": "Average Percentage"}
)

st.plotly_chart(fig_comparison, use_container_width=True)

# ==================================================
# KEY INSIGHTS
# ==================================================

st.divider()
st.header("🔍 Key Insights")

best_student = df.loc[df["Average"].idxmax()]
lowest_student = df.loc[df["Average"].idxmin()]

best_subject = subject_averages.loc[
    subject_averages["Average Percentage"].idxmax()
]

weakest_subject = subject_averages.loc[
    subject_averages["Average Percentage"].idxmin()
]

insight1, insight2 = st.columns(2)

with insight1:
    st.success(
        f"🏆 **Top Performer:** {best_student['Student']} "
        f"with an average of {best_student['Average']:.1f}%."
    )

    st.info(
        f"📘 **Strongest Subject:** {best_subject['Subject']} "
        f"with {best_subject['Average Percentage']:.1f}% average."
    )

with insight2:
    st.warning(
        f"📉 **Needs Support:** {lowest_student['Student']} "
        f"has the lowest average of {lowest_student['Average']:.1f}%."
    )

    st.info(
        f"📖 **Subject to Focus On:** {weakest_subject['Subject']} "
        f"with {weakest_subject['Average Percentage']:.1f}% average."
    )

# ==================================================
# INDIVIDUAL STUDENT REPORT
# ==================================================

st.divider()
st.header("👤 Individual Student Report")

student_names = df["Student"].drop_duplicates().tolist()

selected_student = st.selectbox(
    "Select a student",
    options=student_names,
    key="individual_student"
)

student = df[df["Student"] == selected_student].iloc[0]

st.subheader(f"Report for {selected_student}")

if has_attendance:
    r1, r2, r3 = st.columns(3)

    r1.metric("Average Percentage", f"{student['Average']:.1f}%")
    r2.metric("Attendance", f"{student['Attendance']:.1f}%")
    r3.metric("Result", student["Result"])
else:
    r1, r2 = st.columns(2)

    r1.metric("Average Percentage", f"{student['Average']:.1f}%")
    r2.metric("Result", student["Result"])

st.caption(
    f"Performance Category: {student['Category']} | "
    f"Exam: {MAX_MARKS} marks | Passing mark: {PASS_MARKS}"
)

student_marks = pd.DataFrame({
    "Subject": subjects,
    "Marks": [student[subject] for subject in subjects]
})

fig_student = px.bar(
    student_marks,
    x="Subject",
    y="Marks",
    color="Subject",
    range_y=[0, MAX_MARKS],
    title=f"{selected_student}'s Subject-wise Marks",
    text_auto=".1f"
)

st.plotly_chart(fig_student, use_container_width=True)

st.download_button(
    "📥 Download Individual Student Report",
    data=pd.DataFrame([student]).to_csv(index=False),
    file_name="student_report.csv",
    mime="text/csv"
)

# ==================================================
# PERSONALIZED RECOMMENDATIONS
# ==================================================

st.divider()
st.header("💡 Personalized Recommendations")

st.write(f"Suggestions for **{selected_student}**:")

recommendations = []

for subject in subjects:
    marks = student[subject]

    if marks < PASS_MARKS:
        recommendations.append(
            f"⚠️ **{subject}:** Below the passing mark of "
            f"{PASS_MARKS}/{MAX_MARKS}. Revise difficult topics "
            "and seek additional academic support."
        )
    elif marks < MAX_MARKS * 0.60:
        recommendations.append(
            f"📚 **{subject}:** You passed, but consider practising "
            "more questions to strengthen your understanding."
        )

if has_attendance and student["Attendance"] < 75:
    recommendations.append(
        "📅 **Attendance:** Attendance is below 75%. "
        "Improve class attendance where possible."
    )

if not recommendations:
    recommendations.append(
        "🌟 Good progress! Maintain your study routine and continue "
        "reviewing your subjects regularly."
    )

for recommendation in recommendations:
    st.markdown(f"- {recommendation}")

# ==================================================
# SEARCH, FILTERS, AND RECORDS
# ==================================================

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

display_columns = ["Student"] + subjects + ["Average"]

if has_attendance:
    display_columns.append("Attendance")

display_columns += ["Result", "Category"]

st.dataframe(
    filtered[display_columns].round(1),
    use_container_width=True,
    hide_index=True
)

st.download_button(
    "📥 Download Filtered Student Records",
    data=filtered.to_csv(index=False),
    file_name="filtered_student_records.csv",
    mime="text/csv"
)

# ==================================================
# FOOTER
# ==================================================

st.divider()
st.caption(
    "Student Performance Analyzer | Python • Streamlit • "
    "Pandas • Plotly"
)
