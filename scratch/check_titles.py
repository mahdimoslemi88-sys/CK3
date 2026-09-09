import sys
sys.stdout.reconfigure(encoding='utf-8')

titles_to_check = [5980, 5982, 8196]

with open('reports/melted.txt', 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        for t in titles_to_check:
            if line.strip() == f'{t}={{':
                print(f"Title {t} at line {i}:")
                for _ in range(12):
                    print("  ", f.readline().strip())
