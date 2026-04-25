import sys
sys.path.insert(0, ".")

from knowledge_spider.query.query_engine import generate_queries
from knowledge_spider.utils.lang_detect import detect_script, split_by_language
from knowledge_spider.nlp.extractor import extract_terms
from knowledge_spider.nlp.summariser import generate_summary

print("--- Testing Script Detection ---")
print("DNS ->", detect_script("DNS"))
print("نظام أسماء النطاقات ->", detect_script("نظام أسماء النطاقات"))
print("DNS نظام أسماء النطاقات ->", detect_script("DNS نظام أسماء النطاقات"))

print("\n--- Testing Query Generation ---")
print("Queries for 'DNS':")
for q in generate_queries("DNS")[:3]:
    print(f"  - {q}")

print("Queries for 'ذكاء اصطناعي':")
for q in generate_queries("ذكاء اصطناعي")[:3]:
    print(f"  - {q}")

print("\n--- Testing Extraction & Summarisation ---")
mixed_text = "الذكاء الاصطناعي (Artificial Intelligence) هو مجال علوم الحاسب المخصص لحل المشاكل المعرفية. Machine learning is a core part of AI."
print("Text:", mixed_text)
print("Terms:", extract_terms(mixed_text))

# Let's add more text to test the summariser, it needs at least 50 chars.
long_mixed_text = "الذكاء الاصطناعي هو مجال علوم الحاسب المخصص لحل المشاكل المعرفية المرتبطة عادةً بالذكاء البشري، مثل التعلم والإبداع والتعرف على الصور. Machine learning is a core part of AI. It involves training algorithms to learn from data. Deep learning is a subset of machine learning based on artificial neural networks."

# Mock config for summariser
from knowledge_spider.core.config import Config
cfg = Config()
cfg.nlp.summary_sentence_count = 2

print("\nSummary:", generate_summary(long_mixed_text, config=cfg))
print("\n[OK] Arabic support tested.")
