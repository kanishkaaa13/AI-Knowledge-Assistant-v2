<div align="center">
  
# 🧠 AI Knowledge Assistant

<p align="center">

<img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
<img src="https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white" />
<img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" />
<img src="https://img.shields.io/badge/AI-Powered-purple?style=for-the-badge" />
<img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />

</p>

<p align="center">
An AI-powered personal knowledge workspace designed to supercharge your productivity.
</p>

[**Report a Bug**](https://github.com/kanishkaaa13/AI-Knowledge-Assistant-/issues) • [**Request a Feature**](https://github.com/kanishkaaa13/AI-Knowledge-Assistant-/issues)

</div>

---

## 📖 Introduction

**AI Knowledge Assistant** is a modern, enterprise-grade personal knowledge workspace. It allows users to seamlessly upload documents, chat with their personalized AI assistant, search across their entire conversation history, generate summaries, and even create dynamic quizzes. 

Built on a robust **RAG (Retrieval-Augmented Generation) + LLM** architecture, this platform combines real-time token streaming with persistent memory to deliver a seamless, Claude-inspired conversational experience. 

---

## 📸 Screenshots

<h3 align="center">🏠 AI Knowledge Assistant</h3>

<p align="center">
  <img width="1701" height="966"
       alt="AI Knowledge Assistant Dashboard"
       src="https://github.com/user-attachments/assets/da270a69-9c7c-4163-b72e-e47b4c4374b7" />
</p>

<h3 align="center">📊 Analytics & Insights</h3>

<p align="center">
  <img width="1396" height="970"
       alt="Analytics & Insights"
       src="https://github.com/user-attachments/assets/b2eb8809-9e43-4b73-a668-9ceb23434455" />
</p>

<h3 align="center">📄 Document Management</h3>

<p align="center">
  <img width="839" height="892"
       alt="Document Management"
       src="https://github.com/user-attachments/assets/bde5d782-43d5-4de6-a92e-116deb1dc22c" />
</p>

---

## ✨ Core Features

* **🧠 Persistent Conversation Memory:** Context-aware conversations that remember your past interactions.
* **💬 AI-Powered Document Chat:** Talk directly to your documents (PDF/DOCX/TXT/Markdown) to extract insights instantly.
* **🔍 Semantic Knowledge Search:** Vector-based retrieval to search across your entire uploaded knowledge base.
* **⚡ Real-Time Streaming AI:** Ultra-low latency responses with real-time token streaming.
* **📋 Smart Summaries & Quizzes:** Automatically generate document summaries and interactive quizzes to test your knowledge.
* **🎨 Modern SaaS Interface:** A beautiful, responsive UI featuring white cards, Inter font, and a premium purple accent theme.
* **🔐 Secure Authentication:** Enterprise-grade security with JWT authentication and protected routing.
* **📊 Analytics Dashboard:** Interactive charts (via Recharts), risk analytics visualizations, and role-based views (Student/Admin).
* **🎯 Goal Tracking:** Built-in weekly goals and progress tracking.
* **🤖 AI Counselor Support:** Built-in chatbot support tailored for guidance and personalized assistance.

---

## 🛠 Tech Stack

Our stack is carefully curated for scale, speed, and modern developer experience.

| Category | Technology |
| :--- | :--- |
| **Frontend** | Next.js, React, Tailwind CSS, TypeScript, Recharts, Framer Motion |
| **Backend** | FastAPI, Python, SQLAlchemy, PostgreSQL / SQLite, JWT, Server-Sent Events (SSE) |
| **AI / Machine Learning** | LangChain, Ollama, Vector Embeddings, RAG Pipeline, Semantic Search |
| **Deployment** | Vercel (Frontend), Render (Backend), Docker |

---

## 🏗 System Architecture

### 🧠 AI RAG Architecture

Our RAG (Retrieval-Augmented Generation) pipeline ensures the LLM is grounded in your private data.

```text
[User Upload] ──> [Document Parsing] ──> [Text Chunking]
                                               │
                                               ▼
[LLM Context Injection] <── [Vector DB] <── [Embedding Generation]
        │
        ▼
[Streaming Response] ──> [Persistent Conversation Memory]
```

1. **Document Upload Pipeline:** Extracts text from PDFs, DOCX, TXT, and Markdown files.
2. **Embedding Generation:** Converts text chunks into high-dimensional vector representations.
3. **Vector Database Retrieval:** Performs semantic similarity search against user queries.
4. **RAG Context Injection:** Feeds the most relevant chunks into the LLM prompt.
5. **Streaming LLM Responses:** Returns tokens in real-time for zero perceived latency.

### ⚡ Streaming Chat Architecture

Real-time streaming provides a snappy, native feel similar to Claude or ChatGPT.

* **SSE Endpoint:** FastAPI streams tokens via Server-Sent Events.
* **Frontend Rendering:** `ReadableStream` consumes the event stream chunk-by-chunk.
* **Typing Indicator System:** Dynamic UI updates as tokens arrive, providing immediate visual feedback.

### 🔐 Authentication Flow

* **JWT Authentication:** Cryptographically secure stateless tokens.
* **Secure Storage:** Tokens are securely stored and managed on the frontend.
* **Protected Routes:** Next.js middleware guards private dashboards.
* **Session Persistence:** Seamless token refresh flows prevent unexpected logouts.

---

## 📂 Folder Structure

```text
📦 AI-Knowledge-Assistant
├── 📁 frontend/                # Next.js application
│   ├── 📁 app/                 # App router, pages, layouts
│   ├── 📁 components/          # Reusable UI, Chat Bubbles, Sidebars
│   ├── 📁 lib/                 # API clients, utilities
│   ├── 📁 types/               # TypeScript interfaces
│   └── 📄 package.json
└── 📁 backend/                 # FastAPI application
    ├── 📁 app/                 
    │   ├── 📁 api/             # Routers, endpoints, deps
    │   ├── 📁 core/            # Config, security, middleware
    │   ├── 📁 models/          # SQLAlchemy ORM models
    │   └── 📁 services/        # AI orchestration, Vector Store
    ├── 📁 uploads/             # Local document storage
    ├── 📄 requirements.txt
    └── 📄 main.py              # Application entrypoint
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/auth/login` | Authenticate user and return JWT tokens |
| `POST` | `/auth/register` | Create a new account |
| `POST` | `/chat/stream` | Stream AI response (SSE) |
| `GET` | `/chat/history` | Retrieve persistent conversation memory |
| `POST` | `/documents/upload`| Process and embed documents into Vector DB |
| `POST` | `/search` | Perform semantic search on the knowledge base |
| `POST` | `/summary` | Generate an AI summary of a specific document |
| `POST` | `/quiz` | Generate interactive questions from document context |
| `GET` | `/analytics` | Retrieve metrics for the admin/user dashboard |

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/kanishkaaa13/AI-Knowledge-Assistant-.git
cd AI-Knowledge-Assistant-
```

### 2. Backend Setup (FastAPI)
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt

# Create your .env file
cp .env.example .env

# Start the server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup (Next.js)
```bash
cd frontend
npm install

# Create your .env.local file
cp .env.example .env.local

# Start the development server
npm run dev
```

Your frontend will now be running on `http://localhost:3000` and the backend on `http://localhost:8000`.

---

## 🔮 Future Improvements

We are constantly evolving to stay at the cutting edge of AI SaaS features:
* [ ] **Multi-model AI support:** Toggle between Claude, GPT-4, and local open-source models.
* [ ] **Voice Assistant:** Native speech-to-text and text-to-speech interaction.
* [ ] **Advanced OCR:** Extract text from scanned PDFs and images seamlessly.
* [ ] **Team Collaboration:** Shared workspaces and document repositories.
* [ ] **AI Autonomous Agents:** Agents that execute multi-step web research.
* [ ] **Knowledge Graphs:** Visual mappings of how your documents interlink.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Kanishka Shailendra Arde**
* **GitHub:** [@kanishkaaa13](https://github.com/kanishkaaa13)

<div align="center">
  <i>Built with ❤️ for the future of personal knowledge management.</i>
</div>
