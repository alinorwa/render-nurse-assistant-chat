# 🏥 Medical Support System | AI-Powered Refugee Assistance

A secure, real-time medical communication platform designed to bridge the language barrier between **Refugees** and **Nurses** in asylum centers. The system leverages **Azure AI** for real-time translation, voice-to-text transcription, and medical image analysis, ensuring rapid and accurate medical triage while maintaining strict **GDPR compliance**.

---

## 🌟 Project Overview

In refugee camps, language differences often delay critical medical care. This system allows refugees to communicate symptoms in their native language (text, voice, or image), while nurses receive everything translated and analyzed in Norwegian (or English). It features an intelligent triage system to prioritize urgent cases and an early warning system for potential epidemics.

---

## 🚀 Key Features

### 1. 💬 Intelligent Chat System
- **Real-Time Communication:** Instant messaging powered by **WebSockets (Django Channels & Daphne)**.
- **Bi-Directional Translation:** Seamless translation between the refugee's native language and the nurse's language using **Azure Translator**.
- **Voice Notes (Whisper):** Refugees can send voice messages, which are automatically transcribed to text using **Azure OpenAI Whisper**.
- **Medical Image Analysis:** Users can upload medical images (e.g., rashes, medication), which are analyzed by **GPT-4o Vision** to provide context to the nurse.

### 2. 📊 Medical Dashboard & Analytics
A comprehensive admin dashboard provides real-time insights into the camp's health status:
- **Total Refugees:** Overview of registered users.
- **🚨 Urgent Cases:** Instant counter for high-priority cases requiring a doctor.
- **Active Chats:** Monitor ongoing consultations.
- **Daily Activity:** 7-day chart showing communication volume.
- **Language Distribution:** Visual breakdown of languages spoken in the camp (helps in resource planning).
- **Epidemic Alerts History:** Log of detected health outbreaks.

### 3. 💰 Cost-Efficiency & Caching
To optimize cloud costs, the system implements a smart caching layer:
- **Translation Cache:** Stores previously translated phrases to avoid redundant calls to Azure API.
- **Image Analysis Cache:** Caches AI analysis results for duplicate or similar images.
- **Result:** Significant reduction in Azure operational costs while maintaining speed.

### 4. 🛡️ Security & GDPR Compliance
- **Auto-Cleanup (Retention Policy):** Automated tasks delete messages and media files older than **14 days** (configurable) to comply with privacy laws.
- **Right to be Forgotten:** Users can permanently delete their accounts and data instantly.
- **Brute-Force Protection:** Integrated **Django Axes** to prevent unauthorized login attempts.
- **Data Encryption:** Sensitive fields are encrypted at rest in the database.

### 5. 🚨 Epidemic Early Warning System
An automated background task scans messages for clusters of symptoms (e.g., "diarrhea", "rash") within a specific timeframe. If a threshold is crossed, the system triggers an **Epidemic Alert** to warn medical staff of a potential outbreak.

---

## 🛠️ Tech Stack

Built with a robust, scalable architecture:

- **Backend:** Django 6.0 (Python 3.12)
- **Real-time:** Django Channels + Daphne
- **Async Processing:** Celery + Redis
- **Database:** PostgreSQL
- **Infrastructure:** Docker & Docker Compose
- **Hosting:** Render (Infrastructure as Code via Blueprints)
- **AI & Cloud Services (Azure):**
    - Azure OpenAI (GPT-4o & Whisper)
    - Azure Translator
    - Azure Blob Storage (Secure Media Storage)

---

## 📂 Architecture (Service Layer Pattern)

The codebase follows the **Service Layer Pattern** to ensure clean separation of concerns and maintainability:

```text
apps/chat/
├── services/
│   ├── message_service.py      # Orchestrates message creation & routing
│   ├── audio_service.py        # Handles Audio-to-Text (Whisper) logic
│   ├── image_service.py        # Handles Image Compression & Processing
│   ├── triage_service.py       # Logic for detecting urgent cases & keywords
│   └── notification_service.py # Manages WebSockets & Email Notifications
├── tasks.py                    # Celery Background Tasks
├── consumers.py                # WebSocket Interface
└── views.py                    # HTTP Endpoints


⚙️ Local Development Setup
Prerequisites
. Docker & Docker Compose
. Azure Account (for API Keys)
Steps
1.Clone the repository:
    git clone https://github.com/your-username/nurse-assistant-chat.git
    cd nurse-assistant-chat

2.Environment Variables:
    Create a .env file in the root directory and configure your keys (see .env.example).

3.Build and Run:   
    docker-compose up --build

4.Create Superuser:  
    docker-compose exec web python manage.py createsuperuser  

5.Access the Application:
    App: http://localhost:8000
    Admin/Dashboard: http://localhost:8000/dashboard/    

_______________________________________________________________

☁️ Deployment (Render)
This project is fully configured for Render using render.yaml Blueprints.
1.Push the code to a GitHub repository.
2.In Render, select "New Blueprint Instance".
3.Connect your repo. Render will automatically provision:
    .Web Service (Django + Daphne)
    .Background Worker (Celery)
    .Redis
    .PostgreSQL
4.Add your AZURE_* and SECRET_KEY variables in the Render Dashboard environment settings.

____________________________________________________________________

📄 License
This project is intended for humanitarian and medical support purposes.



## 📞 Contact & Support

This project was architected and developed by Ali .

If you have any questions regarding the architecture, security features, or potential deployment of this system, feel free to reach out:

- 📧 Email: alialrubay499@gmail.com
- 🐙 GitHub: [alinorwa](https://github.com/alinorwa)
- 💼 LinkedIn: [Ali Alrubay](https://www.linkedin.com/) # Don't forget to add your actual profile 
