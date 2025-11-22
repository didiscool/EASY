#!/usr/bin/env python3
"""
Manager pour les clés de répartition temporelles avec hiérarchie correcte:
Créneau (30min) → Jour → Semaine

Formula: nb = global_val × key_temporal × key_type × key_segmacro × key_segment × key_dcr × key_file × key_offre

où key_temporal = poids_créneau(dans jour) × poids_jour(dans semaine) × poids_semaine(dans plage)
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
import copy


class TemporalKeysManager:
    """Gestionnaire des clés de répartition temporelles avec hiérarchie"""

    def __init__(self):
        """Initialiser le gestionnaire"""
        self.keys = {
            "creneaux": {},      # Clés par créneau dans chaque jour {YYYY-MM-DD: {HH:MM: weight}}
            "jours": {},         # Clés par jour dans chaque semaine {S##-YYYY: {YYYY-MM-DD: weight}}
            "semaines": {},      # Clés par semaine dans la plage {YYYY-MM-DD: weight}
        }
        self.baseline = copy.deepcopy(self.keys)  # Sauvegarde de la base
        self.current_step = "jour"  # Pas courant: "semaine", "jour", "creneau"

    def set_step(self, step: str):
        """Définir le pas temporel courant"""
        if step in ["semaine", "jour", "creneau"]:
            self.current_step = step

    # ============================================================================
    # CALCUL DES CLÉS À PARTIR DES DONNÉES EXISTANTES
    # ============================================================================

    def calculate_from_dataframe(self, df: pd.DataFrame):
        """Calculer les clés temporelles depuis les données existantes"""
        if df.empty or "Date_debut" not in df.columns:
            return

        # Copie de travail
        work_df = df.copy()
        work_df["Date_debut"] = pd.to_datetime(work_df["Date_debut"], errors='coerce')
        work_df = work_df.dropna(subset=["Date_debut"])

        if work_df.empty:
            return

        total = work_df["NbInteractions"].sum()
        if total == 0:
            return

        # Extraire les clés selon le Pas présent dans les données
        pas_values = work_df["Pas"].unique() if "Pas" in work_df.columns else ["jour"]

        for pas in pas_values:
            if pas == "creneau" or pas == "Creneau":
                self._calculate_creneau_keys(work_df, total)
            elif pas == "jour" or pas == "Jour":
                self._calculate_jour_keys(work_df, total)
            elif pas == "semaine" or pas == "Semaine":
                self._calculate_semaine_keys(work_df, total)

        # Sauvegarder comme baseline
        self.baseline = copy.deepcopy(self.keys)

    def _calculate_creneau_keys(self, df: pd.DataFrame, total: float):
        """Calculer les clés par créneau dans chaque jour"""
        # Groupe par (Date, Créneau)
        if "Creneau" not in df.columns:
            return

        df_creneaux = df[df["Creneau"].notna() & (df["Creneau"] != "")].copy()
        if df_creneaux.empty:
            return

        df_creneaux["Date"] = df_creneaux["Date_debut"].dt.strftime("%Y-%m-%d")

        # Par jour
        for date, day_group in df_creneaux.groupby("Date"):
            day_total = day_group["NbInteractions"].sum()
            creneau_weights = {}

            for creneau, creneau_group in day_group.groupby("Creneau"):
                creneau_total = creneau_group["NbInteractions"].sum()
                weight = (creneau_total / day_total * 100) if day_total > 0 else 0
                creneau_weights[str(creneau)] = round(weight, 2)

            self.keys["creneaux"][date] = creneau_weights

    def _calculate_jour_keys(self, df: pd.DataFrame, total: float):
        """Calculer les clés par jour dans chaque semaine"""
        df_jours = df.copy()
        df_jours["Date"] = df_jours["Date_debut"].dt.strftime("%Y-%m-%d")
        df_jours["Semaine"] = df_jours["Date_debut"].dt.strftime("S%V-%Y")

        # Par semaine
        for semaine, week_group in df_jours.groupby("Semaine"):
            week_total = week_group["NbInteractions"].sum()
            jour_weights = {}

            for jour, jour_group in week_group.groupby("Date"):
                jour_total = jour_group["NbInteractions"].sum()
                weight = (jour_total / week_total * 100) if week_total > 0 else 0
                jour_weights[jour] = round(weight, 2)

            self.keys["jours"][semaine] = jour_weights

    def _calculate_semaine_keys(self, df: pd.DataFrame, total: float):
        """Calculer les clés par semaine dans la plage"""
        df_semaines = df.copy()
        df_semaines["Semaine"] = df_semaines["Date_debut"].dt.strftime("S%V-%Y")

        semaine_weights = df_semaines.groupby("Semaine")["NbInteractions"].sum()
        semaine_weights = (semaine_weights / total * 100).round(2)

        self.keys["semaines"] = semaine_weights.to_dict()

    # ============================================================================
    # CALCUL DE LA CLÉ TEMPORELLE COMPOSITE
    # ============================================================================

    def get_temporal_key(self, date_debut: datetime, creneau: Optional[str] = None,
                        date_str: Optional[str] = None) -> float:
        """
        Calculer la clé temporelle composite pour un point donné

        key_temporal = poids_créneau(dans jour) × poids_jour(dans semaine) × poids_semaine(dans plage)

        Args:
            date_debut: datetime ou date string
            creneau: HH:MM format ou None
            date_str: YYYY-MM-DD format si date_debut n'est pas au bon format

        Returns:
            float: Clé temporelle (multiplier par 100 pour obtenir le %)
        """
        if isinstance(date_debut, str):
            try:
                date_debut = pd.to_datetime(date_debut)
            except:
                return 1.0

        if not date_str:
            date_str = date_debut.strftime("%Y-%m-%d")

        semaine = date_debut.strftime("S%V-%Y")

        # Calcul hiérarchique
        key_creneau = 1.0
        key_jour = 1.0
        key_semaine = 1.0

        # Poids créneau dans le jour
        if creneau and date_str in self.keys["creneaux"]:
            creneau_dict = self.keys["creneaux"][date_str]
            if str(creneau) in creneau_dict:
                key_creneau = creneau_dict[str(creneau)] / 100.0

        # Poids jour dans la semaine
        if date_str and semaine in self.keys["jours"]:
            jour_dict = self.keys["jours"][semaine]
            if date_str in jour_dict:
                key_jour = jour_dict[date_str] / 100.0

        # Poids semaine dans la plage
        if semaine in self.keys["semaines"]:
            key_semaine = self.keys["semaines"][semaine] / 100.0

        # Formule composite
        temporal_key = key_creneau * key_jour * key_semaine

        return temporal_key

    # ============================================================================
    # MODIFICATION ET NORMALISATION DES CLÉS
    # ============================================================================

    def set_creneau_weight(self, date: str, creneau: str, weight: float):
        """Définir le poids d'un créneau dans un jour (0-100)"""
        if date not in self.keys["creneaux"]:
            self.keys["creneaux"][date] = {}
        self.keys["creneaux"][date][str(creneau)] = round(weight, 2)

    def set_jour_weight(self, semaine: str, date: str, weight: float):
        """Définir le poids d'un jour dans une semaine (0-100)"""
        if semaine not in self.keys["jours"]:
            self.keys["jours"][semaine] = {}
        self.keys["jours"][semaine][date] = round(weight, 2)

    def set_semaine_weight(self, semaine: str, weight: float):
        """Définir le poids d'une semaine dans la plage (0-100)"""
        self.keys["semaines"][semaine] = round(weight, 2)

    def normalize_creneaux(self, date: str):
        """Normaliser les créneaux d'un jour à 100%"""
        if date not in self.keys["creneaux"]:
            return
        creneau_dict = self.keys["creneaux"][date]
        total = sum(creneau_dict.values())
        if total > 0:
            for creneau in creneau_dict:
                creneau_dict[creneau] = round(creneau_dict[creneau] / total * 100, 2)

    def normalize_jours(self, semaine: str):
        """Normaliser les jours d'une semaine à 100%"""
        if semaine not in self.keys["jours"]:
            return
        jour_dict = self.keys["jours"][semaine]
        total = sum(jour_dict.values())
        if total > 0:
            for jour in jour_dict:
                jour_dict[jour] = round(jour_dict[jour] / total * 100, 2)

    def normalize_semaines(self):
        """Normaliser les semaines à 100%"""
        total = sum(self.keys["semaines"].values())
        if total > 0:
            for semaine in self.keys["semaines"]:
                self.keys["semaines"][semaine] = round(self.keys["semaines"][semaine] / total * 100, 2)

    # ============================================================================
    # CONVERSION DE FICHIER (Semaine ↔ Jour ↔ Créneau)
    # ============================================================================

    def convert_file(self, df: pd.DataFrame, from_step: str, to_step: str,
                    day_weights: Optional[Dict] = None,
                    creneau_weights: Optional[Dict] = None) -> Tuple[pd.DataFrame, Dict]:
        """
        Convertir un fichier d'un pas temporel à un autre

        Args:
            df: DataFrame avec colonnes Date_debut, Pas, Creneau
            from_step: "semaine", "jour", ou "creneau"
            to_step: cible "semaine", "jour", ou "creneau"
            day_weights: Si conversion Semaine→Jour: {lundi: 20, mardi: 15, ...}
            creneau_weights: Si conversion Jour→Créneau: {08:00: 10, 08:30: 8, ...}

        Returns:
            (new_df, conversion_summary)
        """
        if from_step == to_step:
            return df.copy(), {"status": "no_conversion"}

        new_df = df.copy()
        summary = {
            "original_count": len(df),
            "from_step": from_step,
            "to_step": to_step,
            "new_count": 0,
            "conversion_method": "",
            "details": []
        }

        if from_step == "semaine" and to_step == "jour":
            new_df = self._convert_semaine_to_jour(new_df, day_weights, summary)

        elif from_step == "jour" and to_step == "creneau":
            new_df = self._convert_jour_to_creneau(new_df, creneau_weights, summary)

        elif from_step == "semaine" and to_step == "creneau":
            # Conversion intermédiaire
            new_df = self._convert_semaine_to_jour(new_df, day_weights, summary)
            new_df = self._convert_jour_to_creneau(new_df, creneau_weights, summary)

        elif from_step == "creneau" and to_step == "jour":
            new_df = self._convert_creneau_to_jour(new_df, summary)

        elif from_step == "jour" and to_step == "semaine":
            new_df = self._convert_jour_to_semaine(new_df, summary)

        summary["new_count"] = len(new_df)
        return new_df, summary

    def _convert_semaine_to_jour(self, df: pd.DataFrame, day_weights: Optional[Dict],
                                 summary: Dict) -> pd.DataFrame:
        """Convertir Semaine → Jour"""
        summary["conversion_method"] = "Semaine→Jour: expansion par jour de semaine"

        rows = []
        for idx, row in df.iterrows():
            if row.get("Pas", "Semaine").lower() != "semaine":
                rows.append(row)
                continue

            semaine = row.get("Semaine", "")
            if not semaine:
                rows.append(row)
                continue

            # Extraire année de Semaine (S##-YYYY)
            try:
                week_num = int(semaine.replace("S", "").split("-")[0])
                year = int(semaine.split("-")[1])
            except:
                rows.append(row)
                continue

            # Générer tous les jours de cette semaine
            from datetime import datetime, timedelta
            jan1 = datetime(year, 1, 1)
            start_of_week = jan1 + timedelta(weeks=week_num-1) - timedelta(days=jan1.weekday())

            # Jours lundi-dimanche
            day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

            for day_offset in range(7):
                day_date = start_of_week + timedelta(days=day_offset)
                day_name = day_names[day_offset]

                # Poids du jour (par défaut: uniforme)
                if day_weights and day_name in day_weights:
                    weight = day_weights[day_name] / 100.0
                else:
                    weight = 1.0 / 7  # Uniforme par défaut

                new_row = row.copy()
                new_row["Date_debut"] = day_date.strftime("%Y-%m-%d")
                new_row["Date_fin"] = day_date.strftime("%Y-%m-%d")
                new_row["Pas"] = "Jour"
                new_row["Creneau"] = ""
                new_row["NbInteractions"] = int(row.get("NbInteractions", 0) * weight)

                rows.append(new_row)
                summary["details"].append(f"{semaine} → {day_date.strftime('%Y-%m-%d')} ({weight*100:.1f}%)")

        return pd.DataFrame(rows)

    def _convert_jour_to_creneau(self, df: pd.DataFrame, creneau_weights: Optional[Dict],
                                summary: Dict) -> pd.DataFrame:
        """Convertir Jour → Créneau"""
        summary["conversion_method"] = "Jour→Créneau: expansion par créneaux 30min"

        # Créneaux par défaut: 8h-18h
        if not creneau_weights:
            creneaux = [f"{h:02d}:{m:02d}" for h in range(8, 18) for m in [0, 30]]
            creneau_weights = {c: 100/len(creneaux) for c in creneaux}

        rows = []
        for idx, row in df.iterrows():
            if row.get("Pas", "Jour").lower() != "jour":
                rows.append(row)
                continue

            date_str = str(row.get("Date_debut", ""))
            if not date_str or date_str == "":
                rows.append(row)
                continue

            for creneau, weight in creneau_weights.items():
                new_row = row.copy()
                new_row["Date_debut"] = f"{date_str} {creneau}"
                new_row["Date_fin"] = f"{date_str} {creneau}"
                new_row["Pas"] = "Creneau"
                new_row["Creneau"] = creneau
                new_row["NbInteractions"] = int(row.get("NbInteractions", 0) * weight / 100)

                rows.append(new_row)
                summary["details"].append(f"{date_str} → {creneau} ({weight:.1f}%)")

        return pd.DataFrame(rows)

    def _convert_creneau_to_jour(self, df: pd.DataFrame, summary: Dict) -> pd.DataFrame:
        """Convertir Créneau → Jour (agrégation)"""
        summary["conversion_method"] = "Créneau→Jour: agrégation par jour"

        groupby_cols = ["Date_debut", "Segment", "File", "SegmentMacro", "DCR", "Offre", "Type"]
        groupby_cols = [c for c in groupby_cols if c in df.columns]

        # Extraire la date sans l'heure
        df_copy = df.copy()
        df_copy["DateOnly"] = pd.to_datetime(df_copy["Date_debut"], errors='coerce').dt.strftime("%Y-%m-%d")

        rows = []
        for (date,), group in df_copy.groupby(["DateOnly"]):
            for attrs_tuple, attr_group in group.groupby([c for c in groupby_cols if c != "Date_debut"]):
                new_row = attr_group.iloc[0].copy()
                new_row["Date_debut"] = date
                new_row["Date_fin"] = date
                new_row["Pas"] = "Jour"
                new_row["Creneau"] = ""
                new_row["NbInteractions"] = attr_group["NbInteractions"].sum()
                rows.append(new_row)

        return pd.DataFrame(rows)

    def _convert_jour_to_semaine(self, df: pd.DataFrame, summary: Dict) -> pd.DataFrame:
        """Convertir Jour → Semaine (agrégation)"""
        summary["conversion_method"] = "Jour→Semaine: agrégation par semaine"

        df_copy = df.copy()
        df_copy["Semaine"] = pd.to_datetime(df_copy["Date_debut"], errors='coerce').dt.strftime("S%V-%Y")

        groupby_cols = ["Semaine", "Segment", "File", "SegmentMacro", "DCR", "Offre", "Type"]
        groupby_cols = [c for c in groupby_cols if c in df_copy.columns]

        rows = []
        for group_tuple, group in df_copy.groupby([c for c in groupby_cols if c != "Semaine"], sort=False):
            new_row = group.iloc[0].copy()
            new_row["Semaine"] = group["Semaine"].iloc[0]
            new_row["Date_debut"] = group["Date_debut"].iloc[0]
            new_row["Date_fin"] = group["Date_fin"].iloc[-1]
            new_row["Pas"] = "Semaine"
            new_row["Creneau"] = ""
            new_row["NbInteractions"] = group["NbInteractions"].sum()
            rows.append(new_row)

        return pd.DataFrame(rows)

    # ============================================================================
    # IMPORT/EXPORT
    # ============================================================================

    def to_dict(self) -> Dict:
        """Exporter les clés en dictionnaire"""
        return copy.deepcopy(self.keys)

    def from_dict(self, data: Dict):
        """Importer les clés depuis un dictionnaire"""
        self.keys = copy.deepcopy(data)
        self.baseline = copy.deepcopy(data)

    def to_json(self, filename: str):
        """Exporter les clés en JSON"""
        with open(filename, 'w') as f:
            json.dump(self.keys, f, indent=2)

    def from_json(self, filename: str):
        """Importer les clés depuis JSON"""
        with open(filename, 'r') as f:
            self.keys = json.load(f)
            self.baseline = copy.deepcopy(self.keys)

    # ============================================================================
    # REVERT ET BASELINE
    # ============================================================================

    def revert_to_baseline(self):
        """Revenir aux valeurs de base"""
        self.keys = copy.deepcopy(self.baseline)

    def save_baseline(self):
        """Sauvegarder les valeurs actuelles comme baseline"""
        self.baseline = copy.deepcopy(self.keys)

    def get_differences(self) -> Dict:
        """Obtenir les différences entre valeurs actuelles et baseline"""
        diffs = {
            "creneaux": {},
            "jours": {},
            "semaines": {}
        }

        # Différences créneau
        for date in set(list(self.keys["creneaux"].keys()) + list(self.baseline["creneaux"].keys())):
            current = self.keys["creneaux"].get(date, {})
            original = self.baseline["creneaux"].get(date, {})
            if current != original:
                diffs["creneaux"][date] = {"current": current, "baseline": original}

        # Idem pour jours et semaines
        for semaine in set(list(self.keys["jours"].keys()) + list(self.baseline["jours"].keys())):
            current = self.keys["jours"].get(semaine, {})
            original = self.baseline["jours"].get(semaine, {})
            if current != original:
                diffs["jours"][semaine] = {"current": current, "baseline": original}

        for semaine in set(list(self.keys["semaines"].keys()) + list(self.baseline["semaines"].keys())):
            current_val = self.keys["semaines"].get(semaine, 0)
            original_val = self.baseline["semaines"].get(semaine, 0)
            if current_val != original_val:
                diffs["semaines"][semaine] = {"current": current_val, "baseline": original_val}

        return diffs
