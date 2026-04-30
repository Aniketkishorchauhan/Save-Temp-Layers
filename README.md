# Save Temp Layers

A QGIS plugin to save all temporary/memory layers to disk with one click.

## Description

When working with QGIS Processing tools, results are often stored as temporary
(in-memory) layers that disappear when you close the project. This plugin detects
all such temporary layers and lets you save them permanently in one click.

**Supported layer types:**
- Vector layers (in-memory) → GeoPackage, Shapefile, or GeoJSON
- Raster layers (stored in system temp folder) → GeoTIFF

## Features

- One-click detection of all temporary layers in the current project
- Checkbox list to select which layers to save
- Choose output format: GeoPackage / Shapefile / GeoJSON (vector), GeoTIFF (raster)
- Progress bar with success/failure summary
- Option to open the output folder after saving

## Installation

### From the QGIS Plugin Repository
1. Open QGIS
2. Go to **Plugins → Manage and Install Plugins**
3. Search for **Save Temp Layers**
4. Click **Install**

### From ZIP
1. Download `save_temp_layers.zip`
2. Go to **Plugins → Manage and Install Plugins → Install from ZIP**
3. Browse to the downloaded ZIP and click **Install Plugin**

## Usage

1. Load your project and run any Processing tools that produce temporary layers
2. Click the **💾 Save Temporary Layers** button in the toolbar,
   or go to **Plugins → Save Temp Layers → Save Temporary Layers**
3. In the dialog:
   - Check/uncheck the layers you want to save
   - Select your preferred output format
   - Choose an output folder
4. Click **Save Selected Layers**

## Requirements

- QGIS 3.0 or later
- No additional Python dependencies required

## License

This plugin is distributed under the terms of the
[GNU General Public License v2 or later](https://www.gnu.org/licenses/gpl-2.0.html).

## Author

**Cyanide**

## Bug Reports & Contributions

Please report issues and suggest features via the GitHub issue tracker:
https://github.com/Aniketkishorchauhan/save-temp-layers/issues
