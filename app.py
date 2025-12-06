import streamlit as st
import google.generativeai as genai
import PyPDF2
import plotly.graph_objects as go
import requests
import json
import os
import re

# =======================
# 🔐 Load Secrets
# =======================
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    N8N_WEBHOOK_URL = st.secrets.get("N8N_WEBHOOK_URL", "")
except:
    from dotenv import load_dotenv
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")

# =======================
# ⚙️ Gemini Config
# =======================
genai.configure(api_key=GEMINI_API_KEY)

# =======================
# 📐 Page Config
# =======================
st.set_page_config(page_title="Resume Analyzer", page_icon="📄", layout="wide")

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
st.markdown('<div class="subtitle">Gemini-powered resume vs job description matcher</div>', unsafe_allow_html=True)

# =======================
# 🛠️ Helper Functions
# =======================

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += (page.extract_text() or "")
    return text[:3000]


# ✅ ✅ ✅ ABSOLUTE SAFE GEMINI HANDLER
def analyze_with_gemini(resume_text, job_description):

    prompt = f"""
Return ONLY valid raw JSON. No explanation. No markdown.

Resume:
{resume_text}

Job Description:
{job_description}

JSON FORMAT:
{{
  "score": 0,
  "name": "N/A",
  "email": "N/A",
  "experience": "N/A",
  "skills": [],
  "matching_skills": [],
  "missing_skills": [],
  "summary": "N/A"
}}
"""

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    # ✅ Ultra-safe text extraction for ALL Gemini formats
    try:
        raw_text = ""
        for cand in response.candidates:
            for part in cand.content.parts:
                if hasattr(part, "text"):
                    raw_text += part.text
        raw_text = raw_text.strip()
    except:
        raw_text = ""

    # ✅ Strip markdown if added
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    # ✅ Auto-extract JSON if Gemini adds garbage text
    json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)

    if not json_match:
        return {
            "score": 0,
            "name": "N/A",
            "email": "N/A",
            "experience": "N/A",
            "skills": [],
            "matching_skills": [],
            "missing_skills": [],
            "summary": "Gemini failed to return valid data."
        }

    json_text = json_match.group(0)

    try:
        return json.loads(json_text)
    except:
        return {
            "score": 0,
            "name": "N/A",
            "email": "N/A",
            "experience": "N/A",
            "skills": [],
            "matching_skills": [],
            "missing_skills": [],
            "summary": "Gemini response could not be parsed."
        }


def create_score_gauge(score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": "Match Score"},
        gauge={"axis": {"range": [0, 100]}}
    ))
    fig.update_layout(height=250)
    return fig


def create_skills_chart(matching, missing):
    fig = go.Figure([
        go.Bar(name="Matching", x=["Skills"], y=[len(matching)]),
        go.Bar(name="Missing", x=["Skills"], y=[len(missing)])
    ])
    fig.update_layout(title="Skills Analysis", barmode="group")
    return fig


def send_to_n8n(data):
    if N8N_WEBHOOK_URL:
        try:
            requests.post(N8N_WEBHOOK_URL, json=data, timeout=10)
            return True
        except:
            return False
    return False


# =======================
# 📥 Input UI
# =======================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Upload Resume (PDF)")
    resume_file = st.file_uploader("Upload PDF", type=["pdf"])

with col2:
    st.subheader("💼 Job Description")
    job_desc = st.text_area("Paste JD", height=160)

analyze_clicked = st.button("🚀 Analyze Resume", type="primary")

# =======================
# 🔍 Analysis
# =======================
if analyze_clicked:

    if not resume_file:
        st.error("Upload resume")
    elif not job_desc.strip():
        st.error("Enter job description")
    else:
        with st.spinner("Analyzing with Gemini..."):

            resume_text = extract_text_from_pdf(resume_file)
            results = analyze_with_gemini(resume_text, job_desc)

            st.header("📊 Results")

            st.plotly_chart(create_score_gauge(results["score"]), use_container_width=True)

            st.metric("Score", f"{results['score']}%")
            st.metric("Name", results["name"])
            st.metric("Experience", results["experience"])

            st.subheader("✅ Matching Skills")
            st.write(results["matching_skills"])

            st.subheader("❌ Missing Skills")
            st.write(results["missing_skills"])

            st.subheader("📝 Summary")
            st.info(results["summary"])

            send_to_n8n(results)
