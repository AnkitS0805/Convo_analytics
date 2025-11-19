
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from ..llm.bedrock_client import BedrockClient
from ..logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class SqlPlan:
    """SQL query plan with detailed explanation."""

    sql: str
    explanation: str
    tables_used: List[str]
    key_metrics: List[str]
    confidence: str


class SqlPlannerAgent:
   

    def __init__(self, llm: BedrockClient, schema_text: str) -> None:
        self.llm = llm
        self.schema_text = schema_text
        logger.info("SqlPlannerAgent initialized with schema")

    def plan(self, question: str) -> SqlPlan:
        
        logger.info("Planning SQL for question: %s", question[:150])

        prompt = (
            "You are an expert SQL query planner for a business analytics database (SQLite).\n\n"
            "CRITICAL RULES (MUST FOLLOW):\n"
            "1. Use ONLY tables and columns that exist in the schema below\n"
            "2. Verify every column name against the schema - NO guessing or hallucination\n"
            "3. Use proper JOIN relationships based on shared key columns\n"
            "4. Write efficient, optimized SQLite queries\n"
            "5. Add helpful column aliases for readability\n"
            "6. Use appropriate aggregations (SUM, COUNT, AVG) for metrics\n"
            "7. Add ORDER BY and LIMIT clauses when showing top/bottom results\n"
            "8. IMPORTANT: Do NOT include semicolons (;) at the end of SQL queries\n"
            "9. CRITICAL: If you define a table alias (e.g., 's2015'), you MUST use that exact alias in all column references (e.g., 's2015.OrderQuantity')\n"
            "10. For multi-year sales analysis: Use UNION ALL to combine years, NOT JOIN (JOIN creates cartesian products)\n"
            "11. CRITICAL UNION ALL PATTERN: Each SELECT in UNION ALL must have its OWN GROUP BY before combining. Never put GROUP BY after UNION ALL.\n\n"
            "EXAMPLES:\n"
            "- CORRECT: SELECT p.ProductName FROM AdventureWorks_Products p WHERE p.ProductKey = 123\n"
            "- WRONG: SELECT p.ProductName FROM AdventureWorks_Products p WHERE ProductKey = 123 (missing alias)\n"
            "- CORRECT (multi-year with GROUP BY): \n"
            "  SELECT strftime('%Y', OrderDate) AS Year, SUM(OrderQuantity) AS TotalSales\n"
            "  FROM AdventureWorks_Sales_2015 GROUP BY strftime('%Y', OrderDate)\n"
            "  UNION ALL\n"
            "  SELECT strftime('%Y', OrderDate) AS Year, SUM(OrderQuantity) AS TotalSales\n"
            "  FROM AdventureWorks_Sales_2016 GROUP BY strftime('%Y', OrderDate)\n"
            "  UNION ALL\n"
            "  SELECT strftime('%Y', OrderDate) AS Year, SUM(OrderQuantity) AS TotalSales\n"
            "  FROM AdventureWorks_Sales_2017 GROUP BY strftime('%Y', OrderDate)\n"
            "  ORDER BY Year\n"
            "- WRONG (multi-year): SELECT ... FROM Sales_2015 UNION ALL SELECT ... FROM Sales_2016 GROUP BY Year (GROUP BY after UNION!)\n"
            "- WRONG (multi-year): SELECT ... FROM Sales_2015 s15 JOIN Sales_2016 s16 ON 1=1 (creates cartesian product)\n\n"
            f"DATABASE SCHEMA:\n{self.schema_text}\n\n"
            "CRITICAL SCHEMA RELATIONSHIPS (memorize these):\n"
            "1. Sales tables (Sales_2015/2016/2017) contain: CustomerKey, TerritoryKey, ProductKey, OrderQuantity\n"
            "2. Customers table contains: CustomerKey, FirstName, LastName, etc. (NO TerritoryKey!)\n"
            "3. Territories table contains: SalesTerritoryKey, Region, Country\n"
            "4. Products table contains: ProductKey, ProductSubcategoryKey (NOT ProductCategoryKey!)\n\n"
            "CORRECT JOIN PATHS:\n"
            "- For regions/territories: Sales.TerritoryKey → Territories.SalesTerritoryKey\n"
            "- For customer info: Sales.CustomerKey → Customers.CustomerKey\n"
            "- For product categories: Sales.ProductKey → Products.ProductKey → Subcategories.ProductSubcategoryKey → Categories.ProductCategoryKey\n\n"
            "COMMON MISTAKES TO AVOID:\n"
            "Customers.TerritoryKey (doesn't exist! Use Sales.TerritoryKey instead)\n"
            "Products.ProductCategoryKey (doesn't exist! Join through Subcategories)\n"
            "JOIN Sales_2015 s15 JOIN Sales_2016 s16 ON 1=1 (creates cartesian product!)\n\n"
            "EXAMPLE QUERIES (use these as templates):\n\n"
            
            f"USER QUESTION: {question}\n\n"
            "Generate a response with:\n"
            "1. sql: Complete SQLite query (optimized and tested logic)\n"
            "2. explanation: Business-friendly explanation of what the query does (2-3 sentences)\n"
            "3. tables_used: Array of table names used in the query\n"
            "4. key_metrics: Array of key metrics/columns being analyzed\n"
            "5. confidence: 'high', 'medium', or 'low' based on schema match\n\n"
            "If you cannot answer due to missing columns, return: sql='SELECT 1', "
            "explanation describing the limitation, confidence='low'\n\n"
            "Return JSON with keys: sql, explanation, tables_used (list), key_metrics (list), confidence"
        )

        schema = {
            "sql": "str",
            "explanation": "str",
            "tables_used": "list",
            "key_metrics": "list",
            "confidence": "str",
        }

        rsp = self.llm.complete_json(prompt, schema=schema)

        sql = rsp.get("sql", "SELECT 1")
        plan = SqlPlan(
            sql=sql,
            explanation=rsp.get("explanation", "No explanation provided"),
            tables_used=rsp.get("tables_used", []),
            key_metrics=rsp.get("key_metrics", []),
            confidence=rsp.get("confidence", "medium"),
        )

        logger.info(
            "SQL plan generated: tables=%s, metrics=%s, confidence=%s",
            plan.tables_used,
            plan.key_metrics,
            plan.confidence,
        )
        logger.debug("Generated SQL:\n%s", sql)

        return plan
