import os

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QComboBox, QListWidget, QListWidgetItem,
    QLineEdit, QCheckBox, QProgressBar, QMessageBox, QGroupBox,
    QSizePolicy, QAbstractItemView
)
from qgis.PyQt.QtCore import Qt, QSize
from qgis.PyQt.QtGui import QFont, QColor

from qgis.core import (
    QgsVectorFileWriter, QgsRasterFileWriter, QgsMapLayer,
    QgsRasterPipe, QgsProject, QgsCoordinateTransformContext
)


class SaveTempLayersDialog(QDialog):
    def __init__(self, parent, temp_layers):
        super().__init__(parent)
        self.temp_layers = temp_layers
        self.setWindowTitle("Save Temporary Layers")
        self.setMinimumWidth(520)
        self.setMinimumHeight(480)
        self._build_ui()
        self._populate_layers()

    # ------------------------------------------------------------------ UI --

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        # ── Title ──────────────────────────────────────────────────────────
        title = QLabel("Save Temporary Layers to Disk")
        font = QFont()
        font.setBold(True)
        font.setPointSize(11)
        title.setFont(font)
        layout.addWidget(title)

        subtitle = QLabel(
            f"Found <b>{len(self.temp_layers)}</b> temporary layer(s) in this project. "
            "Select the ones you want to save."
        )
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # ── Layer list ─────────────────────────────────────────────────────
        list_group = QGroupBox("Layers to Save")
        list_layout = QVBoxLayout(list_group)

        # Select all / none buttons
        sel_row = QHBoxLayout()
        btn_all = QPushButton("Select All")
        btn_none = QPushButton("Select None")
        btn_all.setFixedHeight(24)
        btn_none.setFixedHeight(24)
        btn_all.clicked.connect(self._select_all)
        btn_none.clicked.connect(self._select_none)
        sel_row.addWidget(btn_all)
        sel_row.addWidget(btn_none)
        sel_row.addStretch()
        list_layout.addLayout(sel_row)

        self.layer_list = QListWidget()
        self.layer_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.layer_list.setAlternatingRowColors(True)
        self.layer_list.setSpacing(2)
        list_layout.addWidget(self.layer_list)
        layout.addWidget(list_group)

        # ── Format options ─────────────────────────────────────────────────
        fmt_group = QGroupBox("Output Format")
        fmt_layout = QHBoxLayout(fmt_group)

        fmt_layout.addWidget(QLabel("Vector:"))
        self.vec_format = QComboBox()
        self.vec_format.addItems(["GeoPackage (.gpkg)", "Shapefile (.shp)", "GeoJSON (.geojson)"])
        fmt_layout.addWidget(self.vec_format)

        fmt_layout.addSpacing(20)
        fmt_layout.addWidget(QLabel("Raster:"))
        self.ras_format = QComboBox()
        self.ras_format.addItems(["GeoTIFF (.tif)"])
        fmt_layout.addWidget(self.ras_format)
        fmt_layout.addStretch()
        layout.addWidget(fmt_group)

        # ── Output folder ──────────────────────────────────────────────────
        out_group = QGroupBox("Output Folder")
        out_layout = QHBoxLayout(out_group)
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("Choose a folder where files will be saved…")
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_folder)
        out_layout.addWidget(self.folder_edit)
        out_layout.addWidget(browse_btn)
        layout.addWidget(out_group)

        # ── Progress bar ───────────────────────────────────────────────────
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # ── Buttons ────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("💾  Save Selected Layers")
        self.save_btn.setFixedHeight(36)
        self.save_btn.setStyleSheet(
            "QPushButton { background-color: #0078d4; color: white; font-weight: bold; "
            "border-radius: 4px; padding: 4px 16px; } "
            "QPushButton:hover { background-color: #006cbd; } "
            "QPushButton:disabled { background-color: #aaa; }"
        )
        self.save_btn.clicked.connect(self._save_layers)

        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(36)
        close_btn.clicked.connect(self.close)

        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

    def _populate_layers(self):
        self.layer_list.clear()
        for layer in self.temp_layers:
            item = QListWidgetItem()
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)

            layer_type = "Vector" if layer.type() == QgsMapLayer.VectorLayer else "Raster"
            item.setText(f"{layer.name()}   [{layer_type}]")
            item.setData(Qt.UserRole, layer)

            if layer.type() == QgsMapLayer.VectorLayer:
                item.setForeground(QColor("#1a5276"))
            else:
                item.setForeground(QColor("#117a65"))

            self.layer_list.addItem(item)

    # ─────────────────────────────────────────────────── Helpers ──────────

    def _select_all(self):
        for i in range(self.layer_list.count()):
            self.layer_list.item(i).setCheckState(Qt.Checked)

    def _select_none(self):
        for i in range(self.layer_list.count()):
            self.layer_list.item(i).setCheckState(Qt.Unchecked)

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.folder_edit.setText(folder)

    def _checked_layers(self):
        layers = []
        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            if item.checkState() == Qt.Checked:
                layers.append(item.data(Qt.UserRole))
        return layers

    # ─────────────────────────────────────────────────── Save ─────────────

    def _save_layers(self):
        output_dir = self.folder_edit.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "No Folder Selected", "Please choose an output folder first.")
            return
        if not os.path.isdir(output_dir):
            QMessageBox.warning(self, "Invalid Folder", f"The folder does not exist:\n{output_dir}")
            return

        selected = self._checked_layers()
        if not selected:
            QMessageBox.warning(self, "Nothing Selected", "Please select at least one layer to save.")
            return

        self.save_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setMaximum(len(selected))
        self.progress.setValue(0)

        # Format mappings
        vec_map = {
            "GeoPackage (.gpkg)": ("GPKG", ".gpkg"),
            "Shapefile (.shp)":   ("ESRI Shapefile", ".shp"),
            "GeoJSON (.geojson)": ("GeoJSON", ".geojson"),
        }
        vec_driver, vec_ext = vec_map[self.vec_format.currentText()]

        saved, failed = [], []

        for idx, layer in enumerate(selected):
            self.status_label.setText(f"Saving: {layer.name()}…")
            self.progress.setValue(idx)
            # Force UI update
            from qgis.PyQt.QtWidgets import QApplication
            QApplication.processEvents()

            safe_name = self._safe_filename(layer.name())
            try:
                if layer.type() == QgsMapLayer.VectorLayer:
                    out_path = os.path.join(output_dir, safe_name + vec_ext)
                    self._save_vector(layer, out_path, vec_driver)
                else:
                    out_path = os.path.join(output_dir, safe_name + ".tif")
                    self._save_raster(layer, out_path)
                saved.append(layer.name())
            except Exception as e:
                failed.append(f"{layer.name()}: {e}")

        self.progress.setValue(len(selected))
        self.save_btn.setEnabled(True)

        # ── Result summary ──────────────────────────────────────────────
        msg = []
        if saved:
            msg.append(f"✅ Successfully saved {len(saved)} layer(s):\n  • " + "\n  • ".join(saved))
        if failed:
            msg.append(f"❌ Failed ({len(failed)}):\n  • " + "\n  • ".join(failed))

        result_text = "\n\n".join(msg)
        self.status_label.setText(result_text)

        if saved:
            reply = QMessageBox.question(
                self,
                "Save Complete",
                f"{result_text}\n\nWould you like to open the output folder?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                import subprocess, sys
                if sys.platform.startswith("win"):
                    os.startfile(output_dir)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", output_dir])
                else:
                    subprocess.Popen(["xdg-open", output_dir])

    def _save_vector(self, layer, out_path, driver):
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = driver
        options.fileEncoding = "UTF-8"

        transform_context = QgsProject.instance().transformContext()
        error, msg, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
            layer, out_path, transform_context, options
        )
        if error != QgsVectorFileWriter.NoError:
            raise RuntimeError(msg)

    def _save_raster(self, layer, out_path):
        provider = layer.dataProvider()
        pipe = QgsRasterPipe()
        if not pipe.set(provider.clone()):
            raise RuntimeError("Failed to create raster pipe.")

        writer = QgsRasterFileWriter(out_path)
        writer.setOutputFormat("GTiff")
        error = writer.writeRaster(
            pipe,
            provider.xSize(),
            provider.ySize(),
            provider.extent(),
            provider.crs()
        )
        if error != QgsRasterFileWriter.NoError:
            raise RuntimeError(f"Raster write error code: {error}")

    @staticmethod
    def _safe_filename(name):
        """Convert layer name to a safe filename."""
        import re
        safe = re.sub(r'[\\/*?:"<>|]', "_", name)
        safe = safe.strip(". ")
        return safe or "layer"
