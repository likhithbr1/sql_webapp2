# tool_registry.py

from trend_analysis_tools import (
    list_databases,
    validate_database,
    load_product_list,
    validate_product_name,
    get_monthly_sales,
    summarize_trend
)

# List of all tools available to the agent
TREND_ANALYSIS_TOOLS = [
    list_databases,
    validate_database,
    load_product_list,
    validate_product_name,
    get_monthly_sales,
    summarize_trend
]
