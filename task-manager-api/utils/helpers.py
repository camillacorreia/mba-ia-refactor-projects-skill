from datetime import datetime, timezone


def utc_now():
    """Agora em UTC, sem tzinfo, compatível com as colunas DateTime já gravadas."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)
