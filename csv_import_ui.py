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

class CSVImportApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Import CSV - Gestion des Interactions")
        self.root.geometry("1400x900")

        self.df = None
        self.filtered_df = None
        self.log_file = "modifications_log.txt"
        self.history = []  # Historique pour annuler
        self.max_history = 50

        self.setup_ui()

    def setup_ui(self):
        # Frame principale
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Section import/export
        import_frame = ttk.LabelFrame(main_frame, text="Import/Export CSV", padding="5")
        import_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(import_frame, text="Importer CSV", command=self.import_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(import_frame, text="Exporter CSV", command=self.export_csv).pack(side=tk.LEFT, padx=5)
        self.file_label = ttk.Label(import_frame, text="Aucun fichier sélectionné")
        self.file_label.pack(side=tk.LEFT, padx=10)

        # Section filtres
        filter_frame = ttk.LabelFrame(main_frame, text="Filtres", padding="5")
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        # Ligne 1 des filtres
        filter_row1 = ttk.Frame(filter_frame)
        filter_row1.pack(fill=tk.X, pady=2)

        # SegmentMacro
        ttk.Label(filter_row1, text="SegmentMacro:").pack(side=tk.LEFT, padx=(0, 5))
        self.segment_macro_var = tk.StringVar()
        self.segment_macro_combo = ttk.Combobox(filter_row1, textvariable=self.segment_macro_var, width=15)
        self.segment_macro_combo.pack(side=tk.LEFT, padx=(0, 15))

        # File
        ttk.Label(filter_row1, text="File:").pack(side=tk.LEFT, padx=(0, 5))
        self.file_var = tk.StringVar()
        self.file_combo = ttk.Combobox(filter_row1, textvariable=self.file_var, width=15)
        self.file_combo.pack(side=tk.LEFT, padx=(0, 15))

        # Segment
        ttk.Label(filter_row1, text="Segment:").pack(side=tk.LEFT, padx=(0, 5))
        self.segment_var = tk.StringVar()
        self.segment_combo = ttk.Combobox(filter_row1, textvariable=self.segment_var, width=15)
        self.segment_combo.pack(side=tk.LEFT, padx=(0, 15))

        # DCR
        ttk.Label(filter_row1, text="DCR:").pack(side=tk.LEFT, padx=(0, 5))
        self.dcr_var = tk.StringVar()
        self.dcr_combo = ttk.Combobox(filter_row1, textvariable=self.dcr_var, width=15)
        self.dcr_combo.pack(side=tk.LEFT, padx=(0, 15))

        # Ligne 2 des filtres
        filter_row2 = ttk.Frame(filter_frame)
        filter_row2.pack(fill=tk.X, pady=2)

        # Semaine
        ttk.Label(filter_row2, text="Semaine:").pack(side=tk.LEFT, padx=(0, 5))
        self.semaine_var = tk.StringVar()
        self.semaine_combo = ttk.Combobox(filter_row2, textvariable=self.semaine_var, width=15)
        self.semaine_combo.pack(side=tk.LEFT, padx=(0, 15))

        # Type
        ttk.Label(filter_row2, text="Type:").pack(side=tk.LEFT, padx=(0, 5))
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(filter_row2, textvariable=self.type_var, width=15)
        self.type_combo.pack(side=tk.LEFT, padx=(0, 15))

        # Filtre Date
        ttk.Label(filter_row2, text="Date début:").pack(side=tk.LEFT, padx=(0, 5))
        self.date_debut_filter = DateEntry(filter_row2, width=12, date_pattern='yyyy-mm-dd')
        self.date_debut_filter.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(filter_row2, text="Date fin:").pack(side=tk.LEFT, padx=(0, 5))
        self.date_fin_filter = DateEntry(filter_row2, width=12, date_pattern='yyyy-mm-dd')
        self.date_fin_filter.pack(side=tk.LEFT, padx=(0, 15))

        # Boutons filtres
        filter_row3 = ttk.Frame(filter_frame)
        filter_row3.pack(fill=tk.X, pady=5)

        ttk.Button(filter_row3, text="Appliquer Filtres", command=self.apply_filters).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_row3, text="Réinitialiser", command=self.reset_filters).pack(side=tk.LEFT, padx=5)

        # Checkbox pour activer filtre date
        self.use_date_filter = tk.BooleanVar(value=False)
        ttk.Checkbutton(filter_row3, text="Filtrer par date", variable=self.use_date_filter).pack(side=tk.LEFT, padx=15)

        # Section résumé par Type
        summary_frame = ttk.LabelFrame(main_frame, text="Somme NbInteractions par Type", padding="5")
        summary_frame.pack(fill=tk.X, pady=(0, 10))

        self.summary_tree = ttk.Treeview(summary_frame, columns=("Type", "Total"), show="headings", height=4)
        self.summary_tree.heading("Type", text="Type")
        self.summary_tree.heading("Total", text="Total Interactions")
        self.summary_tree.column("Type", width=200)
        self.summary_tree.column("Total", width=150)
        self.summary_tree.pack(fill=tk.X)

        # Section prévisualisation
        preview_frame = ttk.LabelFrame(main_frame, text="Prévisualisation des données", padding="5")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Treeview avec scrollbars
        tree_container = ttk.Frame(preview_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)

        self.columns = ["SegmentMacro", "File", "Segment", "DCR", "Semaine", "Offre",
                       "NbInteractions", "Type", "Date_debut", "Date_fin"]

        self.tree = ttk.Treeview(tree_container, columns=self.columns, show="headings", selectmode="extended")

        # Scrollbars
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout pour treeview
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # Configuration colonnes
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, minwidth=50)

        # Bind selection change
        self.tree.bind("<<TreeviewSelect>>", self.on_selection_change)

        # Section résumé sélection (avant/après)
        selection_frame = ttk.LabelFrame(main_frame, text="Résumé de la sélection", padding="5")
        selection_frame.pack(fill=tk.X, pady=(0, 10))

        self.selection_info = ttk.Label(selection_frame, text="Aucune sélection")
        self.selection_info.pack(side=tk.LEFT, padx=10)

        self.before_after_label = ttk.Label(selection_frame, text="")
        self.before_after_label.pack(side=tk.LEFT, padx=20)

        # Section modification
        edit_frame = ttk.LabelFrame(main_frame, text="Modifier NbInteractions", padding="5")
        edit_frame.pack(fill=tk.X)

        # Ligne 1: Type de modification
        edit_row1 = ttk.Frame(edit_frame)
        edit_row1.pack(fill=tk.X, pady=2)

        ttk.Label(edit_row1, text="Mode:").pack(side=tk.LEFT, padx=5)
        self.modify_mode = tk.StringVar(value="global")
        ttk.Radiobutton(edit_row1, text="Valeur globale", variable=self.modify_mode,
                       value="global", command=self.update_preview).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(edit_row1, text="Relatif (%)", variable=self.modify_mode,
                       value="relative", command=self.update_preview).pack(side=tk.LEFT, padx=5)

        ttk.Label(edit_row1, text="Valeur:").pack(side=tk.LEFT, padx=(20, 5))
        self.new_value_var = tk.StringVar()
        self.new_value_var.trace('w', lambda *args: self.update_preview())
        self.new_value_entry = ttk.Entry(edit_row1, textvariable=self.new_value_var, width=15)
        self.new_value_entry.pack(side=tk.LEFT, padx=5)

        # Ligne 2: Boutons d'action
        edit_row2 = ttk.Frame(edit_frame)
        edit_row2.pack(fill=tk.X, pady=5)

        ttk.Button(edit_row2, text="Appliquer modification", command=self.modify_selection).pack(side=tk.LEFT, padx=5)
        ttk.Button(edit_row2, text="Annuler (Ctrl+Z)", command=self.undo).pack(side=tk.LEFT, padx=5)
        ttk.Button(edit_row2, text="Voir Log", command=self.view_log).pack(side=tk.LEFT, padx=5)

        # Raccourci clavier pour annuler
        self.root.bind('<Control-z>', lambda e: self.undo())

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
                self.history = []  # Reset history
                self.populate_filters()
                self.update_treeview()
                self.update_summary()
                messagebox.showinfo("Succès", f"Fichier importé: {len(self.df)} lignes")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'import: {str(e)}")

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
                messagebox.showinfo("Succès", f"Fichier exporté: {file_path}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'export: {str(e)}")

    def populate_filters(self):
        if self.df is None:
            return

        # Remplir les combobox avec les valeurs uniques
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

        # Appliquer les filtres
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

        # Filtre par date si activé
        if self.use_date_filter.get():
            date_debut = self.date_debut_filter.get_date()
            date_fin = self.date_fin_filter.get_date()

            if "Date_debut" in self.filtered_df.columns:
                self.filtered_df["Date_debut"] = pd.to_datetime(self.filtered_df["Date_debut"], errors='coerce')
                self.filtered_df = self.filtered_df[
                    (self.filtered_df["Date_debut"] >= pd.Timestamp(date_debut)) &
                    (self.filtered_df["Date_debut"] <= pd.Timestamp(date_fin))
                ]

        self.update_treeview()
        self.update_summary()

    def reset_filters(self):
        self.segment_macro_var.set("")
        self.file_var.set("")
        self.segment_var.set("")
        self.dcr_var.set("")
        self.semaine_var.set("")
        self.type_var.set("")
        self.use_date_filter.set(False)

        if self.df is not None:
            self.filtered_df = self.df.copy()
            self.update_treeview()
            self.update_summary()

    def update_treeview(self):
        # Effacer les données existantes
        for item in self.tree.get_children():
            self.tree.delete(item)

        if self.filtered_df is None:
            return

        # Ajouter les nouvelles données
        for idx, row in self.filtered_df.iterrows():
            values = [row.get(col, "") for col in self.columns]
            self.tree.insert("", tk.END, iid=idx, values=values)

    def update_summary(self):
        # Effacer le résumé existant
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)

        if self.filtered_df is None or "Type" not in self.filtered_df.columns:
            return

        # Calculer la somme par Type
        if "NbInteractions" in self.filtered_df.columns:
            summary = self.filtered_df.groupby("Type")["NbInteractions"].sum().reset_index()
            for _, row in summary.iterrows():
                self.summary_tree.insert("", tk.END, values=(row["Type"], row["NbInteractions"]))

    def on_selection_change(self, event=None):
        self.update_selection_info()
        self.update_preview()

    def update_selection_info(self):
        selected = self.tree.selection()
        if not selected:
            self.selection_info.config(text="Aucune sélection")
            return

        total = 0
        for item_id in selected:
            try:
                idx = int(item_id)
                if idx in self.df.index:
                    total += self.df.at[idx, "NbInteractions"]
            except (ValueError, KeyError):
                pass

        self.selection_info.config(text=f"Sélection: {len(selected)} ligne(s) | Total NbInteractions: {total}")

    def update_preview(self):
        selected = self.tree.selection()
        if not selected or not self.new_value_var.get():
            self.before_after_label.config(text="")
            return

        try:
            value = float(self.new_value_var.get())
        except ValueError:
            self.before_after_label.config(text="Valeur invalide")
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

        self.before_after_label.config(
            text=f"AVANT: {total_before:.0f} | APRÈS: {total_after:.0f} | Diff: {sign}{diff:.0f} ({sign}{diff_pct:.1f}%)"
        )

    def save_state(self):
        """Sauvegarder l'état actuel pour pouvoir annuler"""
        if self.df is not None:
            state = self.df.copy()
            self.history.append(state)
            if len(self.history) > self.max_history:
                self.history.pop(0)

    def undo(self):
        """Annuler la dernière modification"""
        if not self.history:
            messagebox.showinfo("Info", "Aucune modification à annuler")
            return

        self.df = self.history.pop()
        self.apply_filters()  # Réappliquer les filtres
        messagebox.showinfo("Succès", "Modification annulée")

    def modify_selection(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attention", "Veuillez sélectionner au moins une ligne")
            return

        value_str = self.new_value_var.get()
        try:
            value = float(value_str)
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer un nombre valide")
            return

        # Sauvegarder l'état avant modification
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

                # Modifier dans le DataFrame
                self.df.at[idx, "NbInteractions"] = new_value
                if idx in self.filtered_df.index:
                    self.filtered_df.at[idx, "NbInteractions"] = new_value

                modifications.append((idx, old_value, new_value))

            except (ValueError, KeyError) as e:
                continue

        # Logger les modifications
        for idx, old_val, new_val in modifications:
            self.log_modification(idx, old_val, new_val)

        self.update_treeview()
        self.update_summary()
        self.update_selection_info()

        mode_text = f"{value}%" if self.modify_mode.get() == "relative" else f"= {int(value)}"
        diff = total_after - total_before
        messagebox.showinfo(
            "Succès",
            f"{len(modifications)} ligne(s) modifiée(s) ({mode_text})\n"
            f"Total avant: {total_before}\n"
            f"Total après: {total_after}\n"
            f"Différence: {'+' if diff >= 0 else ''}{diff}"
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

        # Fenêtre pour afficher le log
        log_window = tk.Toplevel(self.root)
        log_window.title("Log des modifications")
        log_window.geometry("800x400")

        text = tk.Text(log_window, wrap=tk.WORD)
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
