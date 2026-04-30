import os
import tempfile
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProject, QgsMapLayer

from .save_dialog import SaveTempLayersDialog


class SaveTempLayersPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

        self.action = QAction(icon, "Save Temporary Layers", self.iface.mainWindow())
        self.action.setToolTip("Save all temporary layers to disk")
        self.action.triggered.connect(self.run)

        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Save Temp Layers", self.action)

    def unload(self):
        self.iface.removePluginMenu("&Save Temp Layers", self.action)
        self.iface.removeToolBarIcon(self.action)
        del self.action

    def run(self):
        temp_layers = self._get_temp_layers()

        if not temp_layers:
            QMessageBox.information(
                self.iface.mainWindow(),
                "Save Temporary Layers",
                "No temporary layers found in the current project.\n\n"
                "Temporary layers are those stored in memory (not yet saved to disk)."
            )
            return

        dlg = SaveTempLayersDialog(self.iface.mainWindow(), temp_layers)
        dlg.exec_()

    def _get_temp_layers(self):
        """Return a list of all temporary/memory layers in the current project."""
        temp_layers = []
        for layer in QgsProject.instance().mapLayers().values():
            if self._is_temp_layer(layer):
                temp_layers.append(layer)
        return temp_layers

    def _is_temp_layer(self, layer):
        """Check if a layer is temporary (in-memory or stored in system temp folder)."""
        provider = layer.dataProvider()
        if provider is None:
            return False

        provider_name = provider.name().lower()

        # Vector layers
        if layer.type() == QgsMapLayer.VectorLayer:
            return provider_name == "memory"

        # Raster layers
        if layer.type() == QgsMapLayer.RasterLayer:
            if provider_name == "memory":
                return True

            if provider_name == "gdal":
                source = layer.source().split("|")[0].strip()

                # 1. File doesn't exist on disk
                if not os.path.exists(source):
                    return True

                # 2. File lives inside the system temp directory
                sys_temp = os.path.normcase(os.path.normpath(tempfile.gettempdir()))
                source_norm = os.path.normcase(os.path.normpath(source))
                if source_norm.startswith(sys_temp):
                    return True

                # 3. Common QGIS temp path keywords
                for keyword in ["processing", "qgis_tmp", "qgistmp"]:
                    if keyword in source_norm:
                        return True

            return False

        return False
