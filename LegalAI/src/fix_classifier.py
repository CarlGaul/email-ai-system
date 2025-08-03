import fileinput
import sys

# Read the file and fix the patterns
with open('src/court_classifier.py', 'r') as f:
    content = f.read()

# Fix the slip op classification logic
old_pattern = """        # Default rules for ambiguous citations
        if '(U)' in citation:
            return 'supreme_court'
        elif 'Dept' in citation or 'Department' in citation:
            return 'appellate_division'
        elif re.match(r'\\d{4}\\s+NY\\s+Slip\\s+Op\\s+\\d{5}$', citation.strip()):
            # Five digits with no parenthetical = Court of Appeals
            return 'court_of_appeals'"""

new_pattern = """        # Default rules for ambiguous citations
        if '(U)' in citation:
            return 'supreme_court'
        elif 'Dept' in citation or 'Department' in citation:
            return 'appellate_division'
        elif re.match(r'\\d{4}\\s+NY\\s+Slip\\s+Op\\s+0\\d{4}$', citation.strip()):
            # Five digits starting with 0 (like 08158, 02768) = often appellate or mixed
            # Need to check content to be sure
            return None
        elif re.match(r'\\d{4}\\s+NY\\s+Slip\\s+Op\\s+[1-9]\\d{4}$', citation.strip()):
            # Five digits not starting with 0 = likely Supreme Court
            return 'supreme_court'"""

content = content.replace(old_pattern, new_pattern)

# Write back
with open('src/court_classifier.py', 'w') as f:
    f.write(content)

print("✅ Fixed classifier patterns")
