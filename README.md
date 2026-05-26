# IFM Tyre Advisor

An AI-powered chat interface for analysing CEAT's In-Fleet Management (IFM) tyre inspection dataset. Ask questions in plain English — the agent writes and executes pandas code against 845,000+ records and returns answers, tables, and charts.

---

## What it does

- Natural language queries over a 845,432-row tyre inspection dataset (87 columns)
- Agentic RAG: GPT-4.1 decides which tools to call, executes pandas code, and interprets results
- Streaming responses with a live "thinking" trace showing each tool call
- On-demand chart generation (bar, line, scatter) via matplotlib
- CEAT-branded UI built with Next.js 14, Tailwind CSS, and shadcn/ui

---

## Stack

| Layer | Technology |
|-------|-----------|
| LLM | OpenAI GPT-4.1 |
| Backend | FastAPI + Uvicorn |
| Data | Pandas on Parquet (data/ifm.parquet) |
| Charts | Matplotlib |
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Streaming | Server-Sent Events (SSE) |
| Backend hosting | Railway |
| Frontend hosting | Vercel |

---

## Agent tools

| Tool | When used |
|------|-----------|
| `run_pandas` | Execute analysis code against the dataset |
| `get_schema` | Inspect column names, dtypes, and sample values |
| `get_value_counts` | Check top values in a categorical column |
| `get_column_stats` | Descriptive statistics for a numeric column |
| `get_office_names` | Resolve an Indian state to matching OFFICE NAME values |
| `create_chart` | Generate a bar / line / scatter chart (only when user asks) |

---

## Domain knowledge (key columns)

| Column | Meaning |
|--------|---------|
| `MANUFACTURER NAME` | Tyre company — e.g. `Ceat Ltd.`, `JK Tyre & Industries Ltd.` |
| `BRAND NAME` | Tyre platform / pattern — e.g. `WINSUPER X3-D`, `JETSTEEL JDE XF` |
| `TYRE SIZE` | Size in data format — e.g. `11.00R20`, `10.00-20` |
| `CONSTRUCTION` | `Radial` or `Crossply` |
| `AXLE NAME` | `Front Axle`, `Rear-Drive Axle`, `Rear-Dummy Axle`, etc. |
| `PROJECTED MILEAGE CPKM` | Cost per km (lower = better) |
| `PROJECT MILEAGE (ALL LIFE)` | Projected total km (higher = better) |
| `IS QUALIFIED` | `True` = met projected mileage target |
| `LIFE` | `0` = new tyre, `1` = 1st retread, `2` = 2nd retread, etc. |
| `WORNOUT BRACKET` | Wear bucket: `20-40%`, `40-60%`, `60-80%`, `80-100%` |
| `Zone Description` | Full zone name — e.g. `East Zone`, `West Zone-2` |
| `Region Description` | Full RO name — e.g. `Kolkata`, `Asansol` |

**Default filters applied to every query:** `IS QUALIFIED == True` AND `LIFE == 0`

---

## Local development

### Prerequisites
- Python 3.11+
- Node.js 18+
- An OpenAI API key

### Backend

```bash
# Clone the repo
git clone git@github.com:anupriyomandal/ifm_agentic_rag.git
cd ifm_agentic_rag

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "OPENAI_API_KEY=sk-..." > .env

# Start the API server
uvicorn api:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8001" > .env.local

# Start the dev server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Deployment

### Backend → Railway

1. New Project → Deploy from GitHub repo → `ifm_agentic_rag`
2. Variables → add `OPENAI_API_KEY`
3. Railway detects the `Dockerfile` and deploys automatically
4. Copy the generated domain (e.g. `https://ifm.up.railway.app`)

### Frontend → Vercel

1. New Project → Import `ifm_agentic_rag` → set Root Directory to `frontend`
2. Environment Variables → add `NEXT_PUBLIC_API_URL` = your Railway URL
3. Deploy

---

## Example queries

```
What is the average CPKM by zone?
Compare CPKM of CEAT vs MRF vs Apollo for 11.00R20 tyres
Which tyre gives the highest projected mileage in West Bengal?
What percentage of tyres are in the 80-100% wornout bracket?
Show me a bar chart of average CPKM by manufacturer
What is the average CPKM of crossply RIB tyres in East Zone?
```

---

## Project structure

```
ifm_agentic_rag/
├── api.py              # FastAPI app — SSE streaming, tool dispatch, system prompt
├── tools.py            # Tool implementations (run_pandas, create_chart, etc.)
├── agent.py            # CLI agent for local testing
├── requirements.txt
├── Dockerfile
├── data/
│   └── ifm.parquet     # 845,432 × 87 tyre inspection dataset
└── frontend/
    ├── app/
    │   ├── page.tsx    # Main chat page
    │   └── globals.css
    ├── components/
    │   ├── ChatArea.tsx
    │   ├── ChatInput.tsx
    │   ├── MessageBubble.tsx
    │   ├── ToolSteps.tsx
    │   └── SuggestedQueries.tsx
    └── lib/
        ├── api.ts      # SSE streaming client
        └── types.ts
```

---

*Made by Anupriyo Mandal*
