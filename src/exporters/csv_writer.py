import csv
import os
from typing import List
from models.candidate import Candidate


class CsvWriter:
    HEADERS = [
        'db_type',
        'db_name',
        'table_name',
        'field_name',
        'record_id',
        'data_form',
        'sensitive_type',
        'sensitive_level',
        'extracted_value'
    ]

    def write(self, candidates: List[Candidate], output_path: str):
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADERS)

            for candidate in candidates:
                writer.writerow(candidate.to_csv_row())

    def write_with_stats(self, candidates: List[Candidate], output_path: str):
        self.write(candidates, output_path)

        stats = self._calculate_stats(candidates)
        print(f"输出统计:")
        print(f"  总记录数: {stats['total']}")
        print(f"  按数据形态:")
        for form, count in stats['by_form'].items():
            print(f"    {form}: {count}")
        print(f"  按敏感类型:")
        for s_type, count in stats['by_type'].items():
            print(f"    {s_type}: {count}")

    def _calculate_stats(self, candidates: List[Candidate]) -> dict:
        stats = {
            'total': len(candidates),
            'by_form': {},
            'by_type': {},
            'by_level': {}
        }

        for candidate in candidates:
            stats['by_form'][candidate.data_form] = stats['by_form'].get(candidate.data_form, 0) + 1
            stats['by_type'][candidate.sensitive_type] = stats['by_type'].get(candidate.sensitive_type, 0) + 1
            stats['by_level'][candidate.sensitive_level] = stats['by_level'].get(candidate.sensitive_level, 0) + 1

        return stats
