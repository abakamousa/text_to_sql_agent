from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal

class SQLQueryResponse(BaseModel):
    """Model for the response returned by the backend agent."""
    sql_query: str                      # Generated SQL
    validation: str                     # "VALID" or validation errors
    data: Optional[List[dict]] = None   # Query results as list of dicts
    answer: Optional[str] = None        # LLM-generated answer
    visualization: Optional[dict] = None # Recommended visualization details
    regenerations_used: Optional[int] = 0
    execution_time: Optional[float] = None  # Query execution time in seconds

    class Config:
        # Handle non-JSON-serializable types like Decimal
        json_encoders = {
            Decimal: float
        }

class SQLQueryRequest(BaseModel):
    """Model for the request sent to the backend agent."""
    query: str