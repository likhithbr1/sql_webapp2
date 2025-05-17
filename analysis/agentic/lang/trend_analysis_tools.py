import pandas as pd
from difflib import get_close_matches
from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import List, Dict

# ------------------ DATABASE MAPPING ------------------
DATABASES = {
    "eon": "data/eon.xlsx",
    "retail": "data/retail.xlsx",
    "telecom": "data/telecom.xlsx"
}

# ------------------ TOOL 1: list_databases ------------------
@tool
def list_databases() -> List[str]:
    """Returns the list of available databases."""
    return list(DATABASES.keys())

# ------------------ TOOL 2: validate_database ------------------
class ValidateDatabaseInput(BaseModel):
    db_name: str = Field(..., description="The name of the database to validate")

@tool(args_schema=ValidateDatabaseInput)
def validate_database(db_name: str) -> Dict:
    """Validates the database name."""
    db_name = db_name.lower().strip()
    if db_name in DATABASES:
        return {"status": "valid", "db_name": db_name}
    
    matches = get_close_matches(db_name, DATABASES.keys(), n=1, cutoff=0.6)
    if matches:
        return {"status": "suggest", "suggestion": matches[0]}
    
    return {"status": "invalid", "suggestion": None}

# ------------------ TOOL 3: load_product_list ------------------
class LoadProductListInput(BaseModel):
    db_name: str = Field(..., description="The name of the database to load products from")

@tool(args_schema=LoadProductListInput)
def load_product_list(db_name: str) -> List[str]:
    """Loads all unique product names from the Excel file."""
    if db_name not in DATABASES:
        raise ValueError(f"Invalid DB: {db_name}")
    
    df = pd.read_excel(DATABASES[db_name])
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return sorted(df["product"].dropna().astype(str).str.strip().unique())

# ------------------ TOOL 4: validate_product_name ------------------
class ValidateProductNameInput(BaseModel):
    product_name: str = Field(..., description="The product name to validate")
    product_list: List[str] = Field(..., description="The list of valid product names")

@tool(args_schema=ValidateProductNameInput)
def validate_product_name(product_name: str, product_list: List[str]) -> Dict:
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
class GetMonthlySalesInput(BaseModel):
    db_name: str = Field(..., description="The name of the database to query")
    product_name: str = Field(..., description="The product to aggregate sales for")

@tool(args_schema=GetMonthlySalesInput)
def get_monthly_sales(db_name: str, product_name: str) -> Dict[str, int]:
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
class SummarizeTrendInput(BaseModel):
    product_name: str = Field(..., description="The product being analyzed")
    monthly_sales: Dict[str, int] = Field(..., description="Monthly sales figures for the product")

@tool(args_schema=SummarizeTrendInput)
def summarize_trend(product_name: str, monthly_sales: Dict[str, int]) -> str:
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

