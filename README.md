# 🌳 KnowledgeHub Buddy — Production Version

AI-powered doubt-clearing assistant for English classes.
Students ask questions, get answers from the teacher's own content, and take quizzes.

---

## 📁 Project Structure

```
knowledgehub-buddy/
├── app.py                          ← Student chat interface (home page)
├── pages/
│   └── 1_Teacher_Admin.py          ← Teacher admin panel (UI)
├── query_engine.py                 ← RAG brain (retrieval + Claude)
├── ingest.py                       ← Content processor
├── logo.png                        ← KnowledgeHub logo
├── requirements.txt                ← Python dependencies
├── Procfile                        ← Deployment start command
├── railway.toml                    ← Railway config
├── .streamlit/config.toml          ← App theme settings
├── .gitignore                      ← Git ignore rules
├── teacher_content/                ← Teaching materials go here
├── sample_content/                 ← Sample content for testing
├── students.json                   ← Auto-created student database
└── chroma_db/                      ← Auto-created vector database
```

---

## 🖥️ Local Setup (For Testing)

### Prerequisites
- Python 3.10+ → https://www.python.org/downloads/
- Anthropic API key → https://console.anthropic.com/

### Steps

```bash
# 1. Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
pip install docx2txt

# 3. Set your API key
# Windows:
set ANTHROPIC_API_KEY=your-key-here
# Mac/Linux:
export ANTHROPIC_API_KEY=your-key-here

# 4. Add teaching files to teacher_content/ folder, then build index
python ingest.py

# 5. Launch the app
streamlit run app.py
```

The app opens at http://localhost:8501

---

## 🚀 Deploy to Railway (Recommended — $5/month)

### Step 1: Install Git

Download from https://git-scm.com/downloads

### Step 2: Create a GitHub Repository

1. Go to https://github.com → Click "New repository"
2. Name it `knowledgehub-buddy`, set to **Private**, click Create
3. In your terminal, navigate to this project folder and run:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/knowledgehub-buddy.git
git push -u origin main
```

### Step 3: Deploy on Railway

1. Go to https://railway.app → Sign up with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `knowledgehub-buddy` repository
4. Railway will auto-detect the Procfile and start building

### Step 4: Set Environment Variables

In Railway dashboard → your project → Variables tab, add:

| Variable | Value |
|----------|-------|
| `ANTHROPIC_API_KEY` | Your API key from console.anthropic.com |
| `ADMIN_PASSWORD` | A strong password for the teacher admin panel |

### Step 5: First-Time Setup

1. Once deployed, Railway gives you a URL like `https://knowledgehub-buddy-xyz.up.railway.app`
2. Visit `your-url/Teacher_Admin` → Log in with your admin password
3. Go to **Upload Content** tab → Upload your teaching files (PDF, DOCX, TXT)
4. Go to **Rebuild Index** tab → Click "Rebuild knowledge base"
5. Go to **Manage Students** tab → Add your students and note their access codes
6. Share the main URL + access codes with students!

### Optional: Custom Domain

In Railway → Settings → Domains → Add your own domain (e.g. `doubts.knowledgehub.com`)

---

## 🔧 Teacher Admin Panel

Access at: `your-app-url/Teacher_Admin`

**Default password:** `teacher123` (change it by setting the `ADMIN_PASSWORD` environment variable)

### Features:
- **Dashboard** — See total students, questions asked, and exhausted quotas at a glance
- **Manage Students** — Add single or bulk students, set per-student quotas, refresh limits, remove access
- **Upload Content** — Upload PDFs, Word docs, text files directly from browser
- **Rebuild Index** — One-click re-processing after adding new content

### Student Access Codes
When you add a student, the system generates a 6-character code (e.g. `XKR482`). Share this code with the student — they use it to log in. Each student has a question quota that you control.

---

## 👩‍🎓 Student Experience

1. Student visits the app URL
2. Enters their 6-character access code
3. Asks questions in a chat interface
4. Gets answers sourced **only** from the teacher's materials, with lesson references
5. Gets a 2-3 question quiz after each answer to confirm understanding
6. Sidebar shows remaining question count with color-coded warnings
7. When quota is exhausted, input is disabled — student contacts teacher for refresh

---

## 💰 Cost Breakdown

| Item | Cost |
|------|------|
| Railway hosting | ~$5/month |
| Claude API (30 students × 5 questions) | ~$9/month |
| ChromaDB, LlamaIndex, Streamlit, Embeddings | Free |
| **Total** | **~$14/month** |

### Pricing Suggestion for Students
At ₹99–199 / £3–7 per 5 questions, you're profitable with just 2-3 paying students.

---

## 🔄 Updating Content

1. Go to Teacher Admin → **Upload Content** tab
2. Upload new files (or delete outdated ones)
3. Go to **Rebuild Index** tab → Click "Rebuild knowledge base"
4. Done — new content is immediately searchable by students

---

## 🛠️ Tech Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| AI / LLM | Claude (via Anthropic API) | Pay per use (~$0.01/question) |
| RAG Framework | LlamaIndex | Free (open source) |
| Vector Database | ChromaDB | Free (local) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 | Free (local) |
| Frontend | Streamlit | Free (open source) |
| Hosting | Railway | ~$5/month |

---

## ❓ Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: llama_index` | Run `pip install -r requirements.txt` with venv activated |
| `ModuleNotFoundError: docx2txt` | Run `pip install docx2txt` |
| `Unknown model` error | Run `pip install --upgrade llama-index-llms-anthropic anthropic` |
| `404 model not found` | Change model in `query_engine.py` to `claude-3-5-sonnet-latest` |
| App crashes on Railway | Check logs in Railway dashboard → Deployments tab |
| "Knowledge base not found" | Go to Admin → Rebuild Index |
| Students can't log in | Check Admin → Manage Students for their codes |
| Wrong or generic answers | Upload more specific content, rebuild index |
| Admin password forgotten | Update `ADMIN_PASSWORD` in Railway Variables tab |
| `chroma_db` folder missing | Run `python ingest.py` — it creates the folder automatically |

---

## 📋 Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | — | Your Claude API key |
| `ADMIN_PASSWORD` | No | `teacher123` | Password for Teacher Admin panel |
