import streamlit as st
import google.generativeai as genai
import PyPDF2
import plotly.graph_objects as go
import requests
import json
import os

# =======================
# 🔐 Load Secrets
# =======================

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    N8N_WEBHOOK_URL = st.secrets["N8N_WEBHOOK_URL"]
except:
    from dotenv import load_dotenv
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

# =======================
# ⚙️ Gemini Configuration
# =======================

genai.configure(api_key=GEMINI_API_KEY)

# =======================
# 📐 Page Config
# =======================

st.set_page_config(
    page_title="Resume Analyzer",
    page_icon="📄",
    layout="wide"
)

# =======================
# 🛠️ Helper Functions
# =======================

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


def analyze_with_gemini(resume_text, job_description):

    prompt = f"""
Analyze this resume against the job description and respond ONLY with valid JSON (no markdown, no backticks).

Resume:
{resume_text}

Job Description:
{job_description}

Respond with this exact JSON format:
{{
    "score": <number 0-100>,
    "name": "<candidate name>",
    "email": "<email or N/A>",
    "experience": "<years/level>",
    "skills": ["skill1", "skill2", "skill3"],
    "matching_skills": ["skill1", "skill2"],
    "missing_skills": ["skill1", "skill2"],
    "summary": "<2-3 sentence summary>"
}}

Score: 75-100=Excellent, 50-74=Good, 0-49=Poor
"""

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    response_text = response.text.strip()

    if response_text.startswith("```json"):
        response_text = response_text[7:-3]
    elif response_text.startswith("```"):
        response_text = response_text[3:-3]

    return json.loads(response_text.strip())


def create_score_gauge(score):

    color = "green" if score >= 75 else "orange" if score >= 50 else "red"

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Match Score", "font": {"size": 20}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": color},
                "steps": [
                    {"range": [0, 50], "color": "lightgray"},
                    {"range": [50, 75], "color": "lightyellow"},
                    {"range": [75, 100], "color": "lightgreen"}
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": 75
                }
            }
        )
    )

    fig.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=10))
    return fig


def create_skills_chart(matching, missing):

    fig = go.Figure([
        go.Bar(name="Matching", x=["Skills"], y=[len(matching)], marker_color="green"),
        go.Bar(name="Missing", x=["Skills"], y=[len(missing)], marker_color="red")
    ])

    fig.update_layout(
        title="Skills Analysis",
        height=300,
        showlegend=True,
        barmode="group"
    )

    return fig


def send_to_n8n(data):

    if N8N_WEBHOOK_URL:
        try:
            response = requests.post(N8N_WEBHOOK_URL, json=data, timeout=10)
            return response.status_code == 200
        except:
            return False
    return False


# =======================
# 🖥️ App UI
# =======================

st.title("🎯 Resume Analyzer")
st.markdown("Upload a resume PDF and paste a job description for instant AI analysis.")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Upload Resume")
    resume_file = st.file_uploader("Upload PDF", type=["pdf"])

with col2:
    st.subheader("💼 Job Description")
    job_desc = st.text_area("Paste job description here", height=150)

st.markdown("")

# =======================
# 🔎 Analyze Button
# =======================

if st.button("🔍 Analyze", type="primary", use_container_width=True):

    if not resume_file:
        st.error("❌ Please upload a resume")

    elif not job_desc.strip():
        st.error("❌ Please enter job description")

    else:
        with st.spinner("🤖 Analyzing with Gemini AI..."):

            try:
                resume_text = extract_text_from_pdf(resume_file)
                results = analyze_with_gemini(resume_text, job_desc)

                st.success("✅ Analysis Complete!")
                st.markdown("---")
                st.header("📊 Analysis Results")

                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.plotly_chart(create_score_gauge(results["score"]), use_container_width=True)

                with col2:
                    st.metric("Score", f"{results['score']}%")

                    if results["score"] >= 75:
                        st.success("✅ Excellent Match")
                    elif results["score"] >= 50:
                        st.warning("⚠️ Good Match")
                    else:
                        st.error("❌ Poor Match")

                with col3:
                    st.metric("Name", results["name"])
                    st.metric("Experience", results["experience"])

                st.markdown("---")
                st.subheader("👤 Candidate Details")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**Email:** {results['email']}")
                    st.markdown(f"**Experience:** {results['experience']}")

                with col2:
                    st.markdown("**Top Skills**")
                    for skill in results["skills"][:5]:
                        st.markdown(f"- {skill}")

                st.markdown("---")

                col1, col2 = st.columns(2)

                with col1:
                    st.plotly_chart(
                        create_skills_chart(
                            results["matching_skills"],
                            results["missing_skills"]
                        ),
                        use_container_width=True
                    )

                with col2:
                    st.markdown("### ✅ Matching Skills")
                    for skill in results["matching_skills"][:5]:
                        st.markdown(f"- {skill}")

                    st.markdown("### ❌ Missing Skills")
                    for skill in results["missing_skills"][:5]:
                        st.markdown(f"- {skill}")

                st.markdown("---")
                st.subheader("📝 Summary")
                st.info(results["summary"])

                st.markdown("---")

                email_data = {
                    "name": results["name"],
                    "email": results["email"],
                    "score": results["score"],
                    "experience": results["experience"],
                    "skills": ", ".join(results["skills"][:5]),
                    "summary": results["summary"]
                }

                if send_to_n8n(email_data):
                    st.success("📊 Data sent to automation workflow!")
                else:
                    st.warning("⚠️ n8n webhook not configured")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


# =======================
# 📌 Sidebar
# =======================

with st.sidebar:

    st.header("ℹ️ Score Guide")

    st.markdown("""
    - **75–100:** Excellent Match ✅  
    - **50–74:** Good Match ⚠️  
    - **0–49:** Poor Match ❌  
    """)

    st.markdown("---")

    st.markdown("### 💡 Why Use Resume Analyzer?")
    st.markdown("""
    - Instant resume vs JD comparison
    - Highlights skills and experience
    - Saves recruiter time
    - Data-driven hiring decisions
    """)

    st.markdown("---")
    st.markdown("### 🔌 System Status")

    if GEMINI_API_KEY:
        st.success("✅ Gemini API Connected")
    else:
        st.error("❌ Add GEMINI_API_KEY to secrets")

    if N8N_WEBHOOK_URL:
        st.success("✅ n8n Webhook Ready")
    else:
        st.warning("⚠️ Add N8N_WEBHOOK_URL to secrets")
