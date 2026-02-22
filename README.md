markdown
# 🛠️ Quore AGS Data Validator & Viewer
A premium, open-source web application for geotechnical engineers to **validate**, **view**, and **edit** AGS4 data files instantly.
![Quore AGS Validator](https://img.shields.io/badge/Status-Deploying_on_Vercel-blue?style=for-the-badge&logo=vercel)
![Tech Stack](https://img.shields.io/badge/Powered_by-Next.js_15_%2B_FastAPI-black?style=for-the-badge&logo=next.js)
---
## ✨ Key Features
- **🚀 Instant Validation**: Drop an `.ags` file to check for formatting errors and structural inconsistencies using the industry-standard `python-ags4` engine.
- **📊 Interactive Data Grid**: View and edit your AGS tables directly in the browser with a sleek, high-performance spreadsheet interface.
- **🪨 Stratigraphic Visualization**: Automatically generate and view stratigraphic columns (borehole logs) from your data.
- **🔃 Format Conversion**: Seamlessly convert `.ags` files to Excel (`.xlsx`) and back again.
- **✨ Premium UI**: Dark-mode optimized interface with glassmorphic elements and smooth micro-animations.
---
## 🛠️ Tech Stack
### Frontend
- **Framework**: Next.js 15 (App Router)
- **Styling**: Tailwind CSS (Lucide Icons, Framer Motion)
- **State Management**: React Hooks & Context API
- **Deployment**: Vercel (Edge-optimized)
### Backend (Python Engine)
- **Framework**: FastAPI
- **Data Processing**: Pandas & NumPy
- **AGS Logic**: `python-ags4`
- **Infrastructure**: Vercel Serverless Functions
---
## 🚀 Getting Started
### Prerequisites
- Node.js 18+
- Python 3.9+
### Installation
1. **Clone the Repo**
   ```bash
   git clone https://github.com/George-595/ags_oss_validateviewedit.git
   cd ags_oss_validateviewedit/frontend
Frontend Setup

bash
npm install
npm run dev
Backend Setup (For local development)

bash
cd api
pip install -r requirements.txt
uvicorn index:app --port 8000 --reload
Environment Variables Create a .env.local in the frontend directory:

env
NEXT_PUBLIC_API_URL=http://localhost:8000
📂 Project Structure
text
├── frontend/
│   ├── api/          # Python FastAPI Backend (Serverless)
│   ├── src/
│   │   ├── app/      # Next.js Pages & Routes
│   │   ├── components/# React UI Components
│   │   └── lib/      # Utility functions
│   └── public/       # Static assets
└── backend/          # Legacy logic (deprecated)
