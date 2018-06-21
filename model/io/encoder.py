from json import dumps
from .legacyencoder import legacy_dict_from_doc


def encode(document, helixOrderList, io):
    obj = legacy_dict_from_doc(document, io.name, helixOrderList)
    json_string = dumps(obj, separators=(',',':'))  # compact encoding
    io.write(json_string)
