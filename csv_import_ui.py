#!/usr/bin/env python3
"""
CSV Import Interface - Application pour importer et gérer des fichiers CSV
avec filtres, prévisualisation et modification des interactions.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
import pandas as pd
from datetime import datetime
import os
import copy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class CSVImportApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Import CSV - Gestion des Interactions")
        self.root.geometry("1400x900")

        self.df = None
        self.filtered_df = None
        self.log_file = "modifications_log.txt"
        self.history = []
        self.max_history = 50

        self.setup_ui()

    def setup_ui(self):
        # Frame principale
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Section import/export (toujours visible en haut)
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        import_frame = ttk.LabelFrame(top_frame, text="Import/Export", padding="5")
        import_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(import_frame, text="Importer CSV", command=self.import_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(import_frame, text="Exporter CSV", command=self.export_csv).pack(side=tk.LEFT, padx=5)
        self.file_label = ttk.Label(import_frame, text="Aucun fichier sélectionné", font=('TkDefaultFont', 9, 'italic'))
        self.file_label.pack(side=tk.LEFT, padx=15)

        # Notebook (onglets)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Onglet 1: Données & Filtres
        self.tab_data = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_data, text="Données & Filtres")

        # Onglet 2: Modifications
        self.tab_modify = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_modify, text="Modifications")

        # Onglet 3: Visualisation
        self.tab_viz = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_viz, text="Visualisation")

        self.setup_data_tab()
        self.setup_modify_tab()
        self.setup_viz_tab()

    def setup_data_tab(self):
        """Configuration de l'onglet Données & Filtres"""

        # Section filtres
        filter_frame = ttk.LabelFrame(self.tab_data, text="Filtres", padding="10")
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        # Ligne 1: Filtres textuels
        filter_row1 = ttk.Frame(filter_frame)
        filter_row1.pack(fill=tk.X, pady=5)

        # SegmentMacro
        ttk.Label(filter_row1, text="SegmentMacro:").pack(side=tk.LEFT, padx=(0, 5))
        self.segment_macro_var = tk.StringVar()
        self.segment_macro_combo = ttk.Combobox(filter_row1, textvariable=self.segment_macro_var, width=12)
        self.segment_macro_combo.pack(side=tk.LEFT, padx=(0, 15))

        # File
        ttk.Label(filter_row1, text="File:").pack(side=tk.LEFT, padx=(0, 5))
        self.file_var = tk.StringVar()
        self.file_combo = ttk.Combobox(filter_row1, textvariable=self.file_var, width=12)
        self.file_combo.pack(side=tk.LEFT, padx=(0, 15))

        # Segment
        ttk.Label(filter_row1, text="Segment:").pack(side=tk.LEFT, padx=(0, 5))
        self.segment_var = tk.StringVar()
        self.segment_combo = ttk.Combobox(filter_row1, textvariable=self.segment_var, width=12)
        self.segment_combo.pack(side=tk.LEFT, padx=(0, 15))

        # DCR
        ttk.Label(filter_row1, text="DCR:").pack(side=tk.LEFT, padx=(0, 5))
        self.dcr_var = tk.StringVar()
        self.dcr_combo = ttk.Combobox(filter_row1, textvariable=self.dcr_var, width=12)
        self.dcr_combo.pack(side=tk.LEFT, padx=(0, 15))

        # Ligne 2: Filtres supplémentaires
        filter_row2 = ttk.Frame(filter_frame)
        filter_row2.pack(fill=tk.X, pady=5)

        # Semaine
        ttk.Label(filter_row2, text="Semaine:").pack(side=tk.LEFT, padx=(0, 5))
        self.semaine_var = tk.StringVar()
        self.semaine_combo = ttk.Combobox(filter_row2, textvariable=self.semaine_var, width=12)
        self.semaine_combo.pack(side=tk.LEFT, padx=(0, 15))

        # Type
        ttk.Label(filter_row2, text="Type:").pack(side=tk.LEFT, padx=(0, 5))
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(filter_row2, textvariable=self.type_var, width=12)
        self.type_combo.pack(side=tk.LEFT, padx=(0, 15))

        # Ligne 3: Filtre Date (sans checkbox)
        filter_row3 = ttk.Frame(filter_frame)
        filter_row3.pack(fill=tk.X, pady=5)

        ttk.Label(filter_row3, text="Date début (de):").pack(side=tk.LEFT, padx=(0, 5))
        self.date_debut_filter = DateEntry(filter_row3, width=12, date_pattern='yyyy-mm-dd')
        self.date_debut_filter.pack(side=tk.LEFT, padx=(0, 10))
        self.date_debut_filter.delete(0, tk.END)  # Vider par défaut

        ttk.Label(filter_row3, text="à:").pack(side=tk.LEFT, padx=(0, 5))
        self.date_fin_filter = DateEntry(filter_row3, width=12, date_pattern='yyyy-mm-dd')
        self.date_fin_filter.pack(side=tk.LEFT, padx=(0, 15))
        self.date_fin_filter.delete(0, tk.END)  # Vider par défaut

        ttk.Button(filter_row3, text="Effacer dates", command=self.clear_date_filters).pack(side=tk.LEFT, padx=5)

        # Ligne 4: Boutons
        filter_row4 = ttk.Frame(filter_frame)
        filter_row4.pack(fill=tk.X, pady=5)

        ttk.Button(filter_row4, text="Appliquer Filtres", command=self.apply_filters,
                  style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_row4, text="Réinitialiser tout", command=self.reset_filters).pack(side=tk.LEFT, padx=5)

        # Section filtres actifs
        active_frame = ttk.LabelFrame(self.tab_data, text="Filtres actifs", padding="5")
        active_frame.pack(fill=tk.X, pady=(0, 10))

        self.active_filters_label = ttk.Label(active_frame, text="Aucun filtre actif",
                                               font=('TkDefaultFont', 10, 'bold'), foreground='gray')
        self.active_filters_label.pack(side=tk.LEFT, padx=10, pady=5)

        # Section prévisualisation
        preview_frame = ttk.LabelFrame(self.tab_data, text="Prévisualisation des données", padding="5")
        preview_frame.pack(fill=tk.BOTH, expand=True)

        # Boutons de sélection
        select_frame = ttk.Frame(preview_frame)
        select_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(select_frame, text="Tout sélectionner", command=self.select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(select_frame, text="Tout désélectionner", command=self.deselect_all).pack(side=tk.LEFT, padx=5)

        self.row_count_label = ttk.Label(select_frame, text="0 lignes")
        self.row_count_label.pack(side=tk.RIGHT, padx=10)

        # Treeview
        tree_container = ttk.Frame(preview_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)

        self.columns = ["SegmentMacro", "File", "Segment", "DCR", "Semaine", "Offre",
                       "NbInteractions", "Type", "Date_debut", "Date_fin"]

        self.tree = ttk.Treeview(tree_container, columns=self.columns, show="headings", selectmode="extended")

        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, minwidth=50)

        self.tree.bind("<<TreeviewSelect>>", self.on_selection_change)

    def setup_modify_tab(self):
        """Configuration de l'onglet Modifications"""

        # Résumé de la sélection
        selection_frame = ttk.LabelFrame(self.tab_modify, text="Sélection actuelle", padding="10")
        selection_frame.pack(fill=tk.X, pady=(0, 10))

        self.selection_info = ttk.Label(selection_frame,
                                        text="Aucune sélection - Sélectionnez des lignes dans l'onglet 'Données & Filtres'",
                                        font=('TkDefaultFont', 11))
        self.selection_info.pack(pady=5)

        # Mode de modification
        mode_frame = ttk.LabelFrame(self.tab_modify, text="Mode de modification", padding="10")
        mode_frame.pack(fill=tk.X, pady=(0, 10))

        self.modify_mode = tk.StringVar(value="global")

        mode_row = ttk.Frame(mode_frame)
        mode_row.pack(fill=tk.X, pady=5)

        ttk.Radiobutton(mode_row, text="Valeur globale (remplacer par)", variable=self.modify_mode,
                       value="global", command=self.update_preview).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_row, text="Modification relative (%)", variable=self.modify_mode,
                       value="relative", command=self.update_preview).pack(side=tk.LEFT, padx=10)

        value_row = ttk.Frame(mode_frame)
        value_row.pack(fill=tk.X, pady=10)

        ttk.Label(value_row, text="Valeur:", font=('TkDefaultFont', 10, 'bold')).pack(side=tk.LEFT, padx=(10, 5))
        self.new_value_var = tk.StringVar()
        self.new_value_var.trace('w', lambda *args: self.update_preview())
        self.new_value_entry = ttk.Entry(value_row, textvariable=self.new_value_var, width=20, font=('TkDefaultFont', 12))
        self.new_value_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(value_row, text="(ex: 100 pour global, +10 ou -20 pour relatif %)",
                 foreground='gray').pack(side=tk.LEFT, padx=10)

        # Aperçu avant/après
        preview_frame = ttk.LabelFrame(self.tab_modify, text="Aperçu des modifications", padding="10")
        preview_frame.pack(fill=tk.X, pady=(0, 10))

        self.before_label = ttk.Label(preview_frame, text="AVANT: -", font=('TkDefaultFont', 12))
        self.before_label.pack(anchor=tk.W, pady=2)

        self.after_label = ttk.Label(preview_frame, text="APRÈS: -", font=('TkDefaultFont', 12, 'bold'))
        self.after_label.pack(anchor=tk.W, pady=2)

        self.diff_label = ttk.Label(preview_frame, text="DIFFÉRENCE: -", font=('TkDefaultFont', 12))
        self.diff_label.pack(anchor=tk.W, pady=2)

        # Actions
        action_frame = ttk.LabelFrame(self.tab_modify, text="Actions", padding="10")
        action_frame.pack(fill=tk.X, pady=(0, 10))

        btn_row = ttk.Frame(action_frame)
        btn_row.pack(fill=tk.X, pady=5)

        apply_btn = ttk.Button(btn_row, text="APPLIQUER LA MODIFICATION",
                               command=self.modify_selection, style='Accent.TButton')
        apply_btn.pack(side=tk.LEFT, padx=10, pady=5)

        undo_btn = ttk.Button(btn_row, text="Annuler (Ctrl+Z)", command=self.undo)
        undo_btn.pack(side=tk.LEFT, padx=10, pady=5)

        log_btn = ttk.Button(btn_row, text="Voir historique", command=self.view_log)
        log_btn.pack(side=tk.LEFT, padx=10, pady=5)

        # Info historique
        self.history_label = ttk.Label(action_frame, text="Historique: 0 modification(s) annulable(s)",
                                       foreground='gray')
        self.history_label.pack(anchor=tk.W, padx=10)

        # Raccourci clavier
        self.root.bind('<Control-z>', lambda e: self.undo())

    def setup_viz_tab(self):
        """Configuration de l'onglet Visualisation"""

        # Résumé par Type
        summary_frame = ttk.LabelFrame(self.tab_viz, text="Somme NbInteractions par Type", padding="10")
        summary_frame.pack(fill=tk.X, pady=(0, 10))

        self.summary_tree = ttk.Treeview(summary_frame, columns=("Type", "Total"), show="headings", height=5)
        self.summary_tree.heading("Type", text="Type")
        self.summary_tree.heading("Total", text="Total Interactions")
        self.summary_tree.column("Type", width=200)
        self.summary_tree.column("Total", width=200)
        self.summary_tree.pack(fill=tk.X)

        # Histogramme
        chart_frame = ttk.LabelFrame(self.tab_viz, text="Évolution NbInteractions par Date début", padding="10")
        chart_frame.pack(fill=tk.BOTH, expand=True)

        self.fig = Figure(figsize=(12, 5), dpi=80)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def clear_date_filters(self):
        """Effacer les filtres de date"""
        self.date_debut_filter.delete(0, tk.END)
        self.date_fin_filter.delete(0, tk.END)

    def select_all(self):
        """Sélectionner toutes les lignes"""
        for item in self.tree.get_children():
            self.tree.selection_add(item)
        self.on_selection_change()

    def deselect_all(self):
        """Désélectionner toutes les lignes"""
        self.tree.selection_remove(*self.tree.get_children())
        self.on_selection_change()

    def import_csv(self):
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if file_path:
            try:
                self.df = pd.read_csv(file_path, sep=None, engine='python')
                self.filtered_df = self.df.copy()
                self.file_label.config(text=f"Fichier: {os.path.basename(file_path)}")
                self.history = []
                self.populate_filters()
                self.update_treeview()
                self.update_summary()
                self.update_histogram()
                self.update_active_filters_display()
                self.update_history_label()
                messagebox.showinfo("Succès", f"Fichier importé avec succès\n{len(self.df)} lignes chargées")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'import:\n{str(e)}")

    def export_csv(self):
        if self.df is None:
            messagebox.showwarning("Attention", "Aucune donnée à exporter")
            return

        file_path = filedialog.asksaveasfilename(
            title="Enregistrer le fichier CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if file_path:
            try:
                self.df.to_csv(file_path, index=False)
                messagebox.showinfo("Succès", f"Fichier exporté:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'export:\n{str(e)}")

    def populate_filters(self):
        if self.df is None:
            return

        filter_configs = [
            (self.segment_macro_combo, "SegmentMacro"),
            (self.file_combo, "File"),
            (self.segment_combo, "Segment"),
            (self.dcr_combo, "DCR"),
            (self.semaine_combo, "Semaine"),
            (self.type_combo, "Type")
        ]

        for combo, col in filter_configs:
            if col in self.df.columns:
                values = [""] + sorted(self.df[col].dropna().unique().astype(str).tolist())
                combo["values"] = values
                combo.set("")

    def apply_filters(self):
        if self.df is None:
            return

        self.filtered_df = self.df.copy()

        # Filtres textuels
        filters = [
            (self.segment_macro_var.get(), "SegmentMacro"),
            (self.file_var.get(), "File"),
            (self.segment_var.get(), "Segment"),
            (self.dcr_var.get(), "DCR"),
            (self.semaine_var.get(), "Semaine"),
            (self.type_var.get(), "Type")
        ]

        for value, col in filters:
            if value and col in self.filtered_df.columns:
                self.filtered_df = self.filtered_df[self.filtered_df[col].astype(str) == value]

        # Filtre par date (si les champs sont remplis)
        date_debut_str = self.date_debut_filter.get()
        date_fin_str = self.date_fin_filter.get()

        if date_debut_str and date_fin_str and "Date_debut" in self.filtered_df.columns:
            try:
                date_debut = pd.to_datetime(date_debut_str)
                date_fin = pd.to_datetime(date_fin_str)
                self.filtered_df["Date_debut"] = pd.to_datetime(self.filtered_df["Date_debut"], errors='coerce')
                self.filtered_df = self.filtered_df[
                    (self.filtered_df["Date_debut"] >= date_debut) &
                    (self.filtered_df["Date_debut"] <= date_fin)
                ]
            except:
                pass

        self.update_treeview()
        self.update_summary()
        self.update_histogram()
        self.update_active_filters_display()

    def reset_filters(self):
        self.segment_macro_var.set("")
        self.file_var.set("")
        self.segment_var.set("")
        self.dcr_var.set("")
        self.semaine_var.set("")
        self.type_var.set("")
        self.clear_date_filters()

        if self.df is not None:
            self.filtered_df = self.df.copy()
            self.update_treeview()
            self.update_summary()
            self.update_histogram()
            self.update_active_filters_display()

    def update_active_filters_display(self):
        """Mettre à jour l'affichage des filtres actifs"""
        active_filters = []

        filter_labels = [
            (self.segment_macro_var.get(), "SegmentMacro"),
            (self.file_var.get(), "File"),
            (self.segment_var.get(), "Segment"),
            (self.dcr_var.get(), "DCR"),
            (self.semaine_var.get(), "Semaine"),
            (self.type_var.get(), "Type")
        ]

        for value, name in filter_labels:
            if value:
                active_filters.append(f"{name}={value}")

        date_debut_str = self.date_debut_filter.get()
        date_fin_str = self.date_fin_filter.get()
        if date_debut_str and date_fin_str:
            active_filters.append(f"Date: {date_debut_str} → {date_fin_str}")

        if active_filters:
            self.active_filters_label.config(
                text=" | ".join(active_filters),
                foreground='#0066cc'
            )
        else:
            self.active_filters_label.config(
                text="Aucun filtre actif - Toutes les données affichées",
                foreground='gray'
            )

    def update_histogram(self):
        """Mettre à jour l'histogramme"""
        self.ax.clear()

        if self.filtered_df is None or self.filtered_df.empty:
            self.ax.text(0.5, 0.5, 'Aucune donnée à afficher', ha='center', va='center', fontsize=14)
            self.canvas.draw()
            return

        if "Date_debut" not in self.filtered_df.columns or "NbInteractions" not in self.filtered_df.columns:
            self.ax.text(0.5, 0.5, 'Colonnes Date_debut ou NbInteractions manquantes',
                        ha='center', va='center', fontsize=12)
            self.canvas.draw()
            return

        df_chart = self.filtered_df.copy()
        df_chart["Date_debut"] = pd.to_datetime(df_chart["Date_debut"], errors='coerce')
        df_chart = df_chart.dropna(subset=["Date_debut"])

        if df_chart.empty:
            self.ax.text(0.5, 0.5, 'Aucune date valide', ha='center', va='center', fontsize=14)
            self.canvas.draw()
            return

        grouped = df_chart.groupby("Date_debut")["NbInteractions"].sum().reset_index()
        grouped = grouped.sort_values("Date_debut")

        dates = grouped["Date_debut"].dt.strftime('%Y-%m-%d')
        values = grouped["NbInteractions"]

        bars = self.ax.bar(dates, values, color='#4CAF50', edgecolor='#2E7D32')

        for bar, val in zip(bars, values):
            height = bar.get_height()
            self.ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(val)}', ha='center', va='bottom', fontsize=9)

        self.ax.set_xlabel('Date début', fontsize=10)
        self.ax.set_ylabel('NbInteractions', fontsize=10)
        self.ax.tick_params(axis='x', rotation=45, labelsize=9)
        self.ax.tick_params(axis='y', labelsize=9)
        self.ax.set_title('Évolution des interactions par date', fontsize=12, fontweight='bold')

        self.fig.tight_layout()
        self.canvas.draw()

    def update_treeview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if self.filtered_df is None:
            self.row_count_label.config(text="0 lignes")
            return

        for idx, row in self.filtered_df.iterrows():
            values = [row.get(col, "") for col in self.columns]
            self.tree.insert("", tk.END, iid=idx, values=values)

        self.row_count_label.config(text=f"{len(self.filtered_df)} lignes")

    def update_summary(self):
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)

        if self.filtered_df is None or "Type" not in self.filtered_df.columns:
            return

        if "NbInteractions" in self.filtered_df.columns:
            summary = self.filtered_df.groupby("Type")["NbInteractions"].sum().reset_index()
            for _, row in summary.iterrows():
                self.summary_tree.insert("", tk.END, values=(row["Type"], f"{int(row['NbInteractions']):,}"))

    def on_selection_change(self, event=None):
        self.update_selection_info()
        self.update_preview()

    def update_selection_info(self):
        selected = self.tree.selection()
        if not selected:
            self.selection_info.config(
                text="Aucune sélection - Sélectionnez des lignes dans l'onglet 'Données & Filtres'"
            )
            return

        total = 0
        for item_id in selected:
            try:
                idx = int(item_id)
                if idx in self.df.index:
                    total += self.df.at[idx, "NbInteractions"]
            except (ValueError, KeyError):
                pass

        self.selection_info.config(
            text=f"{len(selected)} ligne(s) sélectionnée(s) | Total NbInteractions: {total:,}"
        )

    def update_preview(self):
        selected = self.tree.selection()

        if not selected:
            self.before_label.config(text="AVANT: -")
            self.after_label.config(text="APRÈS: -")
            self.diff_label.config(text="DIFFÉRENCE: -")
            return

        if not self.new_value_var.get():
            total = sum(self.df.at[int(item_id), "NbInteractions"]
                       for item_id in selected
                       if int(item_id) in self.df.index)
            self.before_label.config(text=f"AVANT: {total:,}")
            self.after_label.config(text="APRÈS: (entrez une valeur)")
            self.diff_label.config(text="DIFFÉRENCE: -")
            return

        try:
            value = float(self.new_value_var.get())
        except ValueError:
            self.after_label.config(text="APRÈS: (valeur invalide)", foreground='red')
            return

        total_before = 0
        total_after = 0

        for item_id in selected:
            try:
                idx = int(item_id)
                if idx in self.df.index:
                    old_val = self.df.at[idx, "NbInteractions"]
                    total_before += old_val

                    if self.modify_mode.get() == "relative":
                        new_val = old_val * (1 + value / 100)
                    else:
                        new_val = value

                    total_after += new_val
            except (ValueError, KeyError):
                pass

        diff = total_after - total_before
        diff_pct = (diff / total_before * 100) if total_before != 0 else 0
        sign = "+" if diff >= 0 else ""

        self.before_label.config(text=f"AVANT: {total_before:,.0f}")
        self.after_label.config(text=f"APRÈS: {total_after:,.0f}", foreground='#0066cc')

        color = '#008000' if diff >= 0 else '#cc0000'
        self.diff_label.config(
            text=f"DIFFÉRENCE: {sign}{diff:,.0f} ({sign}{diff_pct:.1f}%)",
            foreground=color
        )

    def update_history_label(self):
        self.history_label.config(text=f"Historique: {len(self.history)} modification(s) annulable(s)")

    def save_state(self):
        if self.df is not None:
            state = self.df.copy()
            self.history.append(state)
            if len(self.history) > self.max_history:
                self.history.pop(0)
            self.update_history_label()

    def undo(self):
        if not self.history:
            messagebox.showinfo("Info", "Aucune modification à annuler")
            return

        self.df = self.history.pop()
        self.apply_filters()
        self.update_history_label()
        messagebox.showinfo("Succès", "Dernière modification annulée")

    def modify_selection(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attention", "Veuillez d'abord sélectionner des lignes dans l'onglet 'Données & Filtres'")
            return

        value_str = self.new_value_var.get()
        if not value_str:
            messagebox.showwarning("Attention", "Veuillez entrer une valeur")
            return

        try:
            value = float(value_str)
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer un nombre valide")
            return

        self.save_state()

        modifications = []
        total_before = 0
        total_after = 0

        for item_id in selected:
            try:
                idx = int(item_id)
                if idx not in self.df.index:
                    continue

                old_value = self.df.at[idx, "NbInteractions"]
                total_before += old_value

                if self.modify_mode.get() == "relative":
                    new_value = int(round(old_value * (1 + value / 100)))
                else:
                    new_value = int(value)

                total_after += new_value

                self.df.at[idx, "NbInteractions"] = new_value
                if idx in self.filtered_df.index:
                    self.filtered_df.at[idx, "NbInteractions"] = new_value

                modifications.append((idx, old_value, new_value))

            except (ValueError, KeyError):
                continue

        for idx, old_val, new_val in modifications:
            self.log_modification(idx, old_val, new_val)

        self.update_treeview()
        self.update_summary()
        self.update_histogram()
        self.update_selection_info()

        mode_text = f"{value:+.0f}%" if self.modify_mode.get() == "relative" else f"= {int(value)}"
        diff = total_after - total_before

        messagebox.showinfo(
            "Modification appliquée",
            f"{len(modifications)} ligne(s) modifiée(s)\n"
            f"Mode: {mode_text}\n\n"
            f"Total avant: {total_before:,.0f}\n"
            f"Total après: {total_after:,.0f}\n"
            f"Différence: {'+' if diff >= 0 else ''}{diff:,.0f}"
        )

    def log_modification(self, row_idx, old_value, new_value):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row_data = self.df.loc[row_idx]

        log_entry = (
            f"[{timestamp}] "
            f"SegmentMacro: {row_data.get('SegmentMacro', 'N/A')}, "
            f"File: {row_data.get('File', 'N/A')}, "
            f"Segment: {row_data.get('Segment', 'N/A')}, "
            f"NbInteractions: {old_value} -> {new_value}\n"
        )

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

    def view_log(self):
        if not os.path.exists(self.log_file):
            messagebox.showinfo("Info", "Aucune modification enregistrée")
            return

        log_window = tk.Toplevel(self.root)
        log_window.title("Historique des modifications")
        log_window.geometry("900x500")

        text = tk.Text(log_window, wrap=tk.WORD, font=('Courier', 10))
        scrollbar = ttk.Scrollbar(log_window, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(fill=tk.BOTH, expand=True)

        with open(self.log_file, "r", encoding="utf-8") as f:
            text.insert(tk.END, f.read())

        text.config(state=tk.DISABLED)

def main():
    root = tk.Tk()
    app = CSVImportApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
