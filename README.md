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

---

## ✨ Key Features

- **🧠 AI-Driven Financial Insights** – Natural language processing for intelligent expense categorization and financial analysis
- **🗣️ Natural Language Interface** – Log expenses, set salary, and track income using everyday conversation
- **📊 Real-Time Balance Tracking** – Instant financial snapshots with income vs. expense analysis
- **📄 Automated PDF Reports** – Professional financial statements with dynamic watermarking for document security
- **📧 Secure Email Delivery** – Receive detailed PDF reports directly in your inbox with TLS encryption
- **👥 Multi-User Support** – Isolated financial data for multiple users with personalized reports
- **🔒 Secure Data Storage** – SQLite database with persistent, encrypted data management
- **⚡ Intelligent Intent Classification** – Automatically understands and executes financial actions

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **AI Model** | Llama 3.1 (8B Instant) |
| **AI Provider** | Groq API |
| **Web Interface** | Gradio |
| **Database** | SQLite3 |
| **PDF Generation** | fpdf |
| **Email** | smtplib (SMTP) |
| **Language** | Python 3.9+ |

---

## 📖 Usage Example

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

## 🔒 Data Privacy

- All financial data is stored locally in SQLite database
- Email credentials are managed via environment variables (never committed to version control)
- PDF reports include dynamic watermarking for document security
- Multi-user data isolation ensures privacy between users

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
