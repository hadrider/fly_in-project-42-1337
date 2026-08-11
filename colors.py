"""Small ANSI color helper for terminal output."""

ANSI_COLORS: dict[str, str] = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
}

RESET = "\033[0m"


def color_text(text: str, color: str | None) -> str:
    """Wrap text in an ANSI color when a valid color was supplied."""
    if color is None:
        return text
    code = ANSI_COLORS.get(color)
    if code is None:
        return text
    return f"{code}{text}{RESET}"
