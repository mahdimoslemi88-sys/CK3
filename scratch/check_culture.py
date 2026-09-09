import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('reports/melted.txt', 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        if i == 4589066:
            for j in range(25):
                print(f.readline().rstrip())
            break
