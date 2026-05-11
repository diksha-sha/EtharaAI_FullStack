# EtharaAI_FullStack

Email Automation System
Overview

The Email Automation System is an AI-powered application designed to generate and send personalized emails automatically based on user data. It uses local large language models (LLMs) through Ollama to create dynamic, context-aware email content. The system supports bulk data processing and is suitable for marketing, HR communication, and automated notifications.

Features
Automated email generation using AI models
Personalized email content based on user data
Support for multiple LLMs (Mistral, Llama3, Phi3)
Model fallback mechanism for reliability
Bulk email generation from Excel/CSV files
Flask-based backend API
Integration with SMTP for email sending
Lightweight local execution using Ollama
Tech Stack
Python
Flask
Ollama (Mistral, Llama3, Phi3)
Pandas
NumPy
OpenPyXL
SMTP (Email Service)
dotenv
Project Structure
email-automation/
│
├── backend/
│   ├── app.py
│   ├── email_generator.py
│   ├── models.py
│   ├── utils.py
│   └── config.py
│
├── data/
│   └── input.xlsx
│
├── templates/
│   └── email_template.html
│
├── requirements.txt
├── .env
└── README.md
Installation
Step 1: Clone the Repository
git clone https://github.com/your-username/email-automation.git
cd email-automation
Step 2: Create Virtual Environment
python -m venv venv
venv\Scripts\activate   (Windows)
Step 3: Install Dependencies
pip install -r requirements.txt
Setup Ollama Models

Install Ollama and pull required models:

ollama pull mistral
ollama pull llama3
ollama pull phi3
Running the Project

Navigate to backend and start the server:

cd backend
python app.py

The application will run at:

http://127.0.0.1:5000
Workflow
Input data is provided in Excel/CSV format
Backend processes and extracts user information
AI model generates personalized email content
Email is sent using SMTP configuration
Logs are maintained for tracking and debugging
Model Selection Strategy

The system uses multiple models for better reliability:

Mistral: Fast and balanced performance
Llama3: High-quality detailed responses
Phi3: Lightweight and efficient processing

If one model fails, the system automatically switches to another.

Environment Variables

Create a .env file in the root directory:

EMAIL_USER=your_email@example.com
EMAIL_PASS=your_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
OLLAMA_URL=http://localhost:11434
Use Cases
Automated marketing email campaigns
HR recruitment and outreach emails
Bulk notification systems
Personalized communication automation
Future Improvements
Web dashboard for monitoring email campaigns
Email scheduling system
MongoDB cloud integration
Analytics for open rate and engagement tracking
Multi-language email generation
