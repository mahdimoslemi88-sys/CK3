import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('reports/melted.txt', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if '96352={' in line:
            print("Found 96352 block")
            for _ in range(50):
                l = f.readline()
                if any(k in l for k in ['landed_data', 'domain', 'held_title', 'primary_title', 'realm']):
                    print("  ", l.strip())

