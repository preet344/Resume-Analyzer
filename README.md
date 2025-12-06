# 🎯 AI Resume Analyzer (Gemini + Streamlit + n8n)

An **AI-powered Resume vs Job Description matching system** built using **Streamlit**, **Google Gemini API**, and **n8n automation**.  
This tool analyzes resumes, calculates a match score, extracts skills, highlights gaps, and generates a professional HR-ready summary in a modern ATS-style dashboard.

---

## 🚀 Features

✅ Upload resume in **PDF format**  
✅ Paste **Job Description**  
✅ AI-generated **Match Score (0–100)**  
✅ Extracts:
- Candidate Name  
- Email  
- Experience Level  
- Skills  
- Matching Skills  
- Missing Skills  

✅ **Professional HR Summary (No Raw JSON Displayed)**  
✅ **Interactive Match Score Gauge**  
✅ **Modern ATS-Style UI Dashboard**  
✅ **Send candidate data to n8n workflow automatically**  
✅ Secure environment-based API key handling  

---
## Main Dashboard
<img width="957" height="385" alt="image" src="https://github.com/user-attachments/assets/81f8a3e4-c330-4f81-983c-bf5dce6162f4" />

<img width="865" height="395" alt="image" src="https://github.com/user-attachments/assets/bd56b156-2a31-46a8-95fc-df648f0cf435" />

<img width="931" height="361" alt="image" src="https://github.com/user-attachments/assets/1ec2903a-d593-47d7-a70f-4cc6b8b7648f" />

## N8N Workflow Image

<img width="751" height="215" alt="image" src="https://github.com/user-attachments/assets/c051091c-1fbd-4f8c-a453-357549f0628d" />


## 🛠️ Tech Stack

- **Frontend:** Streamlit  
- **AI Model:** Google Gemini (gemini-2.5-flash)  
- **PDF Processing:** PyPDF2  
- **Charts:** Plotly  
- **Automation:** n8n Webhook  
- **Backend:** Python  
- **API Handling:** Requests  

---

## 📂 Project Structure

📦 ai-resume-analyzer

┣ 📜 app.py

┣ 📜 requirements.txt

┣ 📜 README.md

┣ 📜 .env

┗ 📜 .streamlit/secrets.toml

---

## 🔐 Environment Setup

### ✅ 1. Create `.env` File (For Local Setup)
GEMINI_API_KEY=your_gemini_api_key_here

N8N_WEBHOOK_URL=your_n8n_webhook_url_here

### ✅ 2. For Streamlit Cloud Deployment

#### Create file:

.streamlit/secrets.toml


#### Add:

GEMINI_API_KEY="your_gemini_api_key_here"

N8N_WEBHOOK_URL="your_n8n_webhook_url_here"

## 📦 Install Dependencies

pip install -r requirements.txt

### ✅ `requirements.txt`

streamlit

google-generativeai

PyPDF2

plotly

requests

python-dotenv

## ▶️ Run the Application

streamlit run app.py


The app will open automatically in your browser.

---

## 📊 How It Works

1. Upload a **Resume PDF**
2. Paste the **Job Description**
3. Click **Analyze Resume**
4. Gemini AI:
   - Extracts candidate information
   - Matches skills with job requirements
   - Calculates match percentage
   - Generates professional summary
5. Results appear in a **clean ATS-style dashboard**
6. Candidate data is automatically sent to **n8n workflow**

---

## 🔄 n8n Webhook Payload Format

<img width="295" height="183" alt="image" src="https://github.com/user-attachments/assets/c0b67dd2-a803-4fc6-9e81-451b01a3fc16" />

#### You can connect this to:

---- Google Sheets

---- Notion

---- Email automation

---- CRM

---- ATS systems

## 📸 UI Highlights

📊 Match Score Gauge

👤 Candidate Profile Card

✅ Matching Skills Panel

⚠️ Missing Skills Panel

📝 Professional Summary Section

📤 Workflow Automation Button

## 🔒 Security

✅ API keys are never hardcoded

✅ Environment variable protection

✅ Gemini failures handled safely

✅ JSON validation & fallback protection

✅ n8n webhook secured by secret URL

## 📈 Future Enhancements

✅ Bulk Resume Upload

✅ Candidate Ranking System

✅ Download Candidate Report as PDF

✅ Shortlist & Reject Buttons

✅ Resume Database

✅ Admin Dashboard

✅ Login System

✅ SaaS Deployment

✅ Email Automation

✅ Subscription Billing

## 👨‍💻 Author

Developed by: Preet tyagi

Role: Data Analyst

Project Type: AI-Powered ATS & Recruitment Automation System

