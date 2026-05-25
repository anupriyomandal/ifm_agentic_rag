import io
import traceback
from contextlib import redirect_stdout

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
