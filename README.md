# 🏥 AI-Powered Medical Support System

![Django](https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Azure](https://img.shields.io/badge/Microsoft_Azure-0089D6?style=for-the-badge&logo=microsoft-azure&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-Async_Tasks-37814A?style=for-the-badge&logo=celery&logoColor=white)

An enterprise-grade, real-time medical communication platform designed to bridge the language gap between refugees and medical staff in Norwegian asylum centers. 

The system leverages **Microsoft Azure AI** to provide real-time bi-directional translation, voice-to-text transcription, and medical image analysis, ensuring rapid medical triage while maintaining strict **GDPR compliance**.

---

## 🌟 Key Features

### 💬 Real-Time Multilingual Communication
- **WebSockets:** Instant messaging powered by Django Channels and Daphne.
- **Auto-Translation:** Seamless bi-directional translation (Refugee's Native Language ↔ Norwegian) using **Azure Translator**.
- **Voice Notes:** Users can send voice messages which are automatically transcribed to text via **Azure OpenAI Whisper**.
- **Canned Responses:** Nurses can use predefined templates for faster replies.

### 🤖 AI Triage & Medical Assistance
- **Medical Image Analysis:** Images uploaded by patients (e.g., rashes, prescriptions) are analyzed by **GPT-4o Vision** to provide context to the medical staff.
- **Smart Triage:** The system scans translated text and AI analysis for dangerous keywords (e.g., "bleeding", "chest pain"). If detected, the session is automatically escalated to **High Priority (Doctor)**.
- **Epidemic Early Warning:** A scheduled Celery task groups recent symptoms. If multiple patients report similar infectious symptoms (e.g., respiratory issues) within a short timeframe, it triggers an **Epidemic Outbreak Alert** to the administration.

### 🛡️ Security & GDPR Compliance
- **Automated Data Retention:** Background tasks permanently delete chat history and Azure Blob files older than 14 days.
- **Right to be Forgotten:** Patients can permanently delete their accounts and all associated medical data with a single click.
- **Brute-Force Protection:** Integrated `django-axes` to block suspicious login attempts based on IP and Username combinations.
- **Content Security Policy (CSP):** Strict policies configured to prevent XSS attacks.

---

## 🏗️ System Architecture

The project is built using the **Service Layer Pattern** to ensure scalability, maintainability, and clean decoupling of the business logic from HTTP/WebSocket handlers.

```text
apps/chat/
├── services/
│   ├── message_service.py      # Orchestrates message creation, routing & WebSockets
│   ├── audio_service.py        # Azure Whisper API integration
│   ├── image_service.py        # Pillow image compression
│   ├── triage_service.py       # Triage logic and keyword detection
│   └── notification_service.py # WebSocket broadcasting
├── tasks.py                    # Async Celery workers (AI processing & GDPR cleanup)
├── consumers.py                # AsyncWebsocketConsumer
└── views.py                    # HTTP Endpoints


🗄️ Caching Strategy (Cost Optimization)
To optimize Azure API costs, the system hashes texts and images. It queries TranslationCache and ImageAnalysisCache databases before making external API calls. Caches are safely cleared every 30 days.

⚙️ Local Development Setup
Prerequisites
Docker & Docker Compose
Microsoft Azure Account (OpenAI, Translator, Blob Storage)
Installation Steps
1 . Clone the repository:
       git clone https://github.com/your-github-username/nurse-assistant-chat.git
       cd nurse-assistant-chat

2 . Environment Variables:
        Create a .env file in the root directory based on the provided .env.example and add your Azure credentials.

3 . Build & Run with Docker:
        docker-compose up --build

4 . Create an Admin Account:
        docker-compose exec web python manage.py createsuperuser

5 . Access the platform:
        Patient Interface: http://localhost:8000
        Admin/Nurse Dashboard: http://localhost:8000/admin/

☁️ Deployment (Render Infrastructure as Code)
The application is fully containerized and configured for one-click deployment on Render using a render.yaml blueprint.
The blueprint automatically provisions and connects:
1- Web Service (Django + Daphne)
2- Background Worker (Celery)
3- Cron Job / Beat (Celery Beat for Epidemic scanning & GDPR cleanup)
4- PostgreSQL Database
5- Redis (Broker & Cache)
Note: Media files are stored securely in Azure Blob Storage.  

📞 Contact
Developed and architected by Ali 
Full Stack Software Engineer
🌐 Portfolio: Visit My Portfolio
💼 LinkedIn: Ali 
📧 Email: alialrubay499@gmail.com