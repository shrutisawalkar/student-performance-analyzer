
import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Student Performance Analyzer",
    page_icon="📊",
    layout="wide"
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
# MAIN HEADER
# --------------------------------------------------

st.title("📊 Student Performance Analyzer")
st.write("A simple dashboard for academic insights.")

SUBJECTS = ["Math", "Science", "English"]
REQUIRED = ["Student"] + SUBJECTS + ["Attendance"]

# --------------------------------------------------
# DATA PROCESSING
# --------------------------------------------------

def analyze_data(data):
    data = data.copy()

    # Convert marks and attendance to numbers
    for col in SUBJECTS + ["Attendance"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    # Remove incomplete student records
    data = data.dropna(subset=REQUIRED)

    if data.empty:
        return data

    # Calculate average marks
    data["Average"] = data[SUBJECTS].mean(axis=1).round(2)

    # Determine pass or fail
    data["Result"] = data[SUBJECTS].apply(
        lambda row: "Pass" if (row >= 35).all() else "Fail",
        axis=1
    )

    # Categorize student performance
    def get_category(score):
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Needs Improvement"
        return "At Risk"

    data["Performance"] = data["Average"].apply(get_category)

    return data


# --------------------------------------------------
# CSV FILE UPLOAD
# --------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload a student CSV file",
    type=["csv"]
)

if uploaded_file is not None:
    try:
        raw_data = pd.read_csv(uploaded_file)

        if raw_data.empty:
            st.warning("Your CSV file contains no records.")
            st.stop()

        # Check required columns
        missing = [
            col for col in REQUIRED
            if col not in raw_data.columns
        ]

        if missing:
            st.error(
                "Missing columns: " + ", ".join(missing)
            )
            st.info(
                "Required columns: "
                + ", ".join(REQUIRED)
            )
            st.stop()

        df = analyze_data(raw_data)

        if df.empty:
            st.error(
                "No valid student records were found. "
                "Check your CSV data."
            )
            st.stop()

        # Validate marks and attendance
        if not df["Attendance"].between(0, 100).all():
            st.error("Attendance must be between 0 and 100.")
            st.stop()

        if not df[SUBJECTS].apply(
            lambda col: col.between(0, 100).all()
        ).all():
            st.error("Subject marks must be between 0 and 100.")
            st.stop()

        st.success(
            f"Successfully analyzed {len(df)} students!"
        )

        # --------------------------------------------------
        # SUMMARY METRICS
        # --------------------------------------------------

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Total Students",
            len(df)
        )

        c2.metric(
            "Class Average",
            f"{df['Average'].mean():.1f}%"
        )

        c3.metric(
            "Pass Percentage",
            f"{df['Result'].eq('Pass').mean() * 100:.1f}%"
        )

        c4.metric(
            "Average Attendance",
            f"{df['Attendance'].mean():.1f}%"
        )

        st.divider()

        # --------------------------------------------------
        # CHARTS
        # --------------------------------------------------

        left, right = st.columns(2)

        with left:
            subject_averages = (
                df[SUBJECTS]
                .mean()
                .reset_index()
            )

            subject_averages.columns = [
                "Subject",
                "Average Marks"
            ]

            fig1 = px.bar(
                subject_averages,
                x="Subject",
                y="Average Marks",
                color="Subject",
                range_y=[0, 100],
                title="Subject-wise Class Average",
                labels={
                    "Average Marks": "Average Marks (%)"
                }
            )

            st.plotly_chart(
                fig1,
                use_container_width=True
            )

        with right:
            fig2 = px.histogram(
                df,
                x="Average",
                nbins=10,
                title="Student Marks Distribution",
                labels={
                    "Average": "Average Marks (%)"
                }
            )

            st.plotly_chart(
                fig2,
                use_container_width=True
            )

        # --------------------------------------------------
        # PERFORMANCE BREAKDOWN
        # --------------------------------------------------

        st.subheader("📈 Performance Breakdown")

        counts = (
            df["Performance"]
            .value_counts()
            .rename_axis("Category")
            .reset_index(name="Students")
        )

        fig3 = px.pie(
            counts,
            names="Category",
            values="Students",
            hole=0.4,
            title="Students by Performance"
        )

        st.plotly_chart(
            fig3,
            use_container_width=True
        )

        # --------------------------------------------------
        # STUDENT SEARCH AND FILTER
        # --------------------------------------------------

        st.subheader("👩‍🎓 Student Records")

        search = st.text_input(
            "🔍 Search student by name",
            placeholder="Enter a student name..."
        )

        filtered = df.copy()

        # Search by student name
        if search:
            filtered = filtered[
                filtered["Student"]
                .astype(str)
                .str.contains(
                    search,
                    case=False,
                    na=False,
                    regex=False
                )
            ]

        # Filter by performance
        categories = st.multiselect(
            "Filter by performance category",
            options=df["Performance"].unique().tolist(),
            default=df["Performance"].unique().tolist()
        )

        filtered = filtered[
            filtered["Performance"].isin(categories)
        ]

        st.caption(
            f"Showing {len(filtered)} of {len(df)} students"
        )

        st.dataframe(
            filtered.sort_values(
                "Average",
                ascending=False
            ),
            use_container_width=True,
            hide_index=True
        )

        # --------------------------------------------------
        # DOWNLOAD REPORT
        # --------------------------------------------------

        csv_data = filtered.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="⬇️ Download Analyzed CSV Report",
            data=csv_data,
            file_name="student_performance_report.csv",
            mime="text/csv"
        )

        # --------------------------------------------------
        # KEY INSIGHTS
        # --------------------------------------------------

        st.subheader("💡 Key Insights")

        subject_means = df[SUBJECTS].mean()

        best_subject = subject_means.idxmax()
        weakest_subject = subject_means.idxmin()

        at_risk_count = (
            df["Performance"] == "At Risk"
        ).sum()

        col1, col2, col3 = st.columns(3)

        col1.info(
            f"🏆 Highest class average: {best_subject}"
        )

        col2.warning(
            f"📚 Lowest class average: {weakest_subject}"
        )

        col3.error(
            f"⚠️ At-risk students: {at_risk_count}"
        )

    except Exception as error:
        st.error(
            f"Unable to process the file: {error}"
        )

else:
    st.info(
        "Upload students.csv to view your dashboard."
    )

    st.write("Your CSV must contain these columns:")

    st.code(
        "Student,Math,Science,English,Attendance"
    )