#!/usr/bin/env python3
"""
EASY Application - VERSION CORRECTE

Implémente CORRECTEMENT la formule partout:
  NbInteractions = Global × Key_Temporal × Key_Type × Key_SegMacro × Key_Segment × Key_DCR × Key_File × Key_Offre

Basé sur formula_engine.py qui gère la logique correcte.
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

from formula_engine import FormulaEngine


class EASYCorrected:
    """Application EASY corrigée"""

    def __init__(self, root):
        self.root = root
        self.root.title("EASY - Gestion des Interactions (VERSION CORRIGÉE)")
        self.root.geometry("1800x1000")

        self.df = None
        self.engine = None
        self.filtered_df = None

        # États UI
        self.filters = {}
        self.selected_rows = []

        self.setup_ui()

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
        control_frame = ttk.LabelFrame(paned, text="Filtrer et Visualiser", padding="5")
        paned.add(control_frame, weight=0)

        ttk.Label(control_frame, text="Appliquez les filtres ci-dessus, puis visualisez les données filtrées").pack()

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
            columns=("Type", "SegMacro", "Segment", "File", "DCR", "Offre", "NbInt", "Original"),
            show="headings"
        )

        for col in ["Type", "SegMacro", "Segment", "File", "DCR", "Offre", "NbInt", "Original"]:
            self.filtered_tree.heading(col, text=col)
            self.filtered_tree.column(col, width=100)

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.filtered_tree.yview)
        self.filtered_tree.configure(yscrollcommand=scroll.set)
        self.filtered_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_modify_tab(self):
        """Onglet Modifications"""
        paned = ttk.PanedWindow(self.tab_modify, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Gauche: Tableau
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Sélectionnez des lignes et modifiez les clés", font=('TkDefaultFont', 10, 'bold')).pack()

        self.modify_tree = ttk.Treeview(
            left_frame,
            columns=("Sel", "Type", "Value", "Avant", "Après"),
            show="headings"
        )

        for col in ["Sel", "Type", "Value", "Avant", "Après"]:
            self.modify_tree.heading(col, text=col)
            self.modify_tree.column(col, width=100)

        scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.modify_tree.yview)
        self.modify_tree.configure(yscrollcommand=scroll.set)
        self.modify_tree.pack(fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Droite: Contrôles
        right_frame = ttk.LabelFrame(paned, text="Modification des Clés", padding="10")
        paned.add(right_frame, weight=0)

        ttk.Label(right_frame, text="Type de Clé:", font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W, pady=5)
        self.modify_key_type = ttk.Combobox(
            right_frame,
            values=["temporal", "type", "segmacro", "segment", "dcr", "file", "offre"],
            state='readonly',
            width=15
        )
        self.modify_key_type.pack(anchor=tk.W, padx=5, pady=3)

        ttk.Label(right_frame, text="Nouvelle Valeur (%):", font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        self.modify_value = ttk.Entry(right_frame, width=15)
        self.modify_value.pack(anchor=tk.W, padx=5, pady=3)

        ttk.Button(right_frame, text="[APPLIQUER MODIFICATION]", command=self.apply_key_modification).pack(fill=tk.X, pady=10, padx=5)
        ttk.Button(right_frame, text="[Normaliser (100%)]", command=self.normalize_keys).pack(fill=tk.X, pady=5, padx=5)

        self.modify_info = ttk.Label(right_frame, text="", foreground='blue', wraplength=200)
        self.modify_info.pack(pady=10)

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

            # Initialiser le moteur
            self.engine = FormulaEngine(self.df)

            self.file_label.config(text=f"✓ {path.split('/')[-1]} ({len(self.df)} lignes)")

            # Mettre à jour les combos
            self.update_filter_combos()

            # Afficher la répartition
            self.update_breakdown()

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

        types = [""] + sorted(self.df["Type"].unique().astype(str).tolist())
        self.filter_type['values'] = types

        segmacros = [""] + sorted(self.df["SegmentMacro"].unique().astype(str).tolist())
        self.filter_segmacro['values'] = segmacros

    def reset_breakdown_filters(self):
        """Réinitialiser les filtres"""
        self.filter_type.set("")
        self.filter_segmacro.set("")
        self.update_breakdown()

    def update_breakdown(self):
        """Mettre à jour la répartition combinatoire"""
        if self.engine is None:
            return

        # Collecter les filtres
        filters = {}
        if self.filter_type.get():
            filters["Type"] = self.filter_type.get()
        if self.filter_segmacro.get():
            filters["SegmentMacro"] = self.filter_segmacro.get()

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

    def apply_key_modification(self):
        """Appliquer une modification de clé"""
        key_type = self.modify_key_type.get()
        try:
            new_value = float(self.modify_value.get()) / 100
        except:
            messagebox.showerror("Erreur", "Valeur invalide")
            return

        if self.engine and key_type:
            # Pour simplifier: modifier la première clé du type
            keys = self.engine.keys.get(key_type, {})
            if keys:
                first_key = list(keys.keys())[0]
                self.engine.modify_key(key_type, first_key, new_value)
                self.update_breakdown()

    def normalize_keys(self):
        """Normaliser les clés à 100%"""
        if self.engine:
            for key_type in self.engine.keys:
                total = sum(self.engine.keys[key_type].values())
                if total > 0:
                    for k in self.engine.keys[key_type]:
                        self.engine.keys[key_type][k] = self.engine.keys[key_type][k] / total
            self.update_breakdown()

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
