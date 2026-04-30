def classFactory(iface):
    from .save_temp_layers import SaveTempLayersPlugin
    return SaveTempLayersPlugin(iface)
