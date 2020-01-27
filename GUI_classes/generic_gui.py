from PyQt5.QtWidgets import QPushButton, QLabel, QComboBox, QGridLayout, QGroupBox, \
    QLineEdit, QPlainTextEdit, QWidget, QCheckBox, QMessageBox
from PyQt5.QtCore import QCoreApplication, QRect, Qt
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from imageio import mimsave, imread
import os
from shutil import rmtree

from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure

from sklearn.datasets.samples_generator import make_blobs

from GUI_classes.utils_gui import LabeledSlider


# todo: PARAMETERS REGULARIZATION mettere a posto

class StartingGui(QWidget):
    def __init__(self, name, twinx, second_plot, function, extract=False):
        super().__init__()

        self.name = name
        self.twinx = twinx
        self.second_plot = second_plot
        self.function = function

        self.setWindowTitle(self.name)
        self.setGeometry(100, 100, 1290, 850)

        # upper plot
        self.canvas_up = FigureCanvas(Figure(figsize=(12, 5)))
        self.ax1 = self.canvas_up.figure.subplots()
        self.ax1.set_xticks([], [])
        self.ax1.set_yticks([], [])
        self.ax1.set_title(self.name + " procedure")
        if self.twinx is True:
            self.ax1_t = self.ax1.twinx()
            self.ax1_t.set_xticks([], [])
            self.ax1_t.set_yticks([], [])

        # lower plot
        if self.second_plot is True:
            self.canvas_down = FigureCanvas(Figure(figsize=(12, 5)))
            self.ax = self.canvas_down.figure.subplots()
            self.ax.set_xticks([], [])
            self.ax.set_yticks([], [])
            self.ax.set_title(self.name + " Reachability Plot")
            self.ax.set_ylabel("reachability distance")
            if self.twinx is True:
                self.ax_t = self.ax.twinx()
                self.ax_t.set_xticks([], [])
                self.ax_t.set_yticks([], [])

        # parameters initialization
        self.parameter_initialization()

        # this is used to account for previously created folders in Images to set the self.ind_run correctly
        fold_dir = "./Images/"
        folders = [el for el in os.listdir(fold_dir) if el.startswith(self.name)]
        folders.sort()
        if len(folders) == 0:
            self.ind_run = 0
        else:
            self.ind_run = int(folders[-1][(len(self.name)+1):]) + 1

        # grid where the two pictures, the log and the button box are inserted (row,column)
        self.gridlayout = QGridLayout(self)
        self.gridlayout.addWidget(self.canvas_up, 0, 1)
        if self.second_plot is True:
            self.gridlayout.addWidget(self.canvas_down, 1, 1)

        # START BUTTON
        self.button_run = QPushButton("START", self)
        self.button_run.clicked.connect(self.function)
        self.button_run.setToolTip("Perform clustering.")

        # SLIDER
        self.label_slider = QLabel(self)
        self.label_slider.setText("delay:")
        self.label_slider.setToolTip("Delay each step of the algorithm for the desidered number of seconds.")

        self.slider = LabeledSlider(minimum=0, maximum=3, interval=1, single_step=0.5)
        self.slider.sl.valueChanged.connect(self.changedValue)
        self.slider.setFixedHeight(50)

        # EXTRACT BUTTON
        if extract is True:
            self.button_extract = QPushButton("EXTRACT", self)
            self.button_extract.clicked.connect(lambda: self.start_EXTRACT_OPTICS())
            self.button_extract.setEnabled(False)
            self.button_extract.setToolTip("Extract clusters from OPTICS reachability plot in a"
                                           " DBSCAN way using eps_extr.")

        # CHECKBOX for saving images
        self.checkbox_saveimg = QCheckBox("save plots")
        self.checkbox_saveimg.setToolTip("Check it to save all the plots generated by the algorithm. They are"
                                         " saved in the Images folder.")
        self.checkbox_saveimg.stateChanged.connect(self.checkBoxChangedAction)

        # CHECKBOX for generating GIF
        self.checkbox_gif = QCheckBox("make GIF")
        self.checkbox_gif.setToolTip("Check it to build a GIF from the plots generated by the algorithm. GIF are not"
                                     " produced when new Extractions are performed, \nthey are only produced when the"
                                     " main clustering procedure is executed. The GIF is saved in the same folder of"
                                     " the plots it is composed of.")
        self.checkbox_gif.stateChanged.connect(self.GIFChangedAction)
        self.checkbox_gif.setEnabled(False)

        # BUTTON for removing generated pics and gifs
        self.button_delete_pics = QPushButton("DELETE PICs && GIFs", self)
        self.button_delete_pics.clicked.connect(self.delete_pics)
        self.button_delete_pics.setEnabled(True)
        self.button_delete_pics.setToolTip("Delete all pictures and GIFs generated until now in the folder Images."
                                           " To avoid deleting specific files, just move them out of the folder"
                                           " Images.")

        # n_points LABEL
        self.label_np = QLabel(self)
        self.label_np.setText("n_points:")
        self.label_np.setToolTip("Number of points of the dataset. It can lie between 5 and 200.")

        self.line_edit_np = QLineEdit(self)
        self.line_edit_np.setText(str(self.n_points))

        self.n_points_validator = QIntValidator(5, 200, self)
        self.line_edit_np.setValidator(self.n_points_validator)

        # dataset LABEL
        self.label_ds = QLabel(self)
        self.label_ds.setText("dataset:")
        self.label_ds.setToolTip("Choose among four sklearn generated datasets to perform clustering.")

        # COMBOBOX of datasets
        self.combobox = QComboBox(self)
        self.combobox.addItem("blobs")
        self.combobox.addItem("moons")
        self.combobox.addItem("scatter")
        self.combobox.addItem("circle")

        # labels initialization
        self.label_initialization()

        # LOG
        self.log_initialization()

        # buttons in GROUPBOX (upper left corner)
        self.buttons_groupbox_initialization()

        self.show()

    def parameter_initialization(self):

        self.n_points = 50
        self.X = make_blobs(n_samples=self.n_points, centers=4, n_features=2, cluster_std=1.8, random_state=42)[0]
        self.delay = 0
        self.ind_extr_fig = 0
        self.param_check = True
        self.save_plots = False
        self.first_run_occurred = False
        self.make_gif = False

        if (self.name == "OPTICS") or (self.name == "DBSCAN"):
            self.eps = 2
            self.mp = 3
            self.eps_extr = 1
            self.ClustDist = {}
            self.ClustDict = {}
            self.CoreDist = {}

        elif self.name == "AGGLOMERATIVE":
            self.n_clust = 1
            self.linkage = "single"

    def label_initialization(self):

        if (self.name == "OPTICS") or (self.name == "DBSCAN"):

            # eps LABEL
            self.label_eps = QLabel(self)
            self.label_eps.setText("eps (\u03B5):")
            self.label_eps.setToolTip(
                "The maximum distance between two samples for one to be considered as in the neighborhood"
                " of the other.")

            self.line_edit_eps = QLineEdit(self)
            self.line_edit_eps.setText(str(self.eps))

            self.eps_validator = QDoubleValidator(0, 1000, 4, self)
            self.line_edit_eps.setValidator(self.eps_validator)

            # minPTS LABEL
            self.label_mp = QLabel(self)
            self.label_mp.setText("minPTS:")
            self.label_mp.setToolTip("The number of samples in a neighborhood for a point to "
                                     "be considered as a core point.")

            self.line_edit_mp = QLineEdit(self)
            self.line_edit_mp.setText(str(self.mp))

            self.mp_validator = QIntValidator(1, 200, self)
            self.line_edit_mp.setValidator(self.mp_validator)

            # eps_extr LABEL
            if self.name == "OPTICS":
                self.label_eps_extr = QLabel(self)
                self.label_eps_extr.setText("eps_extr (\u03B5\'):")
                self.label_eps_extr.setToolTip(
                    "The eps parameter to use to extract clusters from the reachability plot in a DBSCAN way.")

                self.line_edit_eps_extr = QLineEdit(self)
                self.line_edit_eps_extr.setText(str(self.eps_extr))

                self.eps_extr_validator = QDoubleValidator(0, 1000, 4, self)
                self.line_edit_eps_extr.setValidator(self.eps_extr_validator)

        elif self.name == "AGGLOMERATIVE":

            # n_clust LABEL
            self.label_n_clust = QLabel(self)
            self.label_n_clust.setText("n_clust:")
            self.label_n_clust.setToolTip("The desired number of clusters to partition the dataset into.")

            self.line_edit_n_clust = QLineEdit(self)
            self.line_edit_n_clust.setText(str(self.n_clust))

            self.n_clust_validator = QIntValidator(1, 1000, self)
            self.line_edit_n_clust.setValidator(self.n_clust_validator)

            # linkage method LABEL
            self.label_linkage = QLabel(self)
            self.label_linkage.setText("linkage:")
            self.label_linkage.setToolTip("Choose among four linkage methods to perform hierarchical "
                                     "agglomerative clustering.")

            # COMBOBOX of linkage methods
            self.combobox_linkage = QComboBox(self)
            self.combobox_linkage.addItem("single")
            self.combobox_linkage.addItem("complete")
            self.combobox_linkage.addItem("average")
            self.combobox_linkage.addItem("ward")

    def log_initialization(self):
        if self.name == "OPTICS":
            self.log = QPlainTextEdit("SEED QUEUE")
            self.log.setStyleSheet(
                """QPlainTextEdit {background-color: #FFF;
                                   color: #000000;
                                   font-family: Courier;}""")

            self.gridlayout.addWidget(self.log, 1, 0)

        elif (self.name == "DBSCAN") or (self.name == "AGGLOMERATIVE"):
            self.log = QPlainTextEdit("{} LOG".format(self.name))
            self.log.setGeometry(900, 60, 350, 400)
            self.log.setStyleSheet(
                """QPlainTextEdit {background-color: #FFF;
                                   color: #000000;
                                   font-family: Courier;}""")
            self.log.setFixedHeight(335)
            self.gridlayout.addWidget(self.log, 1, 1)

    def buttons_groupbox_initialization(self):

        self.groupbox_buttons = QGroupBox("Parameters")
        self.groupbox_buttons.setFixedSize(220, 400)

        self.gridlayout.addWidget(self.groupbox_buttons, 0, 0)

        self.gridlayout_but = QGridLayout(self.groupbox_buttons)

        if (self.name == "OPTICS") or (self.name == "DBSCAN"):

            self.gridlayout_but.addWidget(self.label_ds, 0, 0)
            self.gridlayout_but.addWidget(self.combobox, 0, 1)

            self.gridlayout_but.addWidget(self.label_np, 1, 0)
            self.gridlayout_but.addWidget(self.line_edit_np, 1, 1)
            self.gridlayout_but.addWidget(self.label_eps, 2, 0)
            self.gridlayout_but.addWidget(self.line_edit_eps, 2, 1)
            self.gridlayout_but.addWidget(self.label_mp, 3, 0)
            self.gridlayout_but.addWidget(self.line_edit_mp, 3, 1)

            if self.name == "OPTICS":
                self.gridlayout_but.addWidget(self.label_eps_extr, 4, 0)
                self.gridlayout_but.addWidget(self.line_edit_eps_extr, 4, 1)
                self.gridlayout_but.addWidget(self.button_extract, 5, 1)

            self.gridlayout_but.addWidget(self.button_run, 5, 0)

            self.gridlayout_but.addWidget(self.label_slider, 6, 0)
            self.gridlayout_but.addWidget(self.slider, 6, 1)
            self.gridlayout_but.addWidget(self.checkbox_saveimg, 7, 0)
            self.gridlayout_but.addWidget(self.checkbox_gif, 7, 1)
            self.gridlayout_but.addWidget(self.button_delete_pics, 8, 0, 1, 0)

        elif self.name == "AGGLOMERATIVE":
            self.gridlayout_but.addWidget(self.label_ds, 0, 0)
            self.gridlayout_but.addWidget(self.combobox, 0, 1)
            self.gridlayout_but.addWidget(self.label_np, 1, 0)
            self.gridlayout_but.addWidget(self.line_edit_np, 1, 1)
            self.gridlayout_but.addWidget(self.label_n_clust, 2, 0)
            self.gridlayout_but.addWidget(self.line_edit_n_clust, 2, 1)
            self.gridlayout_but.addWidget(self.label_linkage, 3, 0)
            self.gridlayout_but.addWidget(self.combobox_linkage, 3, 1)

            self.gridlayout_but.addWidget(self.button_run, 4, 0)

            self.gridlayout_but.addWidget(self.label_slider, 5, 0)
            self.gridlayout_but.addWidget(self.slider, 5, 1)
            self.gridlayout_but.addWidget(self.checkbox_saveimg, 6, 0)
            self.gridlayout_but.addWidget(self.checkbox_gif, 6, 1)
            self.gridlayout_but.addWidget(self.button_delete_pics, 7, 0, 1, 0)

    def checkBoxChangedAction(self, state):
        if (Qt.Checked == state):
            self.save_plots = True
            self.checkbox_gif.setEnabled(True)

            try:
                os.mkdir('./Images/{}_{:02}'.format(self.name, self.ind_run))
                print("new folder")

            except OSError as error:
                print(error)
        else:
            self.checkbox_gif.setEnabled(False)
            self.save_plots = False

    def delete_pics(self):

        msg = "Do you really want to delete all PICs and GIFs generated by {} until now?".format(self.name)
        messagebox_reply = QMessageBox.question(self, 'Images removal', msg,
                                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if messagebox_reply == QMessageBox.Yes:

            folders = [fold for fold in os.listdir('./Images/') if fold.startswith('{}'.format(self.name))]
            for folder in folders:
                rmtree('./Images/' + folder)
            self.ind_run = 0
            self.first_run_occurred = False

        elif messagebox_reply == QMessageBox.No:
            return

    def GIFChangedAction(self, state):
        if (Qt.Checked == state):
            self.make_gif = True
        else:
            self.make_gif = False

    def generate_GIF(self):

        png_dir = './Images/{}_{:02}'.format(self.name, self.ind_run)
        images = []
        fig_list = [pic for pic in os.listdir(png_dir) if (pic.startswith('fig')) & ('fin' not in pic)]
        fig_list.sort()
        fin_list = [pic for pic in os.listdir(png_dir) if 'fig_fin' in pic]
        fin_list.sort()
        list_for_gif = fig_list + [fin_list[-1]]

        for file_name in list_for_gif:
            file_path = os.path.join(png_dir, file_name)
            images.append(imread(file_path))

        if int(self.line_edit_np.text()) < 50:
            duration = 0.35
        else:
            duration = 0.25
        mimsave(png_dir + '/movie.gif', images, duration=duration)

    def changedValue(self):
        size = self.slider.sl.value()
        self.delay = size

    def show_error_message(self, check, msg):
        if check[0] != 2:

            if self.param_check is True:
                self.log.clear()

            self.param_check = False
            self.log.appendPlainText("ERROR")
            self.log.appendPlainText("")
            self.log.appendPlainText(msg)
            self.log.appendPlainText("")

    def verify_input_parameters(self, extract=False):

        self.param_check = True
        check_n_points = self.n_points_validator.validate(self.line_edit_np.text(), 0)
        self.show_error_message(check_n_points,
                                "The parameter n_points must be an integer and lie between {0}"
                                " and {1}.".format(5, 200))

        if (self.name == "OPTICS") or (self.name == "DBSCAN"):

            if extract is False:

                check_eps = self.eps_validator.validate(self.line_edit_eps.text(), 0)
                check_mp = self.mp_validator.validate(self.line_edit_mp.text(), 0)

                self.show_error_message(check_eps,
                                        "The parameter eps must lie between {0} and {1}, and can have a maximum of"
                                        " {2} decimal places.".format(0, 1000, 4))
                self.show_error_message(check_mp,
                                        "The parameter minPTS must be an integer and lie "
                                        "between {0} and {1}.".format(1, 200))
            if self.name == "OPTICS":

                check_eps_extr = self.eps_extr_validator.validate(self.line_edit_eps_extr.text(), 0)

                self.show_error_message(check_eps_extr,
                                        "The parameter eps_extr must lie between {0} and {1}, and can "
                                        "have a maximum of {2} decimal places.".format(0, 1000, 4))

        elif self.name == "AGGLOMERATIVE":

            check_n_clust = self.n_clust_validator.validate(self.line_edit_n_clust.text(), 0)

            self.show_error_message(check_n_clust,
                                    "The parameter n_clust must be an integer and lie between "
                                    "{0} and {1}".format(1, 1000))
