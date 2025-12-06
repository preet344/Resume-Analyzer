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
except Exception:
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
st.markdown(
    """
<style>
.main-title {font-size:42px;font-weight:800;color:#4CAF50;text-align:center;margin-bottom:6px;}
.subtitle {text-align:center;font-size:16px;color:#666;margin-bottom:20px;}
.box {background:#f8f9fb;padding:18px;border-radius:12px;border:1px solid #e6e9ef;margin-bottom:16px;}
.metric-large {font-size:28px;font-weight:700;color:#333;}
.small-muted {color:#777;font-size:13px;}
h3 {margin-bottom:6px;}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">🎯 AI Resume Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Gemini-powered Resume vs Job Description Matcher</div>', unsafe_allow_html=True)

# =======================
# 🛠️ Helper Functions
# =======================


def extract_text_from_pdf(pdf_file):
    """Extract text from PDF (first ~3000 chars to control prompt size)."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += (page.extract_text() or "")
        return text[:3000]
    except Exception:
        return ""


def analyze_with_gemini(resume_text, job_description):
    """
    Send prompt to Gemini and return parsed JSON.
    This function tolerates code fences and attempts to extract the first JSON object.
    """
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
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
    except Exception as e:
        # Gemini call failed
        return fallback_result("Gemini API call failed: " + str(e))

    # Collect text parts robustly
    raw_text = ""
    try:
        for cand in response.candidates:
            for part in cand.content.parts:
                if hasattr(part, "text"):
                    raw_text += part.text
        raw_text = raw_text.strip()
    except Exception:
        raw_text = ""

    # Remove markdown code fences if present
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    # Extract first JSON-looking substring
    json_match = re.search(r"\{(?:[^{}]|\{[^}]*\})*\}", raw_text, re.DOTALL)
    if not json_match:
        return fallback_result("Gemini failed to return proper data.")

    json_text = json_match.group(0)

    try:
        parsed = json.loads(json_text)
        # Basic normalization: ensure keys exist
        for key in ["score", "name", "email", "experience", "skills", "matching_skills", "missing_skills", "summary"]:
            if key not in parsed:
                parsed[key] = [] if key.endswith("_skills") or key == "skills" else "N/A" if key != "score" else 0
        # Ensure numeric score
        try:
            parsed["score"] = int(parsed.get("score", 0))
            if parsed["score"] < 0:
                parsed["score"] = 0
            if parsed["score"] > 100:
                parsed["score"] = min(parsed["score"], 100)
        except Exception:
            parsed["score"] = 0
        return parsed
    except Exception:
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
        "summary": message,
    }


def create_score_gauge(score):
    """Create a Plotly gauge for the match score."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "%", "font": {"size": 36}},
            title={"text": "Match Score", "font": {"size": 16}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#198754"},
                "steps": [
                    {"range": [0, 50], "color": "#f8d7da"},
                    {"range": [50, 75], "color": "#fff3cd"},
                    {"range": [75, 100], "color": "#d1e7dd"},
                ],
            },
            domain={"x": [0, 1], "y": [0, 1]},
        )
    )
    fig.update_layout(height=260, margin={"t": 20, "b": 0, "l": 0, "r": 0})
    return fig


def send_to_n8n(data):
    """
    Send sanitized candidate data to n8n webhook.
    Returns True if successful (HTTP 200), False otherwise.
    """
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
        "summary": data.get("summary"),
    }

    try:
        res = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=15)
        return res.status_code == 200
    except Exception:
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
# 🔍 Analysis & Modern Report UI
# =======================
if analyze_clicked:
    if not resume_file:
        st.error("Please upload a resume PDF.")
    elif not job_desc.strip():
        st.error("Please paste the job description.")
    else:
        with st.spinner("Analyzing with Gemini..."):
            resume_text = extract_text_from_pdf(resume_file)
            results = analyze_with_gemini(resume_text, job_desc)

        # Top header
        st.markdown("## 📊 Candidate Analysis Report")

        # --- TOP: Gauge + Candidate Card ---
        top_col1, top_col2 = st.columns([1, 2])

        with top_col1:
            st.plotly_chart(create_score_gauge(results["score"]), use_container_width=True)

        with top_col2:
            # Candidate info box
            st.markdown(
                f"""
<div class="box">
  <h3>👤 Candidate Profile</h3>
  <p class="small-muted"><b>Name:</b> {results.get("name", "N/A")}</p>
  <p class="small-muted"><b>Email:</b> {results.get("email", "N/A")}</p>
  <p class="small-muted"><b>Experience Level:</b> {results.get("experience", "N/A")}</p>
  <p class="small-muted"><b>Match Score:</b> <span class="metric-large">{results.get("score", 0)}%</span></p>
</div>
""",
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # --- SKILLS: Matching vs Missing ---
        skill_col1, skill_col2 = st.columns(2)

        with skill_col1:
            st.markdown('<div class="box"><h3>✅ Key Matching Skills</h3>', unsafe_allow_html=True)
            if results.get("matching_skills"):
                for s in results["matching_skills"]:
                    st.markdown(f"- ✅ {s}")
            else:
                st.markdown("No strong matches detected.")
            st.markdown("</div>", unsafe_allow_html=True)

        with skill_col2:
            st.markdown('<div class="box"><h3>⚠️ Missing / Improvement Areas</h3>', unsafe_allow_html=True)
            if results.get("missing_skills"):
                for s in results["missing_skills"]:
                    st.markdown(f"- ❌ {s}")
            else:
                st.markdown("No major gaps detected.")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        # --- PROFESSIONAL SUMMARY ---
        st.markdown(
            f"""
<div class="box">
  <h3>📝 Professional Summary</h3>
  <p style="font-size:15px;line-height:1.6;">{results.get("summary", "No summary available.")}</p>
</div>
""",
            unsafe_allow_html=True,
        )

        # --- ACTIONS: Send to n8n / Download (basic) ---
        action_col1, action_col2 = st.columns([1, 1])
        with action_col1:
            if st.button("📤 Send candidate to workflow (n8n)"):
                ok = send_to_n8n(results)
                if ok:
                    st.success("✅ Candidate data sent to n8n workflow successfully!")
                else:
                    st.error("❌ Failed to send to n8n. Check webhook URL or network.")

        # Optional lightweight JSON viewer (hidden by default behind an expander)
        with st.expander("🔎 Debug: Raw parsed result (hidden)"):
            st.json(results)
