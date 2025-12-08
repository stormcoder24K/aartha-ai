# 🌱 Aartha.ai: Multi-Language Financial Guidance Assistant for Rural India

A Flask-based full-stack web application providing accessible financial help to Indian villagers through AI-powered guidance, form processing, and interactive tools.

---

## 🧭 Overview

**Aartha.ai** is a full-stack AI assistant designed to help Indian villagers with no prior financial knowledge access simple, step-by-step guidance on:

- Banking
- Loans
- Savings & Fixed Deposits
- Government Schemes
- ATM operations
- Insurance
- Microloan eligibility
- Form-filling assistance (PDF upload)

### Technology Stack

The system combines:
- **Flask** for backend routing
- **Gemini Flash** for natural-language responses
- **Multi-language support** (English, Hindi, Kannada, Tamil, Telugu)
- **PDF parsing** using PyPDF2
- **Structured system prompts** providing targeted guidance for each financial context

Aartha.ai is built with the intention of **improving digital and financial literacy in rural communities**.

---

## ⚙️ Key Features

### 🤖 AI Chatbot
- Simple financial questions answered in real-time
- Domain-specific financial guidance including:
  - Savings accounts
  - Fixed deposits
  - Current accounts
  - Insurance
  - ATM operations
  - Government schemes

### 📄 PDF Form Upload + Extraction
- Accepts PDF bank forms
- Extracts text automatically
- Provides step-by-step filling guidance

### 🎙️ Voice-based ATM Helper
- User describes the ATM screen
- AI gives instructions line-by-line
- Supports multiple Indian languages

### 💰 Microloan Eligibility Evaluator
- Inputs questionnaire responses
- Returns village-friendly eligibility reasoning
- Simplifies complex loan criteria

### 🏦 Additional Features
- Locker facility finder
- Government scheme lookup by village/state
- All routes cleanly modularized with consistent patterns

---

## 🏗️ Architecture
```
User (Web UI)
     |
     v
Flask Backend
     |
     |-- /chat                    → General financial chatbot
     |-- /get_schemes             → GOI scheme lookup by village/state
     |-- /upload_form             → PDF → text extraction → AI guidance
     |-- /process_atm_voice       → ATM voice guidance
     |-- /process_savings_query   → Savings account helper
     |-- /process_fixed_deposit   → FD helper
     |-- /process_current_account → CA helper
     |-- /estimate_microloan      → Eligibility classifier
     |-- /insurance_chat          → Insurance guidance
     |
     v
Gemini API
     |
     v
Multi-language AI Responses
```

---

## 🧩 Technical Highlights

- **Robust Error Handling**: Graceful degradation and user-friendly error messages
- **Secure File Uploads**: Size-limited uploads with automatic cleanup
- **Language-Specific Prompts**: More accurate guidance for each language
- **PDF Parsing**: Automated text extraction using PyPDF2
- **Modular Architecture**: Granular route separation for clarity and maintainability
- **API Fallback**: Graceful fallback to English when needed

---

## 💻 Installation

### 1. Clone Repository
```bash
git clone <repo-url>
cd aartha.ai
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the root directory:
```env
GOOGLE_API_KEY=your_api_key_here
```

### 4. Run Application
```bash
python app.py
```

The app will run at: **http://127.0.0.1:5000**

---

## 🧪 Usage Examples

### 1. Chatbot (`POST /chat`)
```json
{
  "message": "What is a savings account?",
  "language": "hi-IN"
}
```

### 2. Upload Form (`POST /upload_form`)

Upload PDF → AI extracts fields → Guides filling process

### 3. ATM Helper (`POST /process_atm_voice`)
```json
{
  "transcript": "I see Withdraw, Balance",
  "language": "en-US"
}
```

### 4. Government Schemes Lookup (`POST /get_schemes`)

Provide village/state → Returns relevant GOI schemes in simple language

### 5. Microloan Eligibility (`POST /estimate_microloan`)

User provides questionnaire → AI evaluates eligibility with reasoning

---

## 📁 Project Structure
```text
aartha.ai/
├── templates/
│   ├── index.html
│   ├── chatbot.html
│   ├── schemes.html
│   ├── atm_guide.html
│   ├── savings_guide.html
│   ├── fixed_deposit_guide.html
│   ├── current_account_guide.html
│   ├── microloan_eligibility.html
│   ├── insurance.html
│   ├── locker.html
│   └── fraud_alerts.html
│
├── uploads/                    # Temporary file storage
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not committed)
└── README.md                   # This file
```

---

## 📊 Roadmap

- [ ] Add OCR for image-based forms
- [ ] Add Redis caching for scheme lookups
- [ ] Add user accounts + session history
- [ ] Implement PWA mobile mode
- [ ] Add audio guidance (TTS) in all languages
- [ ] Add village-level personalization
- [ ] Expand language support to more Indian languages
- [ ] Create admin dashboard for scheme management

---

## ⚠️ Limitations

- JPG/PNG OCR not yet supported
- No persistent database (stateless sessions)
- PDF extraction may miss formatted data
- Depends on Gemini API uptime
- Requires internet connectivity

---

## 📚 Real-World Context

Aartha.ai addresses critical issues in rural India:

- **Financial illiteracy** in rural regions
- **Difficulty filling forms** without assistance
- **ATM and banking UI confusion**
- **Low awareness** of government schemes
- **Lack of clarity** around loans, FDs, savings, insurance

### Impact Goals

- Empower villagers with financial knowledge
- Reduce dependency on middlemen
- Increase uptake of government schemes
- Improve digital literacy in underserved communities

---

## 🛡️ Security & Privacy

- No user data is stored permanently
- Uploaded files are automatically deleted after processing
- API keys are stored securely in environment variables
- No personal information is logged

---

## 🧑‍💻 Authors

**Aarush, Aryan**  
AI/ML Engineers (CSE — AI & ML)  
Focused on full-stack, AI-for-good, and accessible financial tooling


---

## 🙏 Acknowledgments

- Google Gemini API for AI capabilities
- Government of India for scheme data
- Rural communities providing feedback and use cases

---

## 📜 License

MIT Licence

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📞 Support

For questions or support, please open an issue on GitHub or contact [aarushinc1@gmail.com]

---

**Built with ❤️ for Rural India**
