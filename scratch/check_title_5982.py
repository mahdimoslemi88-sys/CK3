import sys
sys.stdout.reconfigure(encoding='utf-8')

# Let's check title 5980 and 5982
with open('reports/melted.txt', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if line.startswith('5982={') or line.startswith('\t5982={'):
            print("Found 5982:")
            for _ in range(25):
                print(f.readline().rstrip())
            break
