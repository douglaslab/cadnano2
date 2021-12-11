import json
from .legacydecoder import import_legacy_dict
from cadnano2.ui.dialogs.ui_latticetype import Ui_LatticeType
import cadnano2.util as util
import cadnano2.cadnano as cadnano
if cadnano.app().isGui():  # headless:
    from cadnano2.ui.dialogs.ui_latticetype import Ui_LatticeType
    util.qtWrapImport('QtWidgets', globals(),  ['QDialog', 'QDialogButtonBox'])


def decode(document, string):
    if cadnano.app().isGui():
        # from ui.dialogs.ui_latticetype import Ui_LatticeType
        # util.qtWrapImport('QtGui', globals(),  ['QDialog', 'QDialogButtonBox'])
        dialog = QDialog()
        dialogLT = Ui_LatticeType()  # reusing this dialog, should rename
        dialogLT.setupUi(dialog)

    # try:  # try to do it fast
    #     try:
    #         import cjson
    #         packageObject = cjson.decode(string)
    #     except:  # fall back to if cjson not available or on decode error
    #         packageObject = json.loads(string)
    # except ValueError:
    #     dialogLT.label.setText("Error decoding JSON object.")
    #     dialogLT.buttonBox.setStandardButtons(QDialogButtonBox.Ok)
    #     dialog.exec()
    #     return
    packageObject = json.loads(string)

    if packageObject.get('.format', None) != 'caDNAno2':
        import_legacy_dict(document, packageObject)