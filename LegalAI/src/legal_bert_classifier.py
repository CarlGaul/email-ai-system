#!/usr/bin/env python3
import torch
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import time
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️ Transformers not installed. Install with: pip3 install transformers torch")

try:
    import coremltools as ct
    COREML_AVAILABLE = True
except ImportError:
    COREML_AVAILABLE = False

try:
    from config import Config
except ImportError:
    # Fallback configuration if config module not available
    class Config:
        ENABLE_COREML_LEGAL_BERT = True
        LEGAL_BERT_MODEL = "nlpaueb/legal-bert-base-uncased"
        LEGAL_BERT_CONFIDENCE_THRESHOLD = 0.75
        ENABLE_METAL_ACCELERATION = True

logger = logging.getLogger(__name__)

class LegalBERTClassifier:
    """Legal-BERT document classifier with Core ML acceleration"""
    
    def __init__(self, use_coreml: bool = None):
        """Initialize Legal-BERT classifier"""
        self.use_coreml = use_coreml if use_coreml is not None else Config.ENABLE_COREML_LEGAL_BERT
        self.model_name = Config.LEGAL_BERT_MODEL
        self.confidence_threshold = Config.LEGAL_BERT_CONFIDENCE_THRESHOLD
        
        # Legal document categories for pregnancy discrimination
        self.categories = [
            "pregnancy_discrimination_termination",
            "pregnancy_discrimination_hiring", 
            "pregnancy_discrimination_accommodation",
            "pregnancy_discrimination_benefits",
            "pregnancy_discrimination_harassment",
            "pregnancy_discrimination_retaliation",
            "general_employment_law",
            "civil_rights_law",
            "medical_malpractice",
            "other_legal_matter"
        ]
        
        self.tokenizer = None
        self.model = None
        self.coreml_model = None
        
        # Initialize models
        self._load_models()
    
    def _load_models(self):
        """Load Legal-BERT models"""
        if not TRANSFORMERS_AVAILABLE:
            logger.error("Transformers library not available")
            print("❌ Transformers not installed. Falling back to rule-based classification.")
            return False
        
        try:
            print("🔄 Loading Legal-BERT tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Try to load Core ML model first
            if self.use_coreml and COREML_AVAILABLE:
                coreml_path = Path("models/legal_bert_coreml.mlmodel")
                if coreml_path.exists():
                    print("🚀 Loading Core ML Legal-BERT model...")
                    try:
                        self.coreml_model = ct.models.MLModel(str(coreml_path))
                        print("✅ Core ML Legal-BERT loaded successfully")
                        return True
                    except Exception as e:
                        print(f"⚠️ Core ML loading failed: {e}")
                        print("📥 Falling back to PyTorch model...")
            
            # Load PyTorch model
            print("🔄 Loading PyTorch Legal-BERT model...")
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                num_labels=len(self.categories)
            )
            
            # Use Metal acceleration if available
            if Config.ENABLE_METAL_ACCELERATION and torch.backends.mps.is_available():
                self.model = self.model.to("mps")
                print("🚀 Legal-BERT using Metal acceleration")
            
            print("✅ Legal-BERT loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load Legal-BERT: {e}")
            print(f"⚠️ Legal-BERT loading failed: {e}")
            print("📥 Using fallback rule-based classification")
            return False
    
    def classify_document(self, text: str, max_length: int = 512) -> Dict[str, Any]:
        """Classify legal document with confidence scoring"""
        if not self.tokenizer or not TRANSFORMERS_AVAILABLE:
            return self._fallback_classification(text)
        
        try:
            start_time = time.time()
            
            # Tokenize input
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=max_length,
                padding=True
            )
            
            # Run inference
            if self.coreml_model:
                # Core ML inference
                outputs = self._coreml_inference(inputs)
            elif self.model:
                # PyTorch inference
                outputs = self._pytorch_inference(inputs)
            else:
                return self._fallback_classification(text)
            
            # Process results
            probabilities = torch.softmax(outputs, dim=1)
            confidence, predicted_idx = torch.max(probabilities, dim=1)
            
            predicted_category = self.categories[predicted_idx.item()]
            confidence_score = confidence.item()
            
            processing_time = time.time() - start_time
            
            return {
                "category": predicted_category,
                "confidence": confidence_score,
                "all_probabilities": {
                    cat: prob.item() for cat, prob in zip(self.categories, probabilities[0])
                },
                "processing_time": processing_time,
                "model_used": "coreml" if self.coreml_model else "pytorch",
                "meets_threshold": confidence_score >= self.confidence_threshold
            }
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return self._fallback_classification(text, error=str(e))
    
    def _pytorch_inference(self, inputs):
        """Run PyTorch inference"""
        if Config.ENABLE_METAL_ACCELERATION and torch.backends.mps.is_available():
            inputs = {k: v.to("mps") for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        return outputs.logits
    
    def _coreml_inference(self, inputs):
        """Run Core ML inference"""
        # Convert to numpy for Core ML
        input_ids = inputs["input_ids"].numpy()
        
        # Core ML prediction
        coreml_outputs = self.coreml_model.predict({"input_ids": input_ids})
        
        # Convert back to torch tensor
        return torch.tensor(coreml_outputs["logits"])
    
    def _fallback_classification(self, text: str, error: str = None) -> Dict[str, Any]:
        """Fallback classification using rule-based approach"""
        text_lower = text.lower()
        
        # Simple keyword-based classification for pregnancy discrimination
        if any(keyword in text_lower for keyword in ["termination", "fired", "dismissed", "terminate"]):
            category = "pregnancy_discrimination_termination"
            confidence = 0.7
        elif any(keyword in text_lower for keyword in ["hiring", "interview", "application", "recruit"]):
            category = "pregnancy_discrimination_hiring" 
            confidence = 0.7
        elif any(keyword in text_lower for keyword in ["accommodation", "light duty", "modified", "restrict"]):
            category = "pregnancy_discrimination_accommodation"
            confidence = 0.7
        elif any(keyword in text_lower for keyword in ["benefits", "insurance", "leave", "fmla"]):
            category = "pregnancy_discrimination_benefits"
            confidence = 0.7
        elif any(keyword in text_lower for keyword in ["harassment", "hostile environment", "hostile"]):
            category = "pregnancy_discrimination_harassment"
            confidence = 0.7
        elif any(keyword in text_lower for keyword in ["retaliation", "adverse action", "retaliate"]):
            category = "pregnancy_discrimination_retaliation"
            confidence = 0.7
        elif any(keyword in text_lower for keyword in ["pregnancy", "pregnant", "maternity", "prenatal"]):
            category = "pregnancy_discrimination_termination"  # Default pregnancy category
            confidence = 0.6
        elif any(keyword in text_lower for keyword in ["employment", "workplace", "employer"]):
            category = "general_employment_law"
            confidence = 0.5
        else:
            category = "other_legal_matter"
            confidence = 0.4
        
        return {
            "category": category,
            "confidence": confidence,
            "all_probabilities": {},
            "processing_time": 0.001,
            "model_used": "fallback",
            "meets_threshold": confidence >= self.confidence_threshold,
            "error": error
        }

def test_legal_bert():
    """Test Legal-BERT classifier"""
    print("🧪 Testing Legal-BERT Classifier")
    print("-" * 40)
    
    classifier = LegalBERTClassifier()
    
    # Test cases
    test_cases = [
        "Employee was terminated after announcing pregnancy to supervisor during team meeting.",
        "Company refused to provide light duty work for pregnant employee with lifting restrictions.",
        "Pregnant worker denied health insurance benefits during maternity leave period.",
        "Hospital discriminated against nurse during hiring process due to pregnancy status.",
        "Employer retaliated against employee for filing pregnancy discrimination complaint.",
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {test_case[:60]}...")
        result = classifier.classify_document(test_case)
        
        print(f"   Category: {result['category']}")
        print(f"   Confidence: {result['confidence']:.3f}")
        print(f"   Model: {result['model_used']}")
        print(f"   Time: {result['processing_time']:.3f}s")
        print(f"   Meets threshold: {'✅' if result['meets_threshold'] else '❌'}")

if __name__ == "__main__":
    test_legal_bert()
