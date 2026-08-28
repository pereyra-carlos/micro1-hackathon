"""Text helpers shared by the baseline and the agent."""

HEAD_CHARS = 3000
DEFAULT_LIMIT = 9000


def truncate(text: str, limit: int = DEFAULT_LIMIT) -> str:
    """Cap text at `limit` chars, keeping the head and the (larger) tail.

    The tail is favored because logs put the most recent, most relevant
    lines last.
    """
    if len(text) <= limit:
        return text
    head = text[:HEAD_CHARS]
    tail = text[-(limit - HEAD_CHARS):]
    omitted = len(text) - HEAD_CHARS - len(tail)
    return f"{head}\n...[{omitted} chars truncated]...\n{tail}"
