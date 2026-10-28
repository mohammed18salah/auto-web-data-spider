# -*- coding: utf-8 -*-
"""
Test: STEP 11 - nlp/summariser.py
Run:  python test_step11.py
"""
import sys
sys.path.insert(0, ".")

from knowledge_spider.utils.logger import setup_logger
setup_logger("test_summariser")

from knowledge_spider.core.config import get_config
from knowledge_spider.nlp.summariser import generate_summary

cfg = get_config()

test_text = """
The Domain Name System (DNS) is the hierarchical and decentralized naming system used to identify computers, services, and other resources reachable through the Internet or other Internet Protocol (IP) networks.
The resource records contained in the DNS associate domain names with other forms of information.
These are most commonly used to translate human-readable domain names (like example.com) to the numerical IP addresses needed for the purpose of locating and identifying computer services and devices with the underlying network protocols.
By providing a worldwide, distributed directory service, the Domain Name System has been an essential component of the functionality of the Internet since 1985.
The DNS delegates the responsibility of assigning domain names and mapping those names to Internet resources by designating authoritative name servers for each domain.
Network administrators may delegate authority over sub-domains of their allocated name space to other name servers.
"""

# ── Test 1: Configured summary length ─────────────────────────────────────────
# Force config to exactly 2 sentences
cfg.nlp.summary_sentences = 2
summary_2 = generate_summary(test_text, cfg)

assert len(summary_2) > 0
# The summary should be joined by spaces, we can approximate sentence count by splitting on ". "
sentences = [s for s in summary_2.split(". ") if s.strip()]
assert len(sentences) <= 2  # Might be less if text is very short
print(f"[OK] generate_summary (2 sentences): -> {summary_2[:80]}...")

# ── Test 2: Short text handling ───────────────────────────────────────────────
short_text = "This is a very short text."
summary_short = generate_summary(short_text, cfg)
assert summary_short == ""
print("[OK] generate_summary: short text (<50 chars) cleanly returns empty string")

# ── Test 3: Empty string handling ─────────────────────────────────────────────
summary_empty = generate_summary("   ", cfg)
assert summary_empty == ""
print("[OK] generate_summary: empty string cleanly returns empty string")

print("\n=== STEP 11 COMPLETE: Text Summarisation verified ===")
