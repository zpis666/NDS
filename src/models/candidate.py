from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Candidate:
    db_type: str
    db_name: str
    table_name: str
    field_name: str
    record_id: str
    sensitive_type: str
    extracted_value: str

    sensitive_level: str = 'L1'
    data_form: str = 'structured'
    confidence: float = 1.0
    field_semantic: Optional[str] = None

    @property
    def key(self):
        return (
            self.db_type,
            self.db_name,
            self.table_name,
            self.field_name,
            self.record_id,
            self.sensitive_type,
            self.extracted_value
        )

    def to_csv_row(self):
        return [
            self.db_type,
            self.db_name,
            self.table_name,
            self.field_name,
            self.record_id,
            self.data_form,
            self.sensitive_type,
            self.sensitive_level,
            self.extracted_value
        ]

    def __eq__(self, other):
        if not isinstance(other, Candidate):
            return False
        return self.key == other.key

    def __hash__(self):
        return hash(self.key)
