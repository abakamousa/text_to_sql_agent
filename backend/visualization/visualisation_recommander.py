import re
import json
import pandas as pd
import altair as alt
from backend.services.openai_client import OpenAIClient


class VisualizationRecommender:
    """
    Automatically recommends and generates a visualization
    using both heuristics and LLM reasoning.
    """

    def __init__(self, nl_query: str, sql_query: str, data: list[dict]):
        self.nl_query = nl_query or ""
        self.sql_query = sql_query or ""
        self.data = pd.DataFrame(data) if data else pd.DataFrame()

        self.llm_service = OpenAIClient()
        self.llm = self.llm_service.get_llm()

    # -------------------------------------------------------------------------
    # 1. RULE-BASED INTENT DETECTION (FAST)
    # -------------------------------------------------------------------------
    def _heuristic_intent(self) -> str:
        nl_lower = self.nl_query.lower()
        sql_lower = self.sql_query.lower()

        if re.search(r"trend|over time|by month|per day|growth", nl_lower):
            return "time_series"
        if re.search(r"compare|top|rank|most|least|highest|lowest", nl_lower):
            return "bar"
        if re.search(r"distribution|histogram|spread|range", nl_lower):
            return "histogram"
        if re.search(r"relationship|correlation|impact", nl_lower):
            return "scatter"
        if re.search(r"share|percentage|ratio|portion", nl_lower):
            return "pie"

        if "group by" in sql_lower:
            return "bar"
        if "sum" in sql_lower or "avg" in sql_lower or "count" in sql_lower:
            return "bar"

        return "table"

    # -------------------------------------------------------------------------
    # 2. LLM-BASED RECOMMENDATION
    # -------------------------------------------------------------------------
    def _llm_recommendation(self) -> dict:
        """
        Ask the LLM to recommend a visualization type and axes.
        """
        if self.data.empty:
            return {"type": "none", "reason": "No data available"}

        columns = list(self.data.columns)

        prompt = f"""
        You are an expert data visualization assistant.
        The user asked: "{self.nl_query}"
        The SQL executed was: "{self.sql_query}"
        The dataset columns are: {columns}

        Suggest the most suitable visualization for this data.
        Respond strictly in JSON with:
        {{
          "type": "bar" | "line" | "scatter" | "pie" | "histogram" | "table",
          "x_axis": "<column name>",
          "y_axis": "<column name>",
          "title": "<short descriptive title>",
          "reason": "<brief reasoning>"
        }}
        """

        try:
            response = self.llm.invoke(prompt)
            text = response.content if hasattr(response, "content") else str(response)
            result = json.loads(text)
            return result
        except Exception as e:
            # Fallback
            return {
                "type": self._heuristic_intent(),
                "x_axis": self.data.columns[0] if not self.data.empty else None,
                "y_axis": self.data.columns[-1] if len(self.data.columns) > 1 else None,
                "title": "Auto Visualization",
                "reason": f"LLM recommendation failed: {e}",
            }

    # -------------------------------------------------------------------------
    # 3. COMBINE HEURISTICS + LLM
    # -------------------------------------------------------------------------
    def recommend_chart(self) -> dict:
        """
        Combines heuristic and LLM reasoning for visualization recommendation.
        """
        heuristic = self._heuristic_intent()
        llm_suggestion = self._llm_recommendation()

        # Prefer LLM if confident
        chart_type = llm_suggestion.get("type") or heuristic
        x_axis = llm_suggestion.get("x_axis") or (self.data.columns[0] if not self.data.empty else None)
        y_axis = llm_suggestion.get("y_axis") or (self.data.columns[-1] if len(self.data.columns) > 1 else None)
        title = llm_suggestion.get("title") or "Recommended Visualization"
        reason = llm_suggestion.get("reason", "Based on heuristic and query context")

        return {
            "type": chart_type,
            "x_axis": x_axis,
            "y_axis": y_axis,
            "title": title,
            "reason": reason,
        }

    # -------------------------------------------------------------------------
    # 4. BUILD CHART FOR STREAMLIT
    # -------------------------------------------------------------------------
    def build_chart(self):
        """
        Generate Altair chart based on recommended visualization.
        """
        if self.data.empty:
            return None

        rec = self.recommend_chart()
        chart_type = rec["type"]
        x_axis, y_axis = rec["x_axis"], rec["y_axis"]
        title = rec["title"]

        try:
            if chart_type == "line":
                chart = alt.Chart(self.data).mark_line(point=True).encode(
                    x=alt.X(x_axis, title=x_axis),
                    y=alt.Y(y_axis, title=y_axis),
                    tooltip=list(self.data.columns)
                ).properties(title=f"📈 {title}")

            elif chart_type == "bar":
                chart = alt.Chart(self.data).mark_bar().encode(
                    x=alt.X(x_axis, title=x_axis),
                    y=alt.Y(y_axis, title=y_axis),
                    tooltip=list(self.data.columns)
                ).properties(title=f"📊 {title}")

            elif chart_type == "scatter":
                chart = alt.Chart(self.data).mark_circle(size=80).encode(
                    x=x_axis,
                    y=y_axis,
                    tooltip=list(self.data.columns)
                ).interactive().properties(title=f"🔍 {title}")

            elif chart_type == "pie":
                chart = alt.Chart(self.data).mark_arc().encode(
                    theta=alt.Theta(y_axis, type="quantitative"),
                    color=alt.Color(x_axis, type="nominal"),
                    tooltip=list(self.data.columns)
                ).properties(title=f"🥧 {title}")

            elif chart_type == "histogram":
                chart = alt.Chart(self.data).mark_bar().encode(
                    alt.X(y_axis or x_axis, bin=True),
                    y='count()',
                    tooltip=list(self.data.columns)
                ).properties(title=f"📊 {title}")

            else:
                return None

            return chart

        except Exception:
            return None
