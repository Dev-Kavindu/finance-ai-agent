import os
import json
import re
from dotenv import load_dotenv
from groq import Groq
import gradio as gr
import sqlite3
from datetime import datetime
import resend

# Try to import fpdf for PDF generation
try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False
    print("Warning: fpdf library not installed. PDF reports will not be available.")

load_dotenv(override=True)

# Initialize Resend API
resend.api_key = os.getenv("RESEND_API_KEY")

# Hugging Face Spaces persistent storage
DATA_DIR = os.getenv('HF_HOME', '/data')
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, 'finance_tracker.db')

groq_api_key = os.getenv('GROQ_API_KEY')
MODEL = "llama-3.1-8b-instant"
groq = Groq()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS salary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            month TEXT NOT NULL,
            year INTEGER NOT NULL,
            created_at TEXT,
            owner_name TEXT NOT NULL DEFAULT 'guest'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            created_at TEXT,
            owner_name TEXT NOT NULL DEFAULT 'guest'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            content TEXT,
            timestamp TEXT,
            owner_name TEXT NOT NULL DEFAULT 'guest'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT,
            email TEXT,
            updated_at TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS income_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            note TEXT,
            month TEXT NOT NULL,
            year INTEGER NOT NULL,
            created_at TEXT,
            owner_name TEXT NOT NULL DEFAULT 'guest'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    def ensure_column(table_name, column_name, definition):
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        if column_name not in columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")

    ensure_column("salary", "owner_name", "TEXT NOT NULL DEFAULT 'guest'")
    ensure_column("expenses", "owner_name", "TEXT NOT NULL DEFAULT 'guest'")
    ensure_column("chat_history", "owner_name", "TEXT NOT NULL DEFAULT 'guest'")
    ensure_column("user_profile", "email", "TEXT")

    cursor.execute("SELECT value FROM app_state WHERE key = ?", ("first_run_initialized",))
    first_run_flag = cursor.fetchone()
    if not first_run_flag:
        # First run starts from zero balance with an empty history.
        cursor.execute("DELETE FROM salary")
        cursor.execute("DELETE FROM expenses")
        cursor.execute("DELETE FROM chat_history")
        cursor.execute("DELETE FROM income_logs")
        cursor.execute("DELETE FROM user_profile")
        cursor.execute("INSERT INTO app_state (key, value) VALUES (?, ?)", ("first_run_initialized", "1"))
        # Only set to guest on first run
        cursor.execute('''
            INSERT INTO app_state (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        ''', ("active_owner_name", "guest"))

    conn.commit()
    conn.close()
    print("Database and tables are ready.")

init_db()

def get_active_owner_name():
    """Get the currently active owner name from app state"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_state WHERE key = 'active_owner_name'")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "guest"

def get_current_month_context():
    """Get current month and year"""
    now = datetime.now()
    month_name = now.strftime("%B")
    month_num = now.strftime("%m")
    year = now.year
    return month_name, month_num, year

def get_user_email():
    """Get user email from profile"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT email FROM user_profile WHERE id = 1')
    result = cursor.fetchone()
    conn.close()
    return result[0] if result and result[0] else None

def save_user_name(name):
    """Save user name to profile and set as active owner"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Update user profile
    cursor.execute('''
        INSERT INTO user_profile (id, name, updated_at)
        VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET name = excluded.name, updated_at = excluded.updated_at
    ''', (name, updated_at))
    
    # Set active owner
    cursor.execute('''
        INSERT INTO app_state (key, value)
        VALUES ('active_owner_name', ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    ''', (name,))
    
    conn.commit()
    conn.close()
    return f"Name successfully updated to {name}."

def save_user_email(email):
    """Save user email address"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO user_profile (id, email, updated_at)
        VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET email = excluded.email, updated_at = excluded.updated_at
    ''', (email, updated_at))
    conn.commit()
    conn.close()
    return f"Email address successfully updated to {email}."

def set_salary(amount, owner_name=None):
    amount = float(amount)
    owner = owner_name or get_active_owner_name()
    month_name, _, year = get_current_month_context()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Delete old salary for this month
    cursor.execute('''
        DELETE FROM salary WHERE month = ? AND year = ? AND owner_name = ?
    ''', (month_name, year, owner))
    
    # Insert new salary
    cursor.execute('''
        INSERT INTO salary (amount, month, year, created_at, owner_name)
        VALUES (?, ?, ?, ?, ?)
    ''', (amount, month_name, year, created_at, owner))
    
    conn.commit()
    conn.close()
    return f"Salary of Rs {amount:,.2f} (LKR) for {month_name} {year} saved for {owner.title()}."

def log_expense(amount, category, description, date=None, owner_name=None):
    amount = float(amount)
    if amount <= 0:
        return None

    owner = owner_name or get_active_owner_name()
    category = (category or "Misc").strip() or "Misc"
    description = (description or category).strip() or category
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    # Deduplication: Check if same expense was logged in last 60 seconds
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id FROM expenses 
        WHERE owner_name = ? AND amount = ? AND category = ? AND description = ? AND date = ?
        AND datetime(created_at) > datetime('now', '-60 seconds')
    ''', (owner, amount, category, description, date))
    if cursor.fetchone():
        conn.close()
        return f"Duplicate expense skipped: Rs {amount:,.2f} (LKR) for {category} ({date})"

    cursor.execute('''
        INSERT INTO expenses (amount, category, description, date, created_at, owner_name)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (amount, category, description, date, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), owner))

    conn.commit()
    conn.close()

    _, _, salary, total_expenses = get_monthly_financial_totals(owner_name=owner)
    balance = salary - total_expenses

    return f"Logged Rs {amount:,.2f} (LKR) for {category} ({date}) for {owner.title()}. Spent so far: Rs {total_expenses:,.2f} (LKR) | Remaining: Rs {balance:,.2f} (LKR)"

def get_monthly_financial_totals(owner_name=None):
    """Get monthly financial totals for a specific owner with year validation"""
    owner = owner_name or get_active_owner_name()
    month_name, month_num, year = get_current_month_context()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Get salary from salary table
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) FROM salary 
        WHERE month = ? AND year = ? AND owner_name = ?
    ''', (month_name, year, owner))
    salary = cursor.fetchone()[0]
    
    # 2. Get additional income from income_logs table
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) FROM income_logs 
        WHERE month = ? AND year = ? AND owner_name = ?
    ''', (month_name, year, owner))
    additional_income = cursor.fetchone()[0]
    
    total_income = salary + additional_income
    
    # 3. Get expenses (check both year and month - Logic Fix)
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) FROM expenses 
        WHERE owner_name = ? 
        AND strftime('%Y', date) = ? 
        AND strftime('%m', date) = ?
    ''', (owner, str(year), month_num))
    
    expenses = cursor.fetchone()[0]
    
    conn.close()
    return month_name, year, total_income, expenses

def get_expense_summary(owner_name=None):
    owner = owner_name or get_active_owner_name()
    current_month, current_year, total_income, _ = get_monthly_financial_totals(owner_name=owner)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT category, COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE strftime("%m", date) = ?
          AND strftime("%Y", date) = ?
          AND owner_name = ?
        GROUP BY category
        ORDER BY SUM(amount) DESC
    ''', (datetime.now().strftime("%m"), str(current_year), owner))
    summary_data = cursor.fetchall()
    conn.close()

    # Calculate total spent from the query results
    total_spent = sum(total for _, total in summary_data)
    remaining = total_income - total_spent

    if not summary_data:
        return (
            f"{owner.title()} - {current_month} {current_year} spending breakdown:\n"
            f"No expenses logged yet.\n"
            f"Total spent: Rs {total_spent:,.2f} (LKR) | Remaining: Rs {remaining:,.2f} (LKR)"
        )

    summary_lines = [f"{owner.title()} - {current_month} {current_year} spending breakdown:"]
    for category, total in summary_data:
        if total_income > 0:
            percentage = (total / total_income) * 100
            summary_lines.append(f"- {category}: Rs {total:,.2f} (LKR) ({percentage:.1f}% of income)")
        else:
            summary_lines.append(f"- {category}: Rs {total:,.2f} (LKR) (income not recorded yet)")

    summary_lines.append(f"Total spent: Rs {total_spent:,.2f} (LKR) | Remaining: Rs {remaining:,.2f} (LKR)")
    return "\n".join(summary_lines)

def get_balance(owner_name=None):
    owner = owner_name or get_active_owner_name()
    month_name, _, year = get_current_month_context()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Get salary for current month
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) FROM salary 
        WHERE owner_name = ? AND month = ? AND year = ?
    ''', (owner, month_name, year))
    salary = cursor.fetchone()[0]
    
    # 2. Get additional income for current month
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) FROM income_logs 
        WHERE owner_name = ? AND month = ? AND year = ?
    ''', (owner, month_name, year))
    income_logs = cursor.fetchone()[0]
    
    # 3. Get expenses for current month
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) FROM expenses 
        WHERE owner_name = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
    ''', (owner, str(year), datetime.now().strftime('%m')))
    
    expenses = cursor.fetchone()[0]
    conn.close()
    
    total_income = salary + income_logs
    balance = total_income - expenses
    
    return (
        f"{owner.title()} - {month_name} {year} Financial Snapshot:\n"
        f"Total Income: Rs {total_income:,.2f} (LKR)\n"
        f"Total Expenses: Rs {expenses:,.2f} (LKR)\n"
        f"Remaining Balance: Rs {balance:,.2f} (LKR)"
    )

def get_activity_history(owner_name=None, limit=10):
    """Get recent activity history (income and expenses)"""
    owner = owner_name or get_active_owner_name()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 'expense' AS type, date, category, amount, description FROM expenses 
        WHERE owner_name = ?
        UNION ALL
        SELECT 'income' AS type, created_at, 'Salary' as category, amount, note FROM income_logs 
        WHERE owner_name = ?
        ORDER BY date DESC 
        LIMIT ?
    ''', (owner, owner, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return f"No activity history found for {owner.title()}."
    
    lines = [f"{owner.title()} - Recent Activity (last {len(rows)} transactions):", ""]
    for activity_type, date, category, amount, description in rows:
        formatted_amount = f"Rs {amount:,.2f} (LKR)"
        if activity_type == 'income':
            lines.append(f"[{date}] INCOME: {formatted_amount} - {description or category}")
        else:
            lines.append(f"[{date}] EXPENSE: {formatted_amount} - {category} ({description or '-'})")
    
    return "\n".join(lines)

def save_chat(role, content, owner_name=None):
    owner = owner_name or get_active_owner_name()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO chat_history (role, content, timestamp, owner_name) VALUES (?, ?, ?, ?)',
        (role, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), owner)
    )
    conn.commit()
    conn.close()

def get_recent_history(owner_name=None, limit=12):
    owner = owner_name or get_active_owner_name()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT role, content FROM chat_history WHERE owner_name = ? ORDER BY id DESC LIMIT ?',
        (owner, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r, "content": c} for r, c in reversed(rows)]

def add_income(amount, note=None, source=None, owner_name=None):
    amount = float(amount)
    if amount <= 0:
        return "Please provide an income amount greater than zero."

    owner = owner_name or get_active_owner_name()
    month_name, _, year = get_current_month_context()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if note is None:
        note = source or "additional income"
    elif source:
        note = f"{note} (from {source})"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Deduplication check
    cursor.execute('''
        SELECT id FROM income_logs 
        WHERE owner_name = ? AND amount = ? AND note = ? AND month = ? AND year = ?
        AND datetime(created_at) > datetime('now', '-60 seconds')
    ''', (owner, amount, note, month_name, year))
    
    if cursor.fetchone():
        conn.close()
        return f"Duplicate entry prevented: Rs {amount:,.2f}"

    # Important: Only insert into income_logs, do not update salary table
    cursor.execute('''
        INSERT INTO income_logs (amount, note, month, year, created_at, owner_name)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (amount, note, month_name, year, created_at, owner))

    conn.commit()
    conn.close()
    return f"Successfully added Rs {amount:,.2f} income for {month_name} {year}."

def reset_monthly_financial_state(owner_name=None):
    owner = owner_name or get_active_owner_name()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM salary WHERE owner_name = ?', (owner,))
    cursor.execute('DELETE FROM expenses WHERE owner_name = ?', (owner,))
    cursor.execute('DELETE FROM income_logs WHERE owner_name = ?', (owner,))
    conn.commit()
    conn.close()
    return f"Okay {owner.title()}, I reset your financial records. Current balance is Rs 0.00 (LKR)."

def create_financial_pdf(balance, summary, history, owner_name):
    """Create a formatted PDF financial report"""
    if not FPDF_AVAILABLE:
        return None
    
    try:
        pdf = FPDF('P', 'mm', 'A4')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        font_family = 'Helvetica'
        
        # Header Styling
        pdf.set_fill_color(30, 58, 138)
        pdf.rect(0, 0, 210, 40, 'F')
        pdf.set_xy(0, 15)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(font_family, 'B', 18)
        pdf.cell(0, 10, f'FINANCIAL REPORT - {datetime.now().strftime("%B %Y")}', 0, 1, 'C')
        pdf.set_font(font_family, '', 10)
        pdf.cell(0, 8, f'Owner: {owner_name.title()} | Generated: {datetime.now().strftime("%Y-%m-%d")}', 0, 1, 'C')
        
        pdf.set_text_color(0, 0, 0)
        pdf.ln(25)

        
        def add_row(label, value, is_header=False):
            start_y = pdf.get_y()
            if is_header:
                pdf.set_fill_color(240, 240, 240)
                pdf.set_font(font_family, 'B', 10)
                pdf.cell(70, 8, f" {label}", 0, 0, 'L', True)
                pdf.cell(115, 8, f"{value} ", 0, 1, 'R', True)
                pdf.ln(2)
            else:
                pdf.set_font(font_family, '', 10)
                pdf.multi_cell(70, 8, label, 0, 'L')
                end_y1 = pdf.get_y()
                
                pdf.set_xy(82, start_y)
                pdf.set_font(font_family, 'B', 10)
                pdf.multi_cell(103, 8, value, 0, 'R')
                end_y2 = pdf.get_y()
                pdf.set_y(max(end_y1, end_y2))

        # Monthly Snapshot
        pdf.set_font(font_family, 'B', 14)
        pdf.set_text_color(30, 58, 138)
        pdf.cell(0, 10, 'Monthly Snapshot', 0, 1, 'L')
        add_row("Category", "Amount", is_header=True)
        
        for line in balance.split('\n'):
            if ':' in line:
                parts = line.split(':', 1)
                add_row(parts[0].strip(), parts[1].strip())
        pdf.ln(10)

        # Spending Summary
        pdf.set_font(font_family, 'B', 14)
        pdf.set_text_color(16, 185, 129)
        pdf.cell(0, 10, 'Spending Summary', 0, 1, 'L')
        add_row("Category", "Value & %", is_header=True)
        
        for line in summary.split('\n'):
            if ':' in line:
                clean_line = line.replace('- ', '').strip()
                parts = clean_line.split(':', 1)
                add_row(parts[0].strip(), parts[1].strip())
        pdf.ln(10)

        # Recent Activity
        pdf.set_font(font_family, 'B', 14)
        pdf.set_text_color(139, 92, 246)
        pdf.cell(0, 10, 'Recent Activity History', 0, 1, 'L')
        pdf.set_font(font_family, '', 9)
        pdf.multi_cell(0, 7, history, 0, 'L')

        # Use /tmp for temporary PDF files on Hugging Face Spaces
        tmp_dir = '/tmp'
        os.makedirs(tmp_dir, exist_ok=True)
        file_name = os.path.join(tmp_dir, f"Financial_Report_{owner_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        pdf.output(file_name)
        return file_name
    except Exception as e:
        print(f"PDF Error: {e}")
        return None

def send_email_report(recipient_email, report_type="full", owner_name=None):
    owner = owner_name or get_active_owner_name()
    
    # 1. Email Lookup Logic
    if not recipient_email:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT email FROM user_profile WHERE id = 1')
        result = cursor.fetchone()
        conn.close()
        recipient_email = result[0] if result else None
    
    if not recipient_email: return "Error: No email provided."
    if recipient_email.startswith("www."): recipient_email = recipient_email[4:]
    
    # 2. Get Report Data
    balance = get_balance(owner_name=owner)
    summary = get_expense_summary(owner_name=owner)
    history = get_activity_history(owner_name=owner)
    
    # 3. Create PDF
    pdf_path = create_financial_pdf(balance, summary, history, owner)
    if not pdf_path: return "Error creating PDF."

    
    def format_html(text):
        return str(text).strip().replace('\n', '<br>')

    html_balance = format_html(balance)
    html_summary = format_html(summary)
    html_history = format_html(history)

    # 5. Email Setup
    # Validate Resend API key
    if not resend.api_key:
        return "Error: RESEND_API_KEY environment variable must be set."
    
    html_content = f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; color: #000000; line-height: 1.6; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; border: 1px solid #1e3a8a; border-radius: 10px; overflow: hidden;">
            <div style="background-color: #1e3a8a; color: white; padding: 20px; text-align: center;">
                <h1 style="margin:0; font-size: 22px;">FINANCIAL STATEMENT</h1>
                <p style="margin:5px 0 0 0;">{datetime.now().strftime("%B %Y")}</p>
            </div>
            <div style="padding: 25px; background-color: #ffffff;">
                <div style="margin-bottom: 25px;">
                    <h2 style="color: #1e3a8a; font-size: 18px; border-bottom: 2px solid #1e3a8a;">Monthly Snapshot</h2>
                    <div style="background: #f9f9f9; border: 1px solid #000000; padding: 15px; font-family: 'Courier New', monospace; font-size: 14px; color: #000000;">
                        {html_balance}
                    </div>
                </div>
                <div style="margin-bottom: 25px;">
                    <h2 style="color: #16a34a; font-size: 18px; border-bottom: 2px solid #16a34a;">Spending Summary</h2>
                    <div style="background: #f9f9f9; border: 1px solid #000000; padding: 15px; font-family: 'Courier New', monospace; font-size: 14px; color: #000000;">
                        {html_summary}
                    </div>
                </div>
                <div style="margin-bottom: 25px;">
                    <h2 style="color: #7c3aed; font-size: 18px; border-bottom: 2px solid #7c3aed;">Recent Transactions</h2>
                    <div style="background: #f9f9f9; border: 1px solid #000000; padding: 15px; font-family: 'Courier New', monospace; font-size: 14px; color: #000000;">
                        {html_history}
                    </div>
                </div>
            </div>
            <div style="text-align: center; padding: 15px; background: #f4f4f4; font-size: 12px; color: #555;">
                Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>
                <b>A detailed PDF is attached for your records.</b>
            </div>
        </div>
    </body>
    </html>
    """

    # 6. Attach & Send
    try:
        # Validate PDF file exists before attaching
        if not os.path.exists(pdf_path):
            return f"Error: PDF file not found at {pdf_path}"
        
        # Read PDF file as binary
        with open(pdf_path, "rb") as f:
            pdf_content = f.read()
        
        # Send email using Resend
        params = {
            "from": "onboarding@resend.dev",
            "to": [recipient_email],
            "subject": f"Financial Report - {owner.title()}",
            "html": html_content,
            "attachments": [
                {
                    "filename": os.path.basename(pdf_path),
                    "content": pdf_content
                }
            ]
        }
        
        resend.Emails.send(params)
        
        # Clean up temporary PDF file
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        return f"Success: Report sent to {recipient_email}!"
    except Exception as e:
        # Clean up temporary PDF file on error
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        return f"Error: {str(e)}"

system_prompt = """You are a helpful personal finance AI assistant. Your role is to help users track their salary, expenses, and financial activities.

You have access to the following tools:
- set_name: Save the user's name for identity persistence
- set_email: Save the user's email address for reports
- get_user_email: Get the user's saved email address
- set_salary: Set or update monthly salary
- add_income: Log additional income beyond salary
- log_expense: Record new expenses and spending
- get_balance: Check current financial balance
- get_expense_summary: Get spending breakdown by category
- get_activity_history: View recent financial activities
- send_email_report: Email financial reports to user
- reset_data: Clear all financial data (use with caution)

CRITICAL INTENT CLASSIFICATION RULES:
1. READ-ONLY INQUIRIES:
   - User asks: "how much remain", "what is my balance", "explain", "why", "how did this happen", "are you sure"
   - ALWAYS use the get_balance, get_expense_summary, or get_activity_history tools. 
   - NEVER calculate the balance yourself. NEVER guess the balance. ALWAYS call the tool.
   - To check user's email, use get_user_email tool.

2. NEW TRANSACTIONS (log ONLY when user explicitly records NEW data):
   - User explicitly states a NEW purchase, payment, or income.

3. MULTIPLE TRANSACTIONS IN ONE SENTENCE:
   - Parse ALL of them and return multiple actions.

4. CLEAN SUMMARY OUTPUT:
   - Provide a consolidated summary in the "reply" field. Do NOT show individual "Logged..." lines for each transaction.

5. RESETTING DATA:
   - If the user asks to "reset", "clear", or "delete" data, you MUST call the `reset_data` tool. Do NOT just reply with text.
   - "reset email" is NOT a valid command - ask the user to provide a new email address.

6. ACKNOWLEDGMENT PHRASES (NO tool calls):
   - If user says: "OK", "thanks", "clear" - Simply acknowledge.

7. IDENTITY PERSISTENCE:
   - Call set_name ONLY when user introduces their NAME (e.g., "I'm Kavindu", "My name is Kavindu").
   - Call set_email when user provides their EMAIL (e.g., "my email is kchamod1124@gmail.com", "email is kchamod1124@gmail.com").
   - IMPORTANT: "my email is..." should call set_email, NOT set_name.
   - Do NOT call set_email with an empty string or None.

8. NEVER re-log expenses from conversation history. Do NOT call set_salary, add_income, or log_expense for summary requests.

9. Always respond in JSON format with "reply" and "actions" fields.
10. Use Sri Lankan Rupees (LKR) as default currency.
11. Only use the EXACT parameters listed in each tool's schema.

Examples:

SET NAME (ONLY for name):
User: "I'm Kavindu" or "My name is Kavindu"
{
  "reply": "Nice to meet you, Kavindu!",
  "actions": [{"action": "set_name", "params": {"name": "Kavindu"}}]
}

SET EMAIL (for email address):
User: "my email is kchamod1124@gmail.com" or "email is kchamod1124@gmail.com"
{
  "reply": "I've saved your email address.",
  "actions": [{"action": "set_email", "params": {"email": "kchamod1124@gmail.com"}}]
}

GET EMAIL:
User: "what is my email" or "check my email"
{
  "reply": "Let me check your saved email address.",
  "actions": [{"action": "get_user_email", "params": {}}]
}

INVALID REQUEST:
User: "reset email"
{
  "reply": "Please provide a new email address. For example: 'my email is newemail@gmail.com'",
  "actions": []
}

RESET DATA (MUST CALL TOOL):
User: "reset all values" or "clear my data"
{
  "reply": "I am resetting your financial records now.",
  "actions": [{"action": "reset_data", "params": {}}]
}

CHECK BALANCE (MUST CALL TOOL):
User: "now how much remain" or "are you sure"
{
  "reply": "Let me check the database for your current balance.",
  "actions": [{"action": "get_balance", "params": {}}]
}

MULTIPLE TRANSACTIONS:
User: "yesterday i earn 85000 lkr my salaray and i won a swip rs.35000. after i bought tv from rs.70000"
{
  "reply": "I've recorded all your transactions: Salary Rs 85,000, Swip Rs 35,000, and TV Rs 70,000.",
  "actions": [
    {"action": "set_salary", "params": {"amount": 85000}},
    {"action": "add_income", "params": {"amount": 35000, "note": "Won from swip"}},
    {"action": "log_expense", "params": {"amount": 70000, "category": "Electronics", "description": "TV purchase"}}
  ]
}"""

def run_conversation(user_prompt):
    raw_prompt = (user_prompt or "").strip()
    if not raw_prompt: return "Please say something!"

    # Intent validation: Check for acknowledgment phrases (exact match only)
    # Only match if the entire prompt is a simple acknowledgment
    acknowledgment_phrases = ["ok", "okay", "thanks", "thank you", "clear", "fine", "good", "yes", "no", "got it", "alright", "ok thank you", "thank you", "thanks"]
    if raw_prompt.lower().strip() in acknowledgment_phrases:
        # Return acknowledgment without calling AI
        return "Got it!"

    def record_reply(reply_text):
        # Always use the current active owner name for chat history
        current_owner = get_active_owner_name()
        save_chat("user", raw_prompt, owner_name=current_owner)
        save_chat("assistant", reply_text, owner_name=current_owner)
        return reply_text

    def execute_action(action_name, params):
        # Always use the current active owner name for all operations
        owner = get_active_owner_name()
        try:
            if action_name == "set_name": 
                result = save_user_name(params.get("name"))
                # After saving name, refresh the owner variable to use the new name
                owner = get_active_owner_name()
                return result
            if action_name == "set_email": return save_user_email(params.get("email"))
            if action_name == "get_user_email": 
                email = get_user_email()
                return f"Your email address is {email}" if email else "Your email address is not set."
            if action_name == "set_salary": return set_salary(**params, owner_name=owner)
            if action_name == "log_expense": return log_expense(**params, owner_name=owner)
            if action_name == "add_income": return add_income(**params, owner_name=owner)
            if action_name == "get_balance": return get_balance(owner_name=owner)
            if action_name == "get_expense_summary": return get_expense_summary(owner_name=owner)
            if action_name == "get_activity_history": return get_activity_history(owner_name=owner, limit=params.get("limit", 10))
            if action_name == "send_email_report": return send_email_report(
                recipient_email=params.get("recipient_email"),
                report_type=params.get("report_type", "full"),
                owner_name=owner
            )
            if action_name == "reset_data": return reset_monthly_financial_state(owner_name=owner)
        except Exception as e:
            return f"Error: {str(e)}"
        return None

    def execute_payload(data):
        """Execute the AI's JSON response with actions"""
        if not data: return None
        
        # Extract reply
        reply = data.get("reply", "")
        
        # Execute actions
        actions = data.get("actions", [])
        if isinstance(actions, list):
            results = []
            for action in actions:
                if isinstance(action, dict):
                    action_name = action.get("action")
                    params = action.get("params", {})
                    result = execute_action(action_name, params)
                    if result:
                        results.append(result)
            if results:
                # Combine action results with reply
                if reply:
                    return reply + "\n\n" + "\n".join(results)
                return "\n".join(results)
        
        return reply if reply else "No response generated."

    # Context injection - use current active owner for all operations
    current_owner = get_active_owner_name()
    history = get_recent_history(owner_name=current_owner)
    month, _, year = get_current_month_context()
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Build messages with context
    messages = [
        {
            "role": "system",
            "content": system_prompt + f"\n\nCONTEXT:\n- User Name: {current_owner}\n- Current Date: {current_date}\n- Current Month: {month} {year}\n- Active Owner: {current_owner}"
        },
        *history,
        {"role": "user", "content": raw_prompt}
    ]

    try:
        # AI call with JSON mode
        response = groq.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        ai_response = response.choices[0].message.content or ""
        
        # Parse JSON
        data = json.loads(ai_response)
        return record_reply(execute_payload(data))

    except json.JSONDecodeError as e:
        return record_reply(f"JSON Parse Error: {str(e)}\nRaw response: {ai_response}")
    except Exception as e:
        return record_reply(f"AI Error: {str(e)}")

def chat_handler(message, _history):
    _ = _history
    user_message = message["text"] if isinstance(message, dict) else message
    return run_conversation(user_message)

# Creating the Gradio Chat Interface
demo = gr.ChatInterface(
    fn=chat_handler,
    title="💰 Personal Finance AI Agent",
    description="I can help you track your salary and expenses. Just talk to me naturally!",
    examples=[
        "My monthly salary is Rs 3500",
        "I spent Rs 50 on groceries today",
        "Show me my spending breakdown",
        "How much money is left?"
    ]
)

# Launching the application
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
