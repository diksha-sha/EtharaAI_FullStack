# Email Automation System

## Overview

The Email Automation System is an AI-powered application that generates and sends personalized emails automatically based on user data. It uses local large language models (LLMs) through Ollama to create dynamic email content. The system supports bulk email generation and is useful for automation in marketing, HR communication, and notifications.

---

## Features

- Automated email generation using AI models  
- Personalized content based on user data  
- Multiple LLM support (Mistral, Llama3, Phi3)  
- Automatic fallback between models  
- Bulk email generation from Excel/CSV files  
- Flask-based backend API  
- SMTP email sending integration  
- Local execution using Ollama  

---

## Tech Stack

- Python  
- Flask  
- Ollama (Mistral, Llama3, Phi3)  
- Pandas  
- NumPy  
- OpenPyXL  
- SMTP  
- dotenv  

---

## Project Structure


email-automation/
│
├── backend/
│ ├── app.py
│ ├── email_generator.py
│ ├── models.py
│ ├── utils.py
│ └── config.py
│
├── data/
│ └── input.xlsx
│
├── templates/
│ └── email_template.html
│
├── requirements.txt
├── .env
└── README.md


---

## Installation

### Clone Repository
```bash
git clone https://github.com/your-username/email-automation.git
cd email-automation
Create Virtual Environment
python -m venv venv
venv\Scripts\activate
Install Dependencies
pip install -r requirements.txt
Ollama Setup

Install Ollama and pull required models:

ollama pull mistral
ollama pull llama3
ollama pull phi3
Run Project
cd backend
python app.py

Server runs at:

http://127.0.0.1:5000
Workflow
User provides input data (Excel/CSV)
System processes the data
AI model generates email content
Email is sent via SMTP
Logs are stored for tracking
Model Strategy
Mistral: Fast and balanced output
Llama3: High-quality detailed responses
Phi3: Lightweight and quick processing

Automatic fallback ensures reliability.

Environment Variables

Create a .env file:

EMAIL_USER=your_email@example.com
EMAIL_PASS=your_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
OLLAMA_URL=http://localhost:11434
Use Cases
Marketing email automation
HR outreach emails
Bulk notification systems
Personalized email campaigns
Future Improvements
Web dashboard for email tracking
Email scheduling system
MongoDB integration
Analytics for open/click rates
Multi-language support
