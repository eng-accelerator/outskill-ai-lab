import agents as agents_sdk


@agents_sdk.function_tool
def format_citation(title: str, url: str, author: str = "Unknown") -> str:
    """
    Format a citation in a standardized format.
    
    Args:
        title: The title of the source
        url: The URL of the source
        author: The author of the source (optional)
    
    Returns:
        A formatted citation string
    """
    return f"[{author}. \"{title}\". {url}]"


def create_citation_tool():
    return format_citation
