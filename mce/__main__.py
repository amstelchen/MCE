# File: main.py
import sys
import os
# import xdg
import subprocess
import logging
import contextlib
import vdf

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QMessageBox, QLineEdit, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog
# from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import QFile, QIODevice, QCoreApplication, Qt
from PySide6.QtGui import QIcon, QScreen
# from PySide6.QtGui import QImage, QPixmap, QPainter

try:
    from .__init__ import resolutions
except ImportError:
    from __init__ import resolutions

PROG = "Metro 2033 Config Editor"
VERSION = "0.2.0"
AUTHOR = "Copyright (C) 2023, by Michael John"
DESC = "TBD"
GithubLink = "https://github.com/amstelchen/MCE"

Vlang = ["us", "ru", "de", "es", "fr", "it"]
Tlang = Vlang + ["nl", "po", "cz"]

sheet = """
QGroupBox {
    border: 1px solid gray;
    border-radius: 5px;
    margin-top: 1ex; /* leave space at the top for the title */
}

QGroupBox::title {
    margin-left: 0px;
    subcontrol-origin: margin;
    subcontrol-position: top left; /* position at the top center */
    padding: 0 3px;
}"""

STEAM_PATH_DOT = "~/.steam/"
STEAM_PATH_LOCAL = "~/.local/share/Steam/steam"
STEAM_PATH_SNAP = "~/snap/steam/common/.steam/"

def GetSteamPath() -> str:
    logging.debug(f"Checking for {STEAM_PATH_DOT}...")
    if os.path.exists(os.path.expanduser(STEAM_PATH_DOT)):
        return STEAM_PATH_DOT
    logging.debug(f"Checking for {STEAM_PATH_LOCAL}...")
    if os.path.exists(os.path.expanduser(STEAM_PATH_LOCAL)):
        return STEAM_PATH_LOCAL
    logging.debug(f"Checking for {STEAM_PATH_SNAP}...")
    if os.path.exists(os.path.expanduser(STEAM_PATH_SNAP)):
        return STEAM_PATH_SNAP
    raise Exception("Steam installation not found, exiting.")


def GetSteamUserId() -> int:
    loginusersPath = os.path.expanduser(os.path.join(GetSteamPath(), 'steam/config/loginusers.vdf'))
    try:
        d = vdf.parse(open(loginusersPath))
        for user in d['users']:
            return int(user)
    except FileNotFoundError:
        return None


def GetGameFolder(SteamGameId: int) -> str:
    # libraryfoldersPath = os.path.expanduser('~/.steam/steam/config/libraryfolders.vdf')
    libraryfoldersPath = os.path.expanduser(os.path.join(GetSteamPath(), "steam/config/libraryfolders.vdf"))
    try:
        d = vdf.parse(open(libraryfoldersPath))
        for folder in d['libraryfolders']:
            # workaround for Steam on Debian default installations
            if folder == "contentstatsid":
                continue
            dictApps = d['libraryfolders'][folder]['apps']
            if str(SteamGameId) in dictApps.keys():
                GamePath = d['libraryfolders'][folder]['path']
                logging.debug(f"Found game in {GamePath}.")
                return GamePath
        else:
            raise Exception("Game not found")
    except FileNotFoundError:
        raise Exception("Steam library folder not found")
    return


def ReadConfigFile(ConfigPath: str, window):
    config_lines = {}
    if os.path.exists(ConfigPath):
        with open(os.path.join(ConfigPath, "user.cfg"), "r") as config_file:
            # lines = [line.strip() for line in config_file.readlines()]
            for line in config_file.readlines():
                try:
                    key, value = line.strip().split(' ')
                    config_lines[key] = value
                except ValueError:
                    key = line.strip()
                    config_lines[key] = ""

            for config_key, config_value in config_lines.items():
                logging.debug(config_key)
                if config_value == "on" or config_value == "1":
                    pass

                # logging.debug(vars(window))
                widgets = vars(window)
                for each_key, value_of_key in widgets.items():
                    # logging.debug(value_of_key.objectName())
                    # if (value_of_key.__class__.__name__ == 'QPushButton' or value_of_key.__class__.__name__ == 'QLabel'):
                    if value_of_key.__class__.__name__ == 'QCheckBox' and value_of_key.objectName() == "checkBox_" + config_key:
                        widget = window.findChild(QCheckBox, value_of_key.objectName())
                        if config_value == "on" or config_value == "1":
                            widget.setCheckState(Qt.Checked)
                        else:
                            widget.setCheckState(Qt.Unchecked)
                    if value_of_key.__class__.__name__ == 'QLineEdit' and value_of_key.objectName() == "lineEdit_" + config_key:
                        widget = window.findChild(QLineEdit, value_of_key.objectName())
                        widget.setText(config_value)
                    if value_of_key.__class__.__name__ == 'QComboBox' and value_of_key.objectName() == "comboBox_" + config_key:
                        widget = window.findChild(QComboBox, value_of_key.objectName())
                        if config_key == "g_game_difficulty" or config_key == "vibration" \
                                or config_key == "r_msaa_level" or config_key == "r_quality_level":
                            widget.setCurrentIndex(int(config_value))
                        else:
                            widget.setCurrentIndex(Tlang.index(config_value))
                    if value_of_key.__class__.__name__ == 'QDoubleSpinBox' and value_of_key.objectName() == "doubleSpinBox_" + config_key:
                        widget = window.findChild(QDoubleSpinBox, value_of_key.objectName())
                        widget.setValue(float(config_value))

        logging.debug(f"Finished. {len(config_lines)} configuration options read.")


def main():

    if len(sys.argv) > 1:
        loglevel = sys.argv[1]
    else:
        loglevel = "INFO"
    numeric_level = getattr(logging, loglevel.upper(), logging.INFO)
    # logging.debug(loglevel, numeric_level)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(format='%(levelname)s:%(message)s', level=numeric_level)

    SteamRunGameId = "steam://rungameid/286690"
    if sys.platform == "win32":
        SteamPath = r"c:\program files (x86)\steam"
        SteamBinary = "Steam.exe"
        ConfigPath = r"C:\Program Files (x86)\Steam\steamapps\common/Metro 2033 Redux/"
        SavesPath = r"c:\users\michael\documents\4a games\metro 2033"
        ExecutablePath = os.path.join(ConfigPath, "metro.exe") or "Game not found"
    if sys.platform == "linux":
        SteamPath = GetSteamPath()
        if SteamPath is None:
            exit(1)
        SteamBinary = "steam"
        # ConfigPath = "/raid/SteamLibrary/steamapps/common/Metro 2033 Redux/"
        # ConfigPath = "/raid/SteamLibrary/steamapps/common/Metro Last Light Redux/"
        ConfigPath = os.path.join(GetGameFolder(286690), "steamapps/common/Metro 2033 Redux/")
        SavesPath = os.path.join(ConfigPath, format(GetSteamUserId(), "x"))
        ExecutablePath = os.path.join(ConfigPath, "metro") or "Game not found"

    def buttonBrowseSteam_clicked(s):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly)
        directory = dialog.getExistingDirectory(window, 'Choose Directory', window.Steaminstallpath.text())
        logging.debug(f"Selected directory: {directory}")
        window.Steaminstallpath.setText(os.path.join(directory, SteamBinary))

    def buttonBrowseConfig_clicked(s):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly)
        directory = dialog.getExistingDirectory(window, 'Choose Directory', window.Configfilepath.text())
        logging.debug(f"Selected directory: {directory}")
        window.Configfilepath.setText(directory)
        ReadConfigFile(directory, window)

    def buttonBrowseGame_clicked(s):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly)
        directory = dialog.getExistingDirectory(window, 'Choose Directory', os.path.curdir)
        logging.debug(f"Selected directory: {directory}")
        if len(directory) > 0:
            window.Gameexecutablepath.setText(directory)

    def buttonBrowseSaves_clicked(s):
        if os.path.exists(window.Savedgamespath.text()):
            if sys.platform == "linux":
                subprocess.run(["xdg-open", window.Savedgamespath.text()])
            if sys.platform == "win32":
                path = os.path.normpath(window.Savedgamespath.text())
                subprocess.run(["explorer", path])

    def buttonAbout_clicked(s):
        QMessageBox.about(window, PROG + " " + VERSION, PROG + "\n" + VERSION + "\n" + DESC + "\n" + AUTHOR)

    def buttonDonate_clicked(s):
        if sys.platform == "linux":
            subprocess.run(["xdg-open", GithubLink])

    def buttonReportABug_clicked(s):
        if sys.platform == "linux":
            logging.debug(f"Opening {GithubLink}")
            subprocess.run(["xdg-open", GithubLink + "/issues/new"])

    def buttonSteam_clicked(s):
        if sys.platform == "win32":
            subprocess.run([os.path.join(SteamPath, SteamBinary), SteamRunGameId])
        if sys.platform == "linux":
            subprocess.run([SteamBinary, SteamRunGameId])

    def buttonNonSteam_clicked(s):
        if sys.platform == "linux":
            result = subprocess.Popen(ExecutablePath, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logging.debug(result.stdout.read().decode("utf8"))
            logging.debug(result.stderr.read().decode("utf8"))

    def buttonBenchmark_clicked(s):
        pass

    def comboBoxResolution_changed(s):
        if s == 27:
            window.lineEdit_Width.setEnabled(True)
            window.lineEdit_Height.setEnabled(True)
        else:
            window.lineEdit_Width.setEnabled(False)
            window.lineEdit_Height.setEnabled(False)

    # os.environ["PYSIDE_DESIGNER_PLUGINS"]=os.path.dirname(__file__)
    os.environ["MESA_DEBUG"] = "silent"  # https://bugzilla.mozilla.org/show_bug.cgi?id=1744389
    # logging.debug(os.path.dirname(__file__))
    # app = QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    # app = QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, False)
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

    app = QApplication(sys.argv)
    app.setStyleSheet(sheet)

    ui_file_name = os.path.dirname(__file__) + "/MCE.ui"
    ui_file = QFile(ui_file_name)
    if not ui_file.open(QIODevice.ReadOnly):
        logging.error(f"Cannot open {ui_file_name}: {ui_file.errorString()}")
        sys.exit(-1)
    loader = QUiLoader()
    # loader.pluginPaths = [None]
    # loader.clearPluginPaths()
    with contextlib.redirect_stderr(open(os.devnull, 'w')):
        window = loader.load(ui_file)
        logging.debug("UI initialized.")
    ui_file.close()
    if not window:
        logging.error(loader.errorString())
        sys.exit(-1)

    center = QScreen.availableGeometry(QApplication.primaryScreen()).center()
    rect = QScreen.geometry(QApplication.primaryScreen())
    width, height = rect.width(), rect.height()

    geo = window.frameGeometry()
    geo.moveCenter(center)
    window.move(geo.topLeft())

    icon = QIcon(os.path.dirname(__file__) + "/mce.png")
    window.setWindowIcon(icon)
    window.setWindowTitle(PROG + " " + VERSION)
    window.show()

    window.Steaminstallpath.setText(os.path.join(SteamPath, SteamBinary))
    window.Configfilepath.setText(ConfigPath)
    window.Gameexecutablepath.setText(ExecutablePath)
    window.Savedgamespath.setText(SavesPath)

    ReadConfigFile(ConfigPath, window)

    for preset in range(1, 5):
        window.comboBoxPreset.addItem(f"Preset {preset}")
    for dx_version in range(9, 12):
        window.comboBoxDirectX.addItem(f"DirectX {dx_version}")
    for resolution in resolutions:
        window.comboBoxResolution.addItem(resolution)

    window.lineEdit_Width.setText(str(width))
    window.lineEdit_Height.setText(str(height))

    window.pushButtonBrowseSteam.clicked.connect(buttonBrowseSteam_clicked)
    window.pushButtonBrowseConfig.clicked.connect(buttonBrowseConfig_clicked)
    window.pushButtonBrowseGame.clicked.connect(buttonBrowseGame_clicked)
    window.pushButtonBrowseSaves.clicked.connect(buttonBrowseSaves_clicked)

    window.ButtonSteam.clicked.connect(buttonSteam_clicked)
    window.ButtonNonSteam.clicked.connect(buttonNonSteam_clicked)
    window.ButtonBenchmark.clicked.connect(buttonBenchmark_clicked)

    window.ButtonDonate.clicked.connect(buttonDonate_clicked)
    window.ButtonReportABug.clicked.connect(buttonReportABug_clicked)

    window.comboBoxResolution.currentIndexChanged.connect(comboBoxResolution_changed)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
