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
.box {background:#111;padding:20px;border-radius:16px;border:1px solid #333;margin-bottom:20px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🎯 AI Resume Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Gemini-powered Resume vs Job Description Matcher</div>', unsafe_allow_html=True)

# =======================
# 🛠️ Helper Functions
# =======================

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += (page.extract_text() or "")
    return text[:3000]


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

    try:
        raw_text = ""
        for cand in response.candidates:
            for part in cand.content.parts:
                if hasattr(part, "text"):
                    raw_text += part.text
        raw_text = raw_text.strip()
    except:
        raw_text = ""

    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)

    if not json_match:
        return fallback_result("Gemini failed to return proper data.")

    json_text = json_match.group(0)

    try:
        return json.loads(json_text)
    except:
        return fallback_result("Gemini returned broken JSON.")


def fallback_result(message):
    return {
        "score": 0,
        "name": "N/A",
        "email": "N/A",
        "experience": "N/A",
        "skills": [],
        "matching_skills": [],
        "missing_skills": [],
        "summary": message
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


# ✅ ✅ ✅ Final Clean n8n Sender (No UI spam)
def send_to_n8n(data):
    if not N8N_WEBHOOK_URL:
        return False

    payload = {
        "candidate_name": data.get("name"),
        "email": data.get("email"),
        "score": data.get("score"),
        "experience": data.get("experience"),
        "skills": data.get("skills"),
        "matching_skills": data.get("matching_skills"),
        "missing_skills": data.get("missing_skills"),
        "summary": data.get("summary")
    }

    try:
        res = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=15)
        return res.status_code == 200
    except:
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

            st.header("📊 Candidate Analysis Report")

            st.plotly_chart(create_score_gauge(results["score"]), use_container_width=True)

            col1, col2, col3 = st.columns(3)
            col1.metric("Match Score", f"{results['score']}%")
            col2.metric("Candidate Name", results["name"])
            col3.metric("Experience", results["experience"])

            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("✅ Key Strengths")
                st.markdown(", ".join(results["matching_skills"]) if results["matching_skills"] else "No strong matches detected.")

            with col2:
                st.subheader("⚠️ Improvement Areas")
                st.markdown(", ".join(results["missing_skills"]) if results["missing_skills"] else "No major gaps detected.")

            st.markdown("---")

            st.subheader("📝 Professional Summary")
            st.success(results["summary"])

            st.markdown("---")

            success = send_to_n8n(results)

            if success:
                st.success("✅ Candidate data sent to n8n workflow successfully!")
            else:
                st.warning("⚠️ n8n webhook not connected.")
