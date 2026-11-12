import atexit
import gc
import os
import sqlite3
import tempfile
import unittest

import numpy
from osgeo import gdal, osr
from qgis.core import (
    QgsApplication,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsRasterLayer,
    QgsVectorLayer,
)

from save_dialog import SaveTempLayersDialog

gdal.DontUseExceptions()


QgsApplication.setPrefixPath(os.environ["QGIS_PREFIX_PATH"], True)
QGIS_APP = QgsApplication([], False)
QGIS_APP.initQgis()
atexit.register(QGIS_APP.exitQgis)


class GeoPackageExportTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.gpkg_path = os.path.join(self.temp_dir.name, "layers.gpkg")
        self.layers = []

    def tearDown(self):
        self.layers.clear()
        gc.collect()
        self.temp_dir.cleanup()

    def _create_vector_layer(self, name):
        layer = QgsVectorLayer(
            "Point?crs=EPSG:4326&field=name:string",
            name,
            "memory",
        )
        self.assertTrue(layer.isValid())
        feature = QgsFeature(layer.fields())
        feature.setAttributes(["sample"])
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(1, 2)))
        self.assertTrue(layer.dataProvider().addFeatures([feature])[0])
        return layer

    def _create_raster_layer(self, name, data_type, values):
        source_path = os.path.join(self.temp_dir.name, f"{name}.tif")
        driver = gdal.GetDriverByName("GTiff")
        dataset = driver.Create(source_path, 2, 2, 1, data_type)
        dataset.SetGeoTransform((10, 0.5, 0, 20, 0, -0.5))
        spatial_ref = osr.SpatialReference()
        spatial_ref.ImportFromEPSG(4326)
        dataset.SetProjection(spatial_ref.ExportToWkt())
        dataset.GetRasterBand(1).WriteArray(values)
        dataset.FlushCache()
        dataset = None

        layer = QgsRasterLayer(source_path, name, "gdal")
        self.assertTrue(layer.isValid(), layer.error().summary())
        self.layers.append(layer)
        return layer

    def _save_vector(self, layer, table_name):
        SaveTempLayersDialog._save_vector(None, layer, self.gpkg_path, table_name)

    def _save_raster(self, layer, table_name):
        SaveTempLayersDialog._save_raster(None, layer, self.gpkg_path, table_name)

    def _contents(self):
        with sqlite3.connect(self.gpkg_path) as connection:
            return dict(connection.execute(
                "SELECT table_name, data_type FROM gpkg_contents"
            ))

    def _read_raster(self, table_name):
        dataset = gdal.OpenEx(
            self.gpkg_path,
            gdal.OF_RASTER,
            open_options=[f"TABLE={table_name}"],
        )
        self.assertIsNotNone(dataset, f"Could not open raster table {table_name}")
        values = dataset.GetRasterBand(1).ReadAsArray()
        data_type = dataset.GetRasterBand(1).DataType
        dataset = None
        return values, data_type

    def _assert_vector_table(self, table_name):
        with sqlite3.connect(self.gpkg_path) as connection:
            geometry_column = connection.execute(
                "SELECT column_name FROM gpkg_geometry_columns WHERE table_name = ?",
                (table_name,),
            ).fetchone()[0]
            row = connection.execute(
                f'SELECT name, "{geometry_column}" FROM "{table_name}"'
            ).fetchone()

        self.assertEqual(row[0], "sample")
        self.assertTrue(row[1].startswith(b"GP"))

    def test_vector_and_raster_tables_share_one_geopackage(self):
        vector = self._create_vector_layer("roads")
        raster = self._create_raster_layer(
            "elevation",
            gdal.GDT_Byte,
            numpy.array([[1, 2], [3, 4]], dtype="uint8"),
        )

        self._save_vector(vector, "roads")
        self._save_raster(raster, "elevation")

        self.assertEqual(self._contents(), {
            "roads": "features",
            "elevation": "tiles",
        })
        self._assert_vector_table("roads")
        values, _ = self._read_raster("elevation")
        self.assertEqual(values.tolist(), [[1, 2], [3, 4]])

    def test_float_raster_values_are_preserved(self):
        expected = numpy.array([[1.25, -2.5], [3.75, 4.5]], dtype="float32")
        raster = self._create_raster_layer("float", gdal.GDT_Float32, expected)

        self._save_raster(raster, "float_data")

        values, data_type = self._read_raster("float_data")
        self.assertEqual(data_type, gdal.GDT_Float32)
        numpy.testing.assert_allclose(values, expected)

    def test_uint16_raster_values_are_preserved(self):
        expected = numpy.array([[1, 2000], [30000, 65535]], dtype="uint16")
        raster = self._create_raster_layer("uint16", gdal.GDT_UInt16, expected)

        self._save_raster(raster, "uint16_data")

        values, data_type = self._read_raster("uint16_data")
        self.assertEqual(data_type, gdal.GDT_UInt16)
        numpy.testing.assert_array_equal(values, expected)

    def test_int16_raster_values_are_preserved(self):
        expected = numpy.array([[-32768, -1], [0, 32767]], dtype="int16")
        raster = self._create_raster_layer("int16", gdal.GDT_Int16, expected)

        self._save_raster(raster, "int16_data")

        values, data_type = self._read_raster("int16_data")
        self.assertEqual(data_type, gdal.GDT_Int16)
        numpy.testing.assert_array_equal(values, expected)

    def test_unsupported_float64_raster_is_reported_without_conversion(self):
        values = numpy.array([[1.125, -2.25], [3.5, 4.875]], dtype="float64")
        raster = self._create_raster_layer("float64", gdal.GDT_Float64, values)

        with self.assertRaisesRegex(RuntimeError, "only support Byte, Int16, UInt16, and Float32"):
            self._save_raster(raster, "float64_data")

        self.assertFalse(os.path.exists(self.gpkg_path))

    def test_raster_tables_can_be_appended_and_vector_added_after_raster(self):
        first = self._create_raster_layer(
            "first", gdal.GDT_Byte,
            numpy.array([[11, 12], [13, 14]], dtype="uint8"),
        )
        second = self._create_raster_layer(
            "second", gdal.GDT_Byte,
            numpy.array([[21, 22], [23, 24]], dtype="uint8"),
        )

        self._save_raster(first, "first_raster")
        self._save_raster(second, "second_raster")
        self._save_vector(self._create_vector_layer("points"), "points")

        self.assertEqual(self._contents(), {
            "first_raster": "tiles",
            "second_raster": "tiles",
            "points": "features",
        })
        self._assert_vector_table("points")
        first_values, _ = self._read_raster("first_raster")
        second_values, _ = self._read_raster("second_raster")
        self.assertEqual(first_values.tolist(), [[11, 12], [13, 14]])
        self.assertEqual(second_values.tolist(), [[21, 22], [23, 24]])

    def test_table_names_are_safe_and_unique(self):
        used_names = set()
        first_name = SaveTempLayersDialog._unique_layer_name(
            "roads / north", used_names
        )
        second_name = SaveTempLayersDialog._unique_layer_name(
            "roads / north", used_names
        )

        self.assertEqual(first_name, "roads_north")
        self.assertEqual(second_name, "roads_north_2")


if __name__ == "__main__":
    unittest.main()
