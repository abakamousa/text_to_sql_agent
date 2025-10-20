import logging
import azure.functions as func
import json
from decimal import Decimal
from datetime import datetime
from backend.orchestrator.agent import run_agent


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


def convert_json_compatible(obj):
    """
    Recursively convert objects to JSON-serializable types:
    - Decimal -> float
    - datetime -> ISO string
    - nested lists/dicts -> recursively converted
    """
    if isinstance(obj, list):
        return [convert_json_compatible(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_json_compatible(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj


@app.function_name(name="query_agent")
@app.route(route="query", methods=["POST"])
def query_agent(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function endpoint for text-to-SQL agent.
    Expects JSON body: { "query": "..." }
    """
    try:
        body = req.get_json()
        nl_query = body.get("query")

        if not nl_query:
            return func.HttpResponse(
                json.dumps({"error": "Missing 'query' field."}),
                status_code=400,
                mimetype="application/json",
            )

        logging.info("Received query: %s", nl_query)

        # Run the agent
        result = run_agent(nl_query)

        # Safely convert all JSON-incompatible objects
        safe_result = convert_json_compatible(result)

        return func.HttpResponse(
            json.dumps(safe_result, indent=2),
            status_code=200,
            mimetype="application/json",
        )

    except ValueError as ve:
        logging.error("Value error: %s", str(ve))
        return func.HttpResponse(
            json.dumps({"error": str(ve)}),
            status_code=400,
            mimetype="application/json",
        )
    except Exception as e:
        logging.exception("Unexpected error occurred.")
        return func.HttpResponse(
            json.dumps({"error": "Internal Server Error", "details": str(e)}),
            status_code=500,
            mimetype="application/json",
        )
