from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from ..llm.bedrock_client import BedrockClient
from ..logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Synthesis:
    """Rich synthesis of query results with insights and visualizations."""

    summary: str  # Executive summary (2-3 sentences)
    key_findings: List[str]  # Bullet points of insights
    detailed_analysis: str  # Detailed narrative analysis
    recommendations: List[str]  # Business recommendations
    chart_spec: Dict[str, Any] | None  # Vega-Lite chart spec if applicable


class SynthesizerAgent:
    

    def __init__(self, llm: BedrockClient) -> None:
        self.llm = llm
        logger.info("SynthesizerAgent initialized")

    def synthesize(self, columns: List[str], rows: List[List[Any]]) -> Synthesis:
        
        row_count = len(rows)
        logger.info("Synthesizing %d rows with %d columns", row_count, len(columns))

        # Prepare data preview
        preview_rows = rows[:20]
        data_preview = "\n".join(
            [f"  {dict(zip(columns, row))}" for row in preview_rows]
        )

        prompt = (
            "You are a business intelligence analyst transforming query results into actionable insights.\n\n"
            "TASK: Analyze the data and provide comprehensive business insights.\n\n"
            f"DATA SUMMARY:\n"
            f"- Total Rows: {row_count}\n"
            f"- Columns: {', '.join(columns)}\n\n"
            f"DATA PREVIEW (first {len(preview_rows)} rows):\n{data_preview}\n\n"
            "REQUIREMENTS:\n"
            "1. summary: Write a 2-3 sentence executive summary of the key takeaway\n"
            "2. key_findings: List 3-5 specific insights as bullet points (be specific with numbers/trends)\n"
            "3. detailed_analysis: Provide a detailed paragraph (4-6 sentences) analyzing patterns, "
            "trends, comparisons, or notable observations\n"
            "4. recommendations: List 2-4 actionable business recommendations based on the data\n"
            "5. chart_config: If the data is suitable for visualization, provide chart configuration. "
            "Return an object with: 'mark' (bar/line/point), 'x_field' (column name for X-axis), "
            "'x_type' (nominal/quantitative/temporal), 'y_field' (column for Y-axis), 'y_type'. "
            "Return null if visualization isn't helpful. DO NOT include 'data' field.\n\n"
            "BE SPECIFIC: Use actual values from the data, not generic statements.\n\n"
            "Return JSON with keys: summary (str), key_findings (list of str), detailed_analysis (str), "
            "recommendations (list of str), chart_config (dict or null)"
        )

        schema = {
            "summary": "str",
            "key_findings": "list",
            "detailed_analysis": "str",
            "recommendations": "list",
            "chart_config": "dict|null",
        }

        rsp = self.llm.complete_json(prompt, schema=schema)

        # Build complete Vega-Lite spec with actual data
        chart_spec = None
        chart_config = rsp.get("chart_config")
        if chart_config and isinstance(chart_config, dict):
            try:
                # Convert rows to list of dicts for Vega-Lite
                data_values = [dict(zip(columns, row)) for row in rows[:100]]  # Limit to 100 rows
                
                chart_spec = {
                    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                    "data": {"values": data_values},
                    "mark": chart_config.get("mark", "bar"),
                    "width": 400,
                    "height": 300,
                    "encoding": {
                        "x": {
                            "field": chart_config.get("x_field", columns[0] if columns else "x"),
                            "type": chart_config.get("x_type", "nominal"),
                        },
                        "y": {
                            "field": chart_config.get("y_field", columns[1] if len(columns) > 1 else "y"),
                            "type": chart_config.get("y_type", "quantitative"),
                        },
                    },
                }
                logger.info("Built Vega-Lite chart spec with %d data points", len(data_values))
            except Exception as e:  # noqa: BLE001
                logger.warning("Failed to build chart spec: %s", e)
                chart_spec = None

        synthesis = Synthesis(
            summary=rsp.get("summary", "Analysis completed."),
            key_findings=rsp.get("key_findings", []),
            detailed_analysis=rsp.get("detailed_analysis", "No detailed analysis available."),
            recommendations=rsp.get("recommendations", []),
            chart_spec=chart_spec,
        )

        logger.info(
            "Synthesis complete: %d findings, %d recommendations, chart=%s",
            len(synthesis.key_findings),
            len(synthesis.recommendations),
            "yes" if synthesis.chart_spec else "no",
        )

        return synthesis
