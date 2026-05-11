import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
import os
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Email Accounts Configuration - load from environment variables
def load_email_accounts():
    accounts = {}
    # Define account keys
    account_keys = ["admissions", "info", "support", "contact", "dhrupal"]
    
    for key in account_keys:
        env_value = os.getenv(f"EMAIL_ACCOUNT_{key}")
        if env_value:
            # Format: email|password|name|position
            parts = env_value.split("|")
            if len(parts) >= 4:
                accounts[key] = {
                    "email": parts[0],
                    "password": parts[1],
                    "name": parts[2],
                    "position": parts[3]
                }
    return accounts

EMAIL_ACCOUNTS = load_email_accounts()

# SMTP Configuration from environment variables
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
COMPANY_LOGO_PATH = os.getenv("COMPANY_LOGO_PATH", "attachments/company_logo.png")


def convert_markdown_to_html(text):
    if not text:
        return ""

    escaped = (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )

    # Markdown-style formatting
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"__(.+?)__", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
    escaped = re.sub(r"_(.+?)_", r"<em>\1</em>", escaped)

    # Convert newlines to HTML line breaks
    escaped = escaped.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = [p.strip() for p in escaped.split("\n\n") if p.strip()]
    html_paragraphs = [p.replace("\n", "<br>") for p in paragraphs]
    return "<div style='font-family:Arial,sans-serif;line-height:1.6;color:#111;'>" + "</div><div style='font-family:Arial,sans-serif;line-height:1.6;color:#111;'>".join(html_paragraphs) + "</div>"


def send_email(receiver_email, subject, body, sender_key="dhrupal"):
    """
    Send an email using the specified sender account.
    
    Args:
        receiver_email: Recipient email address
        subject: Email subject
        body: Email body content
        sender_key: Key to identify sender account (default: 'dhrupal')
    
    Returns:
        Tuple (success: bool, error: str or None)
    """
    
    sender = EMAIL_ACCOUNTS.get(sender_key)
    
    if not sender:
        return False, "Invalid sender key"
    
    sender_email = sender["email"]
    sender_password = sender["password"]
    
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    
    # Attach body as plain text
    msg.attach(MIMEText(body, "plain"))
    
    try:
        # Connect to SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(sender_email, sender_password)
        
        # Send email
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        
        return True, None
    
    except Exception as e:
        return False, str(e)


def send_email_with_details(receiver_email, subject, body, from_email, from_name, cc_email=None, logo_path=None):
    """
    Enhanced email sending function with custom From name, CC support, and logo.
    
    Args:
        receiver_email: Recipient email address
        subject: Email subject
        body: Email body content
        from_email: Sender email address
        from_name: Sender display name
        cc_email: CC recipient email (optional)
        logo_path: Local path to company logo image (optional)
    
    Returns:
        Tuple (success: bool, error: str or None)
    """
    
    # Find sender account by email
    sender_account = None
    for key, account in EMAIL_ACCOUNTS.items():
        if account['email'] == from_email:
            sender_account = account
            break
    
    if not sender_account:
        return False, "Sender email not configured"
    
    sender_email = sender_account["email"]
    sender_password = sender_account["password"]
    
    logo_path = logo_path or COMPANY_LOGO_PATH
    logo_cid = None
    if logo_path and os.path.exists(logo_path):
        logo_cid = "companylogo"

    msg = MIMEMultipart('related')
    msg["From"] = f"{from_name} <{sender_email}>" if from_name else sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    
    if cc_email:
        msg["CC"] = cc_email
    
    html_body = convert_markdown_to_html(body)
    if logo_cid:
        # Create a table-based signature with logo on left and text on right
        logo_html = f"""
<div style="margin-top:20px;padding-top:15px;border-top:2px solid #e0e0e0;">
  <table cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
    <tr>
      <td style="padding:0 15px 0 0;vertical-align:middle;">
        <img src="cid:{logo_cid}" alt="Company Logo" style="max-width:120px;max-height:120px;width:auto;height:auto;display:block;">
      </td>
      <td style="padding:0;vertical-align:middle;border-left:3px solid #4A90E2;border-left-style:solid;">
        <div style="padding:0 0 0 15px;font-family:Arial,sans-serif;font-size:13px;line-height:1.5;color:#333333;">
          <strong style="font-size:14px;color:#1a1a1a;">Best Regards,</strong><br>
          <span style="color:#666666;">{from_name}</span><br>
          <span style="color:#666666;">{position if position else ''}</span><br>
          <span style="color:#666666;">{company if company else ''}</span><br>
          <span style="color:#666666;">{phone if phone else 'N/A'}</span><br>
          <span style="color:#666666;">{website if website else 'N/A'}</span>
        </div>
      </td>
    </tr>
  </table>
</div>"""
        html_body = html_body + logo_html

    alternative = MIMEMultipart('alternative')
    alternative.attach(MIMEText(html_body, "html"))
    msg.attach(alternative)

    if logo_cid:
        try:
            with open(logo_path, 'rb') as image_file:
                logo_data = image_file.read()
                image = MIMEImage(logo_data)
                image.add_header('Content-ID', f'<{logo_cid}>')
                image.add_header('Content-Disposition', 'inline', filename=os.path.basename(logo_path))
                msg.attach(image)
        except Exception:
            pass
    
    try:
        # Connect to SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(sender_email, sender_password)
        
        recipients = [receiver_email]
        if cc_email:
            recipients.append(cc_email)
        
        server.sendmail(sender_email, recipients, msg.as_string())
        server.quit()
        
        return True, None
    
    except Exception as e:
        return False, str(e)


def get_email_accounts():
    """
    Get all configured email accounts (without passwords).
    
    Returns:
        Dictionary of email accounts with public info
    """
    accounts = {}
    for key, account in EMAIL_ACCOUNTS.items():
        accounts[key] = {
            "email": account["email"],
            "name": account.get("name", key.title())
        }
    return accounts

def remove_existing_signature(text):
    if not text:
        return text

    # Remove common signature patterns
    patterns = [
        r"(?i)best regards[,\\s\\S]*",
        r"(?i)regards[,\\s\\S]*",
        r"(?i)thanks & regards[,\\s\\S]*",
        r"(?i)thank you[,\\s\\S]*"
    ]

    for pattern in patterns:
        text = re.sub(pattern, "", text).strip()

    return text

def send_email_with_logo_base64(receiver_email, subject, body, from_email, from_name, cc_email=None, attachment_path=None, attachment_name=None, sender_password=None, logo_base64=None, signature_data=None):
    """
    Enhanced email sending function with base64-encoded logo support and aligned signature.
    
    Args:
        receiver_email: Recipient email address
        subject: Email subject
        body: Email body content
        from_email: Sender email address
        from_name: Sender display name
        cc_email: CC recipient email (optional)
        attachment_path: Path to attachment file (optional)
        attachment_name: Name for the attachment (optional)
        sender_password: Optional SMTP password for the sender account
        logo_base64: Base64-encoded logo image data (optional)
        signature_data: Dictionary with position, company, phone, website (optional)
    
    Returns:
        Tuple (success: bool, error: str or None)
    """
    import base64
    from io import BytesIO
    
    if signature_data is None:
        signature_data = {}
    
    sender_email = from_email
    password = sender_password

    if password is None:
        sender_account = None
        for key, account in EMAIL_ACCOUNTS.items():
            if account['email'] == from_email:
                sender_account = account
                break
        if not sender_account:
            return False, "Sender email not configured"
        password = sender_account["password"]

    if not password:
        return False, "Sender email password not configured"

    logo_cid = None
    logo_data_bytes = None
    
    # Process base64 logo
    if logo_base64:
        try:
            # Remove data URL prefix if present (e.g., "data:image/png;base64,")
            if ',' in logo_base64:
                logo_base64 = logo_base64.split(',', 1)[1]
            logo_data_bytes = base64.b64decode(logo_base64)
            logo_cid = "companylogo"
        except Exception as e:
            return False, f"Error decoding logo: {str(e)}"

    msg = MIMEMultipart('related')
    msg["From"] = f"{from_name} <{sender_email}>" if from_name else sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    
    if cc_email:
        msg["CC"] = cc_email
    
    clean_body = remove_existing_signature(body)
    html_body = convert_markdown_to_html(clean_body)
    
    # Add aligned signature with logo on left and text on right
    if logo_cid and logo_data_bytes:
        position = signature_data.get('position', '')
        company = signature_data.get('company', '')
        phone = signature_data.get('phone', '')
        website = signature_data.get('website', '')
        
        signature_html = f"""
<div style="margin-top:20px;padding-top:15px;border-top:2px solid #e0e0e0;">
  <table cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
    <tr>
      <td style="padding:0 15px 0 0;vertical-align:middle;">
        <img src="cid:{logo_cid}" alt="Company Logo" style="max-width:100px;max-height:100px;width:auto;height:auto;display:block;">
      </td>
      <td style="padding:0;vertical-align:middle;border-left:3px solid #4A90E2;">
        <div style="padding:0 0 0 15px;font-family:Arial,sans-serif;font-size:13px;line-height:1.5;color:#333333;">
          <strong style="font-size:14px;color:#1a1a1a;">Best Regards,</strong><br>
          <span style="color:#666666;">{from_name}</span><br>
          <span style="color:#666666;">{position}</span><br>
          <span style="color:#666666;">{company}</span><br>
          <span style="color:#666666;">{phone}</span><br>
          <span style="color:#666666;">{website}</span>
        </div>
      </td>
    </tr>
  </table>
</div>"""
        html_body = html_body + signature_html
    elif from_name:
        # Fallback: text-only signature if no logo
        signature_html = f"""
<div style="margin-top:20px;padding-top:15px;border-top:2px solid #e0e0e0;font-family:Arial,sans-serif;">
  <strong style="font-size:14px;color:#1a1a1a;">Best Regards,</strong><br>
  <strong style="font-size:14px;color:#1a1a1a;">{from_name}</strong>
</div>"""
        html_body = html_body + signature_html

    alternative = MIMEMultipart('alternative')
    alternative.attach(MIMEText(clean_body, "plain"))
    alternative.attach(MIMEText(html_body, "html"))
    msg.attach(alternative)

    # Attach base64 logo
    if logo_cid and logo_data_bytes:
        try:
            image = MIMEImage(logo_data_bytes)
            image.add_header('Content-ID', f'<{logo_cid}>')
            image.add_header('Content-Disposition', 'inline', filename='company_logo.png')
            msg.attach(image)
        except Exception as e:
            return False, f"Error attaching logo: {str(e)}"

    # Add attachment if provided
    if attachment_path and os.path.exists(attachment_path):
        try:
            file_ext = os.path.splitext(attachment_path)[1].lower()
            content_types = {
                '.pdf': 'application/pdf',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.doc': 'application/msword',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.xls': 'application/vnd.ms-excel',
                '.txt': 'text/plain',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
            }
            content_type = content_types.get(file_ext, 'application/octet-stream')
            
            with open(attachment_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                filename = attachment_name or os.path.basename(attachment_path)
                part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                part.add_header('Content-Type', f'{content_type}; name="{filename}"')
                msg.attach(part)
        except FileNotFoundError:
            return False, f"Attachment file not found: {attachment_path}"
        except PermissionError:
            return False, f"Permission denied reading attachment: {attachment_path}"
        except Exception as e:
            return False, f"Error attaching file: {str(e)}"
    elif attachment_path and not os.path.exists(attachment_path):
        return False, f"Attachment file does not exist: {attachment_path}"
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(sender_email, password)
        
        recipients = [receiver_email]
        if cc_email:
            recipients.append(cc_email)
        
        server.sendmail(sender_email, recipients, msg.as_string())
        server.quit()
        
        return True, None
    
    except Exception as e:
        return False, str(e)


def send_email_with_attachment(receiver_email, subject, body, from_email, from_name, cc_email=None, attachment_path=None, attachment_name=None, sender_password=None, logo_path=None):
    """
    Enhanced email sending function with attachment support.
    
    Args:
        receiver_email: Recipient email address
        subject: Email subject
        body: Email body content
        from_email: Sender email address
        from_name: Sender display name
        cc_email: CC recipient email (optional)
        attachment_path: Path to attachment file (optional)
        attachment_name: Name for the attachment (optional)
        sender_password: Optional SMTP password for the sender account. If provided, uses this password directly.
        logo_path: Optional local path to company logo image.
    
    Returns:
        Tuple (success: bool, error: str or None)
    """
    
    sender_email = from_email
    password = sender_password

    if password is None:
        # Find sender account by email in environment configs
        sender_account = None
        for key, account in EMAIL_ACCOUNTS.items():
            if account['email'] == from_email:
                sender_account = account
                break

        if not sender_account:
            return False, "Sender email not configured"

        password = sender_account["password"]

    if not password:
        return False, "Sender email password not configured"
    
    logo_path = logo_path or COMPANY_LOGO_PATH
    logo_cid = None
    if logo_path and os.path.exists(logo_path):
        logo_cid = "companylogo"

    msg = MIMEMultipart('related')
    msg["From"] = f"{from_name} <{sender_email}>" if from_name else sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    
    if cc_email:
        msg["CC"] = cc_email
    
    html_body = convert_markdown_to_html(body)
    if logo_cid:
        logo_html = f"<div><img src='cid:{logo_cid}' alt='Company Logo' style='max-width:220px;height:auto;margin-top:18px;'></div>"
        html_body = html_body + logo_html

    alternative = MIMEMultipart('alternative')
    alternative.attach(MIMEText(html_body, "html"))
    msg.attach(alternative)

    if logo_cid:
        try:
            with open(logo_path, 'rb') as image_file:
                logo_data = image_file.read()
                image = MIMEImage(logo_data)
                image.add_header('Content-ID', f'<{logo_cid}>')
                image.add_header('Content-Disposition', 'inline', filename=os.path.basename(logo_path))
                msg.attach(image)
        except Exception:
            pass

    # Add attachment if provided
    if attachment_path and os.path.exists(attachment_path):
        try:
            # Get the file extension to determine mime type
            file_ext = os.path.splitext(attachment_path)[1].lower()
            
            # Determine content type based on file extension
            content_types = {
                '.pdf': 'application/pdf',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.doc': 'application/msword',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.xls': 'application/vnd.ms-excel',
                '.txt': 'text/plain',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
            }
            content_type = content_types.get(file_ext, 'application/octet-stream')
            
            with open(attachment_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                
                # Use provided name or extract from path
                filename = attachment_name or os.path.basename(attachment_path)
                # Fix: Remove extra space in header (filename=  should be filename=)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{filename}"'
                )
                # Also add Content-Type with the proper mime type
                part.add_header('Content-Type', f'{content_type}; name="{filename}"')
                msg.attach(part)
                
        except FileNotFoundError:
            return False, f"Attachment file not found: {attachment_path}"
        except PermissionError:
            return False, f"Permission denied reading attachment: {attachment_path}"
        except Exception as e:
            return False, f"Error attaching file: {str(e)}"
    elif attachment_path and not os.path.exists(attachment_path):
        return False, f"Attachment file does not exist: {attachment_path}"
    
    try:
        # Connect to SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(sender_email, sender_password)
        
        # Prepare recipients
        recipients = [receiver_email]
        if cc_email:
            recipients.append(cc_email)
        
        # Send email
        server.sendmail(sender_email, recipients, msg.as_string())
        server.quit()
        
        return True, None
    
    except Exception as e:
        return False, str(e)
