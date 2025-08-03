import sys
import os

# Read current main.py
with open("src/main.py", "r") as f:
    content = f.read()

# Check if already integrated
if "document_uploader" in content:
    print("✅ Already integrated!")
    sys.exit(0)

# Find import section
import_line = content.find("from legal_ai_core import LegalAI")
if import_line == -1:
    print("❌ Could not find import section")
    sys.exit(1)

# Add import after that line
end_of_line = content.find("\n", import_line)
new_import = "\nfrom document_uploader import DocumentUploader"
content = content[:end_of_line] + new_import + content[end_of_line:]

# Find session state initialization
session_line = content.find("if 'legal_ai' not in st.session_state:")
if session_line != -1:
    # Find the line with LegalAI()
    legal_ai_line = content.find("LegalAI()", session_line)
    if legal_ai_line != -1:
        end_line = content.find("\n", legal_ai_line)
        new_init = "\n        st.session_state.document_uploader = DocumentUploader()"
        content = content[:end_line] + new_init + content[end_line:]

# Write updated file
with open("src/main.py", "w") as f:
    f.write(content)

print("✅ Integration complete!")
