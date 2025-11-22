#!/usr/bin/env python3
"""
Test complet de la formule correcte
"""

import pandas as pd
from formula_engine import FormulaEngine

print("="*80)
print("TEST COMPLET DE LA FORMULE CORRECTE")
print("="*80)

# ===== DONNÉES DE TEST =====
print("\n1. CRÉATION DE DONNÉES DE TEST")
print("-"*80)

data = {
    "Date_debut": ["2024-01-01", "2024-01-01", "2024-01-01", "2024-01-02", "2024-01-02"],
    "Type": ["Appel", "Appel", "Email", "Appel", "Email"],
    "SegmentMacro": ["Retail", "Enterprise", "Retail", "Enterprise", "Retail"],
    "Segment": ["Premium", "Standard", "Premium", "Premium", "Standard"],
    "File": ["Nord", "Sud", "Nord", "Sud", "Nord"],
    "DCR": ["DCR1", "DCR1", "DCR2", "DCR1", "DCR2"],
    "Offre": ["OffA", "OffB", "OffA", "OffB", "OffA"],
    "NbInteractions": [100, 80, 120, 60, 140]
}

df = pd.DataFrame(data)
print(f"✓ {len(df)} lignes créées")
print(f"✓ Total NbInteractions: {df['NbInteractions'].sum():,}")

# ===== INITIALISATION MOTEUR =====
print("\n2. INITIALISATION DU MOTEUR DE FORMULE")
print("-"*80)

engine = FormulaEngine(df)
print(f"✓ FormulaEngine initialisé")
print(f"✓ Global Value: {engine.global_val:,}")

# ===== AFFICHAGE DES CLÉS =====
print("\n3. CLÉS CALCULÉES")
print("-"*80)

engine.print_keys_summary()

# ===== RÉPARTITION COMBINATOIRE =====
print("\n4. RÉPARTITION COMBINATOIRE")
print("-"*80)

breakdown = engine.get_combinatorial_breakdown()
print("\nTableau de répartition (toutes les combinaisons):")
print(breakdown[["Type", "SegmentMacro", "Segment", "File", "DCR", "Offre", "NbInteractions", "NbInteractions_Calculated", "Contribution_%"]].to_string())

print(f"\nTotal Calculé: {breakdown['NbInteractions_Calculated'].sum():.0f}")
print(f"Total Original: {breakdown['NbInteractions'].sum():.0f}")

# ===== FILTRAGE =====
print("\n5. FILTRAGE AVEC FORMULE")
print("-"*80)

filtered = engine.filter_and_apply_formula({"Type": "Appel"})
print(f"Filtre Type='Appel': {len(filtered)} lignes")
print(filtered[["Type", "Date_debut", "SegmentMacro", "NbInteractions"]].head().to_string())

# ===== MODIFICATION DE CLÉS =====
print("\n6. MODIFICATION DE CLÉS")
print("-"*80)

print("Avant modification:")
print(f"  key_type['Appel'] = {engine.keys['type'].get('Appel', 0)*100:.2f}%")

engine.modify_key("type", "Appel", 0.8)
print("Après modification (Appel → 80%):")
print(f"  key_type['Appel'] = {engine.keys['type'].get('Appel', 0)*100:.2f}%")

breakdown_modified = engine.get_combinatorial_breakdown({"Type": "Appel"})
print(f"Contribution Appel: {breakdown_modified['Contribution_%'].sum() if not breakdown_modified.empty else 0:.1f}%")

# ===== CONSTRUCTION DE FICHIER =====
print("\n7. CONSTRUCTION DE FICHIER")
print("-"*80)

constructed = engine.construct_rows(
    global_val=5000,
    types=["Appel", "Email"],
    segmacros=["Retail", "Enterprise"],
    segments=["Premium"],
    files=["Nord"],
    dcrs=["DCR1"],
    offres=["OffA"],
    dates=["2024-01-01", "2024-01-02"]
)

print(f"✓ {len(constructed)} lignes construites")
print(f"✓ Total NbInteractions: {constructed['NbInteractions'].sum():,}")
print("\nPremières lignes construites:")
print(constructed.head(8).to_string())

# ===== VÉRIFICATION =====
print("\n8. VÉRIFICATION DE LA FORMULE")
print("-"*80)

# Vérifier une ligne
sample_row = constructed.iloc[0]
print(f"\nVérification de la ligne 1:")
print(f"  Type: {sample_row['Type']}")
print(f"  SegmentMacro: {sample_row['SegmentMacro']}")
print(f"  File: {sample_row['File']}")
print(f"  NbInteractions: {sample_row['NbInteractions']}")

# Recalculer manuellement
global_val = 5000
key_temporal = engine.keys['temporal'].get("2024-01-01", 0.5)  # ~50%
key_type = engine.keys['type'].get("Appel", 0.5)  # ~50% (modifié)
key_segmacro = engine.keys['segmacro'].get("Retail", 0.5)
key_segment = engine.keys['segment'].get("Premium", 0.5)
key_file = engine.keys['file'].get("Nord", 0.5)
key_dcr = engine.keys['dcr'].get("DCR1", 1.0)
key_offre = engine.keys['offre'].get("OffA", 0.5)

expected = global_val * key_temporal * key_type * key_segmacro * key_segment * key_file * key_dcr * key_offre
print(f"\nCalcul manuel:")
print(f"  {global_val} × {key_temporal:.3f} × {key_type:.3f} × {key_segmacro:.3f} × {key_segment:.3f} × {key_file:.3f} × {key_dcr:.3f} × {key_offre:.3f}")
print(f"  = {expected:.0f}")
print(f"  Calculé: {sample_row['NbInteractions']}")

print("\n" + "="*80)
print("✅ TEST COMPLET TERMINÉ")
print("="*80)
