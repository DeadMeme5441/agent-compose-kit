def sample_tool(a: int, b: int) -> dict:
    """Add two integers and return a dict result.

    Use when simple addition is requested. Returns {'status':'success','sum':<int>}.
    """
    return {"status": "success", "sum": int(a) + int(b)}

