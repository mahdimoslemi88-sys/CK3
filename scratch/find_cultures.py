import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('reports/melted.txt', 'r', encoding='utf-8', errors='ignore') as f:
    for i in range(100):
        line = f.readline()
        if not line:
            break

# Let's search for cultures section
with open('reports/melted.txt', 'r', encoding='utf-8', errors='ignore') as f:
    for line_num, line in enumerate(f):
        if line.startswith('cultures={') or line.startswith('\tcultures={') or 'culture_manager={' in line:
            print(f"Found culture section at line {line_num}: {line.strip()[:80]}")
            # Print next 50 lines
            for _ in range(50):
                print(f.readline().rstrip())
            break
