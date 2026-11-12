# Save Temp Layers

A QGIS plugin to save selected temporary layers into a single GeoPackage.

## Description

When working with QGIS Processing tools, results are often stored as temporary
(in-memory) layers that disappear when you close the project. This plugin detects
temporary layers and saves the selected ones into one GeoPackage.

**Supported layer types:**
- Vector layers (in-memory) → separate feature tables in the GeoPackage
- Raster layers (stored in the system temp folder) → separate raster tables in the GeoPackage

## Features

- One-click detection of all temporary layers in the current project
- Checkbox list to select which layers to save
- Save all selected vector and raster layers into one GeoPackage file
- Store each layer as its own GeoPackage table, with unique table names
- Repoint each successfully saved project layer to its GeoPackage table
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
   - Choose the output `.gpkg` file
4. Click **Save Selected Layers**

Vector layers are written as feature tables. Raster layers are written as
GeoPackage raster tables (subdatasets), using lossless PNG tiles for byte data
and 16-bit integer data, and TIFF tiles for Float32 data. GeoPackage raster
tables support Byte, Int16, UInt16, and Float32; unsupported types are reported
instead of being silently converted. If the chosen file already exists, the
plugin asks before replacing it.

After each selected layer is saved successfully, its project data source is
updated to point to the corresponding GeoPackage table. If that source change
cannot be validated, the original source is left unchanged and the failure is
included in the results.

## Running integration tests

On Windows with QGIS installed through OSGeo4W, run
`tests\run_qgis_tests.bat`. Set `OSGEO4W_ROOT` if QGIS is installed outside
`C:\OSGeo4W`. The headless tests use the QGIS LTR Python runtime and verify
GeoPackage table layout and exact byte, 16-bit integer, and Float32 raster
values.

## Requirements

- QGIS 3.0 or later
- GeoPackage raster support from the GDAL version bundled with QGIS
- No additional Python dependencies required

## License

This plugin is distributed under the terms of the
[GNU General Public License v2 or later](https://www.gnu.org/licenses/gpl-2.0.html).

## Author

**Cyanide**

## Bug Reports & Contributions

Please report issues and suggest features via the GitHub issue tracker:
https://github.com/Aniketkishorchauhan/save-temp-layers/issues
