# LCA_FPV_lagoon
Life cycle assessment (LCA) model of a floating photovoltaic (FPV) platform deployed on a coral lagoon in Raiatea, French Polynesia.
# Floating PV Lagoon LCA (acv_lagon)

Life cycle assessment code for a floating photovoltaic (FPV) demonstrator
installed on the coral lagoon of Raiatea, French Polynesia. This repository
accompanies the article submitted to *Sustainable Energy Technologies and
Assessments* (SETA) and provides the full, cleaned codebase used to produce
the article's figures, tables, and results.

## What this is

The demonstrator consists of four floating platforms with different module
configurations (SH81, SH51, SH81-UV, SH51-UV), originally designed for a
coral-reef shading research programme. This project builds a parametric LCA
model of the system — structure, mooring, submarine export cable, inverters,
PV modules, and end-of-life — and computes environmental impacts across 16
EF v3.1 impact categories, with two end-of-life scenarios (local landfill
baseline vs. prospective export recycling).

## Repository contents

- `acv_lagon/` — the LCA package (27 modules, ~2,200+ lines): parametric
  model definition, inventory construction, impact computation, contribution
  analysis, sensitivity analysis, and figure/table generation.
- `ACV_main.ipynb` — the main notebook, run in the order of the article,
  with each section annotated with the paper subsection, figure, or table it
  produces.
- `README.md` — package documentation and usage notes.

## Methodology

- Built on `brightway2` + `lca_algebraic`, extending a parametric PV model
  (`parasol_lca`) with a custom full-system model for this installation
  (structure, floaters, mooring, submarine cable — avoiding double-counting
  against the upstream parametric model).
- Background inventory: ecoinvent 3.11 (cut-off system model).
- Functional unit: kWh delivered, computed from site-specific irradiance and
  measured productible.
- Contribution analysis by life-cycle phase; global sensitivity analysis
  (Sobol / Morris) on key design and site parameters.

## Data & dependencies

This repository contains the modeling code only. It requires a licensed
ecoinvent database (not included) and a working Brightway2/lca_algebraic
environment to run. Primary measurement data (sensor logs, bills of
materials) used to parameterize the model are summarized in the article and
its supplementary information.

## Citation

If you use this code, please cite the associated article (citation details
to be added once published).
