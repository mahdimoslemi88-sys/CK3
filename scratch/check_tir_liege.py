import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('reports/melted.txt', 'r', encoding='utf-8', errors='ignore') as f:
    found = False
    for i, line in enumerate(f):
        if line.strip() == '33593665={':
            found = True
        if found:
            if 'domain=' in line or 'realm_capital=' in line or 'primary_title=' in line:
                print(line.strip())
            if 'alive_data=' in line:
                # continue reading until landed_data
                pass
            if 'landed_data=' in line:
                print("Found landed data for Ghazi:")
                for _ in range(20):
                    print(f.readline().strip())
                break
