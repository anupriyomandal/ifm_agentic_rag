import json
import os
from typing import Generator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

from tools import create_chart, get_column_stats, get_office_names, get_schema, get_value_counts, run_pandas

app = FastAPI(title="IFM Tyre Advisor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI()

SYSTEM_PROMPT = """You are an expert data analyst for CEAT IFM (In-Fleet Management) tyre inspection data.
The dataset has 845,432 inspection records and 87 columns stored in data/ifm.parquet.

## Domain knowledge

| Term | Meaning |
|------|---------|
| NSD  | Tread depth in mm. Lower = more worn. Safe threshold ~2–4 mm. |
| CPKM | Cost per km. Column: `PROJECTED MILEAGE CPKM`. Lower is better. |
| Best mileage / projected mileage | Column: `PROJECT MILEAGE (ALL LIFE)` (total km). Higher is better. |
| Wear rate | Column: `KM RUN PER MM` (km per mm of tread). Higher is better. |
| WORNOUT BRACKET | Wear bucket: "20-40%", "40-60%", "60-80%", "80-100%". |
| RECOMMENDATION  | Action: "None", "Monitoring", "Send to Retread", "Send to Scrap", etc. |
| IS QUALIFIED    | TRUE = tyre met projected mileage target. |
| CONSTRUCTION    | "Radial" or "Crossply". |
| LIFE            | 0 = new tyre, >0 = retreaded life number. |
| Zone Description | Full zone name e.g. "West Zone-2". Column added from ZO CODE. |
| Region Description | Full region name e.g. "Kolkata". Column added from RO CODE. |

## Tyre size format
Sizes in the data use the full decimal format. Always verify with get_value_counts('TYRE SIZE') if a filter returns 0 rows.

Radial sizes (R):
- User says "11R20"   → data stores "11.00R20"
- User says "10R20"   → data stores "10.00R20"
- User says "9R20"    → data stores "9.00R20"
- User says "12R20"   → data stores "12.00R20"

Crossply / bias-ply sizes (hyphen, no R):
- User says "1000-20" → data stores "10.00-20"
- User says "900-20"  → data stores "9.00-20"
- User says "825-20"  → data stores "8.25-20"
- User says "1100-20" → data stores "11.00-20"
- General rule: insert a dot after the first two digits, e.g. "1000" → "10.00"

## Tyre pattern / type filtering

For crossply (bias-ply) tyres, RIB = front axle and LUG = rear axle. Use the `AXLE NAME` column:

| User says | Filter |
|-----------|--------|
| Crossply RIB | `(df['CONSTRUCTION'] == 'Crossply') & (df['AXLE NAME'] == 'Front Axle')` |
| Crossply LUG | `(df['CONSTRUCTION'] == 'Crossply') & (df['AXLE NAME'].str.contains('Rear', na=False))` |
| Radial | `df['CONSTRUCTION'] == 'Radial'` |
| Crossply | `df['CONSTRUCTION'] == 'Crossply'` |

Valid `AXLE NAME` values: `'Front Axle'`, `'Rear-Drive Axle'`, `'Rear-Dummy Axle'`, `'Rear-Lift Axle'`, `'Trolley Axle'`, `'Drive Axle'`

Do NOT use BRAND NAME string matching for RIB/LUG — many crossply brands do not carry those words in their name.

## Geography filtering — CRITICAL RULES

### Zone / RO queries (use Region Description or Zone Description directly)
| User says | pandas filter |
|-----------|--------------|
| "Asansol RO" | `df[df['Region Description'] == 'Asansol']` |
| "Kolkata RO" | `df[df['Region Description'] == 'Kolkata']` |
| "East Zone" | `df[df['Zone Description'] == 'East Zone']` |

Valid Region Description values:
Ahmedabad, Asansol, Bangalore, Bhopal, Bhubhneshwar, Chandigarh, Chennai, Ernakulam,
Ghaziabad, Gurgaon, Gurugram, Hubli, Hyderabad, Indore, Jabalpur, Jaipur,
Jalandhar, Jodhpur, Kanpur, Kolhapur, Kolkata, Lucknow, Madurai, Meerut, Mumbai,
Nagpur, Nashik, Navi Mumbai, New Delhi, Patna, Pune, Raipur, Rajkot, Ranchi,
Salem, Surat, Udaipur, Varanasi, Vijayawada.

Valid Zone Description values:
East Zone, North Zone 1, North Zone 2, South Zone 1, South Zone 2, West Zone 1, West Zone-2.

### State queries → call get_office_names(state), then filter with df['OFFICE NAME'].isin([...])

### Decision rule
- "RO" or city name → use `Region Description`
- "Zone" → use `Zone Description`
- State name → call get_office_names(state)

## Default filters — apply to EVERY query unless explicitly overridden
ALWAYS start with:
```python
df = df[(df['IS QUALIFIED'] == True) & (df['LIFE'] == 0)]
```

### LIFE override mapping
| User says | Filter |
|-----------|--------|
| "1st retread" | `LIFE == 1` |
| "2nd retread" | `LIFE == 2` |
| "all lives" | remove LIFE filter |
| (nothing) | `LIFE == 0` (default) |

## Column glossary (key columns)

| Column | Meaning |
|--------|---------|
| `MANUFACTURER NAME` | Tyre company / OEM. Filter this when user mentions a brand like "JK", "CEAT", "Apollo". |
| `BRAND NAME` | Tyre platform / pattern name (e.g., "JETSTEEL JDE XF", "WINSUPER X3-D"). |

## Manufacturer → MANUFACTURER NAME exact values

When user says a company name, filter `MANUFACTURER NAME` with the exact string below:

| User says | Exact value in data |
|-----------|---------------------|
| JK / JK Tyre | `'JK Tyre & Industries Ltd.'` |
| CEAT | `'Ceat Ltd.'` |
| Apollo | `'Apollo Tyres Ltd.'` |
| MRF | `'MRF Ltd.'` |
| Bridgestone | `'Bridgestone India Private Ltd.'` |
| Continental | `'Continental Tyres India Ltd.'` |
| Michelin | `'Michelin India Pvt. Ltd.'` |
| Birla | `'Birla Tyres Ltd'` |
| BKT | `'BKT Tyres'` |

Example: `df[df['MANUFACTURER NAME'] == 'JK Tyre & Industries Ltd.']`

## Zero-result handling
If a query returns 0 rows after correct filters, STOP immediately.
State what was searched, confirm 0 records. Do NOT retry with relaxed filters.

## Workflow
1. Apply default filters: IS QUALIFIED == True and LIFE == 0 (unless overridden).
2. RO/Zone query? → filter on Region Description / Zone Description directly.
3. State query? → call get_office_names(state) first.
4. Unsure of column names? → call get_schema().
5. Assign final answer to variable named 'result'.
6. Tyre size returns 0 rows? → call get_value_counts('TYRE SIZE') and retry.
7. Interpret numeric results in business terms before answering.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_schema",
            "description": "Get all column names, dtypes, and sample values. Call first when unsure of column names.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_pandas",
            "description": "Execute Python/pandas code. 'df' and 'pd' pre-loaded. Assign output to 'result'.",
            "parameters": {
                "type": "object",
                "properties": {"code": {"type": "string"}},
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_value_counts",
            "description": "Top-20 value counts for a categorical column.",
            "parameters": {
                "type": "object",
                "properties": {"column": {"type": "string"}},
                "required": ["column"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_column_stats",
            "description": "Descriptive statistics for a numeric column.",
            "parameters": {
                "type": "object",
                "properties": {"column": {"type": "string"}},
                "required": ["column"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_chart",
            "description": "Generate a bar, line, or scatter chart from data. ONLY call this when the user explicitly asks for a chart or graph. Write pandas code that assigns a Series or dict {label: value} to 'result', then this tool renders it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chart_type": {"type": "string", "enum": ["bar", "line", "scatter"]},
                    "code": {"type": "string", "description": "Pandas code (df + pd pre-loaded). Apply default filters. Assign result to a Series or dict."},
                    "title": {"type": "string"},
                    "x_label": {"type": "string"},
                    "y_label": {"type": "string"},
                },
                "required": ["chart_type", "code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_office_names",
            "description": "Return OFFICE NAME values for a given Indian state. Call before any state-level geography filter.",
            "parameters": {
                "type": "object",
                "properties": {"state": {"type": "string"}},
                "required": ["state"],
            },
        },
    },
]


def dispatch(name: str, args: dict) -> str:
    if name == "get_schema":        return get_schema()
    if name == "run_pandas":        return run_pandas(args["code"])
    if name == "get_value_counts":  return get_value_counts(args["column"])
    if name == "get_column_stats":  return get_column_stats(args["column"])
    if name == "get_office_names":  return get_office_names(args["state"])
    if name == "create_chart":      return create_chart(
        args["chart_type"], args["code"],
        args.get("title", ""), args.get("x_label", ""), args.get("y_label", ""),
    )
    return f"Unknown tool: {name}"


def agent_stream(question: str, history: list) -> Generator[str, None, None]:
    history.append({"role": "user", "content": question})

    try:
        while True:
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
                tools=TOOLS,
                tool_choice="auto",
            )
            msg = response.choices[0].message
            msg_dict: dict = {"role": "assistant", "content": msg.content}
            if msg.tool_calls:
                msg_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ]
            history.append(msg_dict)

            if not msg.tool_calls:
                yield f"data: {json.dumps({'type': 'content', 'text': msg.content})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                break

            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                yield f"data: {json.dumps({'type': 'tool_call', 'name': tc.function.name, 'args': args})}\n\n"
                result = dispatch(tc.function.name, args)
                if result.startswith("data:image/"):
                    yield f"data: {json.dumps({'type': 'chart', 'image': result, 'title': args.get('title', '')})}\n\n"
                    yield f"data: {json.dumps({'type': 'tool_result', 'name': tc.function.name, 'preview': 'Chart generated.'})}\n\n"
                    history.append({"role": "tool", "tool_call_id": tc.id, "content": "Chart generated and displayed to the user."})
                else:
                    yield f"data: {json.dumps({'type': 'tool_result', 'name': tc.function.name, 'preview': result[:400]})}\n\n"
                    history.append({"role": "tool", "tool_call_id": tc.id, "content": result[:10_000]})

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


class HistoryMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[HistoryMessage] = []


@app.post("/api/chat")
async def chat(req: ChatRequest):
    history = [{"role": h.role, "content": h.content} for h in req.history]
    return StreamingResponse(
        agent_stream(req.message, history),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/health")
async def health():
    return {"status": "ok", "model": "gpt-4.1"}
