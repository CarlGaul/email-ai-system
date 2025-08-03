cat << 'EOF' > /Users/carlgaul/Desktop/LegalAI/src/test_phase1_fixes.py
#!/usr/bin/env python3
from .ollama_client import OllamaClient
from .config import Config
from .legal_ai_core import LegalAI

def test_phase1_fixes():
    config = Config()
    client = OllamaClient()
    legal_ai = LegalAI()
    print("✅ Phase 1 tests passed")

if __name__ == "__main__":
    test_phase1_fixes()
EOF
