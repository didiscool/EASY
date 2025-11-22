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

# Pas = niveau d'agrégation pour l'export
pas_values = ["Semaine", "Jour", "Creneau"]

# Créneaux de 30 minutes (de 8h à 18h)
creneaux = [f"{h:02d}:{m:02d}" for h in range(8, 18) for m in [0, 30]]

# Generate data
data = []
base_date = datetime(2024, 1, 1)

for i in range(num_rows):
    # Date et heure de début
    day_offset = random.randint(0, 30)
    creneau = random.choice(creneaux)
    hour, minute = map(int, creneau.split(':'))

    date_debut = base_date + timedelta(days=day_offset, hours=hour, minutes=minute)
    # Durée aléatoire de 30min à 2h
    duration_minutes = random.choice([30, 60, 90, 120])
    date_fin = date_debut + timedelta(minutes=duration_minutes)

    row = {
        "SegmentMacro": random.choice(segment_macros),
        "File": random.choice(files),
        "Segment": random.choice(segments),
        "DCR": random.choice(dcrs),
        "Semaine": random.choice(semaines),
        "Offre": random.choice(offres),
        "NbInteractions": random.randint(10, 500),
        "Type": random.choice(types),
        "Date_debut": date_debut.strftime("%Y-%m-%d %H:%M"),
        "Date_fin": date_fin.strftime("%Y-%m-%d %H:%M"),
        "Pas": random.choice(pas_values),
        "Creneau": creneau
    }
    data.append(row)

# Create DataFrame and save
df = pd.DataFrame(data)
df.to_excel("/home/user/EASY/sample_data.xlsx", index=False)
print(f"Created sample_data.xlsx with {len(df)} rows")
print(f"Columns: {list(df.columns)}")
