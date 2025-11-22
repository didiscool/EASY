#!/usr/bin/env python3
"""
Module de visualisation avant/après pour les modifications de clés de répartition
Affiche les tableaux, graphiques et statistiques avant et après modification
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import tkinter as tk
from tkinter import ttk


class BeforeAfterVisualizer:
    """Visualiseur pour comparaison avant/après des modifications de clés"""

    def __init__(self, parent_frame):
        """Initialiser le visualiseur dans un frame Tkinter"""
        self.frame = parent_frame
        self.before_df = None
        self.after_df = None
        self.setup_ui()

    def setup_ui(self):
        """Configurer l'interface utilisateur"""
        # Notebook pour les différentes vues
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Onglet tableaux
        self.tab_tables = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_tables, text="Tableaux Comparatifs")
        self.setup_tables_tab()

        # Onglet graphiques
        self.tab_charts = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_charts, text="Graphiques")
        self.setup_charts_tab()

        # Onglet statistiques
        self.tab_stats = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_stats, text="Statistiques d'Impact")
        self.setup_stats_tab()

    def setup_tables_tab(self):
        """Configurer l'onglet des tableaux comparatifs"""
        paned = ttk.PanedWindow(self.tab_tables, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Avant
        before_frame = ttk.LabelFrame(paned, text="AVANT (Baseline)", padding="3")
        paned.add(before_frame, weight=1)

        self.before_tree = ttk.Treeview(before_frame, columns=("Element", "Value", "%"),
                                        show="headings", height=15)
        self.before_tree.heading("Element", text="Élément")
        self.before_tree.heading("Value", text="Valeur")
        self.before_tree.heading("%", text="% Total")
        self.before_tree.column("Element", width=150)
        self.before_tree.column("Value", width=80)
        self.before_tree.column("%", width=80)

        before_scroll = ttk.Scrollbar(before_frame, orient="vertical", command=self.before_tree.yview)
        self.before_tree.configure(yscrollcommand=before_scroll.set)
        self.before_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        before_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Après
        after_frame = ttk.LabelFrame(paned, text="APRÈS (Modifié)", padding="3")
        paned.add(after_frame, weight=1)

        self.after_tree = ttk.Treeview(after_frame, columns=("Element", "Value", "%"),
                                       show="headings", height=15)
        self.after_tree.heading("Element", text="Élément")
        self.after_tree.heading("Value", text="Valeur")
        self.after_tree.heading("%", text="% Total")
        self.after_tree.column("Element", width=150)
        self.after_tree.column("Value", width=80)
        self.after_tree.column("%", width=80)

        after_scroll = ttk.Scrollbar(after_frame, orient="vertical", command=self.after_tree.yview)
        self.after_tree.configure(yscrollcommand=after_scroll.set)
        self.after_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        after_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_charts_tab(self):
        """Configurer l'onglet des graphiques"""
        # Frame pour les contrôles
        control_frame = ttk.LabelFrame(self.tab_charts, text="Options de visualisation", padding="3")
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        self.chart_type_var = tk.StringVar(value="bar_comparison")
        for text, val in [("Comparaison Barres", "bar_comparison"),
                          ("Distribution Avant", "pie_before"),
                          ("Distribution Après", "pie_after"),
                          ("Tendance", "trend")]:
            ttk.Radiobutton(control_frame, text=text, variable=self.chart_type_var,
                          value=val, command=self.refresh_charts).pack(side=tk.LEFT, padx=5)

        # Frame pour les graphiques
        self.chart_frame = ttk.Frame(self.tab_charts)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def setup_stats_tab(self):
        """Configurer l'onglet des statistiques"""
        self.stats_text = tk.Text(self.tab_charts, height=20, width=80)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.tab_stats, orient="vertical", command=self.stats_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.stats_text.configure(yscrollcommand=scrollbar.set)

    def set_data(self, before_df: pd.DataFrame, after_df: pd.DataFrame, step: str = "jour"):
        """
        Définir les données à comparer

        Args:
            before_df: DataFrame avant modification
            after_df: DataFrame après modification
            step: "creneau", "jour", ou "semaine"
        """
        self.before_df = before_df.copy()
        self.after_df = after_df.copy()
        self.step = step

        self.refresh_all()

    def refresh_all(self):
        """Rafraîchir tous les affichages"""
        self.refresh_tables()
        self.refresh_charts()
        self.refresh_stats()

    def refresh_tables(self):
        """Rafraîchir les tableaux comparatifs"""
        # Vider les arbres
        for item in self.before_tree.get_children():
            self.before_tree.delete(item)
        for item in self.after_tree.get_children():
            self.after_tree.delete(item)

        if self.before_df is None or self.after_df is None:
            return

        # Groupe par étape temporelle
        group_col = self._get_group_column()

        # Avant
        before_grouped = self.before_df.groupby(group_col)["NbInteractions"].sum()
        before_total = before_grouped.sum()

        for element, value in before_grouped.items():
            pct = (value / before_total * 100) if before_total > 0 else 0
            self.before_tree.insert("", tk.END, values=(str(element), f"{int(value):,}", f"{pct:.1f}%"))

        # Après
        after_grouped = self.after_df.groupby(group_col)["NbInteractions"].sum()
        after_total = after_grouped.sum()

        for element, value in after_grouped.items():
            pct = (value / after_total * 100) if after_total > 0 else 0
            self.after_tree.insert("", tk.END, values=(str(element), f"{int(value):,}", f"{pct:.1f}%"))

        # Totaux
        self.before_tree.insert("", tk.END, values=("TOTAL", f"{int(before_total):,}", "100.0%"))
        self.after_tree.insert("", tk.END, values=("TOTAL", f"{int(after_total):,}", "100.0%"))

    def refresh_charts(self):
        """Rafraîchir les graphiques"""
        # Vider le frame
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        if self.before_df is None or self.after_df is None:
            return

        chart_type = self.chart_type_var.get()

        # Créer la figure
        fig = Figure(figsize=(12, 5), dpi=85)

        if chart_type == "bar_comparison":
            self._draw_bar_comparison(fig)
        elif chart_type == "pie_before":
            self._draw_pie(fig, self.before_df, "AVANT")
        elif chart_type == "pie_after":
            self._draw_pie(fig, self.after_df, "APRÈS")
        elif chart_type == "trend":
            self._draw_trend(fig)

        # Embed dans Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        canvas.draw()

    def refresh_stats(self):
        """Rafraîchir les statistiques d'impact"""
        self.stats_text.delete("1.0", tk.END)

        if self.before_df is None or self.after_df is None:
            self.stats_text.insert("1.0", "Pas de données pour comparer")
            return

        # Calcul des statistiques
        group_col = self._get_group_column()

        before_grouped = self.before_df.groupby(group_col)["NbInteractions"].sum()
        after_grouped = self.after_df.groupby(group_col)["NbInteractions"].sum()

        before_total = before_grouped.sum()
        after_total = after_grouped.sum()

        stats_text = "=" * 80 + "\n"
        stats_text += "RÉSUMÉ D'IMPACT\n"
        stats_text += "=" * 80 + "\n\n"

        stats_text += f"Total AVANT:    {int(before_total):>15,} interactions\n"
        stats_text += f"Total APRÈS:    {int(after_total):>15,} interactions\n"
        stats_text += f"Différence:     {int(after_total - before_total):>15,} interactions\n"
        stats_text += f"Variation:      {((after_total - before_total) / before_total * 100):>14.1f}%\n\n"

        stats_text += "-" * 80 + "\n"
        stats_text += "IMPACT PAR ÉLÉMENT\n"
        stats_text += "-" * 80 + "\n"
        stats_text += f"{'Élément':<30} {'Avant':>15} {'Après':>15} {'Diff':>15} {'%':>10}\n"
        stats_text += "-" * 80 + "\n"

        all_elements = set(list(before_grouped.index) + list(after_grouped.index))

        for element in sorted(all_elements):
            before_val = before_grouped.get(element, 0)
            after_val = after_grouped.get(element, 0)
            diff = after_val - before_val
            diff_pct = (diff / before_val * 100) if before_val > 0 else 0

            color = "📈" if diff > 0 else "📉" if diff < 0 else "="
            stats_text += f"{str(element):<30} {int(before_val):>15,} {int(after_val):>15,} {int(diff):>15,} {diff_pct:>9.1f}% {color}\n"

        stats_text += "-" * 80 + "\n\n"

        # Analyse des changements
        stats_text += "ANALYSE DES CHANGEMENTS\n"
        stats_text += "-" * 80 + "\n"

        increased = sum(1 for e in all_elements if after_grouped.get(e, 0) > before_grouped.get(e, 0))
        decreased = sum(1 for e in all_elements if after_grouped.get(e, 0) < before_grouped.get(e, 0))
        unchanged = sum(1 for e in all_elements if after_grouped.get(e, 0) == before_grouped.get(e, 0))

        stats_text += f"Éléments augmentés:  {increased}\n"
        stats_text += f"Éléments diminués:   {decreased}\n"
        stats_text += f"Éléments inchangés:  {unchanged}\n\n"

        # Max impacts
        max_increase = max([(e, after_grouped.get(e, 0) - before_grouped.get(e, 0))
                           for e in all_elements], key=lambda x: x[1], default=(None, 0))
        max_decrease = min([(e, after_grouped.get(e, 0) - before_grouped.get(e, 0))
                           for e in all_elements], key=lambda x: x[1], default=(None, 0))

        if max_increase[0]:
            stats_text += f"Plus augmenté:       {max_increase[0]:<20} (+{int(max_increase[1]):,})\n"
        if max_decrease[0]:
            stats_text += f"Plus diminué:        {max_decrease[0]:<20} ({int(max_decrease[1]):,})\n"

        self.stats_text.insert("1.0", stats_text)

    # ========================================================================
    # Méthodes privées pour dessiner les graphiques
    # ========================================================================

    def _get_group_column(self) -> str:
        """Obtenir la colonne de regroupement selon l'étape temporelle"""
        if self.step == "creneau":
            return "Creneau"
        elif self.step == "semaine":
            return "Semaine"
        else:  # jour
            return "Date_debut"

    def _draw_bar_comparison(self, fig: Figure):
        """Dessiner une comparaison en barres"""
        ax = fig.add_subplot(111)

        group_col = self._get_group_column()
        before_grouped = self.before_df.groupby(group_col)["NbInteractions"].sum()
        after_grouped = self.after_df.groupby(group_col)["NbInteractions"].sum()

        all_elements = sorted(set(list(before_grouped.index) + list(after_grouped.index)))
        before_vals = [before_grouped.get(e, 0) for e in all_elements]
        after_vals = [after_grouped.get(e, 0) for e in all_elements]

        x = np.arange(len(all_elements))
        width = 0.35

        ax.bar(x - width/2, before_vals, width, label="Avant", color="#4CAF50", alpha=0.8)
        ax.bar(x + width/2, after_vals, width, label="Après", color="#2196F3", alpha=0.8)

        ax.set_xlabel("Élément")
        ax.set_ylabel("NbInteractions")
        ax.set_title("Comparaison Avant/Après par Élément")
        ax.set_xticks(x)
        ax.set_xticklabels([str(e)[:10] for e in all_elements], rotation=45, fontsize=8)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        fig.tight_layout()

    def _draw_pie(self, fig: Figure, df: pd.DataFrame, title: str):
        """Dessiner un camembert de distribution"""
        ax = fig.add_subplot(111)

        group_col = self._get_group_column()
        grouped = df.groupby(group_col)["NbInteractions"].sum()

        ax.pie(grouped.values, labels=[str(x)[:15] for x in grouped.index],
              autopct='%1.1f%%', startangle=90)
        ax.set_title(f"Distribution {title}")
        fig.tight_layout()

    def _draw_trend(self, fig: Figure):
        """Dessiner la tendance des changements"""
        ax = fig.add_subplot(111)

        group_col = self._get_group_column()
        before_grouped = self.before_df.groupby(group_col)["NbInteractions"].sum()
        after_grouped = self.after_df.groupby(group_col)["NbInteractions"].sum()

        all_elements = sorted(set(list(before_grouped.index) + list(after_grouped.index)))
        changes = [(after_grouped.get(e, 0) - before_grouped.get(e, 0)) for e in all_elements]

        colors = ['#4CAF50' if c >= 0 else '#F44336' for c in changes]
        ax.barh([str(e)[:15] for e in all_elements], changes, color=colors, alpha=0.8)

        ax.set_xlabel("Variation (interactions)")
        ax.set_title("Variation par Élément")
        ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
        ax.grid(axis='x', alpha=0.3)
        fig.tight_layout()


if __name__ == "__main__":
    # Test simple
    root = tk.Tk()
    root.title("Test BeforeAfter Visualizer")
    root.geometry("1200x700")

    # Créer des données de test
    np.random.seed(42)
    before_data = {
        "Date_debut": pd.date_range("2024-01-01", periods=10),
        "Creneau": ["08:00"] * 10,
        "Semaine": ["S01"] * 10,
        "NbInteractions": np.random.randint(100, 500, 10)
    }
    before_df = pd.DataFrame(before_data)

    after_df = before_df.copy()
    after_df["NbInteractions"] = after_df["NbInteractions"] * 1.2  # 20% augmentation

    viz = BeforeAfterVisualizer(root)
    viz.set_data(before_df, after_df, step="jour")

    root.mainloop()
