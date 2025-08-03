import re
import os
import shutil
from pathlib import Path
from typing import Dict, Tuple, Optional, List
import logging

class ImprovedCourtClassifier:
    def __init__(self):
        """Initialize improved court classification patterns"""
        
        # NY Slip Op patterns - VERY specific to avoid misclassification
        self.slip_op_patterns = {
            'court_of_appeals': [
                # NY Court of Appeals has very specific citation formats
                r'\d{4}\s+NY\s+Slip\s+Op\s+\d{5}(?!\s*\()',  # No parenthetical = Court of Appeals
                r'Court of Appeals.*State of New York',
                r'Court of Appeals\s+of\s+New York',
                r'NEW YORK COURT OF APPEALS'
            ],
            
            'appellate_division': [
                # Appellate Division always has department in parentheses
                r'\d{4}\s+NY\s+Slip\s+Op\s+\d+\s*\([^)]*Dept',
                r'Appellate Division.*Department',
                r'App(?:\.|ellate)?\s*Div(?:\.|ision)?.*(?:First|1st|Second|2nd|Third|3rd|Fourth|4th)\s*Dep',
                r'APPELLATE DIVISION.*DEPARTMENT',
                r'AD3d',
                r'\d+\s+A\.D\.3d\s+\d+'
            ],
            
            'supreme_court': [
                # Supreme Court has (U) for unpublished or county names
                r'\d{4}\s+NY\s+Slip\s+Op\s+\d+\s*\(\s*U\s*\)',  # Unpublished
                r'\d{4}\s+NY\s+Slip\s+Op\s+\d+\s*\([^)]*Sup\s*Ct',
                r'Supreme Court.*County',
                r'Sup(?:\.|reme)?\s*C(?:our)?t\.?(?!.*App)',  # Not appellate
                r'SUPREME COURT.*COUNTY',
                r'Misc\.?\s*3d',
                r'\d+\s+Misc\.3d\s+\d+'
            ]
        }
        
        # Document header patterns - check first few pages
        self.header_patterns = {
            'court_of_appeals': [
                r'Court of Appeals\s+of\s+(?:the\s+)?State of New York',
                r'NEW YORK COURT OF APPEALS',
                r'In the Court of Appeals'
            ],
            
            'appellate_division': [
                r'Supreme Court.*Appellate Division',
                r'APPELLATE DIVISION.*JUDICIAL DEPARTMENT',
                r'Appellate Division.*Department',
                r'AD\s+(?:First|Second|Third|Fourth)'
            ],
            
            'supreme_court': [
                r'Supreme Court.*State of New York',
                r'SUPREME COURT.*COUNTY',
                r'Supreme Court.*County.*State of New York',
                r'At.*Term.*Supreme Court'
            ],
            
            'civil_court': [
                r'Civil Court.*City of New York',
                r'CIVIL COURT.*COUNTY',
                r'Housing Court'
            ]
        }
        
        # Federal court patterns
        self.federal_patterns = {
            'us_supreme_court': [
                r'Supreme Court of the United States',
                r'U\.S\.\s+\d+',
                r'\d+\s+S\.\s*Ct\.'
            ],
            
            'second_circuit': [
                r'United States Court of Appeals.*Second Circuit',
                r'\d+\s+F\.3d\s+\d+.*\(2d Cir',
                r'USCA2',
                r'U\.S\.C\.A\..*Second Circuit'
            ],
            
            'sdny': [
                r'Southern District of New York',
                r'S\.D\.N\.Y\.',
                r'\d+\s+F\.\s*Supp\..*S\.D\.N\.Y'
            ],
            
            'edny': [
                r'Eastern District of New York',
                r'E\.D\.N\.Y\.',
                r'\d+\s+F\.\s*Supp\..*E\.D\.N\.Y'
            ]
        }
        
        self.logger = logging.getLogger(__name__)
    
    def classify_document(self, file_path: str, content: str = None) -> Tuple[str, float]:
        """
        Classify a legal document by court with improved accuracy
        """
        if content is None:
            content = self._extract_text(file_path)
        
        filename = os.path.basename(file_path)
        
        # First check: NY Slip Op in filename (most reliable)
        slip_op_match = re.search(r'(\d{4}\s+NY\s+Slip\s+Op\s+\d+(?:\s*\([^)]*\))?)', filename)
        if slip_op_match:
            citation = slip_op_match.group(1)
            court_type = self._classify_by_slip_op(citation)
            if court_type:
                # Verify with content if possible
                if content:
                    verified = self._verify_classification(court_type, content)
                    if verified:
                        return court_type, 0.95
                else:
                    return court_type, 0.85
        
        # Second check: Document headers (first 2000 chars)
        header_text = content[:2000] if content else ""
        header_classification = self._classify_by_headers(header_text)
        if header_classification[0] != 'unknown':
            return header_classification
        
        # Third check: Full content analysis
        if content:
            return self._classify_by_content(content, filename)
        
        return 'unknown', 0.0
    
    def _classify_by_slip_op(self, citation: str) -> Optional[str]:
        """Classify based on NY Slip Op citation format"""
        
        # Check each pattern type
        for court_type, patterns in self.slip_op_patterns.items():
            for pattern in patterns:
                if re.search(pattern, citation, re.IGNORECASE):
                    return court_type
        
        # Default rules for ambiguous citations
        if '(U)' in citation:
            return 'supreme_court'
        elif 'Dept' in citation or 'Department' in citation:
            return 'appellate_division'
        elif re.match(r'\d{4}\s+NY\s+Slip\s+Op\s+0\d{4}$', citation.strip()):
            # Five digits starting with 0 (like 08158, 02768) = often appellate or mixed
            # Need to check content to be sure
            return None
        elif re.match(r'\d{4}\s+NY\s+Slip\s+Op\s+[1-9]\d{4}$', citation.strip()):
            # Five digits not starting with 0 = likely Supreme Court
            return 'supreme_court'
        
        return None
    
    def _classify_by_headers(self, header_text: str) -> Tuple[str, float]:
        """Classify by document headers"""
        
        scores = {}
        
        # Check federal patterns first (higher priority)
        for court_type, patterns in self.federal_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, header_text, re.IGNORECASE):
                    score += 10
            if score > 0:
                scores[court_type] = score
        
        # Then check state patterns
        for court_type, patterns in self.header_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, header_text, re.IGNORECASE))
                score += matches * 5
            if score > 0:
                scores[court_type] = score
        
        if scores:
            best_match = max(scores.items(), key=lambda x: x[1])
            confidence = min(best_match[1] / 20.0, 1.0)
            return best_match[0], confidence
        
        return 'unknown', 0.0
    
    def _classify_by_content(self, content: str, filename: str) -> Tuple[str, float]:
        """Full content analysis"""
        
        scores = {}
        
        # Combine all pattern dictionaries
        all_patterns = {
            **self.slip_op_patterns,
            **self.header_patterns,
            **self.federal_patterns
        }
        
        for court_type, patterns in all_patterns.items():
            score = 0
            pattern_matches = 0
            
            for pattern in patterns:
                content_matches = len(re.findall(pattern, content[:5000], re.IGNORECASE))
                filename_matches = len(re.findall(pattern, filename, re.IGNORECASE))
                
                if content_matches > 0:
                    score += content_matches * 2
                    pattern_matches += 1
                
                if filename_matches > 0:
                    score += filename_matches * 3
            
            # Bonus for multiple different patterns matching
            if pattern_matches > 2:
                score *= 1.5
            
            scores[court_type] = score
        
        if scores:
            # Get best match
            best_match = max(scores.items(), key=lambda x: x[1])
            
            # Check for close competitors
            if len(sorted_scores) > 1 and sorted_scores[0][1] > 0:
                if sorted_scores[1][1] / sorted_scores[0][1] > 0.8:
                    # Close match - use additional heuristics
                    return self._disambiguate_courts(sorted_scores[:2], content)
            
            confidence = min(best_match[1] / 20.0, 1.0)
            return best_match[0], confidence
        
        return 'unknown', 0.0
    
    def _disambiguate_courts(self, top_matches: List[Tuple[str, float]], content: str) -> Tuple[str, float]:
        """Disambiguate between similar scoring courts"""
        
        court1, score1 = top_matches[0]
        court2, score2 = top_matches[1]
        
        # Special rules for NY courts
        if {court1, court2} == {'court_of_appeals', 'supreme_court'}:
            # Look for definitive markers
            if re.search(r'Court of Appeals\s+of\s+(?:the\s+)?State of New York', content, re.IGNORECASE):
                return 'court_of_appeals', 0.95
            elif re.search(r'County.*State of New York', content, re.IGNORECASE):
                return 'supreme_court', 0.95
        
        elif {court1, court2} == {'appellate_division', 'supreme_court'}:
            # Appellate Division has departments
            if re.search(r'(?:First|Second|Third|Fourth)\s+Department', content, re.IGNORECASE):
                return 'appellate_division', 0.95
        
        # Default to higher score with reduced confidence
        return court1, 0.7
    
    def _verify_classification(self, court_type: str, content: str) -> bool:
        """Verify classification with content check"""
        
        verification_patterns = {
            'court_of_appeals': [
                r'Court of Appeals.*State of New York',
                r'Albany.*New York'  # Court of Appeals is in Albany
            ],
            'appellate_division': [
                r'Appellate Division',
                r'(?:First|Second|Third|Fourth)\s+Department'
            ],
            'supreme_court': [
                r'Supreme Court.*County',
                r'Trial Term'
            ]
        }
        
        if court_type in verification_patterns:
            for pattern in verification_patterns[court_type]:
                if re.search(pattern, content[:2000], re.IGNORECASE):
                    return True
        
        return False
    
    def _extract_text(self, file_path: str) -> str:
        """Extract text from PDF or text file"""
        try:
            if file_path.endswith('.pdf'):
                try:
                    from PyPDF2 import PdfReader
                    reader = PdfReader(file_path)
                    text = ""
                    # Read first 3 pages for classification
                    for i, page in enumerate(reader.pages[:3]):
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n--- Page {i+1} ---\n"
                            text += page_text
                    return text
                except Exception as e:
                    self.logger.error(f"Error reading PDF {file_path}: {e}")
                    return ""
            elif file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()[:5000]
        except Exception as e:
            self.logger.error(f"Error extracting text from {file_path}: {e}")
        
        return ""
    
    def organize_document(self, source_path: str, base_dir: str = "database/cases") -> str:
        """
        Classify and move document to appropriate directory
        """
        court_type, confidence = self.classify_document(source_path)
        
        # Log classification
        filename = os.path.basename(source_path)
        self.logger.info(f"Classified {filename} as {court_type} (confidence: {confidence:.2f})")
        
        # Don't move if confidence is too low
        if confidence < 0.5:
            print(f"⚠️  Low confidence ({confidence:.2f}) for {filename}")
            print(f"   Suggested: {court_type}, but keeping in current location")
            return source_path
        
        # Determine jurisdiction
        if court_type in ['us_supreme_court', 'second_circuit', 'sdny', 'edny']:
            jurisdiction = 'federal'
        else:
            jurisdiction = 'nys'
        
        # Create target directory
        target_dir = Path(base_dir) / jurisdiction / court_type
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate target path
        target_path = target_dir / filename
        
        # Handle duplicates
        if target_path.exists():
            counter = 1
            while target_path.exists():
                stem = target_path.stem
                suffix = target_path.suffix
                target_path = target_path.parent / f"{stem}_{counter}{suffix}"
                counter += 1
        
        # Move or copy file
        try:
            shutil.move(str(source_path), str(target_path))
            print(f"✅ Moved {filename}")
            print(f"   Court: {court_type} (confidence: {confidence:.2f})")
            print(f"   Location: {target_path}")
        except Exception as e:
            self.logger.error(f"Error moving file: {e}")
            print(f"❌ Error moving {filename}: {e}")
            return source_path
        
        return str(target_path)
    
    def batch_classify_directory(self, directory: str, dry_run: bool = True) -> Dict[str, List[Dict]]:
        """
        Classify all documents in a directory and show results
        """
        results = {
            'correct': [],
            'incorrect': [],
            'unknown': []
        }
        
        if not os.path.exists(directory):
            print(f"Directory not found: {directory}")
            return results
        
        print(f"\n🔍 Analyzing documents in: {directory}")
        print("=" * 70)
        
        files = [f for f in os.listdir(directory) if f.endswith('.pdf')]
        
        for filename in sorted(files):
            file_path = os.path.join(directory, filename)
            court_type, confidence = self.classify_document(file_path)
            
            # Determine if classification seems correct based on directory
            current_court = os.path.basename(directory)
            is_correct = (court_type == current_court)
            
            result = {
                'filename': filename,
                'classified_as': court_type,
                'confidence': confidence,
                'current_location': current_court
            }
            
            if court_type == 'unknown':
                results['unknown'].append(result)
                status = "❓"
            elif is_correct or confidence < 0.5:
                results['correct'].append(result)
                status = "✅"
            else:
                results['incorrect'].append(result)
                status = "⚠️ "
            
            print(f"{status} {filename[:60]}")
            print(f"   Classification: {court_type} (confidence: {confidence:.3f})")
            
            if not is_correct and confidence >= 0.5:
                print(f"   📍 Should move from {current_court} → {court_type}")
            
            print()
        
        # Summary
        print("\n📊 Classification Summary")
        print("=" * 70)
        print(f"✅ Correctly classified: {len(results['correct'])}")
        print(f"⚠️  Potentially misplaced: {len(results['incorrect'])}")
        print(f"❓ Unknown/Low confidence: {len(results['unknown'])}")
        
        if not dry_run and results['incorrect']:
            print("\n🚀 Moving misclassified documents...")
            for item in results['incorrect']:
                if item['confidence'] >= 0.5:
                    source = os.path.join(directory, item['filename'])
                    self.organize_document(source)
        
        return results

# Alias for backwards compatibility
EnhancedCourtClassifier = ImprovedCourtClassifier

def test_improved_classifier():
    """Test the improved court classifier"""
    classifier = ImprovedCourtClassifier()
    
    # Test cases with known classifications
    test_cases = [
        # filename, expected_court
        ("Golston-Green v City of New York (2020 NY Slip Op 02768).pdf", "appellate_division"),
        ("Carbonara v Bank of N.Y. Mellon Corp. (2014 NY Slip Op 51135(U)).pdf", "supreme_court"),
        ("Castillo v Montefiore Med. Ctr. (2017 NY Slip Op 07769).pdf", "appellate_division"),
        ("Coronado v Weill Cornell Med. Coll. (2019 NY Slip Op 29372).pdf", "supreme_court"),
        ("Chauca v Abraham (2017 NY Slip Op 08158).pdf", "court_of_appeals"),
    ]
    
    print("🧪 Testing Improved Court Classifier")
    print("=" * 70)
    
    for filename, expected in test_cases:
        # Test with filename only (common scenario)
        court_type, confidence = classifier.classify_document(filename, content="")
        
        status = "✅" if court_type == expected else "❌"
        print(f"{status} {filename}")
        print(f"   Expected: {expected}")
        print(f"   Got: {court_type} (confidence: {confidence:.3f})")
        print()


def analyze_all_documents():
    """Analyze all documents in the database"""
    classifier = ImprovedCourtClassifier()
    
    base_dir = "database/cases/nys"
    courts = ["supreme_court", "appellate_division", "court_of_appeals", "civil_court"]
    
    all_results = {}
    
    for court in courts:
        court_dir = os.path.join(base_dir, court)
        if os.path.exists(court_dir):
            print(f"\n{'='*70}")
            print(f"📁 Analyzing {court.replace('_', ' ').title()}")
            print(f"{'='*70}")
            
            results = classifier.batch_classify_directory(court_dir, dry_run=True)
            all_results[court] = results
    
    # Overall summary
    print(f"\n{'='*70}")
    print("📊 OVERALL SUMMARY")
    print(f"{'='*70}")
    
    total_correct = sum(len(results['correct']) for results in all_results.values())
    total_incorrect = sum(len(results['incorrect']) for results in all_results.values())
    total_unknown = sum(len(results['unknown']) for results in all_results.values())
    total_docs = total_correct + total_incorrect + total_unknown
    
    print(f"Total documents analyzed: {total_docs}")
    print(f"Correctly classified: {total_correct} ({total_correct/total_docs*100:.1f}%)")
    print(f"Potentially misplaced: {total_incorrect} ({total_incorrect/total_docs*100:.1f}%)")
    print(f"Unknown/Low confidence: {total_unknown} ({total_unknown/total_docs*100:.1f}%)")
    
    if total_incorrect > 0:
        print(f"\n⚠️  Found {total_incorrect} potentially misplaced documents.")
        print("Run with dry_run=False to automatically reorganize them.")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_improved_classifier()
        elif sys.argv[1] == "analyze":
            analyze_all_documents()
        elif sys.argv[1] == "organize":
            # Organize with actual moves
            classifier = ImprovedCourtClassifier()
            classifier.batch_classify_directory("database/cases/nys/supreme_court", dry_run=False)
    else:
        # Default: run test
        test_improved_classifier()
