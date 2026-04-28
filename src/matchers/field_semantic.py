from .patterns import SENSITIVE_KEYWORDS


class FieldSemanticMapper:
    def __init__(self):
        self.field_to_type = {}
        self._build_mapping()

    def _build_mapping(self):
        for sensitive_type, keywords in SENSITIVE_KEYWORDS.items():
            for keyword in keywords:
                self.field_to_type[keyword.lower()] = sensitive_type

    def get_semantic(self, field_name):
        if not field_name:
            return None

        field_lower = field_name.lower()

        if field_lower in self.field_to_type:
            return self.field_to_type[field_lower]

        for keyword, sensitive_type in self.field_to_type.items():
            if keyword in field_lower:
                return sensitive_type

        return None

    def is_compatible(self, field_name, detected_type):
        semantic = self.get_semantic(field_name)
        if semantic is None:
            return True
        return semantic == detected_type

    def get_confidence_boost(self, field_name, detected_type):
        semantic = self.get_semantic(field_name)
        if semantic is None:
            return 1.0
        if semantic == detected_type:
            return 2.0
        return 0.5


field_semantic_mapper = FieldSemanticMapper()
