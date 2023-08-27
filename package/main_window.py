import os.path
import shutil

import webbrowser

import pandas as pd

from PyQt5 import QtWidgets, QtCore, QtGui

import package.app_base as ab
import package.AnalyseBRT as brt


class Worker(QtCore.QObject):
    QtCore.Signal = QtCore.pyqtSignal
    image_converted = QtCore.Signal(object, bool)
    finished = QtCore.Signal()

    def __init__(self, path_to_scan, path_to_drop, save_n_cycles, save_path):
        super().__init__()

        self.path_to_scan=path_to_scan
        self.path_to_drop=path_to_drop, 
        self.save_n_cycles=save_n_cycles
        self.save_path = save_path
        self.runs = True
        
        self.trials = list() # Liste qui va recenser tous les essais (=nom de répertoires contenant des .TXT)

    def convert_images(self):
        for image_lw_item in self.path_to_scan:
            if self.runs and not image_lw_item.processed:
                success, self.trials = brt.scan_and_calculate(path_to_scan=image_lw_item.text(), 
                                         trials=self.trials, 
                                         file_caract = self.file_caract,
                                         mgx_to_save=self.mgx_to_save, 
                                         save_n_cycles=self.save_n_cycles,
                                         save_path= self.save_path)

                self.image_converted.emit(image_lw_item, success)

        # Mise en commun de tous les fichier Excel par essais
        df_alldata = pd.DataFrame()
        df_caract = pd.DataFrame()
        df_par_essai = pd.DataFrame()
        
        for trial in self.trials:
            df_temp = pd.read_excel(os.path.join(self.save_path, trial, "data_vb.xlsx"))
            df_alldata = df_alldata.append(df_temp)

            df_temp = pd.read_excel(os.path.join(self.save_path, trial, "data_caract.xlsx"))
            df_caract = df_caract.append(df_temp)

            df_temp = pd.read_excel(os.path.join(self.save_path, trial, "data_trial.xlsx"))
            df_par_essai = df_par_essai.append(df_temp)
            
        brt.save_to_json(df_caract, os.path.join(self.save_path, "vgData_Trials.js"), "data_caract", "w")
        brt.save_to_json(df_par_essai, os.path.join(self.save_path, "vgData_Trials.js"), "data_par_essai", "a")
        brt.save_to_json(df_alldata, os.path.join(self.save_path, "vgData_VB.js"), "data_VB", "w")

        features = {"Essais": self.trials}
        brt.save_features(features, os.path.join(self.save_path, "vgData_CNST.js"), "f_trials", write_mode="w")
        
        self.finished.emit()
        print("Terminé")


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.rootDir = ""

        self.setup_ui()
        self.setWindowTitle(ab.APP_NAME)
        self.setWindowIcon(QtGui.QIcon(ab.APP_ICON))
        self.showNormal()

    def setup_ui(self):
        self.create_widgets()
        self.modify_widgets()
        self.create_layouts()
        self.add_widgets_to_layouts()
        self.setup_connections()


    def create_widgets(self):
        self.lbl_library = QtWidgets.QLabel("Bibliothèque:")
        self.le_library = QtWidgets.QLineEdit()

        self.lbl_outdir = QtWidgets.QLabel("Dossier de sortie:")
        self.le_outdir = QtWidgets.QLineEdit()

        self.lw_files = QtWidgets.QListWidget()

        self.btn_books = QtWidgets.QPushButton("Livres")
        self.btn_travels = QtWidgets.QPushButton("Voyages")
        self.lbl_dropInfo = QtWidgets.QLabel("^ Déplacer les dossiers sur l'interface")

    def modify_widgets(self):
        style = ab.apply_style()
        self.setStyleSheet(style)

        # Divers
        self.le_library.setText(ab.defaultLibrary)
        self.lbl_dropInfo.setVisible(False)

        self.setAcceptDrops(True)
        self.lw_files.setAlternatingRowColors(True)
        self.lw_files.setSelectionMode(QtWidgets.QListWidget.ExtendedSelection)

    def create_layouts(self):
        self.main_layout = QtWidgets.QGridLayout(self)

    def add_widgets_to_layouts(self):
        self.main_layout.addWidget(self.lbl_library, 1, 0, 1, 1)
        self.main_layout.addWidget(self.le_library, 1, 1, 1, 1)

        self.main_layout.addWidget(self.lbl_outdir, 2, 0, 1, 1)
        self.main_layout.addWidget(self.le_outdir, 2, 1, 1, 1)
        
        self.main_layout.addWidget(self.lw_files, 3, 0, 1, 2)
        self.main_layout.addWidget(self.lbl_dropInfo, 4, 0, 1, 2)
        self.main_layout.addWidget(self.btn_books, 5, 0, 1, 1)
        self.main_layout.addWidget(self.btn_travels, 5, 1, 1, 1)

    def setup_connections(self):
        QtWidgets.QShortcut(QtGui.QKeySequence("Backspace"), self.lw_files, self.delete_selected_items)
        QtWidgets.QShortcut(QtGui.QKeySequence("F"), self, self.change_window_state)

        self.btn_books.clicked.connect(self.convert_images)
        self.btn_travels.clicked.connect(self.display_graphs)

    def change_window_state(self):
        self.window_maximized = not self.window_maximized

        if self.window_maximized:
            self.showFullScreen()
        else:
            self.showMaximized()

    def convert_images(self):
        # Création du répertoire de sortie
        cwd = os.getcwd()
        
        save_path = os.path.join(cwd, self.le_outdir.text())
        template_path = os.path.join(cwd, ab.template)
        
        if not os.path.isdir(save_path):
            shutil.copytree(template_path, save_path)

        mgx_to_save = list()
        if self.cb_MGI.isChecked():
            mgx_to_save.append("MGI")
        if self.cb_MGM.isChecked():
            mgx_to_save.append("MGM")
        if self.cb_MGS.isChecked():
            mgx_to_save.append("MGS")
        if self.cb_M05.isChecked():
            mgx_to_save.append("M05")

        if self.le_library.text():
            save_n_cycles = int(self.le_library.text())
        else:
            save_n_cycles = 1

        self.btn_books.setEnabled(False)
        self.btn_travels.setEnabled(False)
        
        lw_items = [self.lw_files.item(index) for index in range(self.lw_files.count())]

        images_a_convertir = [1 for lw_item in lw_items if not lw_item.processed]
        if not images_a_convertir:
            msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
                                            "Pas de répertoire à scanner",
                                            "Tous les répertoires ont été scannés.")
            msg_box.exec_()
            return False

        self.thread = QtCore.QThread(self)

        self.worker = Worker(lw_items, list(), save_n_cycles, save_path)

        self.worker.moveToThread(self.thread)
        self.worker.image_converted.connect(self.image_converted)
        self.thread.started.connect(self.worker.convert_images)
        self.worker.finished.connect(self.all_finished)
        self.thread.start()

    def abort(self):
        self.worker.runs = False
        self.thread.quit()

    def all_finished(self):
        self.btn_scan.setEnabled(True)
        self.btn_display.setEnabled(True)
        self.thread.quit()
        
    def image_converted(self, lw_items, success):
        if success:
            lw_items.setIcon(QtGui.QIcon("assets/checked.png"))
            lw_items.processed = True

    def display_graphs(self):
        url = "file:///" + os.path.join(os.getcwd(), self.le_outdir.text()) + "/Barillets.html"
        webbrowser.open_new_tab(url)

    def delete_selected_items(self):
        for lw_item in self.lw_files.selectedItems():
            row = self.lw_files.row(lw_item)
            self.lw_files.takeItem(row)

    def dragEnterEvent(self, event):
        self.lbl_dropInfo.setVisible(True)
        event.accept()

    def dragLeaveEvent(self, event):
        self.lbl_dropInfo.setVisible(False)

    def dropEvent(self, event):
        event.accept()

        for url in event.mimeData().urls():
            if os.path.isdir(url.toLocalFile()):
                self.add_file(path=url.toLocalFile())
            elif os.path.splitext(url.toLocalFile())[1] == ".xlsx":
                self.le_caract.setText(url.toLocalFile())

        self.lbl_dropInfo.setVisible(False)

    def add_file(self, path):
        items = [self.lw_files.item(index).text() for index in range(self.lw_files.count())]

        if path not in items:
            lw_item = QtWidgets.QListWidgetItem(path)
            lw_item.setIcon(QtGui.QIcon("assets/unchecked.png"))
            lw_item.processed = False
            self.lw_files.addItem(lw_item)


 









