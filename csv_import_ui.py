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
        self.root.geometry("1500x950")

        self.df = None
        self.filtered_df = None
        self.log_file = "modifications_log.txt"
        self.history = []
        self.max_history = 50
        self.check_vars = {}  # Variables pour les checkboxes

        self.setup_ui()

    def setup_ui(self):
        # Frame principale
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ===== SECTION HAUTE: Import/Export =====
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        import_frame = ttk.LabelFrame(top_frame, text="Import/Export", padding="5")
        import_frame.pack(fill=tk.X)

        ttk.Button(import_frame, text="Importer CSV", command=self.import_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(import_frame, text="Exporter CSV", command=self.export_csv).pack(side=tk.LEFT, padx=5)
        self.file_label = ttk.Label(import_frame, text="Aucun fichier", font=('TkDefaultFont', 9, 'italic'))
        self.file_label.pack(side=tk.LEFT, padx=15)

        # ===== FILTRES GLOBAUX (toujours visibles) =====
        filter_frame = ttk.LabelFrame(main_frame, text="Filtres globaux", padding="10")
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        # Ligne 1
        filter_row1 = ttk.Frame(filter_frame)
        filter_row1.pack(fill=tk.X, pady=3)

        ttk.Label(filter_row1, text="SegmentMacro:").pack(side=tk.LEFT, padx=(0, 5))
        self.segment_macro_var = tk.StringVar()
        self.segment_macro_combo = ttk.Combobox(filter_row1, textvariable=self.segment_macro_var, width=10)
        self.segment_macro_combo.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(filter_row1, text="File:").pack(side=tk.LEFT, padx=(0, 5))
        self.file_var = tk.StringVar()
        self.file_combo = ttk.Combobox(filter_row1, textvariable=self.file_var, width=10)
        self.file_combo.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(filter_row1, text="Segment:").pack(side=tk.LEFT, padx=(0, 5))
        self.segment_var = tk.StringVar()
        self.segment_combo = ttk.Combobox(filter_row1, textvariable=self.segment_var, width=10)
        self.segment_combo.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(filter_row1, text="DCR:").pack(side=tk.LEFT, padx=(0, 5))
        self.dcr_var = tk.StringVar()
        self.dcr_combo = ttk.Combobox(filter_row1, textvariable=self.dcr_var, width=10)
        self.dcr_combo.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(filter_row1, text="Semaine:").pack(side=tk.LEFT, padx=(0, 5))
        self.semaine_var = tk.StringVar()
        self.semaine_combo = ttk.Combobox(filter_row1, textvariable=self.semaine_var, width=10)
        self.semaine_combo.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(filter_row1, text="Type:").pack(side=tk.LEFT, padx=(0, 5))
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(filter_row1, textvariable=self.type_var, width=10)
        self.type_combo.pack(side=tk.LEFT)

        # Ligne 2: Dates + boutons
        filter_row2 = ttk.Frame(filter_frame)
        filter_row2.pack(fill=tk.X, pady=3)

        ttk.Label(filter_row2, text="Date du:").pack(side=tk.LEFT, padx=(0, 5))
        self.date_debut_filter = DateEntry(filter_row2, width=10, date_pattern='yyyy-mm-dd')
        self.date_debut_filter.pack(side=tk.LEFT, padx=(0, 5))
        self.date_debut_filter.delete(0, tk.END)

        ttk.Label(filter_row2, text="au:").pack(side=tk.LEFT, padx=(0, 5))
        self.date_fin_filter = DateEntry(filter_row2, width=10, date_pattern='yyyy-mm-dd')
        self.date_fin_filter.pack(side=tk.LEFT, padx=(0, 15))
        self.date_fin_filter.delete(0, tk.END)

        ttk.Button(filter_row2, text="Appliquer", command=self.apply_filters).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_row2, text="Réinitialiser", command=self.reset_filters).pack(side=tk.LEFT, padx=5)

        # Filtres actifs
        self.active_filters_label = ttk.Label(filter_row2, text="", font=('TkDefaultFont', 9, 'bold'), foreground='#0066cc')
        self.active_filters_label.pack(side=tk.LEFT, padx=15)

        # ===== NOTEBOOK (onglets) =====
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Onglet 1: Visualisation (accueil)
        self.tab_viz = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_viz, text="Visualisation")

        # Onglet 2: Données & Sélection
        self.tab_data = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_data, text="Données & Sélection")

        # Onglet 3: Modifications
        self.tab_modify = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_modify, text="Modifications")

        self.setup_viz_tab()
        self.setup_data_tab()
        self.setup_modify_tab()

    def setup_viz_tab(self):
        """Onglet Visualisation - Page d'accueil"""

        # Frame pour le résumé
        summary_frame = ttk.LabelFrame(self.tab_viz, text="Résumé par Type", padding="10")
        summary_frame.pack(fill=tk.X, pady=(0, 10))

        self.summary_tree = ttk.Treeview(summary_frame, columns=("Type", "Total"), show="headings", height=4)
        self.summary_tree.heading("Type", text="Type")
        self.summary_tree.heading("Total", text="Total Interactions")
        self.summary_tree.column("Type", width=200)
        self.summary_tree.column("Total", width=200)
        self.summary_tree.pack(fill=tk.X)

        # Total global
        self.total_label = ttk.Label(summary_frame, text="Total global: 0", font=('TkDefaultFont', 11, 'bold'))
        self.total_label.pack(anchor=tk.E, pady=5)

        # Histogramme
        chart_frame = ttk.LabelFrame(self.tab_viz, text="Évolution par Date début", padding="10")
        chart_frame.pack(fill=tk.BOTH, expand=True)

        self.fig = Figure(figsize=(12, 5), dpi=85)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def setup_data_tab(self):
        """Onglet Données avec sélection par checkbox"""

        # Contrôles de sélection
        control_frame = ttk.Frame(self.tab_data)
        control_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(control_frame, text="Tout cocher", command=self.check_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Tout décocher", command=self.uncheck_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Inverser", command=self.invert_check).pack(side=tk.LEFT, padx=5)

        self.selection_count_label = ttk.Label(control_frame, text="0 / 0 sélectionné(s)")
        self.selection_count_label.pack(side=tk.RIGHT, padx=10)

        # Frame pour le tableau avec checkboxes
        table_frame = ttk.Frame(self.tab_data)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas scrollable pour les checkboxes
        self.data_canvas = tk.Canvas(table_frame)
        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.data_canvas.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.data_canvas.xview)

        self.scrollable_frame = ttk.Frame(self.data_canvas)
        self.scrollable_frame.bind("<Configure>",
            lambda e: self.data_canvas.configure(scrollregion=self.data_canvas.bbox("all")))

        self.data_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.data_canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.data_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind mousewheel
        self.data_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def setup_modify_tab(self):
        """Onglet Modifications avec curseur et aperçu"""

        # Résumé sélection
        selection_frame = ttk.LabelFrame(self.tab_modify, text="Sélection", padding="10")
        selection_frame.pack(fill=tk.X, pady=(0, 10))

        self.modify_selection_label = ttk.Label(selection_frame,
            text="Cochez des lignes dans l'onglet 'Données & Sélection'", font=('TkDefaultFont', 11))
        self.modify_selection_label.pack()

        # Mode de modification
        mode_frame = ttk.LabelFrame(self.tab_modify, text="Type de modification", padding="10")
        mode_frame.pack(fill=tk.X, pady=(0, 10))

        self.modify_mode = tk.StringVar(value="relative")

        mode_row = ttk.Frame(mode_frame)
        mode_row.pack(fill=tk.X)

        ttk.Radiobutton(mode_row, text="Relatif (%)", variable=self.modify_mode,
                       value="relative", command=self.on_mode_change).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_row, text="Valeur absolue", variable=self.modify_mode,
                       value="global", command=self.on_mode_change).pack(side=tk.LEFT, padx=10)

        # Curseur pour modification relative
        self.slider_frame = ttk.LabelFrame(self.tab_modify, text="Ajustement relatif", padding="10")
        self.slider_frame.pack(fill=tk.X, pady=(0, 10))

        slider_row = ttk.Frame(self.slider_frame)
        slider_row.pack(fill=tk.X)

        ttk.Label(slider_row, text="-50%").pack(side=tk.LEFT)

        self.slider_var = tk.DoubleVar(value=0)
        self.slider = ttk.Scale(slider_row, from_=-50, to=50, variable=self.slider_var,
                                orient=tk.HORIZONTAL, command=self.on_slider_change)
        self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        ttk.Label(slider_row, text="+50%").pack(side=tk.LEFT)

        self.slider_value_label = ttk.Label(self.slider_frame, text="0%", font=('TkDefaultFont', 14, 'bold'))
        self.slider_value_label.pack(pady=5)

        # Champ pour valeur absolue
        self.absolute_frame = ttk.LabelFrame(self.tab_modify, text="Valeur absolue", padding="10")

        abs_row = ttk.Frame(self.absolute_frame)
        abs_row.pack(fill=tk.X)

        ttk.Label(abs_row, text="Nouvelle valeur:").pack(side=tk.LEFT, padx=5)
        self.absolute_value_var = tk.StringVar()
        self.absolute_value_var.trace('w', lambda *args: self.update_preview())
        ttk.Entry(abs_row, textvariable=self.absolute_value_var, width=15).pack(side=tk.LEFT, padx=5)

        # Aperçu global
        preview_frame = ttk.LabelFrame(self.tab_modify, text="Aperçu global", padding="10")
        preview_frame.pack(fill=tk.X, pady=(0, 10))

        preview_row = ttk.Frame(preview_frame)
        preview_row.pack(fill=tk.X)

        self.before_label = ttk.Label(preview_row, text="AVANT: 0", font=('TkDefaultFont', 12))
        self.before_label.pack(side=tk.LEFT, padx=20)

        self.after_label = ttk.Label(preview_row, text="APRÈS: 0", font=('TkDefaultFont', 12, 'bold'), foreground='#0066cc')
        self.after_label.pack(side=tk.LEFT, padx=20)

        self.diff_label = ttk.Label(preview_row, text="DIFF: 0", font=('TkDefaultFont', 12))
        self.diff_label.pack(side=tk.LEFT, padx=20)

        # Aperçu détaillé (ligne par ligne)
        detail_frame = ttk.LabelFrame(self.tab_modify, text="Aperçu détaillé (lignes sélectionnées)", padding="5")
        detail_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Treeview pour détail
        self.detail_tree = ttk.Treeview(detail_frame,
            columns=("Segment", "Type", "Avant", "Après", "Diff"), show="headings", height=8)

        for col, width in [("Segment", 100), ("Type", 80), ("Avant", 100), ("Après", 100), ("Diff", 100)]:
            self.detail_tree.heading(col, text=col)
            self.detail_tree.column(col, width=width)

        detail_scroll = ttk.Scrollbar(detail_frame, orient="vertical", command=self.detail_tree.yview)
        self.detail_tree.configure(yscrollcommand=detail_scroll.set)

        self.detail_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Actions
        action_frame = ttk.Frame(self.tab_modify)
        action_frame.pack(fill=tk.X, pady=5)

        ttk.Button(action_frame, text="APPLIQUER", command=self.apply_modification).pack(side=tk.LEFT, padx=10)
        ttk.Button(action_frame, text="Annuler (Ctrl+Z)", command=self.undo).pack(side=tk.LEFT, padx=10)
        ttk.Button(action_frame, text="Historique", command=self.view_log).pack(side=tk.LEFT, padx=10)

        self.history_label = ttk.Label(action_frame, text="0 annulation(s) possible(s)", foreground='gray')
        self.history_label.pack(side=tk.RIGHT, padx=10)

        # Raccourci
        self.root.bind('<Control-z>', lambda e: self.undo())

        # Initialiser l'affichage du bon mode
        self.on_mode_change()

    def _on_mousewheel(self, event):
        self.data_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_mode_change(self):
        """Changer entre mode relatif et absolu"""
        if self.modify_mode.get() == "relative":
            self.slider_frame.pack(fill=tk.X, pady=(0, 10), after=self.slider_frame.master.children['!labelframe2'])
            self.absolute_frame.pack_forget()
        else:
            self.absolute_frame.pack(fill=tk.X, pady=(0, 10), after=self.slider_frame.master.children['!labelframe2'])
            self.slider_frame.pack_forget()
        self.update_preview()

    def on_slider_change(self, value):
        """Mise à jour lors du déplacement du curseur"""
        val = float(value)
        sign = "+" if val >= 0 else ""
        self.slider_value_label.config(text=f"{sign}{val:.0f}%")
        self.update_preview()

    def import_csv(self):
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if file_path:
            try:
                self.df = pd.read_csv(file_path, sep=None, engine='python')
                self.filtered_df = self.df.copy()
                self.file_label.config(text=os.path.basename(file_path))
                self.history = []
                self.check_vars = {}
                self.populate_filters()
                self.update_all_views()
                messagebox.showinfo("Succès", f"{len(self.df)} lignes importées")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur: {str(e)}")

    def export_csv(self):
        if self.df is None:
            messagebox.showwarning("Attention", "Aucune donnée")
            return

        file_path = filedialog.asksaveasfilename(
            title="Enregistrer CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )

        if file_path:
            try:
                self.df.to_csv(file_path, index=False)

                # Afficher aperçu
                preview_window = tk.Toplevel(self.root)
                preview_window.title("Export réussi - Aperçu")
                preview_window.geometry("800x400")

                ttk.Label(preview_window, text=f"Fichier exporté: {file_path}",
                         font=('TkDefaultFont', 10, 'bold')).pack(pady=10)

                text = tk.Text(preview_window, wrap=tk.NONE)
                scroll_y = ttk.Scrollbar(preview_window, command=text.yview)
                scroll_x = ttk.Scrollbar(preview_window, orient=tk.HORIZONTAL, command=text.xview)
                text.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

                scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
                scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
                text.pack(fill=tk.BOTH, expand=True)

                # Afficher les premières lignes
                preview_df = self.df.head(50)
                text.insert(tk.END, preview_df.to_string())
                text.config(state=tk.DISABLED)

            except Exception as e:
                messagebox.showerror("Erreur", str(e))

    def populate_filters(self):
        if self.df is None:
            return

        for combo, col in [
            (self.segment_macro_combo, "SegmentMacro"),
            (self.file_combo, "File"),
            (self.segment_combo, "Segment"),
            (self.dcr_combo, "DCR"),
            (self.semaine_combo, "Semaine"),
            (self.type_combo, "Type")
        ]:
            if col in self.df.columns:
                values = [""] + sorted(self.df[col].dropna().unique().astype(str).tolist())
                combo["values"] = values
                combo.set("")

    def apply_filters(self):
        if self.df is None:
            return

        self.filtered_df = self.df.copy()

        # Filtres textuels
        for value, col in [
            (self.segment_macro_var.get(), "SegmentMacro"),
            (self.file_var.get(), "File"),
            (self.segment_var.get(), "Segment"),
            (self.dcr_var.get(), "DCR"),
            (self.semaine_var.get(), "Semaine"),
            (self.type_var.get(), "Type")
        ]:
            if value and col in self.filtered_df.columns:
                self.filtered_df = self.filtered_df[self.filtered_df[col].astype(str) == value]

        # Filtre date
        date_debut_str = self.date_debut_filter.get()
        date_fin_str = self.date_fin_filter.get()

        if date_debut_str and date_fin_str and "Date_debut" in self.filtered_df.columns:
            try:
                self.filtered_df["Date_debut"] = pd.to_datetime(self.filtered_df["Date_debut"], errors='coerce')
                self.filtered_df = self.filtered_df[
                    (self.filtered_df["Date_debut"] >= pd.to_datetime(date_debut_str)) &
                    (self.filtered_df["Date_debut"] <= pd.to_datetime(date_fin_str))
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
        for value, name in [
            (self.segment_macro_var.get(), "SegmentMacro"),
            (self.file_var.get(), "File"),
            (self.segment_var.get(), "Segment"),
            (self.dcr_var.get(), "DCR"),
            (self.semaine_var.get(), "Semaine"),
            (self.type_var.get(), "Type")
        ]:
            if value:
                active.append(f"{name}={value}")

        if self.date_debut_filter.get() and self.date_fin_filter.get():
            active.append(f"Date: {self.date_debut_filter.get()} → {self.date_fin_filter.get()}")

        self.active_filters_label.config(text=" | ".join(active) if active else "")

    def update_all_views(self):
        self.update_data_table()
        self.update_summary()
        self.update_histogram()
        self.update_preview()
        self.update_history_label()

    def update_data_table(self):
        """Mettre à jour le tableau avec checkboxes"""
        # Effacer l'ancien contenu
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if self.filtered_df is None or self.filtered_df.empty:
            ttk.Label(self.scrollable_frame, text="Aucune donnée").pack()
            return

        # En-têtes
        headers = ["", "SegmentMacro", "Segment", "Type", "NbInteractions", "Date_debut"]
        for i, h in enumerate(headers):
            ttk.Label(self.scrollable_frame, text=h, font=('TkDefaultFont', 9, 'bold'),
                     relief=tk.RIDGE, padding=5).grid(row=0, column=i, sticky="nsew")

        # Données avec checkboxes
        for row_num, (idx, row) in enumerate(self.filtered_df.iterrows(), start=1):
            # Checkbox
            if idx not in self.check_vars:
                self.check_vars[idx] = tk.BooleanVar(value=False)

            cb = ttk.Checkbutton(self.scrollable_frame, variable=self.check_vars[idx],
                                command=self.on_check_change)
            cb.grid(row=row_num, column=0, padx=5)

            # Données
            values = [
                str(row.get("SegmentMacro", "")),
                str(row.get("Segment", "")),
                str(row.get("Type", "")),
                str(row.get("NbInteractions", "")),
                str(row.get("Date_debut", ""))
            ]
            for col_num, val in enumerate(values, start=1):
                ttk.Label(self.scrollable_frame, text=val, padding=3).grid(
                    row=row_num, column=col_num, sticky="w")

        self.update_selection_count()

    def on_check_change(self):
        self.update_selection_count()
        self.update_preview()

    def update_selection_count(self):
        if self.filtered_df is None:
            self.selection_count_label.config(text="0 / 0")
            return

        selected = sum(1 for idx in self.filtered_df.index if self.check_vars.get(idx, tk.BooleanVar()).get())
        total = len(self.filtered_df)
        self.selection_count_label.config(text=f"{selected} / {total} sélectionné(s)")

    def check_all(self):
        if self.filtered_df is None:
            return
        for idx in self.filtered_df.index:
            if idx in self.check_vars:
                self.check_vars[idx].set(True)
        self.update_selection_count()
        self.update_preview()

    def uncheck_all(self):
        for var in self.check_vars.values():
            var.set(False)
        self.update_selection_count()
        self.update_preview()

    def invert_check(self):
        if self.filtered_df is None:
            return
        for idx in self.filtered_df.index:
            if idx in self.check_vars:
                self.check_vars[idx].set(not self.check_vars[idx].get())
        self.update_selection_count()
        self.update_preview()

    def update_summary(self):
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)

        if self.filtered_df is None:
            self.total_label.config(text="Total global: 0")
            return

        if "Type" in self.filtered_df.columns and "NbInteractions" in self.filtered_df.columns:
            summary = self.filtered_df.groupby("Type")["NbInteractions"].sum().reset_index()
            for _, row in summary.iterrows():
                self.summary_tree.insert("", tk.END, values=(row["Type"], f"{int(row['NbInteractions']):,}"))

            total = self.filtered_df["NbInteractions"].sum()
            self.total_label.config(text=f"Total global: {int(total):,}")

    def update_histogram(self):
        self.ax.clear()

        if self.filtered_df is None or self.filtered_df.empty:
            self.ax.text(0.5, 0.5, 'Aucune donnée', ha='center', va='center', fontsize=14)
            self.canvas.draw()
            return

        if "Date_debut" not in self.filtered_df.columns:
            self.canvas.draw()
            return

        df_chart = self.filtered_df.copy()
        df_chart["Date_debut"] = pd.to_datetime(df_chart["Date_debut"], errors='coerce')
        df_chart = df_chart.dropna(subset=["Date_debut"])

        if df_chart.empty:
            self.canvas.draw()
            return

        grouped = df_chart.groupby("Date_debut")["NbInteractions"].sum().reset_index()
        grouped = grouped.sort_values("Date_debut")

        bars = self.ax.bar(grouped["Date_debut"].dt.strftime('%Y-%m-%d'),
                          grouped["NbInteractions"], color='#4CAF50')

        for bar, val in zip(bars, grouped["NbInteractions"]):
            self.ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                        f'{int(val)}', ha='center', va='bottom', fontsize=8)

        self.ax.set_xlabel('Date')
        self.ax.set_ylabel('NbInteractions')
        self.ax.tick_params(axis='x', rotation=45)
        self.fig.tight_layout()
        self.canvas.draw()

    def get_selected_indices(self):
        """Obtenir les indices des lignes cochées"""
        if self.filtered_df is None:
            return []
        return [idx for idx in self.filtered_df.index if self.check_vars.get(idx, tk.BooleanVar()).get()]

    def update_preview(self):
        """Mettre à jour l'aperçu des modifications"""
        selected = self.get_selected_indices()

        # Mise à jour label sélection
        if not selected:
            self.modify_selection_label.config(text="Aucune ligne cochée")
            self.before_label.config(text="AVANT: -")
            self.after_label.config(text="APRÈS: -")
            self.diff_label.config(text="DIFF: -")
            for item in self.detail_tree.get_children():
                self.detail_tree.delete(item)
            return

        total_before = sum(self.df.at[idx, "NbInteractions"] for idx in selected)
        self.modify_selection_label.config(text=f"{len(selected)} ligne(s) sélectionnée(s)")

        # Calculer après
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
        sign = "+" if diff >= 0 else ""
        self.diff_label.config(text=f"DIFF: {sign}{diff:,.0f} ({sign}{diff_pct:.1f}%)", foreground=color)

        # Détail ligne par ligne
        for item in self.detail_tree.get_children():
            self.detail_tree.delete(item)

        for idx in selected[:100]:  # Limiter à 100 lignes
            row = self.df.loc[idx]
            avant = row["NbInteractions"]

            if self.modify_mode.get() == "relative":
                apres = avant * (1 + self.slider_var.get() / 100)
            else:
                try:
                    apres = float(self.absolute_value_var.get())
                except:
                    apres = avant

            diff_row = apres - avant
            sign = "+" if diff_row >= 0 else ""

            self.detail_tree.insert("", tk.END, values=(
                row.get("Segment", ""),
                row.get("Type", ""),
                f"{avant:,.0f}",
                f"{apres:,.0f}",
                f"{sign}{diff_row:,.0f}"
            ))

    def update_history_label(self):
        self.history_label.config(text=f"{len(self.history)} annulation(s) possible(s)")

    def save_state(self):
        if self.df is not None:
            self.history.append(self.df.copy())
            if len(self.history) > self.max_history:
                self.history.pop(0)
            self.update_history_label()

    def apply_modification(self):
        selected = self.get_selected_indices()
        if not selected:
            messagebox.showwarning("Attention", "Cochez des lignes à modifier")
            return

        self.save_state()

        total_before = 0
        total_after = 0

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
            self.log_modification(idx, old_val, new_val)

        self.apply_filters()

        diff = total_after - total_before
        messagebox.showinfo("Modification appliquée",
            f"{len(selected)} ligne(s) modifiée(s)\n\n"
            f"Total avant: {total_before:,}\n"
            f"Total après: {total_after:,}\n"
            f"Différence: {'+' if diff >= 0 else ''}{diff:,}")

    def undo(self):
        if not self.history:
            messagebox.showinfo("Info", "Rien à annuler")
            return
        self.df = self.history.pop()
        self.apply_filters()
        messagebox.showinfo("Succès", "Modification annulée")

    def log_modification(self, row_idx, old_value, new_value):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = self.df.loc[row_idx]

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] Segment: {row.get('Segment', 'N/A')}, "
                   f"Type: {row.get('Type', 'N/A')}, "
                   f"NbInteractions: {old_value} -> {new_value}\n")

    def view_log(self):
        if not os.path.exists(self.log_file):
            messagebox.showinfo("Info", "Aucun historique")
            return

        win = tk.Toplevel(self.root)
        win.title("Historique")
        win.geometry("700x400")

        text = tk.Text(win, wrap=tk.WORD)
        scroll = ttk.Scrollbar(win, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(fill=tk.BOTH, expand=True)

        with open(self.log_file, "r") as f:
            text.insert(tk.END, f.read())
        text.config(state=tk.DISABLED)

def main():
    root = tk.Tk()
    app = CSVImportApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
