import pandas as pd
from difflib import get_close_matches
from langchain.tools import tool

# ------------------ DATABASE MAPPING ------------------
DATABASES = {
    "eon": "data/eon.xlsx",
    "retail": "data/retail.xlsx",
    "telecom": "data/telecom.xlsx"
}

# ------------------ TOOL 1: list_databases ------------------
@tool
def list_databases() -> list:
    """Returns the list of available databases."""
    return list(DATABASES.keys())

# ------------------ TOOL 2: validate_database ------------------
@tool
def validate_database(db_name: str) -> dict:
    """Validates the database name."""
    db_name = db_name.lower().strip()
    if db_name in DATABASES:
        return {"status": "valid", "db_name": db_name}
    
    matches = get_close_matches(db_name, DATABASES.keys(), n=1, cutoff=0.6)
    if matches:
        return {"status": "suggest", "suggestion": matches[0]}
    
    return {"status": "invalid", "suggestion": None}

# ------------------ TOOL 3: load_product_list ------------------
@tool
def load_product_list(db_name: str) -> list:
    """Loads all unique product names from the Excel file."""
    if db_name not in DATABASES:
        raise ValueError(f"Invalid DB: {db_name}")
    
    df = pd.read_excel(DATABASES[db_name])
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return sorted(df["product"].dropna().astype(str).str.strip().unique())

# ------------------ TOOL 4: validate_product_name ------------------
@tool
def validate_product_name(product_name: str, product_list: list) -> dict:
    """Validates or suggests closest product name match."""
    product_name = product_name.strip().lower()
    clean_list = [p.lower() for p in product_list]

    if product_name in clean_list:
        return {"status": "valid", "product_name": product_list[clean_list.index(product_name)]}

    matches = get_close_matches(product_name, clean_list, n=1, cutoff=0.6)
    if matches:
        return {"status": "suggest", "suggestion": product_list[clean_list.index(matches[0])]}

    return {"status": "invalid", "suggestion": None}

# ------------------ TOOL 5: get_monthly_sales ------------------
@tool
def get_monthly_sales(db_name: str, product_name: str) -> dict:
    """Aggregates daily sales into monthly totals for the given product."""
    if db_name not in DATABASES:
        raise ValueError(f"Invalid DB: {db_name}")
    
    df = pd.read_excel(DATABASES[db_name])
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    if not all(col in df.columns for col in ["product", "date", "total_orders"]):
        raise ValueError("Missing required columns.")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    df_filtered = df[df["product"].str.lower().str.strip() == product_name.lower().strip()]
    if df_filtered.empty:
        return {}

    df_filtered["month"] = df_filtered["date"].dt.strftime("%B %Y")
    monthly_sales = df_filtered.groupby("month")["total_orders"].sum().to_dict()
    return dict(sorted(monthly_sales.items(), key=lambda x: pd.to_datetime(x[0])))

# ------------------ TOOL 6: summarize_trend ------------------
@tool
def summarize_trend(product_name: str, monthly_sales: dict) -> str:
    """Generates a trend analysis prompt based on monthly sales."""
    sales_lines = "\n".join([f"{month}: {value}" for month, value in monthly_sales.items()])
    prompt = f"""
The following is the monthly sales data for the product '{product_name}':

{sales_lines}

Based on this pattern, classify the product as one of the following:
- Growing
- Decaying
- Flat
- Obsolete
- Seasonal
- Volatile

Then explain your reasoning in 2–3 sentences.
""".strip()
    return prompt
