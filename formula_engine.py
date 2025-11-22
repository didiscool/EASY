#!/usr/bin/env python3
"""
Moteur de formule centralisé et correct

FORMULE: nb = global_val × key_temporal × key_type × key_segmacro × key_segment × key_dcr × key_file × key_offre

Chaque clé est calculée comme:
  key_X = (somme interactions pour X) / (somme totale)

Toutes les opérations (filtrage, visualisation, modification, construction) utilisent ce moteur.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta


class FormulaEngine:
    """Moteur de calcul de la formule"""

    def __init__(self, df: pd.DataFrame):
        """Initialiser avec les données"""
        self.df = df.copy()
        self.global_val = df["NbInteractions"].sum()
        self.keys = {}
        self.recalculate_keys()

    def recalculate_keys(self):
        """Recalculer toutes les clés depuis les données"""
        if self.df.empty:
            self.keys = {
                "temporal": {},
                "type": {},
                "segmacro": {},
                "segment": {},
                "dcr": {},
                "file": {},
                "offre": {}
            }
            return

        total = self.df["NbInteractions"].sum()
        if total == 0:
            total = 1  # Éviter division par zéro

        # Clé temporelle (par date/créneau)
        if "Date_debut" in self.df.columns:
            self.df["Date_debut"] = pd.to_datetime(self.df["Date_debut"], errors='coerce')
            temporal_by_date = self.df.groupby(self.df["Date_debut"].dt.strftime("%Y-%m-%d"))["NbInteractions"].sum()
            self.keys["temporal"] = (temporal_by_date / total).to_dict()
        else:
            self.keys["temporal"] = {}

        # Clé Type
        if "Type" in self.df.columns:
            type_sum = self.df.groupby("Type")["NbInteractions"].sum()
            self.keys["type"] = (type_sum / total).to_dict()
        else:
            self.keys["type"] = {}

        # Clé SegmentMacro
        if "SegmentMacro" in self.df.columns:
            segmacro_sum = self.df.groupby("SegmentMacro")["NbInteractions"].sum()
            self.keys["segmacro"] = (segmacro_sum / total).to_dict()
        else:
            self.keys["segmacro"] = {}

        # Clé Segment
        if "Segment" in self.df.columns:
            segment_sum = self.df.groupby("Segment")["NbInteractions"].sum()
            self.keys["segment"] = (segment_sum / total).to_dict()
        else:
            self.keys["segment"] = {}

        # Clé DCR
        if "DCR" in self.df.columns:
            dcr_sum = self.df.groupby("DCR")["NbInteractions"].sum()
            self.keys["dcr"] = (dcr_sum / total).to_dict()
        else:
            self.keys["dcr"] = {}

        # Clé File
        if "File" in self.df.columns:
            file_sum = self.df.groupby("File")["NbInteractions"].sum()
            self.keys["file"] = (file_sum / total).to_dict()
        else:
            self.keys["file"] = {}

        # Clé Offre
        if "Offre" in self.df.columns:
            offre_sum = self.df.groupby("Offre")["NbInteractions"].sum()
            self.keys["offre"] = (offre_sum / total).to_dict()
        else:
            self.keys["offre"] = {}

    def get_key(self, key_type: str, value: str) -> float:
        """Obtenir la valeur d'une clé"""
        return self.keys.get(key_type, {}).get(value, 0.0)

    def calculate_for_row(self, row: pd.Series) -> float:
        """Calculer NbInteractions pour une ligne selon la formule"""
        result = self.global_val

        # Appliquer chaque clé
        result *= self.get_key("temporal", str(row.get("Date_debut", "")))
        result *= self.get_key("type", str(row.get("Type", "")))
        result *= self.get_key("segmacro", str(row.get("SegmentMacro", "")))
        result *= self.get_key("segment", str(row.get("Segment", "")))
        result *= self.get_key("dcr", str(row.get("DCR", "")))
        result *= self.get_key("file", str(row.get("File", "")))
        result *= self.get_key("offre", str(row.get("Offre", "")))

        return result

    def apply_formula_to_dataframe(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Appliquer la formule à un DataFrame"""
        if df is None:
            df = self.df.copy()
        else:
            df = df.copy()

        if df.empty:
            return df

        # Convertir les dates
        if "Date_debut" in df.columns:
            df["Date_debut"] = pd.to_datetime(df["Date_debut"], errors='coerce')
            df["Date_debut_str"] = df["Date_debut"].dt.strftime("%Y-%m-%d")
        else:
            df["Date_debut_str"] = ""

        # Calculer NbInteractions selon la formule
        df["NbInteractions_Calculated"] = df.apply(
            lambda row: self.calculate_for_row(row),
            axis=1
        )

        return df

    def get_combinatorial_breakdown(self, filters: Optional[Dict] = None) -> pd.DataFrame:
        """
        Obtenir la répartition combinatoire de toutes les combinations possibles

        Affiche: Type, SegmentMacro, Segment, File, DCR, Offre, NbInteractions calculé

        Args:
            filters: Dict des filtres à appliquer ({"Type": "Appel", ...})
        """
        # Appliquer les filtres
        df = self.df.copy()
        if filters:
            for col, value in filters.items():
                if col in df.columns and value:
                    df = df[df[col] == value]

        if df.empty:
            return pd.DataFrame()

        # Obtenir les dimensions uniques
        columns_to_group = ["Type", "SegmentMacro", "Segment", "File", "DCR", "Offre"]
        columns_available = [c for c in columns_to_group if c in df.columns]

        if not columns_available:
            return pd.DataFrame()

        # Grouper par toutes les dimensions et calculer
        grouped = df.groupby(columns_available, dropna=False).agg({
            "NbInteractions": "sum"
        }).reset_index()

        # Appliquer la formule
        # Pour chaque combinaison, calculer selon les clés existantes
        def calc_for_combo(row):
            result = self.global_val
            for col in columns_available:
                key_type = col.lower()
                value = str(row[col])
                # Si la clé n'existe pas, utiliser 1.0 (100%)
                key_val = self.keys.get(key_type, {}).get(value, 0.0)
                if key_val == 0:
                    # Calculer la clé dynamiquement si elle n'existe pas
                    subset_sum = df[df[col] == value]["NbInteractions"].sum()
                    key_val = subset_sum / self.global_val if self.global_val > 0 else 0
                result *= key_val
            return result

        grouped["NbInteractions_Calculated"] = grouped.apply(calc_for_combo, axis=1)

        # Ajouter colonnes de clés
        for col in columns_available:
            key_type = col.lower()
            grouped[f"{col}_Key_%"] = grouped[col].apply(
                lambda x: self.keys.get(key_type, {}).get(str(x), 0) * 100
            )

        # Ajouter colonne "Contribution"
        total = grouped["NbInteractions_Calculated"].sum()
        if total > 0:
            grouped["Contribution_%"] = (grouped["NbInteractions_Calculated"] / total * 100)
        else:
            grouped["Contribution_%"] = 0

        return grouped.sort_values("NbInteractions_Calculated", ascending=False)

    def filter_and_apply_formula(self, filters: Dict) -> pd.DataFrame:
        """Filtrer les données et appliquer la formule"""
        df = self.df.copy()

        # Appliquer les filtres
        for col, value in filters.items():
            if col in df.columns and value:
                df = df[df[col] == value]

        # Recalculer les clés sur les données filtrées
        if not df.empty:
            self.recalculate_keys()

        # Appliquer la formule
        return self.apply_formula_to_dataframe(df)

    def modify_key(self, key_type: str, key_value: str, new_weight: float):
        """Modifier une clé et recalculer"""
        if key_type in self.keys:
            self.keys[key_type][key_value] = new_weight

            # Normaliser (optionnel)
            total = sum(self.keys[key_type].values())
            if total > 0:
                for k in self.keys[key_type]:
                    self.keys[key_type][k] = self.keys[key_type][k] / total

    def construct_rows(self,
                      global_val: float,
                      types: List[str],
                      segmacros: List[str],
                      segments: List[str],
                      files: List[str],
                      dcrs: List[str],
                      offres: List[str],
                      dates: List[str]) -> pd.DataFrame:
        """
        Construire des lignes selon la formule

        Génère toutes les combinations et calcule NbInteractions
        """
        rows = []

        def get_or_calc_key(key_type: str, value: str) -> float:
            """Obtenir la clé ou calculer une valeur par défaut"""
            key_val = self.keys.get(key_type, {}).get(value, None)
            if key_val is not None:
                return key_val
            else:
                # Valeur par défaut: distribuer uniformément
                dict_size = len(self.keys.get(key_type, {}))
                return 1.0 / dict_size if dict_size > 0 else 0.0

        for date in dates:
            for type_val in types:
                for segmacro_val in segmacros:
                    for segment_val in segments:
                        for file_val in files:
                            for dcr_val in dcrs:
                                for offre_val in offres:
                                    # Créer la ligne
                                    row = {
                                        "Date_debut": date,
                                        "Type": type_val,
                                        "SegmentMacro": segmacro_val,
                                        "Segment": segment_val,
                                        "File": file_val,
                                        "DCR": dcr_val,
                                        "Offre": offre_val
                                    }

                                    # Calculer NbInteractions selon la formule
                                    nb = global_val
                                    nb *= get_or_calc_key("temporal", str(date))
                                    nb *= get_or_calc_key("type", str(type_val))
                                    nb *= get_or_calc_key("segmacro", str(segmacro_val))
                                    nb *= get_or_calc_key("segment", str(segment_val))
                                    nb *= get_or_calc_key("file", str(file_val))
                                    nb *= get_or_calc_key("dcr", str(dcr_val))
                                    nb *= get_or_calc_key("offre", str(offre_val))

                                    row["NbInteractions"] = int(round(nb))
                                    rows.append(row)

        return pd.DataFrame(rows)

    def get_formula_text(self) -> str:
        """Retourner la formule en texte"""
        return (
            "NbInteractions = Global_Value × Key_Temporal × Key_Type × Key_SegmentMacro × "
            "Key_Segment × Key_DCR × Key_File × Key_Offre\n\n"
            "Où chaque clé = (somme interactions pour cet élément) / (somme totale)"
        )

    def print_keys_summary(self):
        """Afficher un résumé des clés"""
        print("\n" + "="*80)
        print("RÉSUMÉ DES CLÉS")
        print("="*80)
        print(f"\nGlobal Value: {self.global_val:,.0f}")

        for key_type, values in self.keys.items():
            print(f"\n{key_type.upper()}:")
            for k, v in sorted(values.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {k:<30}: {v*100:>6.2f}%")
            if len(values) > 5:
                print(f"  ... ({len(values)} total)")


if __name__ == "__main__":
    # Test simple
    data = {
        "Date_debut": ["2024-01-01", "2024-01-01", "2024-01-02"],
        "Type": ["Appel", "Email", "Appel"],
        "SegmentMacro": ["Retail", "Retail", "Enterprise"],
        "Segment": ["Premium", "Premium", "Standard"],
        "File": ["Nord", "Nord", "Sud"],
        "DCR": ["DCR1", "DCR1", "DCR1"],
        "Offre": ["Off_A", "Off_A", "Off_B"],
        "NbInteractions": [100, 80, 120]
    }

    df = pd.DataFrame(data)
    engine = FormulaEngine(df)

    print("\nFORMULE:")
    print(engine.get_formula_text())

    engine.print_keys_summary()

    print("\n" + "="*80)
    print("RÉPARTITION COMBINATOIRE")
    print("="*80)
    breakdown = engine.get_combinatorial_breakdown()
    print(breakdown.to_string())

    print("\n" + "="*80)
    print("TEST CONSTRUCTION")
    print("="*80)
    constructed = engine.construct_rows(
        global_val=1000,
        types=["Appel", "Email"],
        segmacros=["Retail"],
        segments=["Premium"],
        files=["Nord"],
        dcrs=["DCR1"],
        offres=["Off_A"],
        dates=["2024-01-01", "2024-01-02"]
    )
    print(f"Constructed {len(constructed)} rows")
    print(constructed.head().to_string())
