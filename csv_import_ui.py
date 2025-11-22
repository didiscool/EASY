#!/usr/bin/env python3
"""
CSV Import Interface - Application pour importer et gérer des fichiers CSV
avec filtres, clés de répartition et construction de nouvelles lignes.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
import pandas as pd
from datetime import datetime, timedelta
import os
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

class CSVImportApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Import CSV - Gestion des Interactions")
        self.root.geometry("1600x950")

        self.df = None
        self.filtered_df = None
        self.log_file = "modifications_log.txt"
        self.history = []
        self.max_history = 50
        self.check_vars = {}

        # Clés de répartition
        self.distribution_keys = {}

        # Couleurs pour types
        self.type_colors = {}
        self.color_palette = ['#4CAF50', '#2196F3', '#FF9800', '#E91E63', '#9C27B0',
                              '#00BCD4', '#FFEB3B', '#795548', '#607D8B', '#F44336']

        # Colonnes étendues
        self.columns = ["SegmentMacro", "File", "Segment", "DCR", "Semaine", "Offre",
                       "NbInteractions", "Type", "Date_debut", "Date_fin", "Pas", "Creneau"]

        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Import/Export
        top_frame = ttk.LabelFrame(main_frame, text="Import/Export", padding="3")
        top_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(top_frame, text="Importer", command=self.import_csv).pack(side=tk.LEFT, padx=3)
        ttk.Button(top_frame, text="Exporter", command=self.export_csv).pack(side=tk.LEFT, padx=3)
        ttk.Button(top_frame, text="Importer Clés", command=self.import_keys).pack(side=tk.LEFT, padx=3)
        ttk.Button(top_frame, text="Exporter Clés", command=self.export_keys).pack(side=tk.LEFT, padx=3)
        self.file_label = ttk.Label(top_frame, text="Aucun fichier", font=('TkDefaultFont', 9, 'italic'))
        self.file_label.pack(side=tk.LEFT, padx=10)

        # Filtres globaux
        filter_frame = ttk.LabelFrame(main_frame, text="Filtres globaux", padding="5")
        filter_frame.pack(fill=tk.X, pady=(0, 5))

        filter_row = ttk.Frame(filter_frame)
        filter_row.pack(fill=tk.X)

        for label, var_name, combo_name in [
            ("SegmentMacro:", "segment_macro_var", "segment_macro_combo"),
            ("File:", "file_var", "file_combo"),
            ("Segment:", "segment_var", "segment_combo"),
            ("DCR:", "dcr_var", "dcr_combo"),
            ("Semaine:", "semaine_var", "semaine_combo"),
            ("Type:", "type_var", "type_combo")
        ]:
            ttk.Label(filter_row, text=label).pack(side=tk.LEFT, padx=(0, 2))
            setattr(self, var_name, tk.StringVar())
            combo = ttk.Combobox(filter_row, textvariable=getattr(self, var_name), width=8)
            setattr(self, combo_name, combo)
            combo.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(filter_row, text="Date:").pack(side=tk.LEFT, padx=(0, 2))
        self.date_debut_filter = DateEntry(filter_row, width=9, date_pattern='yyyy-mm-dd')
        self.date_debut_filter.pack(side=tk.LEFT, padx=(0, 2))
        self.date_debut_filter.delete(0, tk.END)
        self.date_fin_filter = DateEntry(filter_row, width=9, date_pattern='yyyy-mm-dd')
        self.date_fin_filter.pack(side=tk.LEFT, padx=(0, 5))
        self.date_fin_filter.delete(0, tk.END)

        ttk.Button(filter_row, text="Filtrer", command=self.apply_filters).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_row, text="Reset", command=self.reset_filters).pack(side=tk.LEFT, padx=2)

        self.active_filters_label = ttk.Label(filter_row, text="", foreground='#0066cc')
        self.active_filters_label.pack(side=tk.LEFT, padx=10)

        # Notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Onglet 1: Visualisation
        self.tab_viz = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_viz, text="Visualisation")

        # Onglet 2: Sélection & Modifications
        self.tab_edit = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_edit, text="Sélection & Modifications")

        # Onglet 3: Clés de répartition
        self.tab_keys = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_keys, text="Clés de répartition")

        # Onglet 4: Construction
        self.tab_construct = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_construct, text="Construction")

        self.setup_viz_tab()
        self.setup_edit_tab()
        self.setup_keys_tab()
        self.setup_construct_tab()

    def setup_viz_tab(self):
        """Visualisation avec histogramme et tableau complet"""
        paned = ttk.PanedWindow(self.tab_viz, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Haut: Résumé + Histogramme
        top_pane = ttk.Frame(paned)
        paned.add(top_pane, weight=1)

        # Résumé
        left_frame = ttk.LabelFrame(top_pane, text="Résumé par Type", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 3))

        self.summary_tree = ttk.Treeview(left_frame, columns=("Type", "Total"), show="headings", height=5)
        self.summary_tree.heading("Type", text="Type")
        self.summary_tree.heading("Total", text="Total")
        self.summary_tree.column("Type", width=80)
        self.summary_tree.column("Total", width=80)
        self.summary_tree.pack(fill=tk.BOTH, expand=True)

        self.total_label = ttk.Label(left_frame, text="Total: 0", font=('TkDefaultFont', 9, 'bold'))
        self.total_label.pack(anchor=tk.E)

        # Histogramme
        right_frame = ttk.LabelFrame(top_pane, text="Évolution par Date (par Type)", padding="5")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.fig = Figure(figsize=(7, 3), dpi=85)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Bas: Tableau complet
        bottom_pane = ttk.LabelFrame(paned, text="Données complètes", padding="3")
        paned.add(bottom_pane, weight=1)

        tree_frame = ttk.Frame(bottom_pane)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.viz_tree = ttk.Treeview(tree_frame, columns=self.columns, show="headings", height=8)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.viz_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.viz_tree.xview)
        self.viz_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.viz_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        for col in self.columns:
            self.viz_tree.heading(col, text=col)
            self.viz_tree.column(col, width=75, minwidth=50)

        self.row_count_label = ttk.Label(bottom_pane, text="0 lignes")
        self.row_count_label.pack(anchor=tk.E)

    def setup_edit_tab(self):
        """Sélection & Modifications avec toutes les colonnes"""
        paned = ttk.PanedWindow(self.tab_edit, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Gauche: Tableau avec checkboxes
        left_pane = ttk.Frame(paned)
        paned.add(left_pane, weight=3)

        control_frame = ttk.LabelFrame(left_pane, text="Sélection", padding="3")
        control_frame.pack(fill=tk.X, pady=(0, 3))

        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Tout", command=self.check_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Rien", command=self.uncheck_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Inverser", command=self.invert_check).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Importer clés sélection", command=self.import_keys_from_selection).pack(side=tk.LEFT, padx=5)
        self.selection_count_label = ttk.Label(btn_frame, text="0/0", font=('TkDefaultFont', 9, 'bold'))
        self.selection_count_label.pack(side=tk.RIGHT, padx=5)

        # Treeview avec checkboxes (toutes les colonnes)
        table_frame = ttk.Frame(left_pane)
        table_frame.pack(fill=tk.BOTH, expand=True)

        edit_columns = ["Sel"] + self.columns
        self.edit_tree = ttk.Treeview(table_frame, columns=edit_columns, show="headings", height=15)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.edit_tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.edit_tree.xview)
        self.edit_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.edit_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.edit_tree.heading("Sel", text="✓")
        self.edit_tree.column("Sel", width=30, minwidth=30)
        for col in self.columns:
            self.edit_tree.heading(col, text=col)
            self.edit_tree.column(col, width=70, minwidth=50)

        self.edit_tree.bind('<Button-1>', self.on_tree_click)

        # Droite: Modifications
        right_pane = ttk.Frame(paned)
        paned.add(right_pane, weight=1)

        # Mode
        mode_frame = ttk.LabelFrame(right_pane, text="Modification", padding="5")
        mode_frame.pack(fill=tk.X, pady=(0, 3))

        self.modify_mode = tk.StringVar(value="relative")
        ttk.Radiobutton(mode_frame, text="Relatif (%)", variable=self.modify_mode,
                       value="relative", command=self.on_mode_change).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Absolu", variable=self.modify_mode,
                       value="global", command=self.on_mode_change).pack(anchor=tk.W)

        self.slider_frame = ttk.Frame(mode_frame)
        self.slider_frame.pack(fill=tk.X, pady=3)
        ttk.Label(self.slider_frame, text="-50%").pack(side=tk.LEFT)
        self.slider_var = tk.DoubleVar(value=0)
        self.slider = ttk.Scale(self.slider_frame, from_=-50, to=50, variable=self.slider_var,
                                orient=tk.HORIZONTAL, command=self.on_slider_change)
        self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)
        ttk.Label(self.slider_frame, text="+50%").pack(side=tk.LEFT)

        self.slider_value_label = ttk.Label(mode_frame, text="0%", font=('TkDefaultFont', 11, 'bold'))
        self.slider_value_label.pack()

        self.absolute_frame = ttk.Frame(mode_frame)
        ttk.Label(self.absolute_frame, text="Valeur:").pack(side=tk.LEFT)
        self.absolute_value_var = tk.StringVar()
        self.absolute_value_var.trace('w', lambda *args: self.update_preview())
        ttk.Entry(self.absolute_frame, textvariable=self.absolute_value_var, width=8).pack(side=tk.LEFT, padx=3)

        # Aperçu
        preview_frame = ttk.LabelFrame(right_pane, text="Aperçu", padding="5")
        preview_frame.pack(fill=tk.X, pady=(0, 3))

        self.before_label = ttk.Label(preview_frame, text="AVANT: -")
        self.before_label.pack(anchor=tk.W)
        self.after_label = ttk.Label(preview_frame, text="APRÈS: -", font=('TkDefaultFont', 9, 'bold'), foreground='#0066cc')
        self.after_label.pack(anchor=tk.W)
        self.diff_label = ttk.Label(preview_frame, text="DIFF: -")
        self.diff_label.pack(anchor=tk.W)

        # Détail
        detail_frame = ttk.LabelFrame(right_pane, text="Détail", padding="3")
        detail_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 3))

        self.detail_tree = ttk.Treeview(detail_frame,
            columns=("Seg", "Type", "Avant", "Après"), show="headings", height=6)
        for col, w in [("Seg", 60), ("Type", 50), ("Avant", 60), ("Après", 60)]:
            self.detail_tree.heading(col, text=col)
            self.detail_tree.column(col, width=w)
        self.detail_tree.pack(fill=tk.BOTH, expand=True)

        # Actions
        action_frame = ttk.Frame(right_pane)
        action_frame.pack(fill=tk.X)
        ttk.Button(action_frame, text="APPLIQUER", command=self.apply_modification).pack(fill=tk.X, pady=1)
        ttk.Button(action_frame, text="Annuler", command=self.undo).pack(fill=tk.X, pady=1)
        self.history_label = ttk.Label(action_frame, text="0 undo", foreground='gray')
        self.history_label.pack()

        self.root.bind('<Control-z>', lambda e: self.undo())
        self.on_mode_change()

    def setup_keys_tab(self):
        """Onglet des clés de répartition"""
        # Notebook interne pour les différents types de clés
        keys_notebook = ttk.Notebook(self.tab_keys)
        keys_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Clé temporelle
        self.temporal_frame = ttk.Frame(keys_notebook)
        keys_notebook.add(self.temporal_frame, text="Temporelle")
        self.setup_temporal_keys()

        # Clé par Type
        self.type_keys_frame = ttk.Frame(keys_notebook)
        keys_notebook.add(self.type_keys_frame, text="Par Type")
        self.setup_type_keys()

        # Clé SegmentMacro dans Type
        self.segmacro_keys_frame = ttk.Frame(keys_notebook)
        keys_notebook.add(self.segmacro_keys_frame, text="SegMacro/Type")
        self.setup_hierarchical_keys(self.segmacro_keys_frame, "segmacro_type")

        # Clé Segment dans SegmentMacro
        self.segment_keys_frame = ttk.Frame(keys_notebook)
        keys_notebook.add(self.segment_keys_frame, text="Seg/SegMacro")
        self.setup_hierarchical_keys(self.segment_keys_frame, "segment_segmacro")

        # Clé DCR
        self.dcr_keys_frame = ttk.Frame(keys_notebook)
        keys_notebook.add(self.dcr_keys_frame, text="DCR")
        self.setup_hierarchical_keys(self.dcr_keys_frame, "dcr")

        # Clé File
        self.file_keys_frame = ttk.Frame(keys_notebook)
        keys_notebook.add(self.file_keys_frame, text="File")
        self.setup_hierarchical_keys(self.file_keys_frame, "file")

        # Clé Offre
        self.offre_keys_frame = ttk.Frame(keys_notebook)
        keys_notebook.add(self.offre_keys_frame, text="Offre")
        self.setup_hierarchical_keys(self.offre_keys_frame, "offre")

        # Boutons calcul
        btn_frame = ttk.Frame(self.tab_keys)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="Calculer toutes les clés depuis les données",
                  command=self.calculate_all_keys).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Réinitialiser les clés", command=self.reset_keys).pack(side=tk.LEFT, padx=5)

    def setup_temporal_keys(self):
        """Configuration des clés temporelles"""
        ttk.Label(self.temporal_frame, text="Pas temporel:", font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W, pady=5)

        self.temporal_step = tk.StringVar(value="semaine")
        for text, val in [("Semaine", "semaine"), ("Jour", "jour"), ("Créneau (30min)", "creneau")]:
            ttk.Radiobutton(self.temporal_frame, text=text, variable=self.temporal_step, value=val).pack(anchor=tk.W)

        # Treeview pour les clés temporelles
        tree_frame = ttk.Frame(self.temporal_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.temporal_tree = ttk.Treeview(tree_frame, columns=("Periode", "Cle"), show="headings", height=10)
        self.temporal_tree.heading("Periode", text="Période")
        self.temporal_tree.heading("Cle", text="Clé (%)")
        self.temporal_tree.column("Periode", width=150)
        self.temporal_tree.column("Cle", width=100)

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.temporal_tree.yview)
        self.temporal_tree.configure(yscrollcommand=scroll.set)
        self.temporal_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Double-clic pour éditer
        self.temporal_tree.bind('<Double-1>', lambda e: self.edit_key_value(self.temporal_tree))

    def setup_type_keys(self):
        """Configuration des clés par type"""
        tree_frame = ttk.Frame(self.type_keys_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=5)

        self.type_keys_tree = ttk.Treeview(tree_frame, columns=("Type", "Cle"), show="headings", height=10)
        self.type_keys_tree.heading("Type", text="Type")
        self.type_keys_tree.heading("Cle", text="Clé (%)")
        self.type_keys_tree.column("Type", width=150)
        self.type_keys_tree.column("Cle", width=100)

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.type_keys_tree.yview)
        self.type_keys_tree.configure(yscrollcommand=scroll.set)
        self.type_keys_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.type_keys_tree.bind('<Double-1>', lambda e: self.edit_key_value(self.type_keys_tree))

    def setup_hierarchical_keys(self, frame, key_type):
        """Configuration des clés hiérarchiques génériques"""
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=5)

        tree = ttk.Treeview(tree_frame, columns=("Item", "Parent", "Cle"), show="headings", height=10)
        tree.heading("Item", text="Élément")
        tree.heading("Parent", text="Parent")
        tree.heading("Cle", text="Clé (%)")
        tree.column("Item", width=120)
        tree.column("Parent", width=120)
        tree.column("Cle", width=80)

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        tree.bind('<Double-1>', lambda e: self.edit_key_value(tree))
        setattr(self, f"{key_type}_tree", tree)

    def setup_construct_tab(self):
        """Onglet de construction de nouvelles lignes"""
        # Paramètres de construction
        params_frame = ttk.LabelFrame(self.tab_construct, text="Paramètres de construction", padding="10")
        params_frame.pack(fill=tk.X, padx=5, pady=5)

        # Global
        row1 = ttk.Frame(params_frame)
        row1.pack(fill=tk.X, pady=3)
        ttk.Label(row1, text="NbInteractions Global:").pack(side=tk.LEFT)
        self.global_interactions = tk.StringVar(value="1000")
        ttk.Entry(row1, textvariable=self.global_interactions, width=10).pack(side=tk.LEFT, padx=5)

        # Pas temporel
        row2 = ttk.Frame(params_frame)
        row2.pack(fill=tk.X, pady=3)
        ttk.Label(row2, text="Pas:").pack(side=tk.LEFT)
        self.construct_step = tk.StringVar(value="jour")
        for text, val in [("Semaine", "semaine"), ("Jour", "jour"), ("Créneau", "creneau")]:
            ttk.Radiobutton(row2, text=text, variable=self.construct_step, value=val).pack(side=tk.LEFT, padx=5)

        # Dates
        row3 = ttk.Frame(params_frame)
        row3.pack(fill=tk.X, pady=3)
        ttk.Label(row3, text="Date début:").pack(side=tk.LEFT)
        self.construct_date_debut = DateEntry(row3, width=10, date_pattern='yyyy-mm-dd')
        self.construct_date_debut.pack(side=tk.LEFT, padx=5)
        ttk.Label(row3, text="Date fin:").pack(side=tk.LEFT)
        self.construct_date_fin = DateEntry(row3, width=10, date_pattern='yyyy-mm-dd')
        self.construct_date_fin.pack(side=tk.LEFT, padx=5)

        # Créneaux
        row4 = ttk.Frame(params_frame)
        row4.pack(fill=tk.X, pady=3)
        ttk.Label(row4, text="Heure début:").pack(side=tk.LEFT)
        self.construct_hour_start = tk.StringVar(value="08:00")
        ttk.Entry(row4, textvariable=self.construct_hour_start, width=6).pack(side=tk.LEFT, padx=5)
        ttk.Label(row4, text="Heure fin:").pack(side=tk.LEFT)
        self.construct_hour_end = tk.StringVar(value="18:00")
        ttk.Entry(row4, textvariable=self.construct_hour_end, width=6).pack(side=tk.LEFT, padx=5)

        # Jours inclus
        row5 = ttk.Frame(params_frame)
        row5.pack(fill=tk.X, pady=3)
        ttk.Label(row5, text="Jours:").pack(side=tk.LEFT)
        self.days_included = {}
        for i, day in enumerate(["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]):
            self.days_included[i] = tk.BooleanVar(value=i < 5)  # Lun-Ven par défaut
            ttk.Checkbutton(row5, text=day, variable=self.days_included[i]).pack(side=tk.LEFT, padx=2)

        # Définitions hiérarchiques
        def_frame = ttk.LabelFrame(self.tab_construct, text="Définitions hiérarchiques", padding="5")
        def_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Notebook pour les définitions
        def_notebook = ttk.Notebook(def_frame)
        def_notebook.pack(fill=tk.BOTH, expand=True)

        # SegmentMacro
        self.def_segmacro_frame = ttk.Frame(def_notebook)
        def_notebook.add(self.def_segmacro_frame, text="SegmentMacro")
        self.setup_definition_list(self.def_segmacro_frame, "segmacro")

        # Segments
        self.def_segment_frame = ttk.Frame(def_notebook)
        def_notebook.add(self.def_segment_frame, text="Segment")
        self.setup_definition_list(self.def_segment_frame, "segment")

        # Files
        self.def_file_frame = ttk.Frame(def_notebook)
        def_notebook.add(self.def_file_frame, text="File")
        self.setup_definition_list(self.def_file_frame, "file_def")

        # DCR
        self.def_dcr_frame = ttk.Frame(def_notebook)
        def_notebook.add(self.def_dcr_frame, text="DCR")
        self.setup_definition_list(self.def_dcr_frame, "dcr_def")

        # Offre
        self.def_offre_frame = ttk.Frame(def_notebook)
        def_notebook.add(self.def_offre_frame, text="Offre")
        self.setup_definition_list(self.def_offre_frame, "offre_def")

        # Type
        self.def_type_frame = ttk.Frame(def_notebook)
        def_notebook.add(self.def_type_frame, text="Type")
        self.setup_definition_list(self.def_type_frame, "type_def")

        # Bouton construction
        btn_frame = ttk.Frame(self.tab_construct)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="CONSTRUIRE LES LIGNES", command=self.construct_rows).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Aperçu", command=self.preview_construction).pack(side=tk.LEFT, padx=5)

    def setup_definition_list(self, frame, list_name):
        """Créer une liste de définition avec ajout/suppression"""
        top_frame = ttk.Frame(frame)
        top_frame.pack(fill=tk.X, pady=3)

        ttk.Label(top_frame, text="Valeur:").pack(side=tk.LEFT)
        entry_var = tk.StringVar()
        setattr(self, f"{list_name}_entry", entry_var)
        ttk.Entry(top_frame, textvariable=entry_var, width=15).pack(side=tk.LEFT, padx=3)

        ttk.Label(top_frame, text="Parent:").pack(side=tk.LEFT)
        parent_var = tk.StringVar()
        setattr(self, f"{list_name}_parent", parent_var)
        parent_combo = ttk.Combobox(top_frame, textvariable=parent_var, width=12)
        setattr(self, f"{list_name}_parent_combo", parent_combo)
        parent_combo.pack(side=tk.LEFT, padx=3)

        ttk.Button(top_frame, text="Ajouter",
                  command=lambda: self.add_definition(list_name)).pack(side=tk.LEFT, padx=3)
        ttk.Button(top_frame, text="Supprimer",
                  command=lambda: self.remove_definition(list_name)).pack(side=tk.LEFT, padx=3)

        # Listbox
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=3)

        listbox = tk.Listbox(list_frame, height=8)
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scroll.set)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        setattr(self, f"{list_name}_listbox", listbox)

    def add_definition(self, list_name):
        """Ajouter une définition"""
        entry_var = getattr(self, f"{list_name}_entry")
        parent_var = getattr(self, f"{list_name}_parent")
        listbox = getattr(self, f"{list_name}_listbox")

        value = entry_var.get().strip()
        parent = parent_var.get().strip()

        if value:
            if parent:
                listbox.insert(tk.END, f"{value} ({parent})")
            else:
                listbox.insert(tk.END, value)
            entry_var.set("")

    def remove_definition(self, list_name):
        """Supprimer une définition"""
        listbox = getattr(self, f"{list_name}_listbox")
        selection = listbox.curselection()
        if selection:
            listbox.delete(selection[0])

    def on_tree_click(self, event):
        """Gérer le clic sur le treeview pour toggle checkbox"""
        region = self.edit_tree.identify_region(event.x, event.y)
        if region == "cell":
            col = self.edit_tree.identify_column(event.x)
            if col == "#1":  # Colonne Sel
                item = self.edit_tree.identify_row(event.y)
                if item:
                    idx = int(item)
                    if idx in self.check_vars:
                        self.check_vars[idx].set(not self.check_vars[idx].get())
                        self.update_edit_tree_selection()
                        self.update_selection_count()
                        self.update_preview()

    def update_edit_tree_selection(self):
        """Mettre à jour l'affichage des checkboxes"""
        for item in self.edit_tree.get_children():
            idx = int(item)
            if idx in self.check_vars:
                checked = "✓" if self.check_vars[idx].get() else ""
                values = list(self.edit_tree.item(item)['values'])
                values[0] = checked
                self.edit_tree.item(item, values=values)

    # ... (méthodes existantes conservées et adaptées)

    def _on_mousewheel(self, event):
        pass  # Géré par les treeviews

    def on_mode_change(self):
        if self.modify_mode.get() == "relative":
            self.slider_frame.pack(fill=tk.X, pady=3)
            self.slider_value_label.pack()
            self.absolute_frame.pack_forget()
        else:
            self.slider_frame.pack_forget()
            self.slider_value_label.pack_forget()
            self.absolute_frame.pack(fill=tk.X, pady=3)
        self.update_preview()

    def on_slider_change(self, value):
        val = float(value)
        self.slider_value_label.config(text=f"{'+' if val >= 0 else ''}{val:.0f}%")
        self.update_preview()

    def import_csv(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv"), ("All files", "*.*")])
        if file_path:
            try:
                if file_path.endswith('.xlsx'):
                    self.df = pd.read_excel(file_path, engine='openpyxl')
                else:
                    self.df = pd.read_csv(file_path, sep=None, engine='python')
                # Ajouter colonnes manquantes
                for col in ["Pas", "Creneau"]:
                    if col not in self.df.columns:
                        self.df[col] = ""
                self.filtered_df = self.df.copy()
                self.file_label.config(text=os.path.basename(file_path))
                self.history = []
                self.check_vars = {}
                self.assign_type_colors()
                self.populate_filters()
                self.update_all_views()
                self.calculate_all_keys()
                messagebox.showinfo("OK", f"{len(self.df)} lignes importées")
            except Exception as e:
                messagebox.showerror("Erreur", str(e))

    def export_csv(self):
        if self.df is None:
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                  filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.df.to_csv(file_path, index=False)
            messagebox.showinfo("OK", f"Exporté: {file_path}")

    def import_keys(self):
        """Importer les clés depuis un fichier Excel"""
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx"), ("JSON files", "*.json")])
        if file_path:
            try:
                if file_path.endswith('.xlsx'):
                    # Lire toutes les feuilles Excel
                    xlsx = pd.ExcelFile(file_path, engine='openpyxl')
                    self.distribution_keys = {}
                    for sheet_name in xlsx.sheet_names:
                        df = pd.read_excel(xlsx, sheet_name=sheet_name)
                        if len(df.columns) >= 2:
                            key_dict = dict(zip(df.iloc[:, 0].astype(str), df.iloc[:, 1]))
                            self.distribution_keys[sheet_name] = key_dict
                else:
                    with open(file_path, 'r') as f:
                        self.distribution_keys = json.load(f)
                self.refresh_keys_display()
                messagebox.showinfo("OK", "Clés importées")
            except Exception as e:
                messagebox.showerror("Erreur", str(e))

    def export_keys(self):
        """Exporter les clés vers un fichier Excel"""
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                  filetypes=[("Excel files", "*.xlsx"), ("JSON files", "*.json")])
        if file_path:
            try:
                if file_path.endswith('.xlsx'):
                    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                        for key_name, key_data in self.distribution_keys.items():
                            if isinstance(key_data, dict):
                                df = pd.DataFrame(list(key_data.items()), columns=['Element', 'Cle'])
                                df.to_excel(writer, sheet_name=key_name[:31], index=False)
                else:
                    with open(file_path, 'w') as f:
                        json.dump(self.distribution_keys, f, indent=2)
                messagebox.showinfo("OK", f"Clés exportées: {file_path}")
            except Exception as e:
                messagebox.showerror("Erreur", str(e))

    def import_keys_from_selection(self):
        """Calculer les clés depuis la sélection actuelle"""
        selected = self.get_selected_indices()
        if not selected:
            messagebox.showwarning("Attention", "Sélectionnez des lignes")
            return

        selected_df = self.df.loc[selected]
        self.calculate_keys_from_df(selected_df)
        messagebox.showinfo("OK", "Clés calculées depuis la sélection")

    def calculate_all_keys(self):
        """Calculer toutes les clés depuis les données filtrées"""
        if self.filtered_df is None:
            return
        self.calculate_keys_from_df(self.filtered_df)
        self.refresh_keys_display()

    def calculate_keys_from_df(self, df):
        """Calculer les clés de répartition depuis un DataFrame"""
        if df.empty:
            return

        total = df["NbInteractions"].sum()
        if total == 0:
            return

        # Clés par Type
        type_keys = df.groupby("Type")["NbInteractions"].sum() / total * 100
        self.distribution_keys["type"] = type_keys.to_dict()

        # Clés temporelles
        if "Date_debut" in df.columns:
            df_temp = df.copy()
            df_temp["Date_debut"] = pd.to_datetime(df_temp["Date_debut"], errors='coerce')
            temporal_keys = df_temp.groupby(df_temp["Date_debut"].dt.strftime('%Y-%m-%d'))["NbInteractions"].sum()
            temporal_keys = temporal_keys / total * 100
            self.distribution_keys["temporal"] = temporal_keys.to_dict()

        # Clés SegmentMacro dans Type
        if "SegmentMacro" in df.columns and "Type" in df.columns:
            keys = {}
            for type_name in df["Type"].unique():
                type_df = df[df["Type"] == type_name]
                type_total = type_df["NbInteractions"].sum()
                if type_total > 0:
                    segmacro_keys = type_df.groupby("SegmentMacro")["NbInteractions"].sum() / type_total * 100
                    keys[type_name] = segmacro_keys.to_dict()
            self.distribution_keys["segmacro_type"] = keys

        # Autres clés hiérarchiques...
        self.refresh_keys_display()

    def refresh_keys_display(self):
        """Rafraîchir l'affichage des clés"""
        # Temporel
        for item in self.temporal_tree.get_children():
            self.temporal_tree.delete(item)
        if "temporal" in self.distribution_keys:
            for period, key in self.distribution_keys["temporal"].items():
                self.temporal_tree.insert("", tk.END, values=(period, f"{key:.2f}"))

        # Type
        for item in self.type_keys_tree.get_children():
            self.type_keys_tree.delete(item)
        if "type" in self.distribution_keys:
            for type_name, key in self.distribution_keys["type"].items():
                self.type_keys_tree.insert("", tk.END, values=(type_name, f"{key:.2f}"))

    def reset_keys(self):
        """Réinitialiser les clés"""
        self.distribution_keys = {}
        self.refresh_keys_display()

    def edit_key_value(self, tree):
        """Éditer une valeur de clé"""
        selection = tree.selection()
        if not selection:
            return

        item = selection[0]
        values = tree.item(item)['values']

        # Dialog simple pour éditer
        dialog = tk.Toplevel(self.root)
        dialog.title("Modifier la clé")
        dialog.geometry("250x100")

        ttk.Label(dialog, text="Nouvelle valeur (%):").pack(pady=5)
        entry = ttk.Entry(dialog)
        entry.insert(0, values[-1])
        entry.pack(pady=5)

        def save():
            try:
                new_val = float(entry.get())
                new_values = list(values)
                new_values[-1] = f"{new_val:.2f}"
                tree.item(item, values=new_values)
                dialog.destroy()
            except:
                pass

        ttk.Button(dialog, text="OK", command=save).pack(pady=5)

    def construct_rows(self):
        """Construire les nouvelles lignes"""
        try:
            global_val = float(self.global_interactions.get())
        except:
            messagebox.showerror("Erreur", "Valeur globale invalide")
            return

        # Récupérer les définitions
        rows = []

        # Exemple simplifié - à développer selon les besoins
        messagebox.showinfo("Info", "Construction en cours de développement")

    def preview_construction(self):
        """Aperçu de la construction"""
        messagebox.showinfo("Aperçu", "Aperçu en cours de développement")

    def assign_type_colors(self):
        if self.df is None or "Type" not in self.df.columns:
            return
        types = self.df["Type"].dropna().unique()
        self.type_colors = {t: self.color_palette[i % len(self.color_palette)]
                           for i, t in enumerate(types)}

    def populate_filters(self):
        if self.df is None:
            return
        for combo, col in [
            (self.segment_macro_combo, "SegmentMacro"), (self.file_combo, "File"),
            (self.segment_combo, "Segment"), (self.dcr_combo, "DCR"),
            (self.semaine_combo, "Semaine"), (self.type_combo, "Type")
        ]:
            if col in self.df.columns:
                values = [""] + sorted(self.df[col].dropna().unique().astype(str).tolist())
                combo["values"] = values
                combo.set("")

    def apply_filters(self):
        if self.df is None:
            return
        self.filtered_df = self.df.copy()
        for var, col in [
            (self.segment_macro_var, "SegmentMacro"), (self.file_var, "File"),
            (self.segment_var, "Segment"), (self.dcr_var, "DCR"),
            (self.semaine_var, "Semaine"), (self.type_var, "Type")
        ]:
            if var.get() and col in self.filtered_df.columns:
                self.filtered_df = self.filtered_df[self.filtered_df[col].astype(str) == var.get()]

        if self.date_debut_filter.get() and self.date_fin_filter.get() and "Date_debut" in self.filtered_df.columns:
            try:
                self.filtered_df["Date_debut"] = pd.to_datetime(self.filtered_df["Date_debut"], errors='coerce')
                self.filtered_df = self.filtered_df[
                    (self.filtered_df["Date_debut"] >= pd.to_datetime(self.date_debut_filter.get())) &
                    (self.filtered_df["Date_debut"] <= pd.to_datetime(self.date_fin_filter.get()))
                ]
            except:
                pass

        self.update_active_filters_display()
        self.update_all_views()

    def reset_filters(self):
        for var in [self.segment_macro_var, self.file_var, self.segment_var,
                    self.dcr_var, self.semaine_var, self.type_var]:
            var.set("")
        self.date_debut_filter.delete(0, tk.END)
        self.date_fin_filter.delete(0, tk.END)
        if self.df is not None:
            self.filtered_df = self.df.copy()
            self.update_active_filters_display()
            self.update_all_views()

    def update_active_filters_display(self):
        active = []
        for var, name in [
            (self.segment_macro_var, "SM"), (self.file_var, "F"),
            (self.segment_var, "S"), (self.dcr_var, "D"),
            (self.semaine_var, "Sem"), (self.type_var, "T")
        ]:
            if var.get():
                active.append(f"{name}={var.get()}")
        self.active_filters_label.config(text=" ".join(active) if active else "")

    def update_all_views(self):
        self.update_viz_table()
        self.update_summary()
        self.update_histogram()
        self.update_edit_table()
        self.update_preview()
        self.update_history_label()

    def update_viz_table(self):
        for item in self.viz_tree.get_children():
            self.viz_tree.delete(item)
        if self.filtered_df is None:
            self.row_count_label.config(text="0 lignes")
            return
        for idx, row in self.filtered_df.iterrows():
            values = [row.get(col, "") for col in self.columns]
            self.viz_tree.insert("", tk.END, values=values)
        self.row_count_label.config(text=f"{len(self.filtered_df)} lignes")

    def update_edit_table(self):
        """Mettre à jour le tableau d'édition avec toutes les colonnes"""
        for item in self.edit_tree.get_children():
            self.edit_tree.delete(item)
        if self.filtered_df is None:
            return

        for idx, row in self.filtered_df.iterrows():
            if idx not in self.check_vars:
                self.check_vars[idx] = tk.BooleanVar(value=False)

            checked = "✓" if self.check_vars[idx].get() else ""
            values = [checked] + [row.get(col, "") for col in self.columns]
            self.edit_tree.insert("", tk.END, iid=idx, values=values)

        self.update_selection_count()

    def update_selection_count(self):
        if self.filtered_df is None:
            self.selection_count_label.config(text="0/0")
            return
        selected = sum(1 for idx in self.filtered_df.index if self.check_vars.get(idx, tk.BooleanVar()).get())
        self.selection_count_label.config(text=f"{selected}/{len(self.filtered_df)}")

    def check_all(self):
        if self.filtered_df is None:
            return
        for idx in self.filtered_df.index:
            if idx in self.check_vars:
                self.check_vars[idx].set(True)
        self.update_edit_tree_selection()
        self.update_selection_count()
        self.update_preview()

    def uncheck_all(self):
        for var in self.check_vars.values():
            var.set(False)
        self.update_edit_tree_selection()
        self.update_selection_count()
        self.update_preview()

    def invert_check(self):
        if self.filtered_df is None:
            return
        for idx in self.filtered_df.index:
            if idx in self.check_vars:
                self.check_vars[idx].set(not self.check_vars[idx].get())
        self.update_edit_tree_selection()
        self.update_selection_count()
        self.update_preview()

    def update_summary(self):
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)
        if self.filtered_df is None:
            self.total_label.config(text="Total: 0")
            return
        if "Type" in self.filtered_df.columns and "NbInteractions" in self.filtered_df.columns:
            summary = self.filtered_df.groupby("Type")["NbInteractions"].sum().reset_index()
            for _, row in summary.iterrows():
                self.summary_tree.insert("", tk.END, values=(row["Type"], f"{int(row['NbInteractions']):,}"))
            total = self.filtered_df["NbInteractions"].sum()
            self.total_label.config(text=f"Total: {int(total):,}")

    def update_histogram(self):
        self.ax.clear()
        if self.filtered_df is None or self.filtered_df.empty:
            self.ax.text(0.5, 0.5, 'Aucune donnée', ha='center', va='center')
            self.canvas.draw()
            return
        if "Date_debut" not in self.filtered_df.columns or "Type" not in self.filtered_df.columns:
            self.canvas.draw()
            return

        df_chart = self.filtered_df.copy()
        df_chart["Date_debut"] = pd.to_datetime(df_chart["Date_debut"], errors='coerce')
        df_chart = df_chart.dropna(subset=["Date_debut"])
        if df_chart.empty:
            self.canvas.draw()
            return

        pivot = df_chart.groupby([df_chart["Date_debut"].dt.strftime('%Y-%m-%d'), "Type"])["NbInteractions"].sum().unstack(fill_value=0)
        dates = pivot.index.tolist()
        bottom = np.zeros(len(dates))

        for type_name in pivot.columns:
            values = pivot[type_name].values
            color = self.type_colors.get(type_name, '#888888')
            self.ax.bar(dates, values, bottom=bottom, label=type_name, color=color)
            bottom += values

        self.ax.set_xlabel('Date')
        self.ax.set_ylabel('Interactions')
        self.ax.tick_params(axis='x', rotation=45, labelsize=7)
        self.ax.legend(loc='upper right', fontsize=7)
        self.fig.tight_layout()
        self.canvas.draw()

    def get_selected_indices(self):
        if self.filtered_df is None:
            return []
        return [idx for idx in self.filtered_df.index if self.check_vars.get(idx, tk.BooleanVar()).get()]

    def update_preview(self):
        selected = self.get_selected_indices()
        if not selected:
            self.before_label.config(text="AVANT: -")
            self.after_label.config(text="APRÈS: -")
            self.diff_label.config(text="DIFF: -")
            for item in self.detail_tree.get_children():
                self.detail_tree.delete(item)
            return

        total_before = sum(self.df.at[idx, "NbInteractions"] for idx in selected)
        if self.modify_mode.get() == "relative":
            pct = self.slider_var.get() / 100
            total_after = sum(self.df.at[idx, "NbInteractions"] * (1 + pct) for idx in selected)
        else:
            try:
                val = float(self.absolute_value_var.get())
                total_after = val * len(selected)
            except:
                total_after = total_before

        diff = total_after - total_before
        diff_pct = (diff / total_before * 100) if total_before else 0

        self.before_label.config(text=f"AVANT: {total_before:,.0f}")
        self.after_label.config(text=f"APRÈS: {total_after:,.0f}")
        color = '#008000' if diff >= 0 else '#cc0000'
        self.diff_label.config(text=f"DIFF: {'+' if diff >= 0 else ''}{diff:,.0f} ({diff_pct:+.1f}%)", foreground=color)

        for item in self.detail_tree.get_children():
            self.detail_tree.delete(item)
        for idx in selected[:30]:
            row = self.df.loc[idx]
            avant = row["NbInteractions"]
            if self.modify_mode.get() == "relative":
                apres = avant * (1 + self.slider_var.get() / 100)
            else:
                try:
                    apres = float(self.absolute_value_var.get())
                except:
                    apres = avant
            self.detail_tree.insert("", tk.END, values=(
                row.get("Segment", "")[:8], row.get("Type", "")[:6],
                f"{avant:,.0f}", f"{apres:,.0f}"
            ))

    def update_history_label(self):
        self.history_label.config(text=f"{len(self.history)} undo")

    def save_state(self):
        if self.df is not None:
            self.history.append(self.df.copy())
            if len(self.history) > self.max_history:
                self.history.pop(0)
            self.update_history_label()

    def apply_modification(self):
        selected = self.get_selected_indices()
        if not selected:
            messagebox.showwarning("Attention", "Sélectionnez des lignes")
            return

        self.save_state()
        total_before = total_after = 0

        for idx in selected:
            old_val = self.df.at[idx, "NbInteractions"]
            total_before += old_val
            if self.modify_mode.get() == "relative":
                new_val = int(round(old_val * (1 + self.slider_var.get() / 100)))
            else:
                try:
                    new_val = int(float(self.absolute_value_var.get()))
                except:
                    continue
            total_after += new_val
            self.df.at[idx, "NbInteractions"] = new_val

        self.apply_filters()
        diff = total_after - total_before
        messagebox.showinfo("OK", f"{len(selected)} lignes\nAvant: {total_before:,}\nAprès: {total_after:,}")

    def undo(self):
        if not self.history:
            return
        self.df = self.history.pop()
        self.apply_filters()

def main():
    root = tk.Tk()
    app = CSVImportApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
