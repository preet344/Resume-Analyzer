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
# ⚙️ Gemini Config
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
# 🎨 UI Styling
# =======================
st.markdown("""
<style>
.main-title {font-size:42px;font-weight:800;color:#4CAF50;text-align:center;}
.subtitle {text-align:center;font-size:18px;color:#888;margin-bottom:30px;}
.card {background:#111;padding:20px;border-radius:16px;border:1px solid #333;margin-bottom:20px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🎯 AI Resume Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload a resume and match it with any job description using Gemini AI</div>', unsafe_allow_html=True)

# =======================
# 🛠️ Helper Functions
# =======================

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += (page.extract_text() or "")
    return text[:3000]  # ✅ Speed boost


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

    model = genai.GenerativeModel(
        "gemini-2.5-flash",
        generation_config={
            "temperature": 0.3,
            "max_output_tokens": 400
        }
    )

    response = model.generate_content(prompt)
    response_text = response.text.strip()

    if response_text.startswith("```json"):
        response_text = response_text[7:-3]
    elif response_text.startswith("```"):
        response_text = response_text[3:-3]

    return json.loads(response_text.strip())


def create_score_gauge(score):
    color = "green" if score >= 75 else "orange" if score >= 50 else "red"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": "Match Score"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": color},
            "threshold": {"line": {"color": "red", "width": 4}, "value": 75}
        }
    ))

    fig.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=10))
    return fig


def create_skills_chart(matching, missing):
    fig = go.Figure([
        go.Bar(name="Matching", x=["Skills"], y=[len(matching)]),
        go.Bar(name="Missing", x=["Skills"], y=[len(missing)])
    ])

    fig.update_layout(title="Skills Analysis", height=300, barmode="group")
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
# 📥 Input UI
# =======================
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📄 Upload Resume")
    resume_file = st.file_uploader("Drag & drop PDF", type=["pdf"])
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("💼 Job Description")
    job_desc = st.text_area("Paste JD here", height=160)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

center_col = st.columns([1, 2, 1])[1]
with center_col:
    analyze_clicked = st.button("🚀 Analyze Resume", type="primary", use_container_width=True)

# =======================
# 🔍 Analysis
# =======================
if analyze_clicked:

    if not resume_file:
        st.error("❌ Please upload a resume")

    elif not job_desc.strip():
        st.error("❌ Please enter job description")

    else:
        with st.spinner("🤖 Analyzing with Gemini AI..."):

            try:
                resume_text = extract_text_from_pdf(resume_file)
                results = analyze_with_gemini(resume_text, job_desc)

                st.markdown('<div class="card">', unsafe_allow_html=True)
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

                st.subheader("👤 Candidate Details")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**Email:** {results['email']}")
                    st.markdown(f"**Experience:** {results['experience']}")

                with col2:
                    st.markdown("**Top Skills**")
                    for skill in results["skills"][:5]:
                        st.markdown(f"- {skill}")

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

                st.subheader("📝 Summary")
                st.info(results["summary"])

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

                st.markdown('</div>', unsafe_allow_html=True)

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
    st.markdown("### 🔌 System Status")

    col1, col2 = st.columns(2)

    with col1:
        if GEMINI_API_KEY:
            st.success("✅ Gemini")
        else:
            st.error("❌ Gemini")

    with col2:
        if N8N_WEBHOOK_URL:
            st.success("✅ n8n")
        else:
            st.warning("⚠️ n8n")
