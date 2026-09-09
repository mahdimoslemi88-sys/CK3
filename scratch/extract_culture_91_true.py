import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('reports/melted.txt', 'r', encoding='utf-8', errors='ignore') as f:
    for _ in range(11090340):
        f.readline()
    
    in_cultures = False
    in_91 = False
    depth = 0
    lines = []
    
    for line in f:
        if 'cultures={' in line:
            in_cultures = True
            continue
        if in_cultures:
            if line.startswith('\t\t91={'):
                in_91 = True
                print("Found \\t\\t91={")
            if in_91:
                lines.append(line)
                depth += line.count('{') - line.count('}')
                if depth == 0 and len(lines) > 1:
                    break

print(f"Total lines for culture 91: {len(lines)}")
with open('scratch/culture_91.txt', 'w', encoding='utf-8') as out:
    out.write("".join(lines))

print("Wrote scratch/culture_91.txt")
