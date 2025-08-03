#!/usr/bin/env python3
from .config import Config
from .confidence_document_manager import ConfidenceDocumentManager

class DocumentReviewSystem:
def init(self):
self.config = Config()
self.doc_manager = ConfidenceDocumentManager()
