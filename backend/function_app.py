import logging
import azure.functions as func
import json

from orchestrator.agent import run_agent


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


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

        result = run_agent(nl_query)

        return func.HttpResponse(
            json.dumps(result, indent=2),
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
