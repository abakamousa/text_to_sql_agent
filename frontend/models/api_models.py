from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class SQLQueryResponse(BaseModel):
    """Model for the response returned by the backend agent."""
    result: str                        # Generated SQL
    rows: Optional[List[Dict[str, Any]]] = None  # Query results, if any
    execution_time: Optional[float] = None      # Optional: execution time in seconds
    row_count: Optional[int] = None             # Optional: number of rows returned

class SQLQueryRequest(BaseModel):
    """Model for the request sent to the backend agent."""
    query: str
