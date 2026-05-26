import base64
import io
import traceback
from contextlib import redirect_stdout

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_PATH = "data/ifm.parquet"
_df: pd.DataFrame | None = None

# Keywords per state used for matching against OFFICE NAME values in the data.
# Each keyword is matched case-insensitively as a substring of the office name.
_STATE_KEYWORDS: dict[str, list[str]] = {
    "west bengal":      ["kolkata", "kharagpur", "haldia", "singur", "panagarh", "rampurhat", "behrampur", "sherpur"],
    "odisha":           ["bhubaneswar", "bhubneshwar", "angul", "banarpal", "belpahad", "chandikhol",
                         "cuttack", "duburi", "garjanbahal", "hemgir", "jajpur", "jharsuguda", "koida",
                         "kalinganagar", "kendrapada", "lathikata", "rourkela", "sambalpur", "sinapali",
                         "sundargarh", "sundergarh", "talcher", "chadheidhara", "bimlagarh"],
    "jharkhand":        ["jamshedpur", "bokaro", "dhanbad", "sindri", "pakur", "mahagama", "gumla",
                         "sisai", "ranchi"],
    "karnataka":        ["bangalore", "bengaluru", "mysore", "mysuru", "tumkur", "chitradurga", "hiriyur",
                         "hubli", "belgaum", "bellary", "gulbarga", "hospet", "toranagallu", "torangallu",
                         "torangalu", "mangalore", "jigani", "attibele", "anekal", "nelmangala",
                         "srirangapatna", "wadi jn", "yadwad", "lokapur", "kurekuppa", "kudtuni",
                         "kushalnagar", "uttanahalli", "yeshwanthpur", "dharwad"],
    "tamil nadu":       ["chennai", "madurai", "salem", "coimbatore", "tirupur", "trippur", "tripur",
                         "trichy", "namakkal", "erode", "tirunelveli", "tuticorin", "dindigul", "karur",
                         "vellore", "kanchipuram", "pondicherry", "puducherry", "villupuram", "thiruvallur",
                         "sankari", "thuraiyur", "pollachi", "mettur", "sankagiri", "ariyalur", "ranipet",
                         "arakonam", "chidambaram", "cuddalore", "minjur", "poonamalle", "perambadhur",
                         "madavaram", "navalur", "ayyakkatur", "kayatharu", "sankakiri"],
    "maharashtra":      ["mumbai", "pune", "nagpur", "nashik", "nasik", "aurangabad", "navi mumbai",
                         "bhiwandi", "kolhapur", "solapur", "chandrapur", "wardha", "dhule", "jalna",
                         "nanded", "wani", "akola", "thane", "hotgi", "nira satara", "chittapur", "umerga"],
    "gujarat":          ["ahmedabad", "ahmadabad", "surat", "rajkot", "vadodara", "baroda", "bhuj",
                         "gandhidham", "samkhiyali", "samakhaily", "galpadar", "porbandar", "vapi",
                         "navsari", "navasari", "chikhali", "dumad", "hazira", "sanand", "jamnagar",
                         "bhavnagar", "halol"],
    "rajasthan":        ["jaipur", "jodhpur", "udaipur", "kota", "alwar", "bhilwara", "kishangarh",
                         "beawar", "nasirabad", "shahpura", "kotputli", "rupangarh", "chanderiya",
                         "chittorgarh", "rajsamand", "nimbahera", "nimbhahera", "shambhupura",
                         "wanakbori", "manawar", "raila bhilwara", "ajmer"],
    "telangana":        ["hyderabad", "secunderabad", "rangareddy", "adilabad", "shamshabad",
                         "pedda amberpet", "kodad", "damarcherla", "damarchella"],
    "andhra pradesh":   ["vijayawada", "vijaywada", "visakhapatnam", "rajahmundry", "ananthapur",
                         "kurnool", "proddatur", "produtur", "dachepalle", "duddukuru", "erraguntla",
                         "gadivemula", "jaggaipeta", "macherla", "tadipathri", "kasimkota", "nawada",
                         "i.pangidi", "kadapa", "uba lannka"],
    "uttar pradesh":    ["kanpur", "lucknow", "agra", "varanasi", "gorakhpur", "prayagraj", "unnao",
                         "ghatampur", "fatehpur", "aligarh", "etawah", "faizabad", "palia kalan",
                         "partapgarh", "sitapur", "unchahar", "sultanpur", "muzaffarnagar", "annupur",
                         "narayanpur, mirzapur"],
    "madhya pradesh":   ["indore", "bhopal", "jabalpur", "gwalior", "rewa", "sagar", "satna",
                         "chhindwara", "balaghat", "narsingharh", "mangliya", "mundi", "selda"],
    "chhattisgarh":     ["raipur", "bilaspur", "raigarh", "korba", "rajnandgaon", "baloda bazar",
                         "chakarbhata", "kusmunda", "sargaon", "siltara", "tilda"],
    "punjab":           ["amritsar", "jalandhar", "bathinda", "bhatinda", "mansa", "firozepur", "malout"],
    "haryana":          ["gurgaon", "gurugram", "faridabad", "rohtak", "panipat", "ambala", "karnal",
                         "narnaul", "dharuhera", "rewari", "sonipat", "palwal", "bakoli", "jagadhari",
                         "yamuna nagar", "yamunanagar", "sarsawa", "tepla"],
    "delhi":            ["delhi", "new delhi"],
    "kerala":           ["ernakulam", "kochi", "thiruvananthapuram"],
    "uttarakhand":      ["rudrapur", "haridwar", "tapukhera"],
    "jammu kashmir":    ["jammu"],
    "himachal pradesh": ["anandpur sahib"],
    "goa":              ["panaji", "margao"],
    "meerut":           ["meerut"],  # kept separately — Meerut RO spans UP/Uttarakhand
}

_BLOCKED = [
    "import os", "import sys", "import subprocess", "import shutil",
    "open(", "__import__", "eval(", "exec(",
]


def _get_df() -> pd.DataFrame:
    global _df
    if _df is None:
        print("  [loading parquet...]")
        _df = pd.read_parquet(DATA_PATH)
    return _df


def run_pandas(code: str) -> str:
    """Execute pandas code against the IFM dataframe. 'df' and 'pd' are pre-loaded.
    Assign final answer to a variable named 'result'."""
    for blocked in _BLOCKED:
        if blocked in code:
            return f"Error: '{blocked}' is not permitted."

    df = _get_df()
    local_vars: dict = {"df": df, "pd": pd}

    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            exec(code, {"pd": pd, "__builtins__": __builtins__}, local_vars)  # noqa: S102
    except Exception:
        return f"Error:\n{traceback.format_exc()}"

    printed = buf.getvalue()

    if "result" in local_vars:
        val = local_vars["result"]
        if isinstance(val, pd.DataFrame):
            return val.to_string(max_rows=50)
        if isinstance(val, pd.Series):
            return val.to_string(max_rows=50)
        return str(val)

    return printed if printed else "Executed successfully (no output). Assign to 'result' to return a value."


def get_schema() -> str:
    """Return column names, dtypes, and sample values for every column."""
    df = _get_df()
    lines = [f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns\n"]
    lines.append(f"{'Column':<45} {'Dtype':<15} Sample values")
    lines.append("-" * 100)
    for col in df.columns:
        dtype = str(df[col].dtype)
        samples = df[col].dropna().head(3).tolist()
        lines.append(f"{col:<45} {dtype:<15} {str(samples)[:80]}")
    return "\n".join(lines)


def get_value_counts(column: str) -> str:
    """Return top-20 value counts for a categorical column."""
    df = _get_df()
    if column not in df.columns:
        return f"Column '{column}' not found. Call get_schema() to see valid names."
    return df[column].value_counts().head(20).to_string()


def get_column_stats(column: str) -> str:
    """Return descriptive statistics for a numeric column."""
    df = _get_df()
    if column not in df.columns:
        return f"Column '{column}' not found. Call get_schema() to see valid names."
    return df[column].describe().to_string()


def create_chart(chart_type: str, code: str, title: str = "", x_label: str = "", y_label: str = "") -> str:
    """Run pandas code to produce data, then render a chart. Returns a base64 PNG data-URI.
    chart_type: 'bar' | 'line' | 'scatter'
    code: pandas code with df + pd pre-loaded; assign result to a pandas Series (index=labels, values=numbers)
          or a plain dict {label: value}.
    """
    for blocked in _BLOCKED:
        if blocked in code:
            return f"Error: '{blocked}' is not permitted."

    df = _get_df()
    local_vars: dict = {"df": df.copy(), "pd": pd}
    try:
        exec(code, {"pd": pd, "__builtins__": __builtins__}, local_vars)  # noqa: S102
    except Exception:
        return f"Error in chart code:\n{traceback.format_exc()}"

    result = local_vars.get("result")
    if result is None:
        return "Error: code must assign data to 'result' (Series or dict)."

    # Normalise to labels / values lists
    if isinstance(result, dict):
        labels = [str(k) for k in result.keys()]
        values = [float(v) for v in result.values()]
    elif isinstance(result, pd.Series):
        labels = [str(i) for i in result.index.tolist()]
        values = [float(v) for v in result.values.tolist()]
    elif isinstance(result, pd.DataFrame) and result.shape[1] == 2:
        labels = result.iloc[:, 0].astype(str).tolist()
        values = [float(v) for v in result.iloc[:, 1].tolist()]
    else:
        return "Error: 'result' must be a dict, Series, or 2-column DataFrame."

    # Build chart
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#F8FAFC")
    ax.set_facecolor("#F8FAFC")
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color("#CBD5E1")
    ax.tick_params(colors="#64748B", labelsize=9)
    ax.grid(axis="y", color="#E2E8F0", linewidth=0.8, linestyle="--", zorder=0)

    BLUE, ORANGE = "#0055AA", "#F58220"

    if chart_type == "bar":
        bars = ax.bar(range(len(labels)), values, color=BLUE, width=0.6, zorder=3)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
        max_v = max(values) if values else 1
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, val + max_v * 0.015,
                    f"{val:.3f}", ha="center", va="bottom", fontsize=7.5, color="#334155")

    elif chart_type == "line":
        xs = range(len(labels))
        ax.plot(xs, values, color=BLUE, linewidth=2.5, marker="o",
                markersize=6, markerfacecolor=ORANGE, markeredgecolor="white",
                markeredgewidth=1.5, zorder=3)
        ax.fill_between(xs, values, alpha=0.08, color=BLUE)
        ax.set_xticks(xs)
        ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)

    elif chart_type in ("scatter", "xy"):
        if values and isinstance(values[0], (list, tuple)):
            x_vals = [v[0] for v in values]
            y_vals = [v[1] for v in values]
        else:
            x_vals = list(range(len(values)))
            y_vals = values
        ax.scatter(x_vals, y_vals, color=BLUE, alpha=0.7, s=60,
                   edgecolors="white", linewidths=0.8, zorder=3)
    else:
        plt.close(fig)
        return f"Error: unknown chart_type '{chart_type}'. Use 'bar', 'line', or 'scatter'."

    if title:
        ax.set_title(title, fontsize=12, fontweight="bold", color="#1E293B", pad=12)
    if x_label:
        ax.set_xlabel(x_label, fontsize=9, color="#64748B", labelpad=6)
    if y_label:
        ax.set_ylabel(y_label, fontsize=9, color="#64748B", labelpad=6)

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode()


def get_office_names(state: str) -> str:
    """Return all OFFICE NAME values present in the dataset for a given Indian state.
    Use this whenever a query mentions a state, city-group, or geography —
    never guess office names manually."""
    key = state.lower().strip()

    keywords = _STATE_KEYWORDS.get(key)
    if not keywords:
        for s, kw in _STATE_KEYWORDS.items():
            if key in s or s in key:
                keywords = kw
                key = s
                break

    if not keywords:
        available = sorted(_STATE_KEYWORDS.keys())
        return (
            f"State '{state}' not recognised.\n"
            f"Available states: {available}"
        )

    df = _get_df()
    all_offices: list[str] = df["OFFICE NAME"].dropna().unique().tolist()
    matched = sorted({o for o in all_offices if any(k in o.lower() for k in keywords)})

    if not matched:
        return f"No office names found in the dataset for '{state}'."

    return (
        f"OFFICE NAME values in dataset for '{key}':\n"
        + "\n".join(matched)
        + f"\n\nUse: df['OFFICE NAME'].isin({matched}) to filter."
    )
