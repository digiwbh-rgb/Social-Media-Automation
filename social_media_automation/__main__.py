"""Allow running the package directly: python -m social_media_automation"""

from .cli.commands import cli

if __name__ == "__main__":
    cli()
