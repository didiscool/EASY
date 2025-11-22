#!/usr/bin/env python3
"""
EASY Application - VERSION CORRIGÉE AMÉLIORÉE

Implémente CORRECTEMENT la formule partout:
  NbInteractions = Global × Key_Temporal × Key_Type × Key_SegMacro × Key_Segment × Key_DCR × Key_File × Key_Offre

Basé sur formula_engine.py qui gère la logique correcte.

AMÉLIORATIONS:
- Filtres pour TOUTES les colonnes
- Trois modes de modification: Relatif (%), Absolu, Nombre
- Aperçu avant/après des modifications
- Système d'undo (Ctrl-Z)
- Normalisation automatique
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from datetime import datetime
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import copy

from formula_engine import FormulaEngine


class EASYCorrected:
    """Application EASY corrigée avec toutes les fonctionnalités"""

    def __init__(self, root):
        self.root = root
        self.root.title("EASY - Gestion des Interactions (VERSION CORRIGÉE - AMÉLIORÉE)")
        self.root.geometry("1900x1100")

        self.df = None
        self.engine = None
        self.filtered_df = None

        # Historique des modifications
        self.history = []
        self.history_index = -1
        self.baseline_engine = None

        # États UI
        self.filters = {}
        self.selected_rows = []
        self.modify_mode = tk.StringVar(value="relative")

        self.setup_ui()
        self.root.bind('<Control-z>', lambda e: self.undo())

    def setup_ui(self):
        """Configurer l'interface"""
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ===== BARRE SUPÉRIEURE: IMPORT/EXPORT =====
        top_frame = ttk.LabelFrame(main_frame, text="Import/Export", padding="5")
        top_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(top_frame, text="[Importer]", command=self.import_data).pack(side=tk.LEFT, padx=3)
        ttk.Button(top_frame, text="[Exporter]", command=self.export_data).pack(side=tk.LEFT, padx=3)
        self.file_label = ttk.Label(top_frame, text="Aucun fichier", foreground='gray')
        self.file_label.pack(side=tk.LEFT, padx=20)

        # ===== FILTRES GLOBAUX =====
        filter_frame = ttk.LabelFrame(main_frame, text="Filtres globaux (tous les onglets)", padding="5")
        filter_frame.pack(fill=tk.X, pady=(0, 5))

        filter_row1 = ttk.Frame(filter_frame)
        filter_row1.pack(fill=tk.X, pady=3)

        for label, var_name, combo_name in [
            ("SegmentMacro:", "segment_macro_var", "segment_macro_combo"),
            ("File:", "file_var", "file_combo"),
            ("Segment:", "segment_var", "segment_combo"),
            ("DCR:", "dcr_var", "dcr_combo"),
        ]:
            ttk.Label(filter_row1, text=label).pack(side=tk.LEFT, padx=(0, 2))
            setattr(self, var_name, tk.StringVar())
            combo = ttk.Combobox(filter_row1, textvariable=getattr(self, var_name), width=12, state='readonly')
            setattr(self, combo_name, combo)
            combo.pack(side=tk.LEFT, padx=(0, 10))
            combo.bind('<<ComboboxSelected>>', lambda e: self.apply_all_filters())

        filter_row2 = ttk.Frame(filter_frame)
        filter_row2.pack(fill=tk.X, pady=3)

        for label, var_name, combo_name in [
            ("Type:", "type_var", "type_combo"),
            ("Offre:", "offre_var", "offre_combo"),
            ("Semaine:", "semaine_var", "semaine_combo"),
            ("Pas:", "pas_var", "pas_combo"),
        ]:
            ttk.Label(filter_row2, text=label).pack(side=tk.LEFT, padx=(0, 2))
            setattr(self, var_name, tk.StringVar())
            combo = ttk.Combobox(filter_row2, textvariable=getattr(self, var_name), width=12, state='readonly')
            setattr(self, combo_name, combo)
            combo.pack(side=tk.LEFT, padx=(0, 10))
            combo.bind('<<ComboboxSelected>>', lambda e: self.apply_all_filters())

        ttk.Button(filter_row2, text="[Reset Tous les Filtres]", command=self.reset_all_filters).pack(side=tk.RIGHT, padx=5)
        self.active_filters_label = ttk.Label(filter_row2, text="", foreground='#0066cc')
        self.active_filters_label.pack(side=tk.RIGHT, padx=10)

        # ===== NOTEBOOK PRINCIPAL =====
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Onglet 1: Répartitions Combinatoires
        self.tab_breakdown = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_breakdown, text="Répartitions Combinatoires")
        self.setup_breakdown_tab()

        # Onglet 2: Filtres et Visualisation
        self.tab_filters = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_filters, text="Filtres & Visualisation")
        self.setup_filters_tab()

        # Onglet 3: Modifications
        self.tab_modify = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_modify, text="Modifications")
        self.setup_modify_tab()

        # Onglet 4: Construction
        self.tab_construct = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_construct, text="Construction")
        self.setup_construct_tab()

    def setup_breakdown_tab(self):
        """Onglet Répartitions Combinatoires"""
        paned = ttk.PanedWindow(self.tab_breakdown, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Haut: Contrôles
        control_frame = ttk.LabelFrame(paned, text="Filtres pour répartition", padding="5")
        paned.add(control_frame, weight=0)

        row1 = ttk.Frame(control_frame)
        row1.pack(fill=tk.X, pady=3)

        ttk.Label(row1, text="Type:").pack(side=tk.LEFT, padx=5)
        self.filter_type = ttk.Combobox(row1, width=15, state='readonly')
        self.filter_type.pack(side=tk.LEFT, padx=5)
        self.filter_type.bind('<<ComboboxSelected>>', lambda e: self.update_breakdown())

        ttk.Label(row1, text="SegmentMacro:").pack(side=tk.LEFT, padx=5)
        self.filter_segmacro = ttk.Combobox(row1, width=15, state='readonly')
        self.filter_segmacro.pack(side=tk.LEFT, padx=5)
        self.filter_segmacro.bind('<<ComboboxSelected>>', lambda e: self.update_breakdown())

        ttk.Button(row1, text="[Reset Filtres]", command=self.reset_breakdown_filters).pack(side=tk.RIGHT, padx=5)

        # Bas: Tableau
        table_frame = ttk.Frame(paned)
        paned.add(table_frame, weight=1)

        self.breakdown_tree = ttk.Treeview(
            table_frame,
            columns=("Type", "SegMacro", "Segment", "File", "DCR", "Offre", "Original", "Calculated", "Contribution"),
            show="headings"
        )

        for col in ["Type", "SegMacro", "Segment", "File", "DCR", "Offre", "Original", "Calculated", "Contribution"]:
            self.breakdown_tree.heading(col, text=col)
            width = 100 if col in ["Calculated", "Contribution"] else 80
            self.breakdown_tree.column(col, width=width)

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.breakdown_tree.yview)
        self.breakdown_tree.configure(yscrollcommand=scroll.set)
        self.breakdown_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Lier double-click pour éditer
        self.breakdown_tree.bind('<Double-1>', self.on_breakdown_edit)

        self.breakdown_info = ttk.Label(paned, text="", foreground='blue')
        paned.add(self.breakdown_info, weight=0)

    def setup_filters_tab(self):
        """Onglet Filtres et Visualisation"""
        paned = ttk.PanedWindow(self.tab_filters, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Contrôles filtres
        control_frame = ttk.LabelFrame(paned, text="Options de Visualisation", padding="5")
        paned.add(control_frame, weight=0)

        ttk.Label(control_frame, text="Les filtres globaux (en haut) s'appliquent automatiquement").pack(anchor=tk.W)

        # Graphique
        chart_frame = ttk.Frame(paned)
        paned.add(chart_frame, weight=1)

        self.fig = Figure(figsize=(12, 5), dpi=85)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Tableau données filtrées
        table_frame = ttk.Frame(paned)
        paned.add(table_frame, weight=1)

        self.filtered_tree = ttk.Treeview(
            table_frame,
            columns=("Type", "SegMacro", "Segment", "File", "DCR", "Offre", "NbInt", "Calculated"),
            show="headings"
        )

        for col in ["Type", "SegMacro", "Segment", "File", "DCR", "Offre", "NbInt", "Calculated"]:
            self.filtered_tree.heading(col, text=col)
            self.filtered_tree.column(col, width=100)

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.filtered_tree.yview)
        self.filtered_tree.configure(yscrollcommand=scroll.set)
        self.filtered_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_modify_tab(self):
        """Onglet Modifications avec modes complets"""
        paned = ttk.PanedWindow(self.tab_modify, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Gauche: Tableau des clés
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Clés de répartition", font=('TkDefaultFont', 10, 'bold')).pack()

        self.modify_tree = ttk.Treeview(
            left_frame,
            columns=("Type", "Clé", "Valeur%", "Avant", "Après", "Diff"),
            show="headings"
        )

        for col, width in [("Type", 80), ("Clé", 100), ("Valeur%", 80), ("Avant", 80), ("Après", 80), ("Diff", 80)]:
            self.modify_tree.heading(col, text=col)
            self.modify_tree.column(col, width=width)

        scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.modify_tree.yview)
        self.modify_tree.configure(yscrollcommand=scroll.set)
        self.modify_tree.pack(fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Droite: Contrôles de modification
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=0)

        # Section: Sélection de clé
        select_frame = ttk.LabelFrame(right_frame, text="Sélection de Clé", padding="10")
        select_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(select_frame, text="Type de Clé:", font=('TkDefaultFont', 9, 'bold')).pack(anchor=tk.W)
        self.modify_key_type = ttk.Combobox(
            select_frame,
            values=["temporal", "type", "segmacro", "segment", "dcr", "file", "offre"],
            state='readonly',
            width=20
        )
        self.modify_key_type.pack(anchor=tk.W, padx=5, pady=3)
        self.modify_key_type.bind('<<ComboboxSelected>>', lambda e: self.on_key_type_change())

        ttk.Label(select_frame, text="Valeur de Clé:", font=('TkDefaultFont', 9, 'bold')).pack(anchor=tk.W, pady=(5, 0))
        self.modify_key_value = ttk.Combobox(select_frame, state='readonly', width=20)
        self.modify_key_value.pack(anchor=tk.W, padx=5, pady=3)

        # Section: Mode de modification
        mode_frame = ttk.LabelFrame(right_frame, text="Mode de Modification", padding="10")
        mode_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Radiobutton(mode_frame, text="Relatif (%)", variable=self.modify_mode,
                       value="relative", command=self.on_mode_change).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(mode_frame, text="Absolu (%)", variable=self.modify_mode,
                       value="absolute", command=self.on_mode_change).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(mode_frame, text="Nombre", variable=self.modify_mode,
                       value="number", command=self.on_mode_change).pack(anchor=tk.W, pady=2)

        # Slider pour mode Relatif
        self.slider_frame = ttk.Frame(mode_frame)
        self.slider_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.slider_frame, text="-50%").pack(side=tk.LEFT)
        self.slider_var = tk.DoubleVar(value=0)
        self.slider = ttk.Scale(self.slider_frame, from_=-50, to=50, variable=self.slider_var,
                                orient=tk.HORIZONTAL, command=lambda v: self.on_slider_change())
        self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Label(self.slider_frame, text="+50%").pack(side=tk.LEFT)
        self.slider_value_label = ttk.Label(self.slider_frame, text="0%", font=('TkDefaultFont', 9, 'bold'), width=5)
        self.slider_value_label.pack(side=tk.LEFT, padx=5)

        # Entrée pour mode Absolu
        self.absolute_frame = ttk.Frame(mode_frame)
        ttk.Label(self.absolute_frame, text="Valeur (%):", font=('TkDefaultFont', 9)).pack(side=tk.LEFT)
        self.absolute_value = ttk.Entry(self.absolute_frame, width=10)
        self.absolute_value.pack(side=tk.LEFT, padx=5)
        self.absolute_value.bind('<KeyRelease>', lambda e: self.update_preview())

        # Entrée pour mode Nombre
        self.number_frame = ttk.Frame(mode_frame)
        ttk.Label(self.number_frame, text="Nombre:", font=('TkDefaultFont', 9)).pack(side=tk.LEFT)
        self.number_value = ttk.Entry(self.number_frame, width=10)
        self.number_value.pack(side=tk.LEFT, padx=5)
        self.number_value.bind('<KeyRelease>', lambda e: self.update_preview())

        # Section: Aperçu
        preview_frame = ttk.LabelFrame(right_frame, text="Aperçu", padding="10")
        preview_frame.pack(fill=tk.X, pady=(0, 5))

        self.before_label = ttk.Label(preview_frame, text="AVANT: -", foreground='gray')
        self.before_label.pack(anchor=tk.W, pady=2)
        self.after_label = ttk.Label(preview_frame, text="APRÈS: -", foreground='#0066cc', font=('TkDefaultFont', 9, 'bold'))
        self.after_label.pack(anchor=tk.W, pady=2)
        self.diff_label = ttk.Label(preview_frame, text="DIFF: -", foreground='#ff6600')
        self.diff_label.pack(anchor=tk.W, pady=2)

        # Section: Actions
        action_frame = ttk.Frame(right_frame)
        action_frame.pack(fill=tk.X)

        ttk.Button(action_frame, text="APPLIQUER", command=self.apply_key_modification).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="Normaliser (100%)", command=self.normalize_keys).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="Annuler (Ctrl-Z)", command=self.undo).pack(fill=tk.X, pady=2)

        self.modify_info = ttk.Label(right_frame, text="", foreground='blue', wraplength=200)
        self.modify_info.pack(pady=10)

        self.on_mode_change()

    def setup_construct_tab(self):
        """Onglet Construction"""
        frame = ttk.LabelFrame(self.tab_construct, text="Construire Fichier Selon Mailles Temporelles", padding="10")
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Label(frame, text="CONSTRUCTION À PARTIR DE LA FORMULE", font=('TkDefaultFont', 11, 'bold')).pack(anchor=tk.W, pady=5)

        ttk.Label(frame, text="Global Value:", font=('TkDefaultFont', 10)).pack(anchor=tk.W, padx=5)
        self.construct_global = ttk.Entry(frame, width=20)
        self.construct_global.insert(0, "10000")
        self.construct_global.pack(anchor=tk.W, padx=5, pady=3)

        ttk.Label(frame, text="Maille Temporelle:", font=('TkDefaultFont', 10)).pack(anchor=tk.W, padx=5, pady=(10, 3))
        self.construct_maille = ttk.Combobox(
            frame,
            values=["Jour", "Semaine", "Créneau"],
            state='readonly',
            width=20
        )
        self.construct_maille.pack(anchor=tk.W, padx=5, pady=3)

        ttk.Button(frame, text="[CONSTRUIRE]", command=self.construct_file).pack(anchor=tk.W, padx=5, pady=10)

        self.construct_info = ttk.Label(frame, text="", foreground='blue', wraplength=400)
        self.construct_info.pack(pady=10)

    # ===== MÉTHODES DE CALLBACK =====

    def import_data(self):
        """Importer un fichier"""
        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")])
        if not path:
            return

        try:
            if path.endswith('.xlsx'):
                self.df = pd.read_excel(path)
            else:
                self.df = pd.read_csv(path)

            # Initialiser le moteur et baseline
            self.engine = FormulaEngine(self.df)
            self.baseline_engine = copy.deepcopy(self.engine)
            self.history = []
            self.history_index = -1

            self.file_label.config(text=f"✓ {path.split('/')[-1]} ({len(self.df)} lignes)")

            # Mettre à jour les combos de filtres
            self.update_filter_combos()

            # Mettre à jour l'affichage des clés
            self.update_keys_display()

            # Mettre à jour tous les onglets
            self.apply_all_filters()

            messagebox.showinfo("OK", f"{len(self.df)} lignes importées")

        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def export_data(self):
        """Exporter les données"""
        if self.df is None:
            messagebox.showwarning("Attention", "Aucune donnée")
            return

        path = filedialog.asksaveasfilename(defaultextension=".xlsx")
        if path:
            try:
                self.df.to_excel(path, index=False)
                messagebox.showinfo("OK", f"Exporté: {path}")
            except Exception as e:
                messagebox.showerror("Erreur", str(e))

    def update_filter_combos(self):
        """Mettre à jour les combos de filtres"""
        if self.df is None:
            return

        for col, combo_name in [
            ("Type", "type_combo"),
            ("SegmentMacro", "segment_macro_combo"),
            ("File", "file_combo"),
            ("Segment", "segment_combo"),
            ("DCR", "dcr_combo"),
            ("Offre", "offre_combo"),
            ("Semaine", "semaine_combo"),
            ("Pas", "pas_combo"),
        ]:
            if col in self.df.columns:
                values = [""] + sorted(self.df[col].unique().astype(str).tolist())
                getattr(self, combo_name)['values'] = values

    def reset_all_filters(self):
        """Réinitialiser tous les filtres"""
        self.type_var.set("")
        self.segment_macro_var.set("")
        self.file_var.set("")
        self.segment_var.set("")
        self.dcr_var.set("")
        self.offre_var.set("")
        self.semaine_var.set("")
        self.pas_var.set("")
        self.apply_all_filters()

    def reset_breakdown_filters(self):
        """Réinitialiser les filtres (hérité de l'ancienne version)"""
        self.reset_all_filters()

    def apply_all_filters(self):
        """Appliquer les filtres à tous les onglets"""
        self.update_breakdown()
        self.update_filtered_data()

    def get_current_filters(self):
        """Obtenir les filtres actuels"""
        filters = {}
        for var_name, col_name in [
            ("type_var", "Type"),
            ("segment_macro_var", "SegmentMacro"),
            ("file_var", "File"),
            ("segment_var", "Segment"),
            ("dcr_var", "DCR"),
            ("offre_var", "Offre"),
            ("semaine_var", "Semaine"),
            ("pas_var", "Pas"),
        ]:
            val = getattr(self, var_name).get()
            if val:
                filters[col_name] = val

        # Afficher les filtres actifs
        if filters:
            filter_text = " | ".join([f"{k}={v}" for k, v in filters.items()])
            self.active_filters_label.config(text=f"Filtres: {filter_text}")
        else:
            self.active_filters_label.config(text="Aucun filtre")

        return filters

    def update_breakdown(self):
        """Mettre à jour la répartition combinatoire"""
        if self.engine is None:
            return

        # Collecter les filtres
        filters = self.get_current_filters()

        # Obtenir la répartition
        breakdown = self.engine.get_combinatorial_breakdown(filters)

        # Nettoyer le tableau
        for item in self.breakdown_tree.get_children():
            self.breakdown_tree.delete(item)

        # Remplir le tableau
        total_calculated = breakdown["NbInteractions_Calculated"].sum() if not breakdown.empty else 0

        for idx, row in breakdown.iterrows():
            values = (
                row.get("Type", ""),
                row.get("SegmentMacro", ""),
                row.get("Segment", ""),
                row.get("File", ""),
                row.get("DCR", ""),
                row.get("Offre", ""),
                f"{int(row.get('NbInteractions', 0)):,}",
                f"{int(row.get('NbInteractions_Calculated', 0)):,}",
                f"{row.get('Contribution_%', 0):.1f}%"
            )
            self.breakdown_tree.insert("", tk.END, values=values)

        # Mettre à jour les infos
        info = f"Formule: nb = global × key_temporal × key_type × key_segmacro × key_segment × key_dcr × key_file × key_offre\n"
        info += f"Total Original: {breakdown['NbInteractions'].sum():,.0f}\n"
        info += f"Total Calculé: {total_calculated:,.0f}\n"
        info += f"Lignes: {len(breakdown)}"
        self.breakdown_info.config(text=info)

    def update_filtered_data(self):
        """Mettre à jour les données filtrées avec la formule appliquée"""
        if self.engine is None or self.df is None:
            return

        # Appliquer les filtres
        filtered_df = self.df.copy()
        filters = self.get_current_filters()

        for col, val in filters.items():
            if col in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[col].astype(str) == val]

        # Appliquer la formule
        if not filtered_df.empty:
            filtered_df["Calculated"] = filtered_df.apply(
                lambda row: self.engine.calculate_for_row(row), axis=1
            )
        else:
            filtered_df["Calculated"] = []

        self.filtered_df = filtered_df

        # Afficher dans le tableau
        for item in self.filtered_tree.get_children():
            self.filtered_tree.delete(item)

        for idx, row in filtered_df.iterrows():
            values = (
                row.get("Type", ""),
                row.get("SegmentMacro", ""),
                row.get("Segment", ""),
                row.get("File", ""),
                row.get("DCR", ""),
                row.get("Offre", ""),
                f"{int(row.get('NbInteractions', 0)):,}",
                f"{int(row.get('Calculated', 0)):,}"
            )
            self.filtered_tree.insert("", tk.END, values=values)

    def update_keys_display(self):
        """Mettre à jour l'affichage des clés de répartition"""
        if self.engine is None:
            return

        # Nettoyer
        for item in self.modify_tree.get_children():
            self.modify_tree.delete(item)

        # Remplir avec les clés
        for key_type, keys_dict in self.engine.keys.items():
            for key_name, key_value in keys_dict.items():
                before_val = self.baseline_engine.keys[key_type][key_name] if self.baseline_engine else key_value
                after_val = key_value
                diff = ((after_val - before_val) / before_val * 100) if before_val != 0 else 0

                values = (
                    key_type,
                    key_name,
                    f"{key_value*100:.2f}%",
                    f"{before_val*100:.2f}%",
                    f"{after_val*100:.2f}%",
                    f"{diff:+.1f}%"
                )
                self.modify_tree.insert("", tk.END, values=values)

    def on_key_type_change(self):
        """Remplir la combo des valeurs de clé"""
        key_type = self.modify_key_type.get()
        if not key_type or not self.engine:
            return

        keys_dict = self.engine.keys.get(key_type, {})
        values = [""] + list(keys_dict.keys())
        self.modify_key_value['values'] = values
        if values:
            self.modify_key_value.set(values[1] if len(values) > 1 else "")
        self.update_keys_display()

    def on_mode_change(self):
        """Afficher/masquer les contrôles selon le mode"""
        mode = self.modify_mode.get()

        # Masquer tous
        self.slider_frame.pack_forget()
        self.absolute_frame.pack_forget()
        self.number_frame.pack_forget()

        # Afficher celui approprié
        if mode == "relative":
            self.slider_frame.pack(fill=tk.X, pady=5)
            self.slider_var.set(0)
            self.update_preview()
        elif mode == "absolute":
            self.absolute_frame.pack(fill=tk.X, pady=5)
            self.absolute_value.delete(0, tk.END)
            self.update_preview()
        elif mode == "number":
            self.number_frame.pack(fill=tk.X, pady=5)
            self.number_value.delete(0, tk.END)
            self.update_preview()

    def on_slider_change(self):
        """Mettre à jour l'aperçu lors du changement du slider"""
        value = self.slider_var.get()
        self.slider_value_label.config(text=f"{value:+.0f}%")
        self.update_preview()

    def update_preview(self):
        """Afficher l'aperçu avant/après"""
        key_type = self.modify_key_type.get()
        key_value = self.modify_key_value.get()

        if not key_type or not key_value or not self.engine:
            self.before_label.config(text="AVANT: -")
            self.after_label.config(text="APRÈS: -")
            self.diff_label.config(text="DIFF: -")
            return

        # Valeur actuelle
        current_val = self.engine.keys.get(key_type, {}).get(key_value, 0)

        # Calculer la nouvelle valeur selon le mode
        mode = self.modify_mode.get()
        try:
            if mode == "relative":
                slider_val = self.slider_var.get() / 100
                new_val = current_val * (1 + slider_val)
            elif mode == "absolute":
                new_val = float(self.absolute_value.get()) / 100
            elif mode == "number":
                # Convertir nombre en pourcentage de la somme
                num = float(self.number_value.get())
                total_sum = sum(self.engine.keys[key_type].values())
                if total_sum > 0:
                    new_val = num / total_sum
                else:
                    new_val = 0
            else:
                new_val = current_val

            diff = new_val - current_val
            diff_pct = (diff / current_val * 100) if current_val != 0 else 0

            self.before_label.config(text=f"AVANT: {current_val*100:.2f}%")
            self.after_label.config(text=f"APRÈS: {new_val*100:.2f}%")
            self.diff_label.config(text=f"DIFF: {diff:+.4f} ({diff_pct:+.1f}%)")

        except:
            self.before_label.config(text="AVANT: -")
            self.after_label.config(text="APRÈS: -")
            self.diff_label.config(text="DIFF: Valeur invalide")

    def apply_key_modification(self):
        """Appliquer une modification de clé"""
        key_type = self.modify_key_type.get()
        key_value = self.modify_key_value.get()

        if not key_type or not key_value or not self.engine:
            messagebox.showwarning("Attention", "Sélectionnez une clé")
            return

        try:
            mode = self.modify_mode.get()

            if mode == "relative":
                slider_val = self.slider_var.get() / 100
                current_val = self.engine.keys[key_type][key_value]
                new_val = current_val * (1 + slider_val)
            elif mode == "absolute":
                new_val = float(self.absolute_value.get()) / 100
            elif mode == "number":
                num = float(self.number_value.get())
                total_sum = sum(self.engine.keys[key_type].values())
                new_val = num / total_sum if total_sum > 0 else 0
            else:
                return

            # Sauvegarder dans l'historique
            self.history.append(copy.deepcopy(self.engine.keys))
            self.history_index = len(self.history) - 1

            # Sauvegarder la baseline si première modification
            if self.baseline_engine is None:
                self.baseline_engine = copy.deepcopy(self.engine)

            # Appliquer la modification
            self.engine.keys[key_type][key_value] = new_val

            # Recalculer le moteur
            self.engine.recalculate_keys()

            # Mettre à jour l'affichage
            self.update_keys_display()
            self.update_breakdown()
            self.update_filtered_data()

            messagebox.showinfo("OK", f"Clé modifiée: {key_value} = {new_val*100:.2f}%")

        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def normalize_keys(self):
        """Normaliser les clés à 100%"""
        if not self.engine:
            return

        # Sauvegarder dans l'historique
        self.history.append(copy.deepcopy(self.engine.keys))
        self.history_index = len(self.history) - 1

        # Sauvegarder la baseline si première modification
        if self.baseline_engine is None:
            self.baseline_engine = copy.deepcopy(self.engine)

        # Normaliser
        for key_type in self.engine.keys:
            total = sum(self.engine.keys[key_type].values())
            if total > 0:
                for k in self.engine.keys[key_type]:
                    self.engine.keys[key_type][k] = self.engine.keys[key_type][k] / total

        # Recalculer le moteur
        self.engine.recalculate_keys()

        # Mettre à jour l'affichage
        self.update_keys_display()
        self.update_breakdown()
        self.update_filtered_data()

        messagebox.showinfo("OK", "Clés normalisées à 100%")

    def undo(self):
        """Annuler la dernière modification"""
        if self.history_index > 0:
            self.history_index -= 1
            self.engine.keys = copy.deepcopy(self.history[self.history_index])
            self.engine.recalculate_keys()
            self.update_keys_display()
            self.update_breakdown()
            self.update_filtered_data()
            self.modify_info.config(text=f"Undo: {self.history_index+1}/{len(self.history)}")

    def on_breakdown_edit(self, event):
        """Éditer une clé en double-cliquant"""
        item = self.breakdown_tree.identify('item', event.x, event.y)
        if not item:
            return

        values = self.breakdown_tree.item(item)['values']
        type_val = values[0]

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Modifier clé pour {type_val}")
        dialog.geometry("300x150")

        ttk.Label(dialog, text=f"Nouvelle valeur (%) pour {type_val}:").pack(pady=10)
        entry = ttk.Entry(dialog, width=20)
        entry.insert(0, "100")
        entry.pack(pady=5)

        def save():
            try:
                new_val = float(entry.get()) / 100
                self.engine.modify_key("type", type_val, new_val)
                self.update_breakdown()
                dialog.destroy()
            except:
                messagebox.showerror("Erreur", "Valeur invalide")

        ttk.Button(dialog, text="OK", command=save).pack(pady=5)

    def construct_file(self):
        """Construire un fichier"""
        if self.engine is None:
            messagebox.showwarning("Attention", "Aucune donnée")
            return

        try:
            global_val = float(self.construct_global.get())
            maille = self.construct_maille.get()

            if not maille:
                messagebox.showwarning("Attention", "Sélectionnez une maille")
                return

            # Créer les listes
            types = sorted(self.df["Type"].unique().astype(str).tolist())[:2]  # Limiter pour test
            segmacros = sorted(self.df["SegmentMacro"].unique().astype(str).tolist())[:1]
            segments = sorted(self.df["Segment"].unique().astype(str).tolist())[:1]
            files = sorted(self.df["File"].unique().astype(str).tolist())[:1]
            dcrs = sorted(self.df["DCR"].unique().astype(str).tolist())[:1]
            offres = sorted(self.df["Offre"].unique().astype(str).tolist())[:1]

            # Dates
            if maille == "Jour":
                dates = ["2024-01-01", "2024-01-02", "2024-01-03"]
            elif maille == "Semaine":
                dates = ["2024-01-01", "2024-01-08"]
            else:
                dates = ["2024-01-01"]

            # Construire
            constructed = self.engine.construct_rows(
                global_val, types, segmacros, segments, files, dcrs, offres, dates
            )

            self.construct_info.config(text=f"✓ {len(constructed)} lignes construites\nTotal: {constructed['NbInteractions'].sum():,.0f}")

            # Exporter automatiquement
            path = filedialog.asksaveasfilename(defaultextension=".xlsx")
            if path:
                constructed.to_excel(path, index=False)
                messagebox.showinfo("OK", f"Fichier construit: {path}")

        except Exception as e:
            messagebox.showerror("Erreur", str(e))


def main():
    root = tk.Tk()
    app = EASYCorrected(root)
    root.mainloop()


if __name__ == "__main__":
    main()
