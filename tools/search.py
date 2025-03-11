from langchain_community.tools import DuckDuckGoSearchRun


def search_duck_duck_go(query: str) -> str:
    """Search the web for information.

    Args:
        query: The query to search for.
    """
    search = DuckDuckGoSearchRun()
    return search.invoke(query)
