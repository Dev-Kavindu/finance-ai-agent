"""
Personal Finance Tracker - AI Agent
A chat-based finance assistant using Groq API and SQLite database.
"""

import os
import json
import re
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
import gradio as gr

# Load environment variables
load_dotenv(override=True)
groq_api_key = os.getenv('GROQ_API_KEY')
MODEL = "llama-3.3-70b-versatile"
groq = Groq(api_key=groq_api_key)

# ============================================================================
# DATABASE SETUP
# ============================================================================

def init_db():
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect('finance_tracker.db')
    cursor = conn.cursor()

    # Salary table - stores monthly income
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS salary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            month TEXT NOT NULL,
            year INTEGER NOT NULL,
            created_at TEXT
        )
    ''')

    # Expenses table - stores all expenses
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            created_at TEXT
        )
    ''')

    # Chat history - stores conversation
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            content TEXT,
            timestamp TEXT
        )
    ''')

    # User profile - stores user info
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT,
            updated_at TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("✓ Database initialized successfully!")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_current_month_context():
    """Get current month name, number, and year."""
    now = datetime.now()
    return now.strftime("%B"), now.strftime("%m"), now.year


def get_monthly_financial_totals():
    """Calculate total salary and expenses for current month."""
    month_name, month_number, year = get_current_month_context()
    saved_name = get_saved_name()
    conn = sqlite3.connect('finance_tracker.db')
    cursor = conn.cursor()
    
    # Get salary for current month for current user
    if saved_name:
        cursor.execute(
            'SELECT SUM(amount) FROM salary WHERE month = ? AND year = ? AND user = ?',
            (month_name, year, saved_name)
        )
    else:
        cursor.execute(
            'SELECT SUM(amount) FROM salary WHERE month = ? AND year = ?',
            (month_name, year)
        )
    salary = cursor.fetchone()[0] or 0
    
    # Get expenses for current month for current user
    if saved_name:
        cursor.execute(
            'SELECT SUM(amount) FROM expenses WHERE strftime("%m", date) = ? AND strftime("%Y", date) = ? AND user = ?',
            (month_number, str(year), saved_name)
        )
    else:
        cursor.execute(
            'SELECT SUM(amount) FROM expenses WHERE strftime("%m", date) = ? AND strftime("%Y", date) = ?',
            (month_number, str(year))
        )
    total_expenses = cursor.fetchone()[0] or 0
    conn.close()
    
    return month_name, year, float(salary), float(total_expenses)


def save_chat(role, content):
    """Save chat message to database."""
    conn = sqlite3.connect('finance_tracker.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO chat_history (role, content, timestamp) VALUES (?, ?, ?)',
        (role, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()


def get_recent_history():
    """Get last 10 chat messages for context."""
    conn = sqlite3.connect('finance_tracker.db')
    cursor = conn.cursor()
    cursor.execute('SELECT role, content FROM chat_history ORDER BY id DESC LIMIT 10')
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r, "content": c} for r, c in reversed(rows)]


def save_user_name(name):
    """Save user's name to profile."""
    cleaned_name = (name or "").strip()
    if not cleaned_name:
        return "I couldn't save the name. Please tell me your name again."

    conn = sqlite3.connect('finance_tracker.db')
    cursor = conn.cursor()
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO user_profile (id, name, updated_at)
        VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            updated_at = excluded.updated_at
    ''', (cleaned_name, updated_at))
    conn.commit()
    conn.close()
    return f"Got it! I'll remember your name as {cleaned_name}."


def get_saved_name():
    """Retrieve saved user name from database."""
    conn = sqlite3.connect('finance_tracker.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM user_profile WHERE id = 1')
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] else None


def clear_finance_values():
    """Clear all financial data."""
    conn = sqlite3.connect('finance_tracker.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM salary')
    cursor.execute('DELETE FROM expenses')
    cursor.execute('DELETE FROM chat_history')
    conn.commit()
    conn.close()
    return "Done! I cleared all salary, expenses, and chat history. Your balance is now $0.00."


# ============================================================================
# TOOL FUNCTIONS (Called by AI Agent)
# ============================================================================

def set_salary(amount, month, year):
    """
    Set or add to monthly salary.
    
    Args:
        amount: Income amount
        month: Month name (e.g., "April")
        year: Year (e.g., 2026)
    
    Returns:
        Confirmation message
    """
    saved_name = get_saved_name()
    conn = sqlite3.connect('finance_tracker.db')
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Get current salary for this month for current user
    if saved_name:
        cursor.execute(
            'SELECT SUM(amount) FROM salary WHERE month = ? AND year = ? AND user = ?',
            (month, year, saved_name)
        )
    else:
        cursor.execute(
            'SELECT SUM(amount) FROM salary WHERE month = ? AND year = ?',
            (month, year)
        )
    current_amount = cursor.fetchone()[0] or 0
    new_total = float(current_amount) + float(amount)

    # Replace with new total for current user
    if saved_name:
        cursor.execute('DELETE FROM salary WHERE month = ? AND year = ? AND user = ?', (month, year, saved_name))
        cursor.execute(
            'INSERT INTO salary (amount, month, year, created_at, user) VALUES (?, ?, ?, ?, ?)',
            (new_total, month, year, created_at, saved_name)
        )
    else:
        cursor.execute('DELETE FROM salary WHERE month = ? AND year = ?', (month, year))
        cursor.execute(
            'INSERT INTO salary (amount, month, year, created_at) VALUES (?, ?, ?, ?)',
            (new_total, month, year, created_at)
        )

    conn.commit()
    conn.close()
    return f"✓ Income +${amount:.2f} recorded for {month} {year}. Total income: ${new_total:.2f}"


def log_expense(amount, category, description, date=None):
    """
    Log an expense to the database.
    
    Args:
        amount: Expense amount
        category: Category (e.g., "Rent", "Groceries")
        description: Description of expense
        date: Optional date (YYYY-MM-DD), defaults to today
    
    Returns:
        Confirmation with updated balance
    """
    saved_name = get_saved_name()
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect('finance_tracker.db')
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if saved_name:
        cursor.execute(
            'INSERT INTO expenses (amount, category, description, date, created_at, user) VALUES (?, ?, ?, ?, ?, ?)',
            (amount, category, description, date, created_at, saved_name)
        )
    else:
        cursor.execute(
            'INSERT INTO expenses (amount, category, description, date, created_at) VALUES (?, ?, ?, ?, ?)',
            (amount, category, description, date, created_at)
        )
    conn.commit()
    conn.close()

    # Get updated balance
    current_month, current_year, salary, total_expenses = get_monthly_financial_totals()
    balance = salary - total_expenses

    return f"✓ Logged ${amount:.2f} for {category} ({description}). Spent: ${total_expenses:.2f} | Remaining: ${balance:.2f}"


def get_balance():
    """
    Get current month balance snapshot.
    
    Returns:
        Formatted balance summary
    """
    current_month, current_year, salary, total_expenses = get_monthly_financial_totals()
    balance = salary - total_expenses

    return (
        f"📊 {current_month} {current_year} Snapshot: "
        f"Salary: ${salary:.2f} "
        f"Spent: ${total_expenses:.2f} "
        f"Remaining: ${balance:.2f}"
    )


def get_expense_summary():
    """
    Get detailed spending breakdown by category.
    
    Returns:
        Formatted expense summary
    """
    saved_name = get_saved_name()
    current_month, current_year, salary, total_expenses = get_monthly_financial_totals()
    conn = sqlite3.connect('finance_tracker.db')
    cursor = conn.cursor()

    # Group expenses by category for current user
    if saved_name:
        cursor.execute('''
            SELECT category, SUM(amount)
            FROM expenses
            WHERE strftime("%m", date) = ? AND strftime("%Y", date) = ? AND user = ?
            GROUP BY category
            ORDER BY SUM(amount) DESC
        ''', (datetime.now().strftime("%m"), str(current_year), saved_name))
    else:
        cursor.execute('''
            SELECT category, SUM(amount)
            FROM expenses
            WHERE strftime("%m", date) = ? AND strftime("%Y", date) = ?
            GROUP BY category
            ORDER BY SUM(amount) DESC
        ''', (datetime.now().strftime("%m"), str(current_year)))
    
    summary_data = cursor.fetchall()
    conn.close()

    if not summary_data:
        return (
            f"📈 {current_month} Spending Breakdown: "
            f"No expenses recorded yet. "
            f"Remaining: ${salary - total_expenses:.2f}"
        )

    summary_lines = [f"📈 {current_month} Spending Breakdown:"]
    for category, total in summary_data:
        percentage = (total / salary * 100) if salary > 0 else 0
        summary_lines.append(f"  • {category}: ${total:.2f} ({percentage:.1f}%)")

    balance = salary - total_expenses
    summary_lines.append(f"Total Spent: ${total_expenses:.2f} | Remaining: ${balance:.2f}")
    
    return " ".join(summary_lines)


# ============================================================================
# AI TOOL DEFINITIONS
# ============================================================================

tools = [
    {
        "type": "function",
        "function": {
            "name": "set_salary",
            "description": "Call when user mentions income, salary, earnings, or monthly pay for any month/year.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Income amount"},
                    "month": {"type": "string", "description": "Month name (e.g., 'April')"},
                    "year": {"type": "integer", "description": "Year (e.g., 2026)"}
                },
                "required": ["amount", "month", "year"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_expense",
            "description": "Call when user mentions spending money on anything - groceries, rent, gas, entertainment, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Amount spent"},
                    "category": {"type": "string", "description": "Category: Rent, Groceries, Transport, Entertainment, Health, Utilities, Family, Misc"},
                    "description": {"type": "string", "description": "What was bought"},
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format (optional)"}
                },
                "required": ["amount", "category", "description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_balance",
            "description": "Call when user asks how much money is left, remaining budget, balance, or tracking status.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_expense_summary",
            "description": "Call when user asks for breakdown, summary, where money went, spending by category, or analysis.",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

system_prompt = """You are a professional Personal Finance Assistant. Your role is to:
1. Help users track their monthly income and expenses accurately
2. Understand natural language about money matters
3. Call the appropriate tools when user mentions salary, expenses, balance, or summaries
4. Provide clear, friendly, formatted responses
5. Never invent amounts - always use what user provides
6. Be concise but helpful

Always use emojis to make responses friendly and scannable. Format numbers clearly with $ and decimals."""


# ============================================================================
# TOOL EXECUTION & AI INTEGRATION
# ============================================================================

def execute_tool(function_name, function_args):
    """Execute AI tool calls."""
    if function_name == "set_salary":
        return set_salary(**function_args)
    elif function_name == "log_expense":
        return log_expense(**function_args)
    elif function_name == "get_balance":
        return get_balance()
    elif function_name == "get_expense_summary":
        return get_expense_summary()
    else:
        return f"Error: Unknown tool - {function_name}"


def parse_tool_args(raw_args, function_name):
    """Parse tool arguments robustly."""
    try:
        if isinstance(raw_args, dict):
            return raw_args
        
        if isinstance(raw_args, str):
            return json.loads(raw_args)
    except:
        pass

    # Fallback: set defaults
    args = {}
    if function_name == "set_salary":
        args.setdefault("month", datetime.now().strftime("%B"))
        args.setdefault("year", datetime.now().year)
    elif function_name == "log_expense":
        args.setdefault("category", "Misc")
        args.setdefault("description", "expense")
    
    return args


def run_conversation(user_prompt):
    """Run the AI conversation with tool calling."""
    normalized_prompt = (user_prompt or "").strip().lower()
    saved_name = get_saved_name()

    # Handle simple greetings
    greeting_messages = {
        "hi", "hello", "hey", "hii", "hello there", 
        "good morning", "good afternoon", "good evening"
    }
    if normalized_prompt in greeting_messages:
        if saved_name:
            reply = f"👋 Hi {saved_name}! Ready to manage your finances. What can I help?"
        else:
            reply = "👋 Hello! I'm your finance assistant. What would you like to do?"
        save_chat("user", user_prompt)
        save_chat("assistant", reply)
        return reply

    # Handle name updates
    name_match = re.search(
        r"(?:my name is|i am|call me|i'm)\s+([A-Za-z][A-Za-z\s]{1,40})",
        user_prompt or "",
        re.I
    )
    if name_match:
        detected_name = name_match.group(1).strip()
        reply = save_user_name(detected_name)
        save_chat("user", user_prompt)
        save_chat("assistant", reply)
        return reply

    # Handle name queries
    if re.search(r"(my name|who am i|do you remember)", normalized_prompt):
        if saved_name:
            reply = f"📝 I remember your name as {saved_name}."
        else:
            reply = "I don't have your name saved yet. Tell me: 'My name is ...' and I'll remember!"
        save_chat("user", user_prompt)
        save_chat("assistant", reply)
        return reply

    # Handle reset/clear
    if re.search(r"(clear|reset)\s+(all|data|values)", normalized_prompt):
        reply = clear_finance_values()
        save_chat("user", user_prompt)
        save_chat("assistant", reply)
        return reply

    # Handle date queries
    if re.search(r"(today.*date|what.*today|current.*date)", normalized_prompt):
        reply = f"📅 Today's date is {datetime.now().strftime('%Y-%m-%d')}"
        save_chat("user", user_prompt)
        save_chat("assistant", reply)
        return reply

    # Main AI agent loop with tool calling
    history = get_recent_history()
    profile_context = f"User name: {saved_name}" if saved_name else "User name: Unknown"
    
    messages = [
        {
            "role": "system",
            "content": system_prompt + f"\n\nContext: {profile_context}\nCurrent Date: {datetime.now().strftime('%Y-%m-%d')}"
        }
    ]
    messages.extend(history)
    messages.append({"role": "user", "content": user_prompt})

    try:
        response = groq.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
    except Exception as e:
        error_msg = f"⚠️ I encountered an error: {str(e)}"
        save_chat("user", user_prompt)
        save_chat("assistant", error_msg)
        return error_msg

    # Tool calling loop
    iteration_count = 0
    max_iterations = 8

    while response.choices[0].message.tool_calls and iteration_count < max_iterations:
        response_message = response.choices[0].message
        
        # Add assistant message with tool calls
        assistant_message = {
            "role": "assistant",
            "content": response_message.content,
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                }
                for tool_call in response_message.tool_calls
            ]
        }
        messages.append(assistant_message)

        # Execute tools
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = parse_tool_args(tool_call.function.arguments or "{}", function_name)

            try:
                result = execute_tool(function_name, function_args)
            except Exception as e:
                result = f"Error executing {function_name}: {str(e)}"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": str(result)
            })

        # Get next response
        try:
            response = groq.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
        except Exception as e:
            error_msg = f"⚠️ Error in conversation loop: {str(e)}"
            save_chat("user", user_prompt)
            save_chat("assistant", error_msg)
            return error_msg

        iteration_count += 1

    # Return final response
    final_content = response.choices[0].message.content or "I couldn't generate a response."
    save_chat("user", user_prompt)
    save_chat("assistant", final_content)
    
    return final_content


# ============================================================================
# GRADIO INTERFACE
# ============================================================================

def chat_handler(message, history):
    """Handle chat messages from Gradio."""
    # Extract text from message
    user_text = message if isinstance(message, str) else (message.get("text", "") if isinstance(message, dict) else str(message))
    return run_conversation(user_text)


def create_interface():
    """Create Gradio chat interface."""
    with gr.Blocks(title="💰 Personal Finance Tracker", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 💰 Personal Finance AI Agent
        
        Chat naturally about your income and expenses. I'll track everything accurately and help you manage your money.
        """)

        chatbot = gr.Chatbot(
            label="Chat",
            height=400,
            show_share_button=False
        )
        
        msg = gr.Textbox(
            label="Your message",
            placeholder="e.g., 'My salary is $3,500' or 'I spent $50 on groceries'",
            lines=2
        )
        
        clear = gr.ClearButton([msg, chatbot])

        # Example messages
        gr.Examples(
            examples=[
                "My monthly salary is $3500",
                "I spent $50 on groceries today",
                "How much money is left?",
                "Show me my spending breakdown",
                "I paid $900 for rent",
            ],
            inputs=msg,
            label="Example questions to try:"
        )

        def respond(message, chat_history):
            response = chat_handler(message, chat_history)
            chat_history.append((message, response))
            return "", chat_history

        msg.submit(respond, [msg, chatbot], [msg, chatbot], queue=False)
        
    return demo


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Initialize database
    init_db()
    
    # Create and launch interface
    print("\n" + "="*60)
    print("🚀 Personal Finance Tracker Starting...")
    print("="*60)
    
    demo = create_interface()
    demo.launch(share=False, server_name="127.0.0.1", server_port=7890)
