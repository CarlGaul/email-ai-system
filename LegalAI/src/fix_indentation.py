with open('src/court_classifier.py', 'r') as f:
    lines = f.readlines()

# Find and fix the problematic section
for i in range(len(lines)):
    if 'if len(sorted_scores) > 1:' in lines[i]:
        # Fix this line and the next few
        lines[i] = '            if len(sorted_scores) > 1:\n'
        if i+1 < len(lines) and 'if len(sorted_scores) > 1 and sorted_scores[0][1] > 0:' in lines[i+1]:
            lines[i+1] = '                if sorted_scores[0][1] > 0 and sorted_scores[1][1] / sorted_scores[0][1] > 0.8:\n'

# Write back
with open('src/court_classifier.py', 'w') as f:
    f.writelines(lines)

print("✅ Fixed indentation")
