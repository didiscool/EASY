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
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

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
        self.check_vars = {}

        # Couleurs pour les types
        self.type_colors = {}
        self.color_palette = ['#4CAF50', '#2196F3', '#FF9800', '#E91E63', '#9C27B0',
                              '#00BCD4', '#FFEB3B', '#795548', '#607D8B', '#F44336']

        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Import/Export
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        import_frame = ttk.LabelFrame(top_frame, text="Import/Export", padding="5")
        import_frame.pack(fill=tk.X)

        ttk.Button(import_frame, text="Importer CSV", command=self.import_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(import_frame, text="Exporter CSV", command=self.export_csv).pack(side=tk.LEFT, padx=5)
        self.file_label = ttk.Label(import_frame, text="Aucun fichier", font=('TkDefaultFont', 9, 'italic'))
        self.file_label.pack(side=tk.LEFT, padx=15)

        # Filtres globaux
        filter_frame = ttk.LabelFrame(main_frame, text="Filtres globaux", padding="10")
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        filter_row1 = ttk.Frame(filter_frame)
        filter_row1.pack(fill=tk.X, pady=3)

        for label, var_name, combo_name in [
            ("SegmentMacro:", "segment_macro_var", "segment_macro_combo"),
            ("File:", "file_var", "file_combo"),
            ("Segment:", "segment_var", "segment_combo"),
            ("DCR:", "dcr_var", "dcr_combo"),
            ("Semaine:", "semaine_var", "semaine_combo"),
            ("Type:", "type_var", "type_combo")
        ]:
            ttk.Label(filter_row1, text=label).pack(side=tk.LEFT, padx=(0, 3))
            setattr(self, var_name, tk.StringVar())
            combo = ttk.Combobox(filter_row1, textvariable=getattr(self, var_name), width=10)
            setattr(self, combo_name, combo)
            combo.pack(side=tk.LEFT, padx=(0, 8))

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

        self.active_filters_label = ttk.Label(filter_row2, text="", font=('TkDefaultFont', 9, 'bold'), foreground='#0066cc')
        self.active_filters_label.pack(side=tk.LEFT, padx=15)

        # Notebook avec 2 onglets
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Onglet 1: Visualisation
        self.tab_viz = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_viz, text="Visualisation")

        # Onglet 2: Sélection & Modifications (unifié)
        self.tab_edit = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_edit, text="Sélection & Modifications")

        self.setup_viz_tab()
        self.setup_edit_tab()

    def setup_viz_tab(self):
        """Onglet Visualisation avec tableau complet et histogramme coloré"""

        # PanedWindow pour diviser verticalement
        paned = ttk.PanedWindow(self.tab_viz, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Partie haute: Résumé + Histogramme
        top_pane = ttk.Frame(paned)
        paned.add(top_pane, weight=1)

        # Frame gauche: Résumé par Type
        left_frame = ttk.LabelFrame(top_pane, text="Résumé par Type", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.summary_tree = ttk.Treeview(left_frame, columns=("Type", "Total", "Couleur"), show="headings", height=6)
        self.summary_tree.heading("Type", text="Type")
        self.summary_tree.heading("Total", text="Total")
        self.summary_tree.heading("Couleur", text="")
        self.summary_tree.column("Type", width=100)
        self.summary_tree.column("Total", width=100)
        self.summary_tree.column("Couleur", width=30)
        self.summary_tree.pack(fill=tk.BOTH, expand=True)

        self.total_label = ttk.Label(left_frame, text="Total: 0", font=('TkDefaultFont', 10, 'bold'))
        self.total_label.pack(anchor=tk.E, pady=3)

        # Frame droite: Histogramme
        right_frame = ttk.LabelFrame(top_pane, text="Évolution par Date (coloré par Type)", padding="5")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.fig = Figure(figsize=(8, 4), dpi=85)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Partie basse: Tableau complet
        bottom_pane = ttk.LabelFrame(paned, text="Données complètes", padding="5")
        paned.add(bottom_pane, weight=1)

        # Treeview avec toutes les colonnes
        self.columns = ["SegmentMacro", "File", "Segment", "DCR", "Semaine", "Offre",
                       "NbInteractions", "Type", "Date_debut", "Date_fin"]

        tree_frame = ttk.Frame(bottom_pane)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.viz_tree = ttk.Treeview(tree_frame, columns=self.columns, show="headings", height=10)

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
            self.viz_tree.column(col, width=90, minwidth=60)

        self.row_count_label = ttk.Label(bottom_pane, text="0 lignes")
        self.row_count_label.pack(anchor=tk.E)

    def setup_edit_tab(self):
        """Onglet unifié Sélection & Modifications"""

        # PanedWindow horizontal
        paned = ttk.PanedWindow(self.tab_edit, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Partie gauche: Sélection des données
        left_pane = ttk.Frame(paned)
        paned.add(left_pane, weight=2)

        # Contrôles de sélection
        control_frame = ttk.LabelFrame(left_pane, text="Sélection", padding="5")
        control_frame.pack(fill=tk.X, pady=(0, 5))

        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="Tout cocher", command=self.check_all).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Tout décocher", command=self.uncheck_all).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Inverser", command=self.invert_check).pack(side=tk.LEFT, padx=3)

        self.selection_count_label = ttk.Label(btn_frame, text="0 / 0", font=('TkDefaultFont', 9, 'bold'))
        self.selection_count_label.pack(side=tk.RIGHT, padx=5)

        # Tableau avec checkboxes
        table_frame = ttk.Frame(left_pane)
        table_frame.pack(fill=tk.BOTH, expand=True)

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

        self.data_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Partie droite: Modifications
        right_pane = ttk.Frame(paned)
        paned.add(right_pane, weight=1)

        # Mode de modification
        mode_frame = ttk.LabelFrame(right_pane, text="Modification", padding="10")
        mode_frame.pack(fill=tk.X, pady=(0, 5))

        self.modify_mode = tk.StringVar(value="relative")
        ttk.Radiobutton(mode_frame, text="Relatif (%)", variable=self.modify_mode,
                       value="relative", command=self.on_mode_change).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Valeur absolue", variable=self.modify_mode,
                       value="global", command=self.on_mode_change).pack(anchor=tk.W)

        # Curseur relatif
        self.slider_frame = ttk.Frame(mode_frame)
        self.slider_frame.pack(fill=tk.X, pady=5)

        ttk.Label(self.slider_frame, text="-50%").pack(side=tk.LEFT)
        self.slider_var = tk.DoubleVar(value=0)
        self.slider = ttk.Scale(self.slider_frame, from_=-50, to=50, variable=self.slider_var,
                                orient=tk.HORIZONTAL, command=self.on_slider_change)
        self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Label(self.slider_frame, text="+50%").pack(side=tk.LEFT)

        self.slider_value_label = ttk.Label(mode_frame, text="0%", font=('TkDefaultFont', 12, 'bold'))
        self.slider_value_label.pack()

        # Champ valeur absolue
        self.absolute_frame = ttk.Frame(mode_frame)
        ttk.Label(self.absolute_frame, text="Valeur:").pack(side=tk.LEFT)
        self.absolute_value_var = tk.StringVar()
        self.absolute_value_var.trace('w', lambda *args: self.update_preview())
        ttk.Entry(self.absolute_frame, textvariable=self.absolute_value_var, width=10).pack(side=tk.LEFT, padx=5)

        # Aperçu
        preview_frame = ttk.LabelFrame(right_pane, text="Aperçu", padding="10")
        preview_frame.pack(fill=tk.X, pady=(0, 5))

        self.before_label = ttk.Label(preview_frame, text="AVANT: -", font=('TkDefaultFont', 10))
        self.before_label.pack(anchor=tk.W)
        self.after_label = ttk.Label(preview_frame, text="APRÈS: -", font=('TkDefaultFont', 10, 'bold'), foreground='#0066cc')
        self.after_label.pack(anchor=tk.W)
        self.diff_label = ttk.Label(preview_frame, text="DIFF: -", font=('TkDefaultFont', 10))
        self.diff_label.pack(anchor=tk.W)

        # Détail
        detail_frame = ttk.LabelFrame(right_pane, text="Détail", padding="5")
        detail_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        self.detail_tree = ttk.Treeview(detail_frame,
            columns=("Segment", "Type", "Avant", "Après"), show="headings", height=8)

        for col, width in [("Segment", 80), ("Type", 60), ("Avant", 70), ("Après", 70)]:
            self.detail_tree.heading(col, text=col)
            self.detail_tree.column(col, width=width)

        detail_scroll = ttk.Scrollbar(detail_frame, orient="vertical", command=self.detail_tree.yview)
        self.detail_tree.configure(yscrollcommand=detail_scroll.set)
        self.detail_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Actions
        action_frame = ttk.Frame(right_pane)
        action_frame.pack(fill=tk.X)

        ttk.Button(action_frame, text="APPLIQUER", command=self.apply_modification).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="Annuler", command=self.undo).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="Historique", command=self.view_log).pack(fill=tk.X, pady=2)

        self.history_label = ttk.Label(action_frame, text="0 undo", foreground='gray')
        self.history_label.pack()

        self.root.bind('<Control-z>', lambda e: self.undo())
        self.on_mode_change()

    def _on_mousewheel(self, event):
        self.data_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_mode_change(self):
        if self.modify_mode.get() == "relative":
            self.slider_frame.pack(fill=tk.X, pady=5)
            self.slider_value_label.pack()
            self.absolute_frame.pack_forget()
        else:
            self.slider_frame.pack_forget()
            self.slider_value_label.pack_forget()
            self.absolute_frame.pack(fill=tk.X, pady=5)
        self.update_preview()

    def on_slider_change(self, value):
        val = float(value)
        self.slider_value_label.config(text=f"{'+' if val >= 0 else ''}{val:.0f}%")
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
                self.assign_type_colors()
                self.populate_filters()
                self.update_all_views()
                messagebox.showinfo("Succès", f"{len(self.df)} lignes importées")
            except Exception as e:
                messagebox.showerror("Erreur", str(e))

    def assign_type_colors(self):
        """Assigner une couleur à chaque type"""
        if self.df is None or "Type" not in self.df.columns:
            return
        types = self.df["Type"].dropna().unique()
        self.type_colors = {t: self.color_palette[i % len(self.color_palette)]
                           for i, t in enumerate(types)}

    def export_csv(self):
        if self.df is None:
            messagebox.showwarning("Attention", "Aucune donnée")
            return

        file_path = filedialog.asksaveasfilename(
            title="Enregistrer CSV", defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )

        if file_path:
            try:
                self.df.to_csv(file_path, index=False)
                # Aperçu
                win = tk.Toplevel(self.root)
                win.title("Export réussi")
                win.geometry("800x400")
                ttk.Label(win, text=f"Exporté: {file_path}", font=('TkDefaultFont', 10, 'bold')).pack(pady=5)
                text = tk.Text(win, wrap=tk.NONE)
                text.pack(fill=tk.BOTH, expand=True)
                text.insert(tk.END, self.df.head(50).to_string())
                text.config(state=tk.DISABLED)
            except Exception as e:
                messagebox.showerror("Erreur", str(e))

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

        # Date filter
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
            (self.segment_macro_var, "SegmentMacro"), (self.file_var, "File"),
            (self.segment_var, "Segment"), (self.dcr_var, "DCR"),
            (self.semaine_var, "Semaine"), (self.type_var, "Type")
        ]:
            if var.get():
                active.append(f"{name}={var.get()}")
        if self.date_debut_filter.get() and self.date_fin_filter.get():
            active.append(f"Date: {self.date_debut_filter.get()}→{self.date_fin_filter.get()}")
        self.active_filters_label.config(text=" | ".join(active) if active else "")

    def update_all_views(self):
        self.update_viz_table()
        self.update_summary()
        self.update_histogram()
        self.update_data_table()
        self.update_preview()
        self.update_history_label()

    def update_viz_table(self):
        """Mettre à jour le tableau complet dans visualisation"""
        for item in self.viz_tree.get_children():
            self.viz_tree.delete(item)

        if self.filtered_df is None:
            self.row_count_label.config(text="0 lignes")
            return

        for idx, row in self.filtered_df.iterrows():
            values = [row.get(col, "") for col in self.columns]
            self.viz_tree.insert("", tk.END, values=values)

        self.row_count_label.config(text=f"{len(self.filtered_df)} lignes")

    def update_data_table(self):
        """Tableau avec checkboxes pour sélection"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if self.filtered_df is None or self.filtered_df.empty:
            ttk.Label(self.scrollable_frame, text="Aucune donnée").pack()
            return

        # En-têtes
        headers = ["", "Segment", "Type", "NbInteractions", "Date"]
        for i, h in enumerate(headers):
            ttk.Label(self.scrollable_frame, text=h, font=('TkDefaultFont', 8, 'bold'),
                     relief=tk.RIDGE, padding=3).grid(row=0, column=i, sticky="nsew")

        for row_num, (idx, row) in enumerate(self.filtered_df.iterrows(), start=1):
            if idx not in self.check_vars:
                self.check_vars[idx] = tk.BooleanVar(value=False)

            cb = ttk.Checkbutton(self.scrollable_frame, variable=self.check_vars[idx],
                                command=self.on_check_change)
            cb.grid(row=row_num, column=0)

            for col_num, val in enumerate([
                str(row.get("Segment", "")),
                str(row.get("Type", "")),
                str(row.get("NbInteractions", "")),
                str(row.get("Date_debut", ""))[:10]
            ], start=1):
                ttk.Label(self.scrollable_frame, text=val, padding=2).grid(row=row_num, column=col_num, sticky="w")

        self.update_selection_count()

    def on_check_change(self):
        self.update_selection_count()
        self.update_preview()

    def update_selection_count(self):
        if self.filtered_df is None:
            self.selection_count_label.config(text="0 / 0")
            return
        selected = sum(1 for idx in self.filtered_df.index if self.check_vars.get(idx, tk.BooleanVar()).get())
        self.selection_count_label.config(text=f"{selected} / {len(self.filtered_df)}")

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
            self.total_label.config(text="Total: 0")
            return

        if "Type" in self.filtered_df.columns and "NbInteractions" in self.filtered_df.columns:
            summary = self.filtered_df.groupby("Type")["NbInteractions"].sum().reset_index()
            for _, row in summary.iterrows():
                type_name = row["Type"]
                color = self.type_colors.get(type_name, "#000000")
                self.summary_tree.insert("", tk.END, values=(type_name, f"{int(row['NbInteractions']):,}", "■"),
                                        tags=(type_name,))

            total = self.filtered_df["NbInteractions"].sum()
            self.total_label.config(text=f"Total: {int(total):,}")

    def update_histogram(self):
        """Histogramme avec couleurs par Type"""
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

        # Pivot pour stacked bar
        pivot = df_chart.groupby([df_chart["Date_debut"].dt.strftime('%Y-%m-%d'), "Type"])["NbInteractions"].sum().unstack(fill_value=0)

        # Plot stacked bar
        dates = pivot.index.tolist()
        bottom = np.zeros(len(dates))

        for type_name in pivot.columns:
            values = pivot[type_name].values
            color = self.type_colors.get(type_name, '#888888')
            self.ax.bar(dates, values, bottom=bottom, label=type_name, color=color)
            bottom += values

        self.ax.set_xlabel('Date')
        self.ax.set_ylabel('NbInteractions')
        self.ax.tick_params(axis='x', rotation=45, labelsize=8)
        self.ax.legend(loc='upper right', fontsize=8)
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

        # Détail
        for item in self.detail_tree.get_children():
            self.detail_tree.delete(item)

        for idx in selected[:50]:
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
                row.get("Segment", ""), row.get("Type", ""),
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
            messagebox.showwarning("Attention", "Cochez des lignes")
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
            self.log_modification(idx, old_val, new_val)

        self.apply_filters()
        diff = total_after - total_before
        messagebox.showinfo("OK", f"{len(selected)} lignes modifiées\n"
                           f"Avant: {total_before:,}\nAprès: {total_after:,}\n"
                           f"Diff: {'+' if diff >= 0 else ''}{diff:,}")

    def undo(self):
        if not self.history:
            messagebox.showinfo("Info", "Rien à annuler")
            return
        self.df = self.history.pop()
        self.apply_filters()
        messagebox.showinfo("OK", "Annulé")

    def log_modification(self, row_idx, old_value, new_value):
        with open(self.log_file, "a", encoding="utf-8") as f:
            row = self.df.loc[row_idx]
            f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] "
                   f"{row.get('Segment', '')}, {row.get('Type', '')}: "
                   f"{old_value} -> {new_value}\n")

    def view_log(self):
        if not os.path.exists(self.log_file):
            messagebox.showinfo("Info", "Aucun historique")
            return
        win = tk.Toplevel(self.root)
        win.title("Historique")
        win.geometry("600x400")
        text = tk.Text(win, wrap=tk.WORD)
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
