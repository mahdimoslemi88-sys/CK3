import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('reports/melted.txt', 'r', encoding='utf-8', errors='ignore') as f:
    in_char = False
    depth = 0
    lines = []
    for line in f:
        if line.strip() == '96352={':
            in_char = True
        if in_char:
            lines.append(line)
            depth += line.count('{') - line.count('}')
            if depth == 0 and len(lines) > 1:
                break

for l in lines:
    s = l.strip()
    if any(k in s for k in ['domain=', 'primary_title=', 'capital=', 'faith=', 'culture=', 'liege=', 'first_name=', 'birth=']):
        print(s)
