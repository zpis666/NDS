from typing import List
from models.candidate import Candidate
from .normalizer import Normalizer
from .dedup import Deduplicator
from .suppressor import Suppressor
from .semantic_cleaner import SemanticCleaner
from .csv_writer import CsvWriter


class ExportPipeline:
    def __init__(self):
        self.normalizer = Normalizer()
        self.deduplicator = Deduplicator()
        self.suppressor = Suppressor()
        self.semantic_cleaner = SemanticCleaner()
        self.csv_writer = CsvWriter()

    def run(self, candidates: List[Candidate]) -> List[Candidate]:
        results = candidates

        results = self.normalizer.normalize(results)

        results = self.deduplicator.deduplicate(results)

        results = self.suppressor.suppress(results)

        results = self.semantic_cleaner.clean(results)

        results = self.deduplicator.deduplicate_cross_type(results)

        return results

    def export(self, candidates: List[Candidate], output_path: str):
        results = self.run(candidates)
        self.csv_writer.write_with_stats(results, output_path)
        return results
