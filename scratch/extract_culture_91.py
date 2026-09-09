import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('reports/melted.txt', 'r', encoding='utf-8', errors='ignore') as f:
    # Skip to line 11090000
    for _ in range(11090000):
        f.readline()
    
    in_target_culture = False
    depth = 0
    lines = []
    for line in f:
        if line.strip() == '91={' or line.startswith('\t\t91={'):
            in_target_culture = True
            print("Found 91={")
        if in_target_culture:
            lines.append(line)
            depth += line.count('{') - line.count('}')
            if depth == 0 and len(lines) > 1:
                break

print(f"Total lines for culture 91: {len(lines)}")
# Print full text of culture 91
print("".join(lines))
