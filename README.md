---
title: Finance AI Agent
emoji: 💰
colorFrom: green
colorTo: blue
sdk: gradio
app_file: app.py
license: apache-2.0
---

# 💰 Finance AI Agent

<div align="center">

**An Intelligent Financial Companion Powered by Llama 3.1**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Gradio](https://img.shields.io/badge/Gradio-Latest-orange.svg)](https://gradio.app/)
[![Groq](https://img.shields.io/badge/Groq-API-green.svg)](https://groq.com/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

*A sophisticated AI-powered personal finance tracker that helps you manage your salary, expenses, and financial reports through natural conversation.*

</div>

---

## 🚀 Project Overview

Finance AI Agent is an intelligent financial companion that leverages the power of **Llama 3.1** (via Groq's high-performance API) to provide seamless expense tracking, financial analysis, and automated reporting. Built with a robust SQLite database for persistent storage and a beautiful Gradio interface, this application transforms how you interact with your personal finances.

### 🎯 Key Capabilities

- **AI-Driven Financial Insights**: Natural language processing for intelligent expense categorization and financial analysis
- **Dynamic PDF Watermarking**: Professional PDF reports with security watermarks for document protection
- **Secure Data Storage**: SQLite database with persistent, multi-user support
- **Natural Language Processing**: Interact with your finances using everyday conversation
- **Intelligent Intent Classification**: Automatically understands your financial actions
- **Automated PDF Reports**: Generate professional financial summaries with a single click
- **Secure Email Delivery**: Receive detailed reports directly in your inbox
- **Real-time Balance Tracking**: Always know your financial standing

---

## ✨ Key Features

### 💬 **Natural Language Expense Tracking**
- Log expenses by simply typing: *"I spent Rs 500 on groceries today"*
- Set salary with: *"My monthly salary is Rs 50,000"*
- Add income with: *"I earned Rs 10,000 from freelance work"*
- The AI automatically categorizes and records everything

### 📊 **Monthly Financial Snapshots**
- Real-time balance calculations
- Spending breakdown by category with percentages
- Income vs. expense analysis
- Visual representation of your financial health

### 📄 **Automated Professional PDF Reports**
- Beautifully formatted financial statements using **fpdf**
- Custom-styled headers with your name and date
- Detailed spending summaries with category breakdowns
- Recent transaction history
- Professional layout suitable for record-keeping

### 📧 **Secure Email Delivery**
- SMTP-based email sending with TLS encryption
- Attach professional PDF reports directly to emails
- Configurable email service (Gmail, Outlook, etc.)
- Environment variable-based credential management

### 👥 **Multi-User Support**
- Each user has isolated financial data
- Switch between users seamlessly
- Personalized reports for each individual
- Independent financial tracking

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **AI Model** | Llama 3.1 (8B Instant) | Natural language understanding & intent classification |
| **AI Provider** | Groq API | High-performance, low-latency inference |
| **Web Interface** | Gradio | Modern, responsive chat interface |
| **Database** | SQLite3 | Persistent storage for financial data |
| **PDF Generation** | fpdf | Professional report creation with watermarking |
| **Email** | smtplib (SMTP) | Secure email delivery |
| **Language** | Python 3.9+ | Core application logic |

---

## 📖 User Guide

### Getting Started

1. **Introduce Yourself**
   ```
   "Hi, I'm John"
   ```
   The AI will remember your name for all future interactions.

2. **Set Your Monthly Salary**
   ```
   "My monthly salary is Rs 75,000"
   ```
   This establishes your baseline income for the month.

3. **Log Expenses**
   ```
   "I spent Rs 2,500 on groceries"
   "Bought a new laptop for Rs 45,000"
   "Paid electricity bill: Rs 3,500"
   ```
   The AI automatically categorizes and tracks each expense.

4. **Add Additional Income**
   ```
   "I earned Rs 15,000 from freelance work"
   "Got a bonus of Rs 10,000"
   ```
   Track income beyond your base salary.

5. **Check Your Balance**
   ```
   "How much money do I have left?"
   "What's my current balance?"
   "Show me my financial snapshot"
   ```
   Get real-time updates on your financial status.

6. **View Spending Breakdown**
   ```
   "Show me my spending breakdown"
   "Where did I spend my money?"
   "Category-wise expense summary"
   ```
   See detailed analysis by spending category.

7. **Request Email Reports**
   ```
   "Send the report to my email"
   "Email me the financial summary"
   ```
   Receive a professional PDF report directly in your inbox.

### Example Conversation

```
User: "Hi, I'm Sarah"
AI: "Nice to meet you, Sarah!"

User: "My monthly salary is Rs 60,000"
AI: "Salary of Rs 60,000.00 (LKR) for January 2026 saved for Sarah."

User: "I spent Rs 3,500 on groceries and Rs 1,200 on transport"
AI: "I've recorded all your transactions: Rs 3,500 for Groceries and Rs 1,200 for Transport."

User: "How much do I have left?"
AI: "Sarah - January 2026 Financial Snapshot:
Total Income: Rs 60,000.00 (LKR)
Total Expenses: Rs 4,700.00 (LKR)
Remaining Balance: Rs 55,300.00 (LKR)"

User: "Send the report to my email"
AI: "Success: Report sent to sarah@email.com!"
```

---

## ⚙️ Setup Instructions

### For Hugging Face Spaces Deployment

#### Prerequisites
- A Hugging Face account with Space creation permissions
- Groq API key from [console.groq.com](https://console.groq.com/)
- Email account with app password (for Gmail, enable 2FA and generate app password)

#### Step 1: Create a New Space
1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click **"Create new Space"**
3. Choose **Gradio** as the SDK
4. Select **Free** or **Pro** hardware based on your needs
5. Name your space (e.g., `personal-finance-ai`)

#### Step 2: Upload Files
Upload the following files to your Space:
```
├── app.py                 # Main application
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

#### Step 3: Configure Secrets
Navigate to your Space's **Settings** → **Secrets** and add the following:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `GROQ_API_KEY` | Your Groq API key | `gsk_...` |
| `EMAIL_USER` | Your email address | `your.email@gmail.com` |
| `EMAIL_PASS` | Your email app password | `abcd-efgh-ijkl-mnop` |

**Important:**
- Get your Groq API key from [console.groq.com](https://console.groq.com/)
- For Gmail, generate an app password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
- Never commit secrets to your repository

#### Step 4: Deploy
The Space will automatically build and launch. Once ready, access your AI agent at the provided URL.

---

### For Local Development

#### Prerequisites
- Python 3.9 or higher
- pip package manager

#### Installation

1. **Clone the Repository**
   ```bash
   git clone <your-repository-url>
   cd Assignment-01
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   Create a `.env` file in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   EMAIL_USER=your_email@gmail.com
   EMAIL_PASS=your_email_app_password
   ```

5. **Run the Application**
   ```bash
   python app.py
   ```

6. **Access the Interface**
   Open your browser and navigate to `http://localhost:7860`

---

## 📦 Dependencies

Install all required packages using:

```bash
pip install -r requirements.txt
```

**Key Dependencies:**
- `gradio` - Web interface framework
- `groq` - Groq API client
- `python-dotenv` - Environment variable management
- `fpdf` - PDF generation
- `sqlite3` - Database (built-in Python)

---

## 🔒 Security Best Practices

- **Never commit secrets** to version control
- **Use app passwords** for email authentication, not your main password
- **Rotate API keys** periodically
- **Enable 2FA** on all associated accounts
- **Review permissions** regularly

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Groq** for providing high-performance AI inference
- **Gradio** for the beautiful web interface framework
- **Llama 3.1** by Meta for the powerful language model

---

<div align="center">

**Built with ❤️ by Kaviondu Chamod**

[⭐ Star this repo](https://github.com/Dev-Kavindu/finance-ai-agent) | [🐛 Report Issues](https://github.com/Dev-Kavindu/finance-ai-agent/issues) | [💡 Feature Requests](https://github.com/Dev-Kavindu/finance-ai-agent/issues)

</div>
