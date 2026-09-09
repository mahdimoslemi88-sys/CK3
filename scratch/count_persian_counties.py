import sys
sys.stdout.reconfigure(encoding='utf-8')

# Let's inspect titles of 96352 and how many counties are culture 91
with open('reports/melted.txt', 'r', encoding='utf-8', errors='ignore') as f:
    # Let's count all counties with culture=91 in the world
    count = 0
    in_provinces = False
    in_landed_titles = False
    
# Let's write a focused script to count counties by culture
with open('reports/melted.txt', 'r', encoding='utf-8', errors='ignore') as f:
    persian_counties = 0
    total_counties = 0
    holders_persian = {}
    current_title = None
    current_culture = None
    is_county = False
    
    for line in f:
        if line.startswith('c_'):
            # wait, titles in melted are e.g. 5980={ or key="c_..."
            pass
        if 'culture_template="persian"' in line:
            pass

print("Scanning for county titles with culture 91...")
