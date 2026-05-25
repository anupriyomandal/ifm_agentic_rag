import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from tools import get_column_stats, get_office_names, get_schema, get_value_counts, run_pandas

load_dotenv()
client = OpenAI()  # reads OPENAI_API_KEY from .env

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
| RECOMMENDATION  | Action: "None", "Removal", "Monitoring", etc. |
| IS QUALIFIED    | TRUE = tyre met projected mileage target. |
| CONSTRUCTION    | "Radial" or "Crossply". |
| LIFE            | 0 = new tyre, >0 = retreaded life number. |
| Zone Description | Full zone name e.g. "West Zone-2". Column added from ZO CODE. |
| Region Description | Full region name e.g. "Kolkata". Column added from RO CODE. |

## Tyre size format
Sizes in the data use the full decimal format. Always verify with get_value_counts() if a filter returns 0 rows.
- User says "11R20"  → data stores "11.00R20"
- User says "10R20"  → data stores "10.00R20"
- User says "9R20"   → data stores "9.00R20"
- User says "12R20"  → data stores "12.00R20"

## Geography filtering — CRITICAL RULES

### Zone / RO queries (use Region Description or Zone Description directly)
When a query mentions a Zone or RO by name, filter on the description columns — do NOT use OFFICE NAME.

| User says | pandas filter |
|-----------|--------------|
| "Asansol RO" | `df[df['Region Description'] == 'Asansol']` |
| "Kolkata RO" | `df[df['Region Description'] == 'Kolkata']` |
| "East Zone" | `df[df['Zone Description'] == 'East Zone']` |
| "West Zone-2" | `df[df['Zone Description'] == 'West Zone-2']` |

Valid Region Description values (all 41 ROs):
Ahmedabad, Asansol, Bangalore, Bhopal, Bhubhneshwar, Chandigarh, Chennai, Ernakulam,
Ghaziabad, Gurgaon, Guwahati, Gurugram, Hubli, Hyderabad, Indore, Jabalpur, Jaipur,
Jalandhar, Jodhpur, Kanpur, Kolhapur, Kolkata, Lucknow, Madurai, Meerut, Mumbai,
Nagpur, Nashik, Navi Mumbai, New Delhi, Patna, Pune, Raipur, Rajkot, Ranchi,
Salem, Surat, Udaipur, Varanasi, Vijayawada.

Valid Zone Description values:
East Zone, North Zone 1, North Zone 2, South Zone 1, South Zone 2, West Zone 1, West Zone-2.

### State queries (use get_office_names)
When a query mentions an Indian state (e.g. "West Bengal", "Maharashtra"), call get_office_names(state)
and filter with: df['OFFICE NAME'].isin([...])

### Decision rule
- Query says "RO" or names a known city-RO (Asansol, Kolkata, Pune…) → use `Region Description`
- Query says "Zone" or names a zone → use `Zone Description`
- Query says a state name → call get_office_names(state)

## Default filters — apply to EVERY query unless the user explicitly overrides

ALWAYS start every pandas query with both of these filters:

```python
df = df[(df['IS QUALIFIED'] == True) & (df['LIFE'] == 0)]
```

### IS QUALIFIED
- Default: `IS QUALIFIED == True` only (qualified tyres that met mileage targets)
- Override: only if user explicitly says "include all tyres" or "qualified and unqualified"

### LIFE (tyre life stage)
- `LIFE == 0` → Initial / new tyre life (DEFAULT)
- `LIFE == 1` → 1st retread
- `LIFE == 2` → 2nd retread
- `LIFE == 3` → 3rd retread (and so on)

Override mapping — apply when user says:
| User says | Filter |
|-----------|--------|
| "1st retread" or "first retread" | `LIFE == 1` |
| "2nd retread" or "second retread" | `LIFE == 2` |
| "all lives" or "all retreads" | remove LIFE filter |
| (nothing specified) | `LIFE == 0` (default) |

## Workflow
1. Apply default filters: `IS QUALIFIED == True` and `LIFE == 0` (unless overridden).
2. RO/Zone query? → filter on `Region Description` / `Zone Description` directly.
3. State query? → call get_office_names(state) first.
4. Unsure of column names? → call get_schema().
5. Write pandas code; assign final answer to variable named 'result'.
6. Tyre size filter returns 0 rows? → call get_value_counts('TYRE SIZE') and retry with correct format.
7. run_pandas returns an error? → read traceback carefully and retry with fixed code.
8. Interpret numeric results in business terms before answering.

## Zero-result handling — CRITICAL
If a query returns 0 rows or NaN after applying the correct filters, STOP immediately and report it clearly.
Do NOT retry with different filters, do NOT relax the LIFE or IS QUALIFIED filters, do NOT loop.

Report format when 0 results:
- State what was searched (e.g. "LIFE=1, IS QUALIFIED=True, Kolkata RO, 11.00R20, CEAT")
- Confirm 0 records found
- Optionally mention where that segment does exist (only if you already know from prior tool calls)
- Do NOT make additional tool calls to "find" the data elsewhere unless the user asks
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_schema",
            "description": (
                "Get all 85 column names, their data types, and sample values. "
                "Call this first before writing any pandas code."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_pandas",
            "description": (
                "Execute Python/pandas code against the IFM dataframe. "
                "'df' (the full DataFrame) and 'pd' (pandas) are pre-loaded. "
                "Assign the final output to a variable named 'result'. "
                "Use print() only for intermediate debugging."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Valid Python/pandas code. Must assign output to 'result'.",
                    }
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_value_counts",
            "description": (
                "Get the top-20 most frequent values for a categorical column. "
                "Useful for ZO, RO, BRAND NAME, WEAR, RECOMMENDATION, WORNOUT BRACKET, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "column": {"type": "string", "description": "Exact column name from the dataset."}
                },
                "required": ["column"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_office_names",
            "description": (
                "Return all OFFICE NAME values present in the IFM dataset for a given Indian state. "
                "MUST be called before filtering by any state or geography — never guess office names. "
                "Returns the exact list to pass to df['OFFICE NAME'].isin([...])."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "description": "Indian state name e.g. 'West Bengal', 'Maharashtra', 'Tamil Nadu'.",
                    }
                },
                "required": ["state"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_column_stats",
            "description": (
                "Get descriptive statistics (count, mean, std, min, 25/50/75%, max) "
                "for a numeric column such as CURRENT NSD, KM RUN PER MM, NET TYRE COST, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "column": {"type": "string", "description": "Exact column name from the dataset."}
                },
                "required": ["column"],
            },
        },
    },
]


def _dispatch(name: str, args: dict) -> str:
    if name == "get_schema":
        return get_schema()
    if name == "run_pandas":
        return run_pandas(args["code"])
    if name == "get_value_counts":
        return get_value_counts(args["column"])
    if name == "get_column_stats":
        return get_column_stats(args["column"])
    if name == "get_office_names":
        return get_office_names(args["state"])
    return f"Unknown tool: {name}"


def run_agent(question: str, history: list) -> str:
    history.append({"role": "user", "content": question})

    while True:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
            tools=TOOLS,
            tool_choice="auto",
        )

        msg = response.choices[0].message
        history.append(msg)

        if not msg.tool_calls:
            return msg.content

        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            print(f"  [tool] {tc.function.name}({', '.join(f'{k}={repr(v)[:60]}' for k, v in args.items())})")
            result = _dispatch(tc.function.name, args)
            history.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result[:10_000],
            })


def main() -> None:
    print("=" * 60)
    print("  IFM Tyre Advisor — Agentic RAG")
    print("  Commands: 'exit' | 'reset' (clear history)")
    print("=" * 60)

    history: list = []
    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not question:
            continue
        if question.lower() == "exit":
            break
        if question.lower() == "reset":
            history = []
            print("  [history cleared]")
            continue

        print()
        answer = run_agent(question, history)
        print(f"Agent: {answer}")


if __name__ == "__main__":
    main()
