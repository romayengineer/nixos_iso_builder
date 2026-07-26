"""Load help content from markdown files"""

from pathlib import Path

HELP_DIR = Path(__file__).parent / "help"


def load_help(name: str) -> str:
    """Load help content from a markdown file

    Args:
        name: Name of the help file (without .md extension)

    Returns:
        Content of the markdown file

    Raises:
        FileNotFoundError: If the help file does not exist
        IOError: If the file cannot be read
    """
    help_file = HELP_DIR / f"{name}.md"
    return help_file.read_text(encoding="utf-8")


def get_main_help() -> str:
    """Get main help content from main.md

    Returns:
        Main help text

    Raises:
        FileNotFoundError: If main.md does not exist
        IOError: If the file cannot be read
    """
    return load_help("main")


def get_burn_help() -> str:
    """Get USB burning help content from burn.md

    Returns:
        Burn help text

    Raises:
        FileNotFoundError: If burn.md does not exist
        IOError: If the file cannot be read
    """
    return load_help("burn")
