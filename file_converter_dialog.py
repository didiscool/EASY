#!/usr/bin/env python3
"""
Dialogue interactif pour convertir les fichiers entre pas temporels
avec sélection des poids de répartition
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta


class FileConverterDialog(tk.Toplevel):
    """Dialogue de conversion de fichier interactif"""

    def __init__(self, parent, df: pd.DataFrame, current_step: str, temporal_keys_manager=None):
        """
        Initialiser le dialogue

        Args:
            parent: Fenêtre parent
            df: DataFrame à convertir
            current_step: Pas courant ("semaine", "jour", "creneau")
            temporal_keys_manager: Instance de TemporalKeysManager
        """
        super().__init__(parent)
        self.title("Conversion de Fichier")
        self.geometry("600x700")
        self.resizable(True, True)
        self.transient(parent)

        self.df = df.copy()
        self.current_step = current_step
        self.temporal_keys_manager = temporal_keys_manager
        self.result_df = None
        self.result_summary = None

        self.setup_ui()

    def setup_ui(self):
        """Configurer l'interface"""
        # Header
        header = ttk.LabelFrame(self, text="Conversion", padding="10")
        header.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(header, text=f"Pas courant:", font=('TkDefaultFont', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        ttk.Label(header, text=self.current_step.upper(), font=('TkDefaultFont', 10), foreground='blue').pack(side=tk.LEFT, padx=5)

        ttk.Label(header, text="→", font=('TkDefaultFont', 14, 'bold')).pack(side=tk.LEFT, padx=10)

        ttk.Label(header, text="Convertir en:", font=('TkDefaultFont', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        self.target_step_var = tk.StringVar(value="jour")
        target_combo = ttk.Combobox(header, textvariable=self.target_step_var,
                                   values=[s for s in ["semaine", "jour", "creneau"] if s != self.current_step],
                                   state="readonly", width=10)
        target_combo.pack(side=tk.LEFT, padx=5)
        target_combo.bind('<<ComboboxSelected>>', lambda e: self.on_target_changed())

        # Panel de configuration
        config_frame = ttk.LabelFrame(self, text="Configuration des poids", padding="10")
        config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.config_notebook = ttk.Notebook(config_frame)
        self.config_notebook.pack(fill=tk.BOTH, expand=True)

        self.setup_weight_panels()

        # Preview
        preview_frame = ttk.LabelFrame(self, text="Aperçu de conversion", padding="5")
        preview_frame.pack(fill=tk.X, padx=10, pady=5)

        self.preview_text = tk.Text(preview_frame, height=4, width=70)
        self.preview_text.pack(fill=tk.BOTH, expand=True)

        # Boutons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(btn_frame, text="Aperçu Complet", command=self.show_full_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Convertir", command=self.do_conversion).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annuler", command=self.cancel_conversion).pack(side=tk.RIGHT, padx=5)

        self.on_target_changed()

    def on_target_changed(self):
        """Rafraîchir les panels quand la cible change"""
        # Vider le notebook
        for tab in self.config_notebook.tabs():
            self.config_notebook.forget(tab)

        self.setup_weight_panels()
        self.update_preview()

    def setup_weight_panels(self):
        """Configurer les panels de poids selon la conversion"""
        target = self.target_step_var.get()

        if self.current_step == "semaine" and target == "jour":
            self._setup_day_weights_panel()

        elif self.current_step == "jour" and target == "creneau":
            self._setup_creneau_weights_panel()

        elif self.current_step == "semaine" and target == "creneau":
            self._setup_full_hierarchy_panel()

    def _setup_day_weights_panel(self):
        """Configuration des poids des jours (Semaine → Jour)"""
        panel = ttk.Frame(self.config_notebook)
        self.config_notebook.add(panel, text="Poids des jours")

        # Description
        ttk.Label(panel, text="Définir le poids de chaque jour de la semaine", font=('TkDefaultFont', 9, 'italic')).pack(anchor=tk.W, padx=10, pady=5)

        # Frame pour les sliders
        slider_frame = ttk.LabelFrame(panel, text="Distribution", padding="10")
        slider_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.day_sliders = {}
        days_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        default_weights = [20, 20, 20, 20, 20, 0, 0]  # Par défaut: jours ouvrables

        for i, (day_name, default_weight) in enumerate(zip(days_fr, default_weights)):
            row = ttk.Frame(slider_frame)
            row.pack(fill=tk.X, pady=5)

            ttk.Label(row, text=day_name, width=12).pack(side=tk.LEFT, padx=5)

            var = tk.DoubleVar(value=default_weight)
            slider = ttk.Scale(row, from_=0, to=100, variable=var, orient=tk.HORIZONTAL, command=lambda v, d=day_name: self.update_preview())
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

            label = ttk.Label(row, text=f"{default_weight:.0f}%", width=6)
            label.pack(side=tk.LEFT, padx=5)
            var.trace('w', lambda *args, l=label, v=var: l.config(text=f"{v.get():.0f}%"))

            self.day_sliders[day_name] = var

        # Boutons helpers
        helper_frame = ttk.Frame(slider_frame)
        helper_frame.pack(fill=tk.X, pady=10)

        ttk.Button(helper_frame, text="Jours ouvrables (5 jours)",
                  command=self._set_weekdays_equal).pack(side=tk.LEFT, padx=5)
        ttk.Button(helper_frame, text="Égal (7 jours)",
                  command=self._set_all_equal).pack(side=tk.LEFT, padx=5)
        ttk.Button(helper_frame, text="Normaliser",
                  command=self._normalize_weights).pack(side=tk.LEFT, padx=5)

    def _setup_creneau_weights_panel(self):
        """Configuration des poids des créneaux (Jour → Créneau)"""
        panel = ttk.Frame(self.config_notebook)
        self.config_notebook.add(panel, text="Poids des créneaux")

        # Description
        ttk.Label(panel, text="Définir le poids de chaque créneau 30 minutes", font=('TkDefaultFont', 9, 'italic')).pack(anchor=tk.W, padx=10, pady=5)

        # Frame avec scroll pour les créneaux
        scroll_frame = ttk.Frame(panel)
        scroll_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        canvas = tk.Canvas(scroll_frame)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Créneaux 8h-18h par défaut
        self.creneau_sliders = {}
        creneaux = [f"{h:02d}:{m:02d}" for h in range(8, 18) for m in [0, 30]]

        for creneau in creneaux:
            row = ttk.Frame(scrollable_frame)
            row.pack(fill=tk.X, pady=3)

            ttk.Label(row, text=creneau, width=8).pack(side=tk.LEFT, padx=5)

            var = tk.DoubleVar(value=100/len(creneaux))
            slider = ttk.Scale(row, from_=0, to=100, variable=var, orient=tk.HORIZONTAL, command=lambda v: self.update_preview())
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

            label = ttk.Label(row, text=f"{100/len(creneaux):.1f}%", width=6)
            label.pack(side=tk.LEFT, padx=5)
            var.trace('w', lambda *args, l=label, v=var: l.config(text=f"{v.get():.1f}%"))

            self.creneau_sliders[creneau] = var

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Boutons helpers
        helper_frame = ttk.Frame(panel)
        helper_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(helper_frame, text="Heures de pointe (9-17)",
                  command=self._set_peak_hours).pack(side=tk.LEFT, padx=5)
        ttk.Button(helper_frame, text="Distribution égale",
                  command=self._set_creneaux_equal).pack(side=tk.LEFT, padx=5)
        ttk.Button(helper_frame, text="Normaliser",
                  command=self._normalize_weights).pack(side=tk.LEFT, padx=5)

    def _setup_full_hierarchy_panel(self):
        """Configuration complète pour Semaine → Créneau (2 étapes)"""
        panel = ttk.Frame(self.config_notebook)
        self.config_notebook.add(panel, text="Jours & Créneaux")

        ttk.Label(panel, text="Configuration en deux étapes", font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W, padx=10, pady=5)

        # Étape 1: Jours
        day_frame = ttk.LabelFrame(panel, text="Étape 1: Distribution par jour", padding="5")
        day_frame.pack(fill=tk.X, padx=10, pady=5)

        self.day_sliders = {}
        days_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

        for day_name in days_fr:
            row = ttk.Frame(day_frame)
            row.pack(fill=tk.X, pady=2)

            ttk.Label(row, text=day_name, width=12).pack(side=tk.LEFT, padx=5)

            var = tk.DoubleVar(value=20 if days_fr.index(day_name) < 5 else 0)
            slider = ttk.Scale(row, from_=0, to=100, variable=var, orient=tk.HORIZONTAL, command=lambda v: self.update_preview())
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

            label = ttk.Label(row, text=f"{var.get():.0f}%", width=5)
            label.pack(side=tk.LEFT, padx=5)
            var.trace('w', lambda *args, l=label, v=var: l.config(text=f"{v.get():.0f}%"))

            self.day_sliders[day_name] = var

        # Étape 2: Créneaux
        creneau_frame = ttk.LabelFrame(panel, text="Étape 2: Distribution par créneau", padding="5")
        creneau_frame.pack(fill=tk.X, padx=10, pady=5)

        self.creneau_sliders = {}
        creneaux = [f"{h:02d}:{m:02d}" for h in range(8, 18) for m in [0, 30]]

        creneau_inner = ttk.Frame(creneau_frame)
        creneau_inner.pack(fill=tk.X)

        for i, creneau in enumerate(creneaux):
            if i % 4 == 0:
                row = ttk.Frame(creneau_frame)
                row.pack(fill=tk.X, pady=2)

            ttk.Label(row, text=creneau, width=6).pack(side=tk.LEFT, padx=2)

            var = tk.DoubleVar(value=100/len(creneaux))
            slider = ttk.Scale(row, from_=0, to=100, variable=var, orient=tk.HORIZONTAL, length=80, command=lambda v: self.update_preview())
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

            label = ttk.Label(row, text=f"{100/len(creneaux):.0f}%", width=5)
            label.pack(side=tk.LEFT, padx=2)
            var.trace('w', lambda *args, l=label, v=var: l.config(text=f"{v.get():.0f}%"))

            self.creneau_sliders[creneau] = var

    # ========================================================================
    # Helper methods for weights
    # ========================================================================

    def _set_weekdays_equal(self):
        """Répartir également sur les 5 jours ouvrables"""
        weight = 100 / 5
        for i, day in enumerate(["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]):
            self.day_sliders[day].set(weight)
        for day in ["Samedi", "Dimanche"]:
            self.day_sliders[day].set(0)
        self.update_preview()

    def _set_all_equal(self):
        """Répartir également sur les 7 jours"""
        weight = 100 / 7
        for day in self.day_sliders:
            self.day_sliders[day].set(weight)
        self.update_preview()

    def _set_creneaux_equal(self):
        """Répartir également sur tous les créneaux"""
        weight = 100 / len(self.creneau_sliders)
        for creneau in self.creneau_sliders:
            self.creneau_sliders[creneau].set(weight)
        self.update_preview()

    def _set_peak_hours(self):
        """Donner plus de poids aux heures de pointe (9-17)"""
        peak_hours = [f"{h:02d}:{m:02d}" for h in range(9, 17) for m in [0, 30]]
        off_peak_hours = [c for c in self.creneau_sliders.keys() if c not in peak_hours]

        peak_weight = 100 * 0.7 / len(peak_hours) if peak_hours else 0
        off_peak_weight = 100 * 0.3 / len(off_peak_hours) if off_peak_hours else 0

        for creneau in peak_hours:
            self.creneau_sliders[creneau].set(peak_weight)
        for creneau in off_peak_hours:
            self.creneau_sliders[creneau].set(off_peak_weight)

        self.update_preview()

    def _normalize_weights(self):
        """Normaliser les poids à 100%"""
        if hasattr(self, 'day_sliders'):
            total = sum(v.get() for v in self.day_sliders.values())
            if total > 0:
                for var in self.day_sliders.values():
                    var.set(var.get() / total * 100)

        if hasattr(self, 'creneau_sliders'):
            total = sum(v.get() for v in self.creneau_sliders.values())
            if total > 0:
                for var in self.creneau_sliders.values():
                    var.set(var.get() / total * 100)

        self.update_preview()

    def update_preview(self):
        """Mettre à jour l'aperçu"""
        target = self.target_step_var.get()
        current = self.current_step

        preview = f"Conversion: {current.upper()} → {target.upper()}\n"
        preview += "-" * 50 + "\n"

        if current == "semaine" and target == "jour":
            total = sum(v.get() for v in self.day_sliders.values())
            preview += f"Distribution jours (Total: {total:.0f}%)\n"
            for day, var in self.day_sliders.items():
                if var.get() > 0:
                    preview += f"  {day:<12}: {var.get():>6.1f}%\n"

        elif current == "jour" and target == "creneau":
            total = sum(v.get() for v in self.creneau_sliders.values())
            preview += f"Distribution créneaux (Total: {total:.0f}%)\n"
            count = 0
            for creneau, var in sorted(self.creneau_sliders.items()):
                if var.get() > 0 and count < 5:
                    preview += f"  {creneau}: {var.get():>6.1f}%\n"
                    count += 1
            if len([v for v in self.creneau_sliders.values() if v.get() > 0]) > 5:
                preview += f"  ... ({len(self.creneau_sliders)} créneaux)\n"

        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", preview)

    def show_full_preview(self):
        """Afficher un aperçu complet de la conversion"""
        messagebox.showinfo("Aperçu Complet",
            f"La conversion appliquera les poids définis à {len(self.df)} ligne(s)\n\n"
            "Cela créera potentiellement plusieurs lignes par ligne source.\n"
            "Le total des interactions restera identique.")

    def do_conversion(self):
        """Effectuer la conversion"""
        target = self.target_step_var.get()
        current = self.current_step

        # Collecter les poids
        day_weights = {}
        creneau_weights = {}

        if hasattr(self, 'day_sliders'):
            day_weights = {day: var.get() for day, var in self.day_sliders.items()}

        if hasattr(self, 'creneau_sliders'):
            creneau_weights = {creneau: var.get() for creneau, var in self.creneau_sliders.items()}

        if self.temporal_keys_manager:
            self.result_df, self.result_summary = self.temporal_keys_manager.convert_file(
                self.df, current, target,
                day_weights=day_weights if day_weights else None,
                creneau_weights=creneau_weights if creneau_weights else None
            )
        else:
            messagebox.showerror("Erreur", "TemporalKeysManager non configuré")
            return

        messagebox.showinfo("Conversion Réussie",
            f"Conversion effectuée:\n"
            f"  Lignes avant: {len(self.df)}\n"
            f"  Lignes après: {len(self.result_df)}\n"
            f"  Interactions: {self.df['NbInteractions'].sum():,} → {self.result_df['NbInteractions'].sum():,}")

        self.destroy()

    def cancel_conversion(self):
        """Annuler la conversion"""
        self.result_df = None
        self.result_summary = None
        self.destroy()

    def get_result(self) -> Optional[Tuple[pd.DataFrame, Dict]]:
        """Récupérer le résultat de la conversion"""
        return (self.result_df, self.result_summary) if self.result_df is not None else None
