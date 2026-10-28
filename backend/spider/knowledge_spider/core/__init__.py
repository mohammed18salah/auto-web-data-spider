"""
Module: core/__init__.py
Purpose: Core package initializer — re-exports the config API so other
         modules can simply write: from knowledge_spider.core import get_config
Author: KnowledgeSpider Engine
"""

from knowledge_spider.core.config import (  # noqa: F401
    Config,
    get_config,
    load_config,
    reset_config,
)
