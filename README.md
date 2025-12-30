# ⚡️ Omni-Core Engine
> **The Autonomous Content Repurposing Super-Agent**

Turn a single video into a month's worth of high-performance content across LinkedIn, Twitter, Blogs, and Newsletters—generated in seconds, not hours.

![Dashboard Preview](frontend/public/window.svg)

## 🚀 Key Capabilities

### 1. **Turbo Mode Architecture** 🏎️💨
Unlike traditional sequential agents, Omni-Core uses a **Parallel Swarm Engine**:
- **Foreground Stream**: Watch the LinkedIn post being drafted live (Real-time token streaming).
- **Background Swarm**: Twitter threads, Blog posts, Newsletters, and Visuals generate *simultaneously* in the background.
- **Result**: Reduces 90s+ generation times to **~15-20s**.

### 2. **Multi-Modal Research** 🧠
- **Deep Research**: Agents scan the web (Tavily) to fact-check claims and find relevant case studies.
- **Parallel Verification**: Verifies multiple claims concurrently using `asyncio` swarms.

### 3. **Visual Intelligence ("The Eye")** 👁️
- **LinkedIn Carousels**: Auto-generates branded, high-conversion PDF carousels using **Playwright** (Cyberpunk/Minimalist styles).
- **Viral Thumbnails**: Uses **DALL-E 3** to dream up high-CTR YouTube thumbnails with face composition logic.

### 4. **Neural Audio Hub ("The Voice")** 🎙️
- **Voice Cloning**: Clones the speaker's voice using **ElevenLabs Flash v2.5**.
- **Auto-Dubbing**: Translates and re-voices content into Spanish/Hindi (via DeepL + ElevenLabs).

### 5. **Ultra-Fast Transcription** ⚡️
- Powered by **Groq Whisper**, transcribing hours of audio in seconds.
- Smart caching and YouTube caption fetching (Zero-Download strategy).

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11, FastAPI, Celery, LangChain
- **Frontend**: Next.js 14, TypeScript, TailwindCSS, Framer Motion
- **AI Models**: 
  - GPT-4o (Reasoning & Writing)
  - Groq Whisper-v3 (Transcription)
  - DALL-E 3 (Image Generation)
  - ElevenLabs (Voice Synthesis)
- **Infrastructure**: Redis (Task Queue), Airtable (CMS)

---

## 📦 Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- FFmpeg (for audio processing)

### 1. Backend Setup
```bash
# Clone and enter
git clone https://github.com/vishal124942/omi_core.git
cd omi_core

# Install dependencies
pip install -r requirements.txt

# Create .env file with your keys
# (OPENAI_API_KEY, GROQ_API_KEY, ELEVENLABS_API_KEY, TAVILY_API_KEY, etc.)

# Start the server
python -m uvicorn app.main:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Usage
1. Open `http://localhost:3000`.
2. Paste a YouTube URL.
3. Select desired platforms (LinkedIn, Twitter, Blog, etc.).
4. Click **ACTIVATE**.
5. Watch the Neural Link establish and the swarm go to work.

---

## 🔄 Reset & Maintenance
- **New Project**: The UI features a "New" button that performs a **Deep Clean**—wiping local state and physically deleting temporary audio/visual files from the disk to ensure zero contamination between runs.
- **Git Hygiene**: The repo is configured to ignore heavy media files (`data/`) while preserving structure.

---

## 🤝 Contributing
Built for speed and scale. PRs welcome for new platform adapters or model optimizations.
