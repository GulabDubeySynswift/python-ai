from sqlalchemy import create_engine, text
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
import re

DATABASE_URL = "mysql+pymysql://root:@localhost:3306/python_db"

engine = create_engine(DATABASE_URL)


def is_safe_query(query: str) -> bool:
    forbidden = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "create",
        "grant",
        "revoke"
    ]

    query = query.lower()

    return not any(word in query for word in forbidden)


def enforce_workspace_filter(query: str, workspace_id: int) -> str:
    """
    Ensures workspace_id filter is always applied.
    """

    query_lower = query.lower()

    # If WHERE exists append workspace filter
    if " where " in query_lower:
        query = re.sub(
            r"\bwhere\b",
            f"WHERE workspace_id = {workspace_id} AND",
            query,
            flags=re.IGNORECASE,
            count=1
        )
    else:
        # No WHERE clause
        query += f" WHERE workspace_id = {workspace_id}"

    return query


@tool
def db_query(query: str, config: RunnableConfig) -> str:
    """
    Execute SQL SELECT query safely with workspace isolation.

    Args:
        query: SQL SELECT query
        workspace_id: Workspace ID for tenant isolation
    """
    workspace_id = config["configurable"]["workspace_id"]
    query_lower = query.lower()

    # Only SELECT allowed
    if not query_lower.startswith("select"):
        return "❌ Only SELECT queries allowed."

    # Block dangerous keywords
    if not is_safe_query(query):
        return "❌ Dangerous SQL query blocked."

    # Prevent injection attempts
    injection_patterns = ["--", ";", "/*", "*/", " or ", " and 1=1"]
    if any(pattern in query_lower for pattern in injection_patterns):
        return "❌ Possible SQL injection detected."

    # Enforce workspace filter
    query = enforce_workspace_filter(query, workspace_id)

    # Add limit if not provided
    if "limit" not in query_lower:
        query += " LIMIT 50"

    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = result.fetchall()

            if not rows:
                return "No results found"

            return str([dict(row._mapping) for row in rows])

    except Exception as e:
        return f"Database error: {str(e)}"