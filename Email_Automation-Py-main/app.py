# Flask
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_from_directory

# Environment variables
from dotenv import load_dotenv

# Database
from pymongo import MongoClient
from bson.objectid import ObjectId

# Load environment variables from .env file
load_dotenv()

# Data processing
import pandas as pd

# Standard libraries
import os
from datetime import datetime
from functools import wraps

# Email functions
from send_email import send_email_with_attachment, send_email_with_logo_base64

# AI Email Generator
from ai_email_generator import generate_email

try:
    from bson.objectid import ObjectId
except ImportError:
    from bson import ObjectId

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_secret_key_here")
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["ATTACHMENTS_FOLDER"] = "attachments"

# Create folders if they don't exist
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])
if not os.path.exists(app.config["ATTACHMENTS_FOLDER"]):
    os.makedirs(app.config["ATTACHMENTS_FOLDER"])

# MongoDB Connection
mongodb_uri = os.getenv("MONGODB_URI", "mongodb+srv://Prompt_em:asdfghjkl@cluster0.o9em7j3.mongodb.net/")
mongodb_database = os.getenv("MONGODB_DATABASE", "email_generator")
client = MongoClient(mongodb_uri)
db = client[mongodb_database]

# Collections
recipients_collection = db["recipients"]
users_collection = db["users"]
settings_collection = db["settings"]
prompts_collection = db["prompts"]
email_accounts_collection = db["email_accounts"]
global_cc_collection = db["global_cc"]
logs_collection = db["logs"]
signatures_collection = db["signatures"]


# ============================================
# INITIALIZATION FUNCTIONS
# ============================================

def initialize_prompts():
    default_prompts = [
        {"id": 1, "name": "Business Proposal", "template": """You are writing the email as Hansraj Ventures Private Limited, a staffing and recruitment company.

Draft a professional hiring support email responding to the following requirement.

Instructions:
- Address the client who posted the requirement
- Position Hansraj Ventures as a staffing partner
- Keep it concise, professional, and business-focused (150-180 words)
- Maintain a confident but polite tone

Include:
1. Professional greeting
2. Brief understanding of the hiring requirement
3. Hiring models: Contractual, Contract-to-hire, Full-time staffing
4. Screening and validation approach
5. Short meeting request
6. Mention company profile attachment
7. Professional closing

Do NOT include signature - it will be added automatically.

Hiring Requirement: {requirement}"""},
        {"id": 2, "name": "Quick Hiring Support Pitch", "template": "Draft a short hiring support email for the below requirement from Hansraj Ventures. Include: Quick understanding of roles, Immediate sourcing capability, Flexible engagement models, 15-minute meeting request, Mention attachments. Keep it crisp, under 200 words. Do NOT include signature. Requirement: {requirement}"},
        {"id": 3, "name": "Strategic Staffing Partnership Proposal", "template": "Write a professional hiring collaboration email positioning Hansraj Ventures as a long-term staffing partner. Include: Strategic hiring approach, Performance-driven screening, Contractual + permanent hiring options, Meeting proposal. Tone: Confident, structured. Do NOT include signature. Requirement: {requirement}"},
        {"id": 4, "name": "Contractual Hiring Proposal", "template": "Prepare a hiring proposal email focused on contractual on-site and task-based hiring. Include: Risk reduction benefits, Cost optimization, Flexible scaling, Quick meeting request. Keep it simple and professional. Do NOT include signature. Requirement: {requirement}"},
        {"id": 5, "name": "Urgent Hiring Support Email", "template": "Draft a professional hiring support email for urgent requirement. Emphasize: Fast-track sourcing, Pre-screened talent pool, Immediate interview coordination, 24-hour initiation timeline. Keep it short and impactful. Do NOT include signature. Requirement: {requirement}"},
        {"id": 6, "name": "Structured Hiring Proposal Email", "template": "Generate a structured hiring proposal email with: Greeting, Understanding of requirement, Engagement models, Screening process, Meeting request, Mention attachments, Professional closing. Do NOT include signature. Requirement: {requirement}"},
        {"id": 7, "name": "Short Hiring Collaboration Pitch", "template": "Write a compact hiring collaboration email for LinkedIn or WhatsApp. Include: Understanding of roles, Contractual + full staffing support, Quick meeting request, Attachments mention. Under 170 words. Do NOT include signature. Requirement: {requirement}"}
    ]
    if prompts_collection.count_documents({}) == 0:
        prompts_collection.insert_many(default_prompts)
        print("Default prompts initialized in MongoDB")


def initialize_global_cc():
    default_cc = [
        {"email": "manager@hansrajventures.com", "name": "Manager"},
        {"email": "hr@hansrajventures.com", "name": "HR Department"},
        {"email": "dhrupalmakwana149@gmail.com", "name": "Dhrupal Makwana"}
    ]
    if global_cc_collection.count_documents({}) == 0:
        global_cc_collection.insert_many(default_cc)
        print("Default global CC emails initialized")


def initialize_admin():
    admin = users_collection.find_one({"username": "admin", "role": "admin"})
    if not admin:
        users_collection.insert_one({
            "username": "admin",
            "password": "admin123",
            "role": "admin",
            "created_at": datetime.now()
        })
        print("Default admin created: admin / admin123")
    elif not admin.get("password"):
        users_collection.update_one(
            {"_id": admin["_id"]},
            {"$set": {"password": "admin123"}}
        )
        print("Existing admin account had no password; default admin123 has been restored")


def get_prompts_from_db():
    prompts = list(prompts_collection.find({}))
    for p in prompts:
        p["_id"] = str(p["_id"])
    prompts.sort(key=lambda x: x.get("id", 0), reverse=True)
    return prompts


def get_global_cc():
    cc_emails = list(global_cc_collection.find({}))
    for cc in cc_emails:
        cc["_id"] = str(cc["_id"])
    return cc_emails


# Initialize on startup
initialize_prompts()
initialize_global_cc()
initialize_admin()


# ============================================
# ROOT ROUTE
# ============================================

@app.route("/")
def index():
    if "user_id" in session:
        if session.get("role") == "admin":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("user_dashboard"))
    return redirect(url_for("login"))


# ============================================
# AUTHENTICATION MIDDLEWARE
# ============================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            return redirect(url_for("user_dashboard"))
        return f(*args, **kwargs)
    return decorated_function


def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("login"))
        if session.get("role") != "user":
            return redirect(url_for("admin_dashboard"))
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# AUTHENTICATION ROUTES
# ============================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.get_json()
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        if not username or not password:
            return jsonify({"success": False, "message": "Username and password are required"}), 400

        user = users_collection.find_one({"username": username, "password": password})
        if user:
            session["user_id"] = str(user["_id"])
            session["username"] = user["username"]
            session["role"] = user.get("role", "user")

            if session["role"] == "admin":
                return jsonify({"success": True, "redirect": url_for("admin_dashboard")})
            else:
                return jsonify({"success": True, "redirect": url_for("user_dashboard")})

        user_with_usernames = users_collection.find_one({"username": username})
        if user_with_usernames and not user_with_usernames.get("password"):
            return jsonify({"success": False, "message": "This account exists but has no password set. Please register again or contact the administrator."}), 401

        return jsonify({"success": False, "message": "Invalid username or password"}), 401

    return render_template("login.html")


@app.route("/register", methods=["POST"])
def register():
    if request.method == "POST":
        data = request.get_json()
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        confirm_password = data.get("confirm_password", "").strip()

        if not username or not password:
            return jsonify({"success": False, "message": "Username and password are required"}), 400
        if len(username) < 3:
            return jsonify({"success": False, "message": "Username must be at least 3 characters"}), 400
        if len(password) < 4:
            return jsonify({"success": False, "message": "Password must be at least 4 characters"}), 400
        if password != confirm_password:
            return jsonify({"success": False, "message": "Passwords do not match"}), 400

        existing_user = users_collection.find_one({"username": username})
        if existing_user:
            if existing_user.get("role") != "admin" and not existing_user.get("password"):
                users_collection.update_one(
                    {"_id": existing_user["_id"]},
                    {"$set": {"password": password, "created_at": datetime.now()}}
                )
                session["user_id"] = str(existing_user["_id"])
                session["username"] = username
                session["role"] = existing_user.get("role", "user")
                return jsonify({"success": True, "redirect": url_for("user_dashboard")})
            return jsonify({"success": False, "message": "Username already exists"}), 400

        result = users_collection.insert_one({
            "username": username,
            "password": password,
            "role": "user",
            "created_at": datetime.now()
        })

        session["user_id"] = str(result.inserted_id)
        session["username"] = username
        session["role"] = "user"

        return jsonify({"success": True, "redirect": url_for("user_dashboard")})


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ============================================
# ADMIN PANEL ROUTES
# ============================================

@app.route("/admin")
@admin_required
def admin_dashboard():
    total_users = users_collection.count_documents({"role": "user"})
    total_emails_sent = logs_collection.count_documents({"status": "sent"})
    total_recipients = recipients_collection.count_documents({})
    total_email_accounts = email_accounts_collection.count_documents({})

    recent_logs = list(logs_collection.find().sort("created_at", -1).limit(10))
    for log in recent_logs:
        log["_id"] = str(log["_id"])

    return render_template("admin/dashboard.html",
                         total_users=total_users,
                         total_emails_sent=total_emails_sent,
                         total_recipients=total_recipients,
                         total_email_accounts=total_email_accounts,
                         recent_logs=recent_logs)


@app.route("/admin/users")
@admin_required
def admin_users():
    users = list(users_collection.find({"role": "user"}).sort("created_at", -1))
    for user in users:
        user["_id"] = str(user["_id"])
        user["email_accounts_count"] = email_accounts_collection.count_documents({"user_id": user["_id"]})
        user["recipients_count"] = recipients_collection.count_documents({"user_id": user["_id"]})
        user["emails_sent"] = logs_collection.count_documents({"user_id": user["_id"], "status": "sent"})
    return render_template("admin/users.html", users=users)


@app.route("/admin/users/<user_id>")
@admin_required
def admin_user_details(user_id):
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return redirect(url_for("admin_users"))

        user["_id"] = str(user["_id"])
        email_accounts = list(email_accounts_collection.find({"user_id": user_id}))
        recipients = list(recipients_collection.find({"user_id": user_id}).limit(50))
        logs = list(logs_collection.find({"user_id": user_id}).sort("created_at", -1).limit(50))

        for ea in email_accounts:
            ea["_id"] = str(ea["_id"])
        for r in recipients:
            r["_id"] = str(r["_id"])
        for l in logs:
            l["_id"] = str(l["_id"])

        return render_template("admin/user_details.html",
                             user=user,
                             email_accounts=email_accounts,
                             recipients=recipients,
                             logs=logs)
    except:
        return redirect(url_for("admin_users"))


@app.route("/admin/users/<user_id>/delete", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if user and user.get("role") == "admin":
            return jsonify({"success": False, "message": "Cannot delete admin user"}), 400

        users_collection.delete_one({"_id": ObjectId(user_id)})
        email_accounts_collection.delete_many({"user_id": user_id})
        recipients_collection.delete_many({"user_id": user_id})
        logs_collection.delete_many({"user_id": user_id})
        settings_collection.delete_many({"user_id": user_id})
        signatures_collection.delete_many({"user_id": user_id})

        return jsonify({"success": True, "message": "User deleted successfully"})
    except:
        return jsonify({"success": False, "message": "Error deleting user"}), 500


@app.route("/admin/prompts")
@admin_required
def admin_prompts():
    prompts = get_prompts_from_db()
    return render_template("admin/prompts.html", prompts=prompts)


@app.route("/admin/cc-emails")
@admin_required
def admin_cc_emails():
    cc_emails = get_global_cc()
    return render_template("admin/cc_emails.html", cc_emails=cc_emails)


@app.route("/admin/logs")
@admin_required
def admin_logs():
    user_filter = request.args.get("user", "")
    status_filter = request.args.get("status", "")

    query = {}
    if user_filter:
        query["user_id"] = user_filter
    if status_filter:
        query["status"] = status_filter

    logs = list(logs_collection.find(query).sort("created_at", -1).limit(200))
    for log in logs:
        log["_id"] = str(log["_id"])

    users = list(users_collection.find({"role": "user"}))

    return render_template("admin/logs.html", logs=logs, users=users)


# ============================================
# ADMIN MANAGER ROUTES
# ============================================

@app.route("/admin/email-accounts")
@admin_required
def admin_email_accounts():
    user_id = session["user_id"]
    email_accounts = list(email_accounts_collection.find({"user_id": user_id}))
    for ea in email_accounts:
        ea["_id"] = str(ea["_id"])
    return render_template("admin/email_accounts.html", email_accounts=email_accounts)


@app.route("/admin/upload")
@admin_required
def admin_upload():
    return render_template("admin/upload.html")


@app.route("/admin/compose")
@admin_required
def admin_compose():
    user_id = session["user_id"]
    email_accounts = list(email_accounts_collection.find({"user_id": user_id}))
    prompts = get_prompts_from_db()
    cc_emails = get_global_cc()
    signature = signatures_collection.find_one({"user_id": user_id})
    return render_template("admin/compose.html",
                         email_accounts=email_accounts,
                         prompts=prompts,
                         cc_emails=cc_emails,
                         user_signature=signature)


@app.route("/admin/signature")
@admin_required
def admin_signature():
    user_id = session["user_id"]
    signature = signatures_collection.find_one({"user_id": user_id})
    if signature:
        signature["_id"] = str(signature["_id"])
    return render_template("admin/signature.html", signature=signature)


# ============================================
# USER PANEL ROUTES
# ============================================

@app.route("/user")
@user_required
def user_dashboard():
    user_id = session["user_id"]

    pending = recipients_collection.count_documents({"status": "pending", "user_id": user_id})
    generated = recipients_collection.count_documents({"status": "generated", "user_id": user_id})
    sent = logs_collection.count_documents({"status": "sent", "user_id": user_id})
    failed = logs_collection.count_documents({"status": "failed", "user_id": user_id})
    total_recipients = recipients_collection.count_documents({"user_id": user_id})
    email_accounts_count = email_accounts_collection.count_documents({"user_id": user_id})

    recent_logs = list(logs_collection.find({"user_id": user_id}).sort("created_at", -1).limit(5))
    for log in recent_logs:
        log["_id"] = str(log["_id"])

    return render_template("user/dashboard.html",
                         pending=pending,
                         generated=generated,
                         sent=sent,
                         failed=failed,
                         total_recipients=total_recipients,
                         email_accounts_count=email_accounts_count,
                         recent_logs=recent_logs)


@app.route("/user/email-accounts")
@user_required
def user_email_accounts():
    user_id = session["user_id"]
    email_accounts = list(email_accounts_collection.find({"user_id": user_id}))
    for ea in email_accounts:
        ea["_id"] = str(ea["_id"])
    return render_template("user/email_accounts.html", email_accounts=email_accounts)


@app.route("/user/upload")
@user_required
def user_upload():
    return render_template("user/upload.html")


@app.route("/user/compose")
@user_required
def user_compose():
    user_id = session["user_id"]
    email_accounts = list(email_accounts_collection.find({"user_id": user_id}))
    prompts = get_prompts_from_db()
    cc_emails = get_global_cc()
    signature = signatures_collection.find_one({"user_id": user_id})
    return render_template("user/compose.html",
                         email_accounts=email_accounts,
                         prompts=prompts,
                         cc_emails=cc_emails,
                         user_signature=signature)


@app.route("/user/logs")
@user_required
def user_logs():
    user_id = session["user_id"]
    status_filter = request.args.get("status", "")

    query = {"user_id": user_id}
    if status_filter:
        query["status"] = status_filter

    logs = list(logs_collection.find(query).sort("created_at", -1).limit(200))
    for log in logs:
        log["_id"] = str(log["_id"])

    return render_template("user/logs.html", logs=logs)


@app.route("/user/signature")
@user_required
def user_signature():
    user_id = session["user_id"]
    signature = signatures_collection.find_one({"user_id": user_id})
    if signature:
        signature["_id"] = str(signature["_id"])
    return render_template("user/signature.html", signature=signature)


# ============================================
# API ROUTES (Shared)
# ============================================

# Prompts API
@app.route("/api/prompts", methods=["GET"])
@login_required
def get_prompts_api():
    return jsonify(get_prompts_from_db())


@app.route("/api/prompts", methods=["POST"])
@admin_required
def add_prompt():
    data = request.get_json()
    name = data.get("name")
    template = data.get("template")

    if not name or not template:
        return jsonify({"error": "Name and template are required"}), 400

    existing = list(prompts_collection.find({}, {"id": 1}).sort("id", -1).limit(1))
    new_id = existing[0]["id"] + 1 if existing else 1

    result = prompts_collection.insert_one({"id": new_id, "name": name, "template": template})
    return jsonify({"success": True, "prompt": {"_id": str(result.inserted_id), "id": new_id, "name": name, "template": template}})


@app.route("/api/prompts/<int:prompt_id>", methods=["PUT"])
@admin_required
def update_prompt(prompt_id):
    data = request.get_json()
    name = data.get("name")
    template = data.get("template")

    if not name or not template:
        return jsonify({"error": "Name and template are required"}), 400

    result = prompts_collection.update_one({"id": prompt_id}, {"$set": {"name": name, "template": template}})
    if result.matched_count == 0:
        return jsonify({"error": "Prompt not found"}), 404

    return jsonify({"success": True})


@app.route("/api/prompts/<int:prompt_id>", methods=["DELETE"])
@admin_required
def delete_prompt(prompt_id):
    result = prompts_collection.delete_one({"id": prompt_id})
    if result.deleted_count == 0:
        return jsonify({"error": "Prompt not found"}), 404
    return jsonify({"success": True})


# Global CC API
@app.route("/api/cc-emails", methods=["GET"])
@login_required
def get_cc_emails_api():
    return jsonify(get_global_cc())


@app.route("/api/cc-emails", methods=["POST"])
@admin_required
def add_cc_email():
    data = request.get_json()
    email = data.get("email")
    name = data.get("name")

    if not email or not name:
        return jsonify({"error": "Email and name are required"}), 400

    result = global_cc_collection.insert_one({"email": email, "name": name})
    return jsonify({"success": True, "_id": str(result.inserted_id)})


@app.route("/api/cc-emails/<cc_id>", methods=["PUT"])
@admin_required
def update_cc_email(cc_id):
    data = request.get_json()
    email = data.get("email")
    name = data.get("name")

    if not email or not name:
        return jsonify({"error": "Email and name are required"}), 400

    result = global_cc_collection.update_one({"_id": ObjectId(cc_id)}, {"$set": {"email": email, "name": name}})
    if result.matched_count == 0:
        return jsonify({"error": "CC email not found"}), 404

    return jsonify({"success": True})


@app.route("/api/cc-emails/<cc_id>", methods=["DELETE"])
@admin_required
def delete_cc_email(cc_id):
    result = global_cc_collection.delete_one({"_id": ObjectId(cc_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "CC email not found"}), 404
    return jsonify({"success": True})


# User Email Accounts API
@app.route("/api/user/email-accounts", methods=["GET"])
@login_required
def get_user_email_accounts():
    accounts = list(email_accounts_collection.find({"user_id": session["user_id"]}))
    for account in accounts:
        account["_id"] = str(account["_id"])
    return jsonify(accounts)


@app.route("/api/user/email-accounts", methods=["POST"])
@login_required
def add_user_email_account():
    data = request.get_json()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    sender_name = data.get("sender_name", "").strip()

    if not email or not password or not sender_name:
        return jsonify({"error": "All fields are required"}), 400

    result = email_accounts_collection.insert_one({
        "user_id": session["user_id"],
        "email": email,
        "password": password,
        "sender_name": sender_name,
        "created_at": datetime.now()
    })
    return jsonify({"success": True, "_id": str(result.inserted_id)})


@app.route("/api/user/email-accounts/<account_id>", methods=["PUT"])
@login_required
def update_user_email_account(account_id):
    data = request.get_json()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    sender_name = data.get("sender_name", "").strip()

    if not email or not password or not sender_name:
        return jsonify({"error": "All fields are required"}), 400

    result = email_accounts_collection.update_one(
        {"_id": ObjectId(account_id), "user_id": session["user_id"]},
        {"$set": {"email": email, "password": password, "sender_name": sender_name}}
    )
    if result.matched_count == 0:
        return jsonify({"error": "Account not found"}), 404

    return jsonify({"success": True})


@app.route("/api/user/email-accounts/<account_id>", methods=["DELETE"])
@login_required
def delete_user_email_account(account_id):
    result = email_accounts_collection.delete_one({"_id": ObjectId(account_id), "user_id": session["user_id"]})
    if result.deleted_count == 0:
        return jsonify({"error": "Account not found"}), 404
    return jsonify({"success": True})


# User Signature API
@app.route("/api/user/signature", methods=["GET"])
@login_required
def get_user_signature():
    signature = signatures_collection.find_one({"user_id": session["user_id"]})
    if signature:
        signature["_id"] = str(signature["_id"])
        return jsonify(signature)
    return jsonify({})


@app.route("/api/user/signature", methods=["POST"])
@login_required
def save_user_signature():
    data = request.get_json()
    sender_name = data.get("sender_name", "").strip()
    position = data.get("position", "").strip()
    company = data.get("company", "").strip()
    phone = data.get("phone", "").strip()
    website = data.get("website", "").strip()
    logo_base64 = data.get("logo_base64", "")

    if not sender_name or not company:
        return jsonify({"error": "Sender name and company are required"}), 400

    # Build the signature data
    signature_data = {
        "sender_name": sender_name,
        "position": position,
        "company": company,
        "phone": phone,
        "website": website
    }
    
    # Only store logo_base64 if it's provided (non-empty)
    if logo_base64:
        signature_data["logo_base64"] = logo_base64

    signatures_collection.update_one(
        {"user_id": session["user_id"]},
        {"$set": signature_data},
        upsert=True
    )
    return jsonify({"success": True})


# Recipients API
@app.route("/api/recipients", methods=["GET"])
@login_required
def get_recipients():
    user_id = session["user_id"]
    status = request.args.get("status", "all")

    query = {"user_id": user_id}
    if status != "all":
        query["status"] = status

    recipients = list(recipients_collection.find(query))

    for r in recipients:
        r["_id"] = str(r["_id"])
    return jsonify(recipients)


@app.route("/api/status")
@login_required
def get_status():
    user_id = session["user_id"]
    if session.get("role") == "admin":
        pending = recipients_collection.count_documents({})
        sent = logs_collection.count_documents({"status": "sent"})
        failed = logs_collection.count_documents({"status": "failed"})
        total = recipients_collection.count_documents({})
    else:
        pending = recipients_collection.count_documents({"status": "pending", "user_id": user_id})
        sent = logs_collection.count_documents({"status": "sent", "user_id": user_id})
        failed = logs_collection.count_documents({"status": "failed", "user_id": user_id})
        total = recipients_collection.count_documents({"user_id": user_id})
    return jsonify({"pending": pending, "sent": sent, "failed": failed, "total": total})


# Upload Excel
@app.route("/upload", methods=["POST"])
@login_required
def upload_file():
    file = request.files["file"]
    if file and file.filename.endswith(".xlsx"):
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)
        df = pd.read_excel(filepath)
        df.columns = df.columns.str.strip().str.lower()

        column_mapping = {
            "name": "name", "first name": "name", "full name": "name",
            "email": "email", "email address": "email",
            "phone": "phone", "phone number": "phone",
            "company": "company", "company name": "company",
            "requirement": "requirement", "requirements": "requirement", "need": "requirement", "description": "requirement"
        }
        df = df.rename(columns=column_mapping)

        required_columns = ["name", "email", "phone", "company", "requirement"]
        df = df[[col for col in required_columns if col in df.columns]]
        df = df.fillna("")

        records = df.to_dict(orient="records")
        for r in records:
            r["status"] = "pending"
            r["created_at"] = datetime.now()
            r["user_id"] = session.get("user_id")

        if records:
            recipients_collection.insert_many(records)
        os.remove(filepath)
        return jsonify({"message": f"{len(records)} records stored successfully!"})
    return jsonify({"error": "Please upload .xlsx file only"}), 400


# Generate Email
@app.route("/generate_email", methods=["POST"])
@login_required
def generate_single_email():
    data = request.get_json()
    recipient_id = data.get("recipient_id")
    prompt_id = data.get("prompt_id")
    subject = data.get("subject", "AI Generated Email")

    if not recipient_id or not prompt_id:
        return jsonify({"error": "Recipient ID and Prompt ID required"}), 400

    try:
        recipient = recipients_collection.find_one({"_id": ObjectId(recipient_id), "user_id": session["user_id"]})
    except:
        return jsonify({"error": "Invalid recipient ID"}), 400

    if not recipient:
        return jsonify({"error": "Recipient not found"}), 404

    prompts = get_prompts_from_db()
    prompt_obj = next((p for p in prompts if p["id"] == int(prompt_id)), None)
    if not prompt_obj:
        return jsonify({"error": "Prompt not found"}), 404

    recipient_name = recipient.get("name", "").strip()
    greeting_name = recipient_name if recipient_name else "Sir/Madam"

    try:
        email_body = generate_email(recipient, prompt_obj["template"])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    recipients_collection.update_one(
        {"_id": recipient["_id"]},
        {"$set": {
            "email_content": email_body,
            "subject": subject,
            "prompt_used": prompt_obj["name"],
            "generated_at": datetime.now(),
            "generated_by": session.get("username", "admin"),
            "recipient_name": greeting_name,
            "recipient_email": recipient.get("email"),
            "status": "generated"
        }}
    )

    return jsonify({"success": True, "email_content": email_body, "prompt_used": prompt_obj["name"], "subject": subject})


# Send Email
@app.route("/send_single_email", methods=["POST"])
@login_required
def send_single_email():
    data = request.get_json()
    recipient_id = data.get("recipient_id")
    sender_account_id = data.get("sender_account_id")
    cc_email = data.get("cc_email", "")
    subject = data.get("subject", "AI Generated Email")
    custom_email = data.get("custom_email", "")

    try:
        recipient = recipients_collection.find_one({"_id": ObjectId(recipient_id), "user_id": session["user_id"]})
    except:
        return jsonify({"error": "Invalid recipient ID"}), 400

    if not recipient:
        return jsonify({"error": "Recipient not found"}), 404

    sender_account = email_accounts_collection.find_one({"_id": ObjectId(sender_account_id), "user_id": session["user_id"]})
    if not sender_account:
        return jsonify({"error": "Invalid sender account"}), 400

    email_body = custom_email or recipient.get("email_content", "")
    if not email_body:
        return jsonify({"error": "No email content available"}), 400

    # Clean up any existing signature-like content from AI-generated email
    # Remove lines that look like signatures (name, position, company, phone, website patterns)
    lines = email_body.split('\n')
    cleaned_lines = []
    signature_start_index = -1
    
    # Signature patterns to detect
    signature_patterns = [
        r'^Best\s+Regards',
        r'^Regards',
        r'^Sincerely',
        r'^Thank\s+you',
        r'^Looking\s+forward',
        r'^HR\s+Team',
        r'^Phone:',
        r'^Website:',
        r'^[a-zA-Z]+\s+[A-Z][a-zA-Z]+\s*$',  # Name pattern (e.g., "Krish Makwana")
    ]
    
    import re
    
    # Find where signature might start (look from the end)
    for i in range(len(lines) - 1, -1, -1):
        stripped = lines[i].strip()
        if not stripped:
            continue
        
        # Check for signature patterns
        is_signature_line = False
        for pattern in signature_patterns:
            if re.search(pattern, stripped, re.IGNORECASE):
                is_signature_line = True
                break
        
        # Also check if this looks like a signature block (multiple signature-like lines in a row)
        if i < len(lines) - 1:
            remaining_lines = [l.strip() for l in lines[i:] if l.strip()]
            if len(remaining_lines) <= 6:  # Signature block is usually short
                # Check if remaining lines contain signature indicators
                sig_indicators = ['HR Team', 'HV', 'Phone:', 'Website:', 'hr@', 'info@', 
                                  'hansraj', 'ventures', 'recruitment']
                has_sig_indicator = any(
                    any(ind.lower() in line.lower() for ind in sig_indicators)
                    for line in remaining_lines
                )
                if has_sig_indicator or is_signature_line:
                    signature_start_index = i
                    break
        elif is_signature_line:
            signature_start_index = i
            break
    
    # Remove signature block if found
    if signature_start_index >= 0:
        cleaned_lines = lines[:signature_start_index]
    else:
        cleaned_lines = lines
    
    # Remove trailing empty lines
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()
    
    email_body = '\n'.join(cleaned_lines)

    # Build signature and require it before sending
    signature = signatures_collection.find_one({"user_id": session["user_id"]})
    if not signature:
        return jsonify({"error": "Please configure your email signature before sending."}), 400

    # Plain text signature (without "Best Regards" as it's in HTML signature)
    sig_name = signature.get('sender_name', sender_account.get('sender_name', ''))
    sig_position = signature.get('position', '')
    sig_company = signature.get('company', '')
    sig_phone = signature.get('phone', '')
    sig_website = signature.get('website', '')
    
    sig_text = f"\n\n{sig_name}\n{sig_position}\n{sig_company}\nPhone: {sig_phone}\nWebsite: {sig_website}"

    full_email = email_body 

    # Handle attachment
    attachment_data = data.get("attachment")
    attachment_path = None
    attachment_name = None
    if attachment_data and isinstance(attachment_data, dict):
        attachment_path = attachment_data.get("filepath")
        attachment_name = attachment_data.get("original_name")

    # Build signature data for aligned display
    sig_data = {
        "position": signature.get("position", ""),
        "company": signature.get("company", ""),
        "phone": signature.get("phone", ""),
        "website": signature.get("website", "")
    }

    # Use the new function with logo_base64 support and aligned signature
    success, error = send_email_with_logo_base64(
        recipient["email"],
        subject,
        full_email,
        sender_account["email"],
        sender_account["sender_name"],
        cc_email,
        attachment_path,
        attachment_name,
        sender_password=sender_account.get("password"),
        logo_base64=signature.get("logo_base64") if signature else None,
        signature_data=sig_data
    )

    # Log the email
    log_entry = {
        "user_id": session["user_id"],
        "username": session.get("username"),
        "recipient_email": recipient.get("email"),
        "recipient_name": recipient.get("name"),
        "sender_email": sender_account["email"],
        "sender_name": sender_account["sender_name"],
        "subject": subject,
        "cc_email": cc_email,
        "status": "sent" if success else "failed",
        "error": error if not success else None,
        "created_at": datetime.now()
    }
    logs_collection.insert_one(log_entry)

    if success:
        recipients_collection.update_one(
            {"_id": recipient["_id"]},
            {"$set": {
                "status": "sent",
                "sent_at": datetime.now(),
                "sender_email": sender_account["email"],
                "cc_email": cc_email
            }}
        )
        return jsonify({"success": True, "message": "Email sent successfully"})
    else:
        recipients_collection.update_one(
            {"_id": recipient["_id"]},
            {"$set": {"status": "failed", "error": error}}
        )
        return jsonify({"success": False, "error": error}), 500


# Attachment upload
@app.route("/upload_attachment", methods=["POST"])
@login_required
def upload_attachment():
    if 'attachment' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['attachment']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    filename = f"{datetime.now().timestamp()}_{file.filename}"
    filepath = os.path.join(app.config["ATTACHMENTS_FOLDER"], filename)
    file.save(filepath)

    return jsonify({
        "success": True,
        "filename": filename,
        "filepath": filepath,
        "original_name": file.filename
    })


@app.route("/attachments/<filename>")
@login_required
def get_attachment(filename):
    return send_from_directory(app.config["ATTACHMENTS_FOLDER"], filename)


# Clear data
@app.route("/clear_data", methods=["POST"])
@login_required
def clear_data():
    user_id = session.get("user_id")
    result = recipients_collection.delete_many({"user_id": user_id})
    return jsonify({"message": f"Deleted {result.deleted_count} records"})


# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    app.run(debug=True, port=5003, use_reloader=False)