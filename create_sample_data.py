#!/usr/bin/env python3
"""Generate sample XLSX data for testing the CSV import UI"""

import pandas as pd
from datetime import datetime, timedelta
import random

# Configuration
num_rows = 200

# Sample values
segment_macros = ["Retail", "Enterprise", "SMB"]
files = ["Nord", "Sud", "Est", "Ouest", "Centre"]
segments = ["Premium", "Standard", "Basic"]
dcrs = ["DCR1", "DCR2", "DCR3"]
semaines = ["S01", "S02", "S03", "S04"]
offres = ["Offre_A", "Offre_B", "Offre_C"]
types = ["Appel", "Email", "Chat", "SMS"]
pas_values = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
creneaux = ["8h-10h", "10h-12h", "12h-14h", "14h-16h", "16h-18h"]

# Generate data
data = []
base_date = datetime(2024, 1, 1)

for i in range(num_rows):
    date_debut = base_date + timedelta(days=random.randint(0, 30))
    date_fin = date_debut + timedelta(days=random.randint(1, 7))

    row = {
        "SegmentMacro": random.choice(segment_macros),
        "File": random.choice(files),
        "Segment": random.choice(segments),
        "DCR": random.choice(dcrs),
        "Semaine": random.choice(semaines),
        "Offre": random.choice(offres),
        "NbInteractions": random.randint(10, 500),
        "Type": random.choice(types),
        "Date_debut": date_debut.strftime("%Y-%m-%d"),
        "Date_fin": date_fin.strftime("%Y-%m-%d"),
        "Pas": random.choice(pas_values),
        "Creneau": random.choice(creneaux)
    }
    data.append(row)

# Create DataFrame and save
df = pd.DataFrame(data)
df.to_excel("/home/user/EASY/sample_data.xlsx", index=False)
print(f"Created sample_data.xlsx with {len(df)} rows")
print(f"Columns: {list(df.columns)}")
