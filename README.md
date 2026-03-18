# New York City Building Footprints

A data visualization of New York City building footprints, built for a data visualization course.

## Overview

This project displays building footprint geometries from NYC open data as an interactive web visualization. The map supports filtering and exploration of the built environment.

## Project structure

- **`index.html`** – Main visualization (map, controls, styling)
- **`buildings.json`** – Processed building geometries for the browser (derived from the GeoJSON)
- **`data/footprints.geojson`** – Source NYC building footprints (via [Git LFS](https://git-lfs.github.com/))
- **`extract.py`** – Script that converts the GeoJSON into the simplified JSON used by the viz (requires Python, Shapely)

## Running locally

1. Serve the project with a local HTTP server (e.g. from the project root):
   ```bash
   python3 -m http.server 8000
