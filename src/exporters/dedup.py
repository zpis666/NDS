from typing import List, Dict
from models.candidate import Candidate


class Deduplicator:
    def deduplicate(self, candidates: List[Candidate]) -> List[Candidate]:
        seen = set()
        result = []

        candidates.sort(key=lambda c: c.confidence, reverse=True)

        for candidate in candidates:
            key = candidate.key
            if key not in seen:
                seen.add(key)
                result.append(candidate)

        return result

    def deduplicate_cross_type(self, candidates: List[Candidate]) -> List[Candidate]:
        seen = {}
        result = []

        candidates.sort(key=lambda c: c.confidence, reverse=True)

        for candidate in candidates:
            value_key = (
                candidate.db_type,
                candidate.db_name,
                candidate.table_name,
                candidate.field_name,
                candidate.record_id,
                candidate.extracted_value
            )

            if value_key not in seen:
                seen[value_key] = candidate
                result.append(candidate)
            else:
                existing = seen[value_key]
                if candidate.confidence > existing.confidence:
                    result.remove(existing)
                    seen[value_key] = candidate
                    result.append(candidate)

        return result
