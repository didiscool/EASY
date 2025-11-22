# Quick Start Guide - EASY Temporal Keys System

## 🚀 Installation & Launch

### Prerequisites
```bash
# Install dependencies
pip install pandas tkcalendar matplotlib openpyxl

# Navigate to EASY directory
cd /home/user/EASY
```

### Run Application
```bash
python csv_import_ui.py
```

### Run Tests
```bash
python test_temporal_hierarchy.py
```

---

## 📊 3-Minute Tutorial

### Step 1: Import Data

```
1. Click [Importer] in Import/Export section
2. Select sample_data.xlsx
3. Click OK
   → 200 rows imported
   → Filters auto-populated
   → Keys calculated automatically
```

### Step 2: Visualize

```
1. Go to "Visualisation" tab
2. See stacked bar chart (interactive)
3. Select different chart type:
   - Line, Area, Pie, Grouped Bar, Cumulative, Heatmap
4. View data table below chart
5. See summary by Type on left
```

### Step 3: Modify Keys

```
1. Go to "Clés Avancées" tab
2. Click [Visualiser Avant/Après Modifications]
   → Shows before/after data comparison
   → Tables, charts, and impact statistics
3. Close window
```

### Step 4: Convert File

```
1. Go to "Clés Avancées" tab
2. Click [Convertir Fichier]
   → Dialog opens showing current Pas (e.g., "Semaine")
3. Select target Pas → "Jour"
4. Configure day weights:
   - Lundi-Vendredi: 20% each
   - Samedi-Dimanche: 0%
5. Click [Convertir]
   → 4 rows become ~28 rows
   → Total interactions preserved
6. See updated data with Pas="Jour"
```

### Step 5: Save & Revert

```
1. Stay in "Clés Avancées" tab
2. Click [Sauvegarder comme Baseline]
   → Current state saved as reference
3. Make some modifications to data
4. Click [Revenir à Baseline]
   → All changes reverted
   → State restored to saved point
```

---

## 📐 Formula Explanation

### Simple Version
```
nb = total × proportion_créneau × proportion_jour × proportion_semaine
```

### Full Formula
```
NbInteractions = Global_Value
               × Key_Temporal
               × Key_Type
               × Key_SegMacro
               × Key_Segment
               × Key_DCR
               × Key_File
               × Key_Offre

Where:
  Key_Temporal = Weight_Creneau (in Day)
               × Weight_Day (in Week)
               × Weight_Week (in Range)
```

### Example
```
Data:
  • Global: 10,000 interactions
  • Week S01: 50% of range
  • Monday: 20% of week
  • 08:00: 5% of day

Calculation:
  nb = 10,000 × 0.05 × 0.20 × 0.50 = 50 interactions
```

---

## 🔑 Key Types

### Temporal Keys (NEW)
- **Creneaux** (30-min slots): 08:00, 08:30, ..., 17:30
- **Jours** (Days): Monday through Sunday
- **Semaines** (Weeks): S01-S52
- Compose: créneau × jour × semaine

### Distribution Keys (Existing)
- **Type**: Appel, Email, Chat, SMS
- **SegmentMacro**: Retail, Enterprise, SMB
- **Segment**: Premium, Standard, Basic
- **File**: Nord, Sud, Est, Ouest, Centre
- **DCR**: DCR1, DCR2, DCR3
- **Offre**: Offre_A, Offre_B, Offre_C

---

## 🔄 Conversions

### Semaine → Jour
```
Input:  S01-2024: 1,000 interactions
        Pas = "Semaine"

Config: Lundi-Vendredi: 20% each
        Samedi-Dimanche: 0%

Output: 2024-01-01: 200 (Lundi)
        2024-01-02: 200 (Mardi)
        2024-01-03: 200 (Mercredi)
        2024-01-04: 200 (Jeudi)
        2024-01-05: 200 (Vendredi)
        2024-01-06: 0   (Samedi)
        2024-01-07: 0   (Dimanche)
        Total: 1,000 ✓
```

### Jour → Créneau
```
Input:  2024-01-01: 1,000 interactions
        Pas = "Jour"

Config: 20 créneaux × 5%

Output: 2024-01-01 08:00: 50
        2024-01-01 08:30: 50
        ... (20 rows)
        Total: 1,000 ✓
```

---

## 📈 Data Tables

### Tab: Visualisation
```
┌─ Type de visualisation ─────────────┐
│ ○ Barres empilées ● ○ Lignes ○ Pie  │
│ ○ Aires ○ Barres groupées ○ Heatmap │
└─────────────────────────────────────┘

[Large Chart Area - 12x5"]

┌─ Résumé par Type ─┐  ┌─ Données ──────────┐
│ Type      Total % │  │ Columns from data  │
│ Appel  150  30.0% │  │ scrollable table    │
│ Email  100  20.0% │  │ 200 rows displayed │
│ SMS    250  50.0% │  │                    │
└────────────────────┘  └────────────────────┘
```

### Tab: Sélection & Modifications
```
┌─ Sélection ──────────────────────┐
│ [Tout] [Rien] [Inverser]         │ 0/200 selected
└──────────────────────────────────┘

[Data table with checkboxes]
 ✓ Row 1 | Appel | 100
 ✓ Row 2 | Email | 80
   Row 3 | SMS   | 120

┌─ Modification ────────────────────┐
│ ○ Relatif (%) ● ○ Absolu         │
│ -50% ══●═══ +50%  [0%]           │
└──────────────────────────────────┘

┌─ Aperçu ─────────────────────────┐
│ AVANT: 200 interactions          │
│ APRÈS: 230 interactions (↑15%)   │
│ DIFF:  +30 (+15%)                │
└──────────────────────────────────┘
```

### Tab: Clés Avancées
```
┌─ Outils Avancés ──────────────────────────┐
│ [Visualiser Avant/Après]                  │
│ [Convertir Fichier (Sem↔Jour↔Crén)]       │
│ [Sauvegarder comme Baseline]              │
│ [Revenir à Baseline]                      │
└───────────────────────────────────────────┘

┌─ Informations ────────────────────────────┐
│ HIÉRARCHIE TEMPORELLE                     │
│ Formule: nb = global × key_temp × ...     │
│ key_temp = poids_crén × poids_jour × ... │
│                                           │
│ Structure:                                │
│ Semaine (S01-S52)                         │
│   ├─ Jour (lun-dim)                       │
│   │   ├─ Créneau (08:00-17:30)            │
│                                           │
│ ⚠️ MODIFICATIONS DÉTECTÉES                │
│ S01-2024: 50.00% → 30.00% (-20%)          │
│ S02-2024: 50.00% → 70.00% (+20%)          │
│                                           │
│ ÉTAT DU GESTIONNAIRE                      │
│ Semaines: 2 semaines                      │
│ Jours: 2 semaines avec jours              │
│ Créneaux: 5 jours avec créneaux           │
└───────────────────────────────────────────┘
```

---

## 🧪 Common Test Cases

### Test 1: Calculate Keys from Data
```bash
# Automatic on import, but can also:
1. Import data
2. Go to "Clés de répartition" tab
3. Click [Calculer clés depuis données]
4. See temporal keys populated
```

### Test 2: Convert and Verify Total
```bash
# Ensure no data loss in conversion
1. Note total NbInteractions before
2. Semaine → Jour: Total preserved? ✓
3. Jour → Créneau: Total preserved? ✓
4. Créneau → Jour: Totals merge correctly? ✓
```

### Test 3: Baseline Operations
```bash
1. [Sauvegarder comme Baseline]
2. Modify some values
3. [Revenir à Baseline]
4. Verify all restored to saved state
```

### Test 4: Before/After Visualization
```bash
1. Import data
2. [Visualiser Avant/Après]
3. See 3 tabs: Tables, Charts, Stats
4. Verify impact calculations correct
```

### Test 5: Weight Distribution
```bash
1. Open file converter
2. Set weights that DON'T sum to 100%
3. Click [Normaliser]
4. Verify sum now equals 100%
```

---

## 💾 Import/Export

### Export Data
```
1. Click [Exporter]
2. Choose format:
   - .xlsx (Excel)
   - .csv (Comma-separated)
3. Save location
4. Click Save
```

### Export Keys
```
1. Click [Exporter Clés]
2. Choose format:
   - .xlsx (Excel with sheets for each key type)
   - .json (JSON structure)
3. Save location
4. Click Save
```

### Import Keys
```
1. Click [Importer Clés]
2. Select previously saved keys file
3. Keys loaded into distribution_keys
4. Can now use for construction
```

---

## 🐛 Troubleshooting

### Problem: "No data to visualize"
**Solution**: Import data first with [Importer]

### Problem: "TemporalKeysManager not configured"
**Solution**: Shouldn't happen - it's initialized in __init__. Restart app.

### Problem: Conversion shows wrong count
**Solution**: Check that weights sum to 100%. Use [Normaliser].

### Problem: Date format error
**Solution**: Ensure dates in YYYY-MM-DD format. Check sample_data.xlsx.

### Problem: Can't convert file
**Solution**: Need at least one row with Pas column set to source level.

---

## 📚 Files Overview

| File | Purpose | Size |
|------|---------|------|
| `csv_import_ui.py` | Main application | 1500+ lines |
| `temporal_keys_manager.py` | Temporal keys system | 430 lines |
| `before_after_visualizer.py` | Visualization | 350 lines |
| `file_converter_dialog.py` | Conversion UI | 450 lines |
| `test_temporal_hierarchy.py` | Test suite | 310 lines |
| `sample_data.xlsx` | Test data | 200 rows |
| `IMPLEMENTATION_SUMMARY_FR.md` | Detailed doc | French |
| `ARCHITECTURE.md` | Technical details | English |
| `QUICKSTART.md` | This guide | English |

---

## 🎓 Learning Path

1. **Beginner**: Run app, import data, view charts (5 min)
2. **Intermediate**: Try conversions, modify keys (10 min)
3. **Advanced**: Understand formula, use baseline (15 min)
4. **Expert**: Read ARCHITECTURE.md, modify code (30+ min)

---

## ✅ Checklist

- [ ] Python 3.7+ installed
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] App launches: `python csv_import_ui.py`
- [ ] Tests pass: `python test_temporal_hierarchy.py`
- [ ] Can import data
- [ ] Can visualize data
- [ ] Can convert files
- [ ] Can save/revert baseline

---

## 🔗 Key Resources

- **Code**: All files in `/home/user/EASY/`
- **Git Branch**: `claude/fix-temporal-key-calc-012dvwJosjQcT7fqWqn3Qp8G`
- **Documentation**: IMPLEMENTATION_SUMMARY_FR.md (French), ARCHITECTURE.md (English)
- **Tests**: `test_temporal_hierarchy.py` (all 5 tests pass ✓)

---

**Ready to go!** 🚀

Questions? Check ARCHITECTURE.md or run `python test_temporal_hierarchy.py` for examples.
