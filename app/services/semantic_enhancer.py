# app/services/semantic_enhancer.py
class SemanticEnhancer:
    def __init__(self):
        self.synonyms = {
            "main branch": ["main campus", "central campus", "primary location"],
            "fees": ["tuition", "costs", "payment", "charges"],
            "dorm": ["housing", "residence", "accommodation", "dormitory"],
            "prof": ["professor", "teacher", "instructor", "faculty"],
            "class": ["course", "lecture", "session", "module"],
            "apply": ["application", "admission", "enroll"],
            "visa": ["immigration", "student visa", "permit"]
        }

    def expand_query(self, query: str) -> list:
        """Generate synonym variations of the query"""
        expanded = [query]
        query_lower = query.lower()
        for key, synonyms in self.synonyms.items():
            if key in query_lower:
                for synonym in synonyms:
                    new_query = query_lower.replace(key, synonym)
                    expanded.append(new_query)
        return expanded