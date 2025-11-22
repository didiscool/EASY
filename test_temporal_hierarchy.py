#!/usr/bin/env python3
"""
Tests complets pour la hiérarchie temporelle et la conversion de fichiers
"""

import pandas as pd
from datetime import datetime, timedelta
from temporal_keys_manager import TemporalKeysManager
import json


def test_temporal_keys_calculation():
    """Test du calcul des clés temporelles avec hiérarchie"""
    print("\n" + "="*80)
    print("TEST 1: Calcul des clés temporelles")
    print("="*80)

    # Créer des données de test
    data = []
    base_date = datetime(2024, 1, 1)

    # Semaine 1, 5 jours
    for day in range(5):
        for creneau_idx, (h, m) in enumerate([(8, 0), (8, 30), (9, 0), (9, 30)]):
            date = base_date + timedelta(days=day, hours=h, minutes=m)
            data.append({
                "Date_debut": date,
                "Creneau": f"{h:02d}:{m:02d}",
                "Type": "Appel",
                "NbInteractions": 100 + creneau_idx * 10
            })

    df = pd.DataFrame(data)

    # Calculer les clés
    mgr = TemporalKeysManager()
    mgr.calculate_from_dataframe(df)

    print(f"\nDonnées de test: {len(df)} lignes")
    print(f"Date range: {df['Date_debut'].min()} to {df['Date_debut'].max()}")

    print("\n--- Clés Créneaux ---")
    for date, creneaux in mgr.keys["creneaux"].items():
        print(f"{date}: {creneaux}")

    print("\n--- Clés Jours ---")
    for semaine, jours in mgr.keys["jours"].items():
        print(f"{semaine}: {jours}")

    print("\n--- Clés Semaines ---")
    for semaine, weight in mgr.keys["semaines"].items():
        print(f"{semaine}: {weight:.2f}%")

    # Test de la clé temporelle composite
    print("\n--- Test de Clé Temporelle Composite ---")
    test_date = base_date
    test_creneau = "08:00"

    key = mgr.get_temporal_key(test_date, test_creneau)
    print(f"Clé temporelle pour {test_date.strftime('%Y-%m-%d')} {test_creneau}: {key:.6f}")
    print(f"Formule: key_creneau × key_jour × key_semaine")


def test_file_conversion_semaine_to_jour():
    """Test conversion Semaine → Jour"""
    print("\n" + "="*80)
    print("TEST 2: Conversion Semaine → Jour")
    print("="*80)

    # Données: 2 semaines
    data = []
    for week in [1, 2]:
        for seg in ["Seg1", "Seg2"]:
            data.append({
                "SegmentMacro": "Macro1",
                "File": "File1",
                "Segment": seg,
                "DCR": "DCR1",
                "Semaine": f"S{week:02d}-2024",
                "Offre": "Off1",
                "NbInteractions": 1000,
                "Type": "Appel",
                "Date_debut": f"2024-01-{1 + (week-1)*7:02d}",
                "Date_fin": f"2024-01-{7 + (week-1)*7:02d}",
                "Pas": "Semaine",
                "Creneau": ""
            })

    df = pd.DataFrame(data)
    print(f"\nDonnées avant conversion: {len(df)} lignes")
    print(f"Total NbInteractions: {df['NbInteractions'].sum()}")

    mgr = TemporalKeysManager()
    new_df, summary = mgr.convert_file(
        df, "semaine", "jour",
        day_weights={
            "Lundi": 20, "Mardi": 20, "Mercredi": 20,
            "Jeudi": 20, "Vendredi": 20, "Samedi": 0, "Dimanche": 0
        }
    )

    print(f"\nDonnées après conversion: {len(new_df)} lignes")
    print(f"Total NbInteractions: {new_df['NbInteractions'].sum()}")
    print(f"\nSommaire: {json.dumps(summary, indent=2, default=str)}")

    # Vérifier l'intégrité
    assert df['NbInteractions'].sum() == new_df['NbInteractions'].sum(), "Total NbInteractions ne correspond pas!"
    print("✓ Intégrité confirmée: Total conservé")


def test_file_conversion_jour_to_creneau():
    """Test conversion Jour → Créneau"""
    print("\n" + "="*80)
    print("TEST 3: Conversion Jour → Créneau")
    print("="*80)

    # Données: 3 jours
    data = []
    for day in range(3):
        data.append({
            "SegmentMacro": "Macro1",
            "File": "File1",
            "Segment": "Seg1",
            "DCR": "DCR1",
            "Semaine": "S01-2024",
            "Offre": "Off1",
            "NbInteractions": 1000,
            "Type": "Appel",
            "Date_debut": f"2024-01-{1+day:02d}",
            "Date_fin": f"2024-01-{1+day:02d}",
            "Pas": "Jour",
            "Creneau": ""
        })

    df = pd.DataFrame(data)
    print(f"\nDonnées avant conversion: {len(df)} lignes")
    print(f"Total NbInteractions: {df['NbInteractions'].sum()}")

    mgr = TemporalKeysManager()
    creneaux_8_18 = {f"{h:02d}:{m:02d}": 100/20
                     for h in range(8, 18) for m in [0, 30]}

    new_df, summary = mgr.convert_file(
        df, "jour", "creneau",
        creneau_weights=creneaux_8_18
    )

    print(f"\nDonnées après conversion: {len(new_df)} lignes")
    print(f"Total NbInteractions: {new_df['NbInteractions'].sum()}")
    print(f"Créneaux par jour: {len(new_df) / len(df):.0f}")

    assert df['NbInteractions'].sum() == new_df['NbInteractions'].sum(), "Total NbInteractions ne correspond pas!"
    print("✓ Intégrité confirmée: Total conservé")


def test_baseline_and_revert():
    """Test sauvegarde et revert de baseline"""
    print("\n" + "="*80)
    print("TEST 4: Baseline et Revert")
    print("="*80)

    mgr = TemporalKeysManager()

    # Définir des clés
    mgr.set_semaine_weight("S01-2024", 50.0)
    mgr.set_semaine_weight("S02-2024", 50.0)

    print("\nClés initiales:")
    print(f"  S01-2024: {mgr.keys['semaines']['S01-2024']:.2f}%")
    print(f"  S02-2024: {mgr.keys['semaines']['S02-2024']:.2f}%")

    # Sauvegarder comme baseline
    mgr.save_baseline()
    print("\n✓ Baseline sauvegardée")

    # Modifier les clés
    mgr.set_semaine_weight("S01-2024", 30.0)
    mgr.set_semaine_weight("S02-2024", 70.0)

    print("\nClés modifiées:")
    print(f"  S01-2024: {mgr.keys['semaines']['S01-2024']:.2f}%")
    print(f"  S02-2024: {mgr.keys['semaines']['S02-2024']:.2f}%")

    # Détecter les différences
    diffs = mgr.get_differences()
    print(f"\nDifférences détectées: {len(diffs['semaines'])} semaines modifiées")
    for semaine, vals in diffs['semaines'].items():
        print(f"  {semaine}: {vals['baseline']:.2f}% → {vals['current']:.2f}%")

    # Revenir à baseline
    mgr.revert_to_baseline()
    print("\n✓ Revenu à baseline")
    print(f"  S01-2024: {mgr.keys['semaines']['S01-2024']:.2f}%")
    print(f"  S02-2024: {mgr.keys['semaines']['S02-2024']:.2f}%")

    diffs_after = mgr.get_differences()
    print(f"\nDifférences après revert: {len(diffs_after['semaines'])} (devrait être 0)")
    assert len(diffs_after['semaines']) == 0, "Revert n'a pas fonctionné!"
    print("✓ Intégrité confirmée")


def test_normalization():
    """Test normalisation des clés"""
    print("\n" + "="*80)
    print("TEST 5: Normalisation des clés")
    print("="*80)

    mgr = TemporalKeysManager()

    # Définir des clés non-normalisées
    mgr.set_semaine_weight("S01-2024", 60.0)
    mgr.set_semaine_weight("S02-2024", 40.0)
    mgr.set_semaine_weight("S03-2024", 30.0)

    total_before = sum(mgr.keys['semaines'].values())
    print(f"\nTotal avant normalisation: {total_before:.2f}%")

    # Normaliser
    mgr.normalize_semaines()

    total_after = sum(mgr.keys['semaines'].values())
    print(f"Total après normalisation: {total_after:.2f}%")

    for semaine, weight in sorted(mgr.keys['semaines'].items()):
        print(f"  {semaine}: {weight:.2f}%")

    assert abs(total_after - 100.0) < 0.01, "La normalisation n'a pas fonctionné!"
    print("✓ Intégrité confirmée: Total = 100%")


def run_all_tests():
    """Exécuter tous les tests"""
    print("\n" + "#"*80)
    print("# TESTS DE HIÉRARCHIE TEMPORELLE ET CONVERSION DE FICHIERS")
    print("#"*80)

    try:
        test_temporal_keys_calculation()
        test_file_conversion_semaine_to_jour()
        test_file_conversion_jour_to_creneau()
        test_baseline_and_revert()
        test_normalization()

        print("\n" + "#"*80)
        print("# TOUS LES TESTS RÉUSSIS ✓")
        print("#"*80 + "\n")

    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
