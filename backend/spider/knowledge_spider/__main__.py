"""
knowledge_spider/__main__.py

Allows running the CLI directly as a module:
    python -m knowledge_spider <command> [options]
"""
from knowledge_spider.cli.main import app

if __name__ == "__main__":
    app()
