import sys
sys.stdout.reconfigure(encoding='utf-8')
import re

def compute_relevance(seed_topic: str, title: str, url: str, content: str) -> tuple[float, str]:
    """
    Computes semantic relevance (0.0 to 1.0) between page content and seed topic.
    Returns (score, reason).
    """
    text_lower = (title + " " + content[:2500]).lower()
    url_lower = url.lower()
    seed_lower = seed_topic.lower()
    
    # Extract entities from seed topic
    academic_titles = ["دكتور", "الدكتور", "د.", "د/", "أستاذ", "الاستاذ", "أ.د", "بروفيسور", "مهندس"]
    clean_seed = seed_lower
    for t in academic_titles:
        clean_seed = re.sub(rf'^{re.escape(t)}\s+', '', clean_seed)
        
    institution_keywords = ["جامعة", "كلية", "معهد", "مستشفى", "مركز", "أكاديمية"]
    
    # Check if seed has institution / location
    has_institution = any(inst in seed_lower for inst in institution_keywords) or "انبار" in seed_lower or "بغداد" in seed_lower
    
    score = 0.0
    matched_reasons = []
    
    # 1. Exact phrase match
    if clean_seed in text_lower:
        score += 0.5
        matched_reasons.append("exact_seed_match")
    
    # 2. Check person name
    name_parts = re.split(r'\s+(?=جامعة|كلية|معهد|مستشفى|مركز)', clean_seed)
    person_name = name_parts[0].strip() if name_parts else clean_seed
    
    if len(person_name) > 3:
        if person_name in text_lower:
            score += 0.4
            matched_reasons.append("person_name_match")
        else:
            # Check 2+ tokens of name
            tokens = [w for w in person_name.split() if len(w) > 2]
            matched_tokens = sum(1 for tok in tokens if tok in text_lower)
            if matched_tokens >= 2:
                score += 0.25
                matched_reasons.append(f"partial_name_{matched_tokens}_tokens")
                
    # 3. Check Institution / Location constraint
    if has_institution:
        inst_tokens = ["انبار", "الأنبار", "uoanbar", "جامعة الانبار", "جامعة الأنبار", "العراق"]
        inst_matched = any(it in text_lower or it in url_lower for it in inst_tokens)
        if inst_matched:
            score += 0.35
            matched_reasons.append("institution_location_verified")
        else:
            # Check for conflicting distant locations (e.g. Sharqia, Egypt clinic)
            conflicting_locations = ["الشرقية", "ديرب نجم", "الزقازيق", "مصر", "القاهرة", "طنطا", "المنصورة"]
            conflict_found = any(c in text_lower for c in conflicting_locations)
            if conflict_found:
                return 0.0, "rejected: conflicting geographic location (Egypt/Sharqia instead of Anbar/Iraq)"
            else:
                score *= 0.3 # Heavy penalty for missing requested institution
                matched_reasons.append("penalty_missing_institution")
                
    return min(1.0, score), ", ".join(matched_reasons)

# Test 1: The Egyptian ENT Clinic
egyptian_clinic_title = "دكتور محمد صلاح ابراهيم داخل دكتور انف واذن وحنجره | دليل شفيقة"
egyptian_clinic_url = "https://sannfor.com/dr-mohamed-salah"
egyptian_clinic_content = "ديرب نجم، الشرقية. 1 تقييم احجز الآن محمد صلاح ابراهيم التفاصيل دكتور انف واذن وحنجرة في الشرقية الزقازيق..."

# Test 2: Anbar University
anbar_title = "كلية علوم الحاسوب وتكنولوجيا المعلومات / جامعة الانبار"
anbar_url = "https://www.uoanbar.edu.iq/faculty/mohamed-salah"
anbar_content = "المناقشة العلمية بحضور التدريسي دكتور محمد صلاح ابراهيم في جامعة الانبار قسم علوم الحاسبات كلية الحاسوب..."

s1, r1 = compute_relevance("دكتور محمد صلاح ابراهيم جامعة الانبار", egyptian_clinic_title, egyptian_clinic_url, egyptian_clinic_content)
print(f"Egyptian Clinic Score: {s1:.2f} -> Reason: {r1}")

s2, r2 = compute_relevance("دكتور محمد صلاح ابراهيم جامعة الانبار", anbar_title, anbar_url, anbar_content)
print(f"Anbar University Score: {s2:.2f} -> Reason: {r2}")
