# Muswellbrook Twin Circuits – Analysis Programs

## Project Overview

This repository contains the Python 3 analysis and visualisation programs for the **Muswellbrook Twin Circuits** project.

The scripts generate circuit geometry, perform terrain and earthworks analysis, simulate lap performance, calculate run-off and facility requirements, and produce master plan drawings and export files.

## Project Structure

| File / Directory | Description |
|---|---|
| `base.py` | Terrain grid, parcel boundary, entry zone, and start points. |
| `geom.py` | Clothoid–arc–clothoid corner geometry. |
| `pi.py` | Corner-speed helper functions used by the geometry calculations. |
| `layouts.py` | Defines the two circuits as lists of corner points in the format `[name, E, N, radius, banking]`. |
| `circuit.py` | Circuit class: builds the centreline, fits levels to the terrain, calculates earthworks, and performs lap simulations. Also contains car data (`CARS`). |
| `model.py` | Builds both circuits and assigns names to the corners. |
| `analysis.py` | Performs compulsory and additional calculations, including run-off, facilities, and land budget analysis. |
| `render.py` | Generates the master plan and individual circuit sheets as PNG files. |
| `export.py` | Exports circuit centrelines to CSV, GeoJSON, KML, and DXF formats. |
| `roads.json` | Access-road waypoints. |
| `data/grid.npz` | Team-provided 10 m terrain grid containing E, N, and Z arrays. |

## Requirements

The project requires **Python 3** and the following dependencies:

- NumPy
- SciPy
- Shapely
- CVXPY
- Matplotlib
- PyProj

Install the required dependencies using:

```bash
pip install numpy scipy shapely cvxpy matplotlib pyproj
```

## Setup

### 1. Configure Directory Paths

The scripts currently use hard-coded directory paths:

```text
/home/claude/v3
/mnt/user-data/outputs/v3
```

Before running the programs, search for and replace both paths throughout the scripts with the corresponding directories on your local machine.

### 2. Add Input Data

Ensure that the terrain data file is available at:

```text
data/grid.npz
```

The project also requires `roads.json` for access-road waypoint information.

## Execution Order

The scripts are designed to run sequentially. Execute them in the following order:

### 1. Run the Analysis

```bash
python3 analysis.py
```

This performs the circuit analysis and generates:

- `results.json`
- `shapes.pkl`
- Printed analysis log

### 2. Generate Drawings

```bash
python3 render.py
```

This generates:

- Master plan
- Individual circuit sheets
- PNG visualisations

### 3. Export Circuit Geometry

```bash
python3 export.py
```

This exports the circuit centrelines in the following formats:

- CSV
- GeoJSON
- KML
- DXF

### Execution Dependencies

The scripts must be executed in the following sequence:

```text
analysis.py
    |
    v
render.py
    |
    v
export.py
```

**Important:** Run `analysis.py` first to ensure that the required analysis outputs are available before rendering and exporting.

## Important Notes

### Car Comparison Plot

In `render.py`, there is currently a dashed comparison line for Car 4.

For the **Car 5 version of the analysis**, delete the corresponding Car 4 plot call so that it is not displayed in the rendered circuit drawings.

### Input Data

The project uses the team's supplied **10 m terrain grid**:

```text
data/grid.npz
```

The file contains three arrays:

| Array | Description |
|---|---|
| `E` | Easting coordinates |
| `N` | Northing coordinates |
| `Z` | Terrain elevation values |

The project also uses `roads.json` for access-road waypoint information.

## Project Information

| Property | Details |
|---|---|
| Project | Muswellbrook Twin Circuits |
| Language | Python 3 |
| Purpose | Circuit geometry, terrain analysis, earthworks, lap simulation, master planning, and geometry export |