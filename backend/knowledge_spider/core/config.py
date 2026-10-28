"""
Module: core/config.py
Purpose: Typed configuration loader for config.toml. Provides a validated
         Config dataclass and a module-level singleton so every module can
         call get_config() without re-parsing the TOML file on every access.
         All system defaults live here; no hardcoded values elsewhere.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import toml

from knowledge_spider.utils.logger import logger

# ── Default config path ───────────────────────────────────────────────────────
_DEFAULT_CONFIG_PATH: Path = Path(__file__).resolve().parent.parent.parent / "config.toml"
_config_singleton: Optional["Config"] = None


# ── Sub-section dataclasses ───────────────────────────────────────────────────

@dataclass
class CrawlerConfig:
    """Settings that control the crawl loop behaviour."""

    max_depth: int = 3
    max_sources: int = 200
    time_limit_minutes: int = 60
    crawl_delay_seconds: float = 2.0
    max_urls_per_query: int = 5
    respect_robots: bool = True
    trusted_only: bool = False


@dataclass
class NLPConfig:
    """Settings that control NLP processing thresholds."""

    min_content_words: int = 150
    relevance_threshold: float = 0.45
    max_topics_per_page: int = 8
    summary_sentence_count: int = 5


@dataclass
class ScoringConfig:
    """Weights used in the composite source quality score formula."""

    domain_weight: float = 0.35
    content_weight: float = 0.15
    relevance_weight: float = 0.35
    freshness_weight: float = 0.15

    def validate_weights(self) -> None:
        """Assert that the four weights sum to 1.0 (±0.01 tolerance)."""
        total = self.domain_weight + self.content_weight \
              + self.relevance_weight + self.freshness_weight
        if abs(total - 1.0) > 0.01:
            raise ValueError(
                f"Scoring weights must sum to 1.0, got {total:.4f}"
            )


@dataclass
class ExportConfig:
    """Export path and format defaults."""

    output_dir: str = "./output"
    default_format: str = "json"


@dataclass
class Config:
    """
    Root configuration object.

    Aggregates all sub-section configs plus the flat trusted_domains
    list and domain_scores mapping.
    """

    crawler: CrawlerConfig = field(default_factory=CrawlerConfig)
    nlp: NLPConfig = field(default_factory=NLPConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    trusted_domains: list[str] = field(default_factory=list)
    domain_scores: dict[str, float] = field(default_factory=dict)

    # ── Helpers ───────────────────────────────────────────────────────────

    def get_domain_score(self, domain: str) -> float:
        """
        Look up the quality score for a domain, falling back to 'default'.

        Args:
            domain: Registered domain string (e.g. 'wikipedia.org').

        Returns:
            Float score in [0.0, 1.0].
        """
        return self.domain_scores.get(domain, self.domain_scores.get("default", 0.40))

    def is_trusted_domain(self, domain: str) -> bool:
        """
        Return True if the domain appears in the trusted_domains list.

        Args:
            domain: Registered domain string.

        Returns:
            Boolean.
        """
        return any(trusted in domain for trusted in self.trusted_domains)

    def to_json(self) -> str:
        """
        Serialise the config to a JSON string for snapshot storage.

        Returns:
            JSON string representation of all config values.
        """
        return json.dumps(
            {
                "crawler":        self.crawler.__dict__,
                "nlp":            self.nlp.__dict__,
                "scoring":        self.scoring.__dict__,
                "export":         self.export.__dict__,
                "trusted_domains": self.trusted_domains,
                "domain_scores":  self.domain_scores,
            },
            indent=2,
        )


# ── Loader ────────────────────────────────────────────────────────────────────

def _parse_config(raw: dict) -> Config:
    """
    Convert a raw TOML dict into a validated Config object.

    Args:
        raw: Dict produced by toml.load().

    Returns:
        Validated Config dataclass instance.

    Raises:
        KeyError: If a required section is missing.
        ValueError: If scoring weights don't sum to 1.0.
    """
    required = ["crawler", "nlp", "scoring", "trusted_domains", "domain_scores", "export"]
    for section in required:
        if section not in raw:
            raise KeyError(f"config.toml is missing required section: [{section}]")

    crawler = CrawlerConfig(**raw["crawler"])
    nlp     = NLPConfig(**raw["nlp"])
    scoring = ScoringConfig(**raw["scoring"])
    export  = ExportConfig(**raw["export"])
    scoring.validate_weights()

    trusted = raw["trusted_domains"].get("domains", [])
    domain_scores: dict[str, float] = {
        k: float(v) for k, v in raw["domain_scores"].items()
    }

    return Config(
        crawler=crawler,
        nlp=nlp,
        scoring=scoring,
        export=export,
        trusted_domains=trusted,
        domain_scores=domain_scores,
    )


def _find_config_file(custom_path: Optional[Path] = None) -> Path:
    """Find config.toml searching standard candidate locations."""
    if custom_path is not None and Path(custom_path).exists():
        return Path(custom_path)
    candidates = [
        _DEFAULT_CONFIG_PATH,
        Path.cwd() / "config.toml",
        Path(__file__).resolve().parent.parent.parent / "config.toml",
        Path(__file__).resolve().parent.parent / "config.toml",
    ]
    for p in candidates:
        if p.exists():
            return p
    return _DEFAULT_CONFIG_PATH


def load_config(path: Optional[Path] = None) -> Config:
    """
    Parse config.toml and cache the result as a module-level singleton.

    Subsequent calls return the cached instance without re-reading the file,
    unless force=True is used via reset_config() or reload_config().

    Args:
        path: Path to the config.toml file, or None to auto-locate.

    Returns:
        Validated Config instance.

    Raises:
        FileNotFoundError: If config.toml cannot be found.
        KeyError: If a required section is absent.
    """
    global _config_singleton

    if _config_singleton is not None and path is None:
        return _config_singleton

    config_path = _find_config_file(path)
    if not config_path.exists():
        raise FileNotFoundError(f"config.toml not found at {config_path.resolve()}")

    raw = toml.load(config_path)
    _config_singleton = _parse_config(raw)
    logger.info(f"Config loaded from {config_path.resolve()}")
    logger.debug(
        f"  max_depth={_config_singleton.crawler.max_depth} "
        f"max_sources={_config_singleton.crawler.max_sources} "
        f"trusted_domains={len(_config_singleton.trusted_domains)}"
    )
    return _config_singleton


def get_config() -> Config:
    """
    Return the global Config singleton, loading from disk if needed.

    Returns:
        The cached Config instance.
    """
    if _config_singleton is None:
        return load_config()
    return _config_singleton


def reload_config(path: Optional[Path] = None) -> Config:
    """
    Clear the cached singleton and re-read configuration from disk.

    Returns:
        Freshly loaded Config instance.
    """
    global _config_singleton
    _config_singleton = None
    return load_config(path)


def reset_config() -> None:
    """
    Clear the singleton so the next get_config() re-reads from disk.

    Primarily used in tests.
    """
    global _config_singleton
    _config_singleton = None


def get_session_config(overrides: Optional[dict] = None) -> Config:
    """
    Return a detached deep copy of the configuration for a specific session.
    Prevents per-crawl overrides from corrupting the global singleton.

    Args:
        overrides: Optional nested dictionary of config updates.

    Returns:
        Isolated Config instance.
    """
    cfg = copy.deepcopy(get_config())
    if overrides:
        for section, values in overrides.items():
            if hasattr(cfg, section) and isinstance(values, dict):
                sub = getattr(cfg, section)
                for k, v in values.items():
                    if hasattr(sub, k):
                        setattr(sub, k, v)
            elif hasattr(cfg, section):
                setattr(cfg, section, values)
    return cfg


def update_config(updates: dict) -> Config:
    """
    Update the global config singleton in-memory safely.
    Useful when settings are modified from UI or API endpoints.

    Args:
        updates: Dict of config changes e.g. {"crawler": {"max_depth": 2}}

    Returns:
        Updated Config singleton.
    """
    cfg = get_config()
    for section, values in updates.items():
        if hasattr(cfg, section) and isinstance(values, dict):
            sub = getattr(cfg, section)
            for k, v in values.items():
                if hasattr(sub, k):
                    setattr(sub, k, v)
        elif hasattr(cfg, section):
            setattr(cfg, section, values)

    if hasattr(cfg, "scoring") and hasattr(cfg.scoring, "validate_weights"):
        cfg.scoring.validate_weights()

    logger.info("Global config singleton updated successfully")
    return cfg

