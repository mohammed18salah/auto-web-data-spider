"""
Module: knowledge/graph.py
Purpose: NetworkX-based Knowledge Graph & Entity Relationship Engine.
         Extracts entities (People/Colleagues, Organizations/Universities,
         Key Concepts/Research Domains, and Publications) from crawl sessions.
         Constructs an interconnected Knowledge Graph with PageRank, centrality,
         and computed 2D layout coordinates for visual rendering.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import re
from collections import Counter
import networkx as nx

from knowledge_spider.storage.database import (
    get_edges_by_session,
    get_topics_by_session,
    get_sources_by_session,
    get_terms_by_session,
)
from knowledge_spider.storage.models import SessionModel
from knowledge_spider.storage.database import get_engine, DBSession
from knowledge_spider.utils.logger import logger


class KnowledgeGraphManager:
    """
    Builds and analyses rich knowledge and entity graphs from crawl session data.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.graph = nx.DiGraph()

    def _get_session_row(self) -> SessionModel | None:
        """Fetch the session row to inspect the seed topic."""
        with DBSession(get_engine()) as db:
            return db.get(SessionModel, self.session_id)

    def build_rich_graph(self) -> dict:
        """
        Build an interconnected Knowledge Graph including:
        - Root Entity (The main searched Person or Topic)
        - Connected People & Colleagues (الزملاء والأشخاص المرتبطين)
        - Organizations & Universities (المؤسسات والجامعات التابع لها)
        - Research Concepts & Domains (التخصصات والمفاهيم العلمية)
        - Publications & Articles (الأبحاث والمنشورات الموثقة)
        """
        session_row = self._get_session_row()
        seed_topic = session_row.seed_topic if session_row else "Knowledge Core"

        sources = get_sources_by_session(self.session_id)
        terms = get_terms_by_session(self.session_id)
        topics = get_topics_by_session(self.session_id)
        db_edges = get_edges_by_session(self.session_id)

        # Detect if seed topic is a person query
        academic_titles = ["دكتور", "الدكتور", "د.", "د/", "أستاذ", "الاستاذ", "أ.د", "بروفيسور", "مهندس", "Dr.", "Prof."]
        is_person_query = any(t.lower() in seed_topic.lower() for t in academic_titles)

        nodes_dict: dict[str, dict] = {}
        links_list: list[dict] = []
        links_seen: set[tuple[str, str, str]] = set()

        def add_link(source_id: str, target_id: str, label: str, weight: float = 1.0):
            if source_id == target_id:
                return
            pair = (source_id, target_id, label)
            rev_pair = (target_id, source_id, label)
            if pair in links_seen or rev_pair in links_seen:
                return
            links_seen.add(pair)
            links_list.append({
                "source": source_id,
                "target": target_id,
                "label": label,
                "weight": round(weight, 2),
            })

        # 1. Root Node
        root_id = "node_root"
        nodes_dict[root_id] = {
            "id": root_id,
            "name": seed_topic,
            "type": "person" if is_person_query else "concept",
            "is_root": True,
            "val": 42,
            "details": f"الكيان الرئيسي المستهدف في البحث ({'شخصية أكاديمية' if is_person_query else 'موضوع المعرفة'})",
            "group": "root",
        }

        # 2. Extract Organizations from sources & seed
        org_patterns = [
            r'(?:جامعة|كلية|معهد|مركز\s+أبحاث|أكاديمية|قسم)\s+[\u0600-\u06FF\w]{3,25}(?:\s+[\u0600-\u06FF\w]{3,20}){0,3}',
            r'(?:University\s+of\s+[A-Za-z]+|[A-Za-z]+\s+University|College\s+of\s+[A-Za-z]+)',
        ]
        
        found_orgs: Counter = Counter()
        found_people: Counter = Counter()

        combined_text = ""
        for s in sources:
            combined_text += f" {s.title} {s.summary or ''} "

        for pat in org_patterns:
            for match in re.finditer(pat, combined_text, flags=re.IGNORECASE):
                org_name = match.group(0).strip()
                if len(org_name) > 6 and org_name.lower() != seed_topic.lower():
                    found_orgs[org_name] += 1

        # Also check seed topic for organization (e.g. جامعة الانبار)
        for org_kw in ["جامعة الانبار", "جامعة الأنبار", "كلية علوم الحاسوب", "جامعة بغداد"]:
            if org_kw in seed_topic or org_kw in combined_text:
                found_orgs[org_kw] += 5

        # Add top organizations
        for org_name, count in found_orgs.most_common(5):
            org_id = f"org_{abs(hash(org_name)) % 100000}"
            if org_id not in nodes_dict:
                nodes_dict[org_id] = {
                    "id": org_id,
                    "name": org_name,
                    "type": "organization",
                    "val": min(32, 20 + count * 2),
                    "details": "مؤسسة / جامعة أكاديمية مرتبطة",
                    "group": "organization",
                }
                add_link(root_id, org_id, "ينتمي إلى / جهة أكاديمية", weight=0.95)

        # 3. Extract Associated People / Colleagues
        # Regex for doctors, professors, researchers mentioned
        people_pattern = r'(?:الدكتور|دكتور|د\.|أستاذ|الاستاذ|أ\.د|الباحث|المهندس|البروفيسور|Dr\.|Prof\.)\s+([\u0600-\u06FF]{3,16}(?:\s+[\u0600-\u06FF]{3,16}){1,3})'
        
        medical_noise = {
            "أنف", "اذن", "أذن", "حنجرة", "حنجره", "باطنة", "باطنه", "أسنان", "اسنان", "طوارئ",
            "طوارىء", "عملية", "عمليه", "جراحة", "جراحه", "عيادة", "عياده", "مركز", "مستشفى",
            "تخصص", "حجز", "تقييم", "كشف", "استشارة", "استشاره", "دليل", "موقع", "صفحة",
            "تفاصيل", "عرض", "داخل", "جديد", "سعر", "مدينة", "شارع", "محافظة"
        }

        for match in re.finditer(people_pattern, combined_text):
            p_name = match.group(1).strip()
            # Exclude if it's the root person themselves
            clean_seed = re.sub(r'^(?:دكتور|الدكتور|د\.|أستاذ|الاستاذ|أ\.د)\s+', '', seed_topic).strip()
            if p_name not in clean_seed and clean_seed not in p_name and len(p_name.split()) >= 2:
                # Exclude medical noise words and stop words
                words = p_name.split()
                if not any(w in medical_noise for w in words):
                    if not any(stop in p_name for stop in ["جامعة", "كلية", "قسم", "محافظة", "العراق", "مدينة"]):
                        found_people[p_name] += 1

        # Add top connected people
        for p_name, count in found_people.most_common(6):
            p_id = f"person_{abs(hash(p_name)) % 100000}"
            if p_id not in nodes_dict:
                nodes_dict[p_id] = {
                    "id": p_id,
                    "name": f"د. {p_name}",
                    "type": "person",
                    "val": min(28, 16 + count * 2),
                    "details": "باحث مشارك / زميل أكاديمي تم رصده في الأوراق والمنشورات",
                    "group": "person",
                }
                add_link(root_id, p_id, "زميل / باحث مشارك", weight=0.85)
                # Link person with the top organization if present
                for org_id, org_node in list(nodes_dict.items()):
                    if org_node["type"] == "organization":
                        add_link(p_id, org_id, "هيئة التدريس", weight=0.6)
                        break

        # 4. Extract Key Concepts & Research Domains from Terms
        generic_stopwords = {
            "الشرقية", "عملية", "الأذن", "طلب", "الجامعة", "خدمات", "معلومات", "تواصل", "الرئيسية",
            "دليل", "حجز", "طعام", "مطاعم", "شرح", "صفحة", "موقع", "تحميل", "بحث", "دخول",
            "تسجيل", "اخبار", "فيديو", "صور", "ar", "en", "http", "https", "com", "net", "org"
        }

        top_concepts = []
        for t in terms:
            clean_t = re.sub(r'^(?:ar:|en:)', '', t.term).strip()
            if len(clean_t) >= 4 and clean_t not in generic_stopwords and clean_t not in seed_topic:
                top_concepts.append((clean_t, t.frequency))

        # Deduplicate and pick top 10 concepts
        seen_concepts = set()
        for c_name, freq in top_concepts:
            if len(seen_concepts) >= 10:
                break
            if c_name in seen_concepts:
                continue
            seen_concepts.add(c_name)

            c_id = f"concept_{abs(hash(c_name)) % 100000}"
            if c_id not in nodes_dict:
                nodes_dict[c_id] = {
                    "id": c_id,
                    "name": c_name,
                    "type": "concept",
                    "val": min(24, 14 + int(freq)),
                    "details": f"مفهوم ومجال بحثي مستخلص (تكرار: {freq})",
                    "group": "concept",
                }
                add_link(root_id, c_id, "مجال بحثي وتخصص", weight=0.75)

        # 5. Extract Publications / Articles
        for s in sources[:6]:
            if s.title and len(s.title) > 6 and s.title != seed_topic:
                pub_id = f"pub_{abs(hash(s.url)) % 100000}"
                short_title = s.title.split("-")[0].split("|")[0].strip()
                if len(short_title) > 35:
                    short_title = short_title[:35] + "..."
                if pub_id not in nodes_dict:
                    nodes_dict[pub_id] = {
                        "id": pub_id,
                        "name": short_title,
                        "type": "publication",
                        "val": 18,
                        "details": f"ورقة علمية / مصدر موثق: {s.domain}",
                        "url": s.url,
                        "group": "publication",
                    }
                    add_link(root_id, pub_id, "ورقة علمية / مصدر", weight=0.8)

        # 6. Build NetworkX graph to compute PageRank & Centrality layout
        nx_graph = nx.Graph()
        for nid in nodes_dict:
            nx_graph.add_node(nid)
        for link in links_list:
            nx_graph.add_edge(link["source"], link["target"], weight=link.get("weight", 1.0))

        # Compute PageRank & Degree
        pagerank_dict = nx.pagerank(nx_graph, weight="weight") if len(nx_graph) > 0 else {}

        for nid, node in nodes_dict.items():
            deg = nx_graph.degree(nid) if nid in nx_graph else 1
            node["degree"] = deg
            node["pagerank"] = round(pagerank_dict.get(nid, 0.05), 3)

        # Compute initial 2D coordinates using spring layout
        try:
            pos = nx.spring_layout(nx_graph, k=0.45, iterations=40, seed=42)
            for nid, (px, py) in pos.items():
                # Normalize from [-1, 1] to [0.08, 0.92]
                nodes_dict[nid]["x"] = round((px + 1.0) / 2.0 * 0.84 + 0.08, 3)
                nodes_dict[nid]["y"] = round((py + 1.0) / 2.0 * 0.84 + 0.08, 3)
        except Exception:
            pass

        # Set root dead center
        if root_id in nodes_dict:
            nodes_dict[root_id]["x"] = 0.50
            nodes_dict[root_id]["y"] = 0.50

        nodes_list = list(nodes_dict.values())

        return {
            "session_id": self.session_id,
            "seed_topic": seed_topic,
            "entity_type": "person" if is_person_query else "topic",
            "stats": {
                "total_nodes": len(nodes_list),
                "total_edges": len(links_list),
                "people_count": sum(1 for n in nodes_list if n["type"] == "person" and not n.get("is_root")),
                "orgs_count": sum(1 for n in nodes_list if n["type"] == "organization"),
                "concepts_count": sum(1 for n in nodes_list if n["type"] == "concept"),
                "publications_count": sum(1 for n in nodes_list if n["type"] == "publication"),
                "density": round(nx.density(nx_graph) if len(nx_graph) > 1 else 0.0, 3)
            },
            "nodes": nodes_list,
            "edges": links_list,
            "categories": [
                {"id": "all", "label": "الكل", "color": "#94a3b8"},
                {"id": "person", "label": "الأشخاص والزملاء", "color": "#10b981"},
                {"id": "organization", "label": "المؤسسات والجامعات", "color": "#a855f7"},
                {"id": "concept", "label": "المفاهيم والتخصصات", "color": "#38bdf8"},
                {"id": "publication", "label": "الأبحاث والمنشورات", "color": "#f43f5e"},
            ]
        }

    def build_graph(self) -> nx.DiGraph:
        """Query the database and populate the NetworkX DiGraph (backwards-compatible)."""
        self.graph.clear()
        topics = get_topics_by_session(self.session_id)
        for topic in topics:
            self.graph.add_node(
                topic.name,
                depth=topic.depth,
                relevance=topic.relevance_score,
                status=topic.status,
            )
        edges = get_edges_by_session(self.session_id)
        for edge in edges:
            if edge.from_topic and edge.to_topic:
                self.graph.add_edge(edge.from_topic, edge.to_topic, weight=edge.weight)
        return self.graph

    def get_central_topics(self, top_n: int = 5) -> list[tuple[str, float]]:
        """Calculate PageRank to find the most central topics."""
        if self.graph.number_of_nodes() == 0:
            self.build_graph()
        if self.graph.number_of_nodes() == 0:
            return []
        try:
            pagerank = nx.pagerank(self.graph, weight="weight")
            sorted_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)
            return sorted_nodes[:top_n]
        except Exception:
            return []

    def get_graph_summary(self) -> dict:
        """Return rich graph representation for visual display and statistics."""
        return self.build_rich_graph()

