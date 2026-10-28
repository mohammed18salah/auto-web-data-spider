import re
import urllib.parse
import base64
import requests
from bs4 import BeautifulSoup

def generate_smart_queries(topic: str, seed_topic: str | None = None) -> list[str]:
    clean_topic = re.sub(r'\s+', ' ', topic.strip())
    academic_titles = ["دكتور", "الدكتور", "د.", "د/", "أستاذ", "الاستاذ", "أ.د", "بروفيسور", "مهندس"]
    institution_indicators = ["جامعة", "كلية", "معهد", "مستشفى", "مركز", "أكاديمية"]
    
    queries = [clean_topic]
    
    # Remove leading title if present
    topic_no_title = clean_topic
    for t in academic_titles:
        topic_no_title = re.sub(rf'^{re.escape(t)}\s+', '', topic_no_title, flags=re.IGNORECASE)
        
    has_inst = any(inst in clean_topic.lower() for inst in institution_indicators) or "انبار" in clean_topic or "الأنبار" in clean_topic
    
    if has_inst:
        parts = re.split(r'\s+(?=جامعة|كلية|معهد|مستشفى|مركز)', topic_no_title)
        if len(parts) >= 2:
            person_part = parts[0].strip()
            inst_part = " ".join(parts[1:]).strip()
            queries.append(f'"{person_part}" "{inst_part}"')
            queries.append(f'"{person_part}" {inst_part}')
            queries.append(f'{person_part} "{inst_part}"')
            if "انبار" in inst_part or "الأنبار" in inst_part:
                queries.append(f'"{person_part}" site:uoanbar.edu.iq')
                queries.append(f'"{person_part}" site:edu.iq')
            queries.append(f'السيرة الذاتية "{person_part}" {inst_part}')
            queries.append(f'أبحاث "{person_part}" {inst_part}')
        else:
            queries.append(f'"{clean_topic}"')
            queries.append(f'"{topic_no_title}"')
    else:
        queries.append(f'"{clean_topic}"')
        queries.append(f'أبحاث {clean_topic}')
        queries.append(f'معلومات عن {clean_topic}')
        
    seen = set()
    deduped = [q for q in queries if not (q in seen or seen.add(q))]
    return deduped

test_q = generate_smart_queries("دكتور محمد صلاح ابراهيم جامعة الانبار")
for i, q in enumerate(test_q, 1):
    print(f"{i}. {q}")
