"""
gui for interaction with the database
based on pyqt6
"""
import sqlite3
import time

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QMovie
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
                             QComboBox, \
                             QCheckBox)

# Adjustable Variables
title = "GraphicArchive"  # changes window title
image = "graphicArchive_logo.png"  # changes banner image
left = 100  # sets offset from left screenborder
top = 100  # sets offset from top screenborder
w_width = 800  # sets window width
w_height = 600  # sets window height
icon = "graphicArchive_logo.ico"  # changes app icon
loading_gif = "loading.gif"  # loading animation


class LoadingScreen(QWidget):
    """
    Class for displaying a loading screen with a banner image and a rotating loading icon.

    Signals:
        loading_complete: Signal emitted when loading is complete.

    Methods:
        __init__(): Constructor to initialize the LoadingScreen widget with a banner image and loading icon.
        close_loading_screen(): Closes the loading screen and emits the loading_complete signal.
    """
    loading_complete = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.SplashScreen)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Banner Image
        self.logo_label = QLabel()
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        screen_width = screen_geometry.width()
        pixmap = QPixmap(image)
        scaled_pixmap = pixmap.scaledToWidth(screen_width // 4,
                                             Qt.TransformationMode.SmoothTransformation)  # Scale to a quarter of the
        # screen width
        self.logo_label.setPixmap(scaled_pixmap)
        layout.addWidget(self.logo_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Rotating Loading Icon
        self.loading_label = QLabel()
        self.loading_movie = QMovie(loading_gif)  # Use an animated gif for loading
        self.loading_label.setMovie(self.loading_movie)
        self.loading_movie.start()
        layout.addWidget(self.loading_label, alignment=Qt.AlignmentFlag.AlignCenter)

    def close_loading_screen(self):
        self.loading_complete.emit()
        self.close()


class WorkerThread(QThread):
    progress_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()

    def run(self):
        time.sleep(3)  # Simulate work being done (e.g., loading a database)
        self.progress_signal.emit(100)


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(title)
        self.setGeometry(left, top, w_width, w_height)
        self.setWindowIcon(QIcon(icon))

        self.cam_selection = QCheckBox("Kameras")
        self.lens_selection = QCheckBox("Objektive")
        self.both_selection = QCheckBox("Beides")

        # Connect checkboxes to mutually exclusive function
        self.cam_selection.toggled.connect(self.on_checkbox_toggled)
        self.lens_selection.toggled.connect(self.on_checkbox_toggled)
        self.both_selection.toggled.connect(self.on_checkbox_toggled)

        # Set default selection
        self.both_selection.setChecked(True)

        self.db_interaction = DB_Interaction(self)

        self.brands = self.db_interaction.get_brands()

        self.lens_categories = {
            "Nikon"   : {"Nikon 1"   : {"1-Mount%"},
                         "Nikon DSLR": {"AF%"},
                         "Nikon Z"   : {"Z%"},
                         },
            "Sony"    : {"E-Mount": {"%SEL%"},
                         "A-Mount": {"%SAL%"},
                         },
            "Canon"   : {"Spiegelreflex": {"EF%"},
                         "R-System"     : {"RF%"}
                         },
            "Fujifilm": {"Fujifilm GFX": {"GF%"},
                         "Fujifilm X"  : {"X%"},
                         },
            "Leica"   : {"Leica M" : {"%-M%"},
                         "Leica SL": {"%-SL%"},
                         "Leica S" : {"%-S%"},
                         "Leica TL": {"%-TL%"},
                         }
        }

        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout for central widget
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)  # Set a small margin for the entire layout
        central_widget.setLayout(main_layout)

        # Logo QLabel setup
        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.pixmap = QPixmap(image)
        self.update_pixmap()

        # Image layout (logo at the top)
        image_layout = QVBoxLayout()
        image_layout.addWidget(self.logo, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        image_layout.setContentsMargins(0, 0, 0, 0)  # Minimal buffer at the top (between status bar and logo)
        main_layout.addLayout(image_layout)

        in_out_layout = QHBoxLayout()

        input_layout = QVBoxLayout()

        # input setup
        cam_lens_label = QLabel("Kategorie")
        input_layout.addWidget(cam_lens_label)

        input_layout.addWidget(self.cam_selection)
        input_layout.addWidget(self.lens_selection)
        input_layout.addWidget(self.both_selection)

        # Set default selection
        self.both_selection.setChecked(True)

        brand_label = QLabel("Marke")
        input_layout.addWidget(brand_label)

        self.brand_input = QComboBox()
        self.brand_input.addItems(self.brands)
        self.brand_input.currentIndexChanged.connect(self.on_brand_selected)
        input_layout.addWidget(self.brand_input)

        category_input_label = QLabel("Kameraklasse")
        input_layout.addWidget(category_input_label)

        if self.lens_cam in [1, 3]:
            self.category_input = QComboBox()
            self.on_brand_selected()
            self.category_input.currentIndexChanged.connect(self.on_category_selected)
            input_layout.addWidget(self.category_input)

        elif self.lens_cam == 2:
            self.lens_category_input = QComboBox()
            self.on_brand_selected()
            self.lens_category_input.addItems(list(self.lens_categories[self.selected_brand].keys()))

        product_input_label = QLabel("Produkt")
        input_layout.addWidget(product_input_label)
        self.product_input = QComboBox()
        self.on_brand_selected()
        input_layout.addWidget(self.product_input)

        in_out_layout.addLayout(input_layout)

        output_layout = QVBoxLayout()

        in_out_layout.addLayout(output_layout)

        main_layout.addLayout(in_out_layout)

        main_layout.addStretch()

        # Connect the resize event
        self.resizeEvent = self.on_resize

    def on_checkbox_toggled(self):
        # Ensure only the clicked checkbox remains checked
        # Legend:
        # 1: Cameras
        # 2: Lenses
        # 3: both
        sender = self.sender()
        if sender.isChecked():
            # Uncheck other checkboxes
            if sender == self.cam_selection:
                self.lens_selection.setChecked(False)
                self.both_selection.setChecked(False)
                self.lens_cam = 1
            elif sender == self.lens_selection:
                self.cam_selection.setChecked(False)
                self.both_selection.setChecked(False)
                self.lens_cam = 2
            elif sender == self.both_selection:
                self.cam_selection.setChecked(False)
                self.lens_selection.setChecked(False)
                self.lens_cam = 3

    def update_pixmap(self):
        # Limit the width of the pixmap to a quarter of the full screen width
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        screen_width = screen_geometry.width()
        label_width = screen_width // 4
        scaled_pixmap = self.pixmap.scaledToWidth(label_width, Qt.TransformationMode.SmoothTransformation)
        self.logo.setPixmap(scaled_pixmap)

    def on_resize(self, event):
        self.update_pixmap()
        super().resizeEvent(event)

    def on_brand_selected(self):
        self.selected_brand = self.brand_input.currentText()
        if self.lens_cam in [1, 3]:
            self.available_categories = self.db_interaction.get_categories(self.selected_brand)
            self.category_input.clear()
            self.category_input.addItems(self.available_categories)
        elif self.lens_cam == 2:
            self.lens_category_input.clear()
            self.lens_category_input.addItems(self.lens_categories[self.selected_brand].keys())

    def on_category_selected(self):
        print(f"Available Categories: {self.available_categories}"
              f"\nSelected Brand: {self.selected_brand}")
        selected_category = self.category_input.currentText()
        selected_brand = self.brand_input.currentText()
        available_products = self.db_interaction.get_products(selected_category, self.selected_brand)
        print(available_products)
        self.product_input.clear()
        self.product_input.addItems(available_products)


class DB_Interaction:
    def __init__(self, app=None):
        self.setup_db_connection()
        self.app = app

    def setup_db_connection(self):
        self.conn = sqlite3.connect("CamerAarchive.db")
        self.c = self.conn.cursor()

    def close_db_connection(self):
        self.conn.close()

    def query_db(self, query):
        self.c.execute(query)

    def query_db_with_argument(self, query, variable):
        self.c.execute(query, (variable,))

    def query_db_with_two_arguments(self, query, variable1, variable2):
        self.c.execute(query, (variable1, variable2))

    def get_brands(self):
        if self.app.lens_cam == 1:
            unique_brands = self.get_brands_per_mode(
                "SELECT DISTINCT brand FROM camerAarchive"
            )
        elif self.app.lens_cam == 2:
            unique_brands = self.get_brands_per_mode(
                "SELECT DISTINCT brand FROM lensAarchive"
            )
        elif self.app.lens_cam == 3:
            self.query_db("SELECT DISTINCT brand FROM camerAarchive")
            cam_brands = {brand[0] for brand in self.c.fetchall()}
            self.query_db("SELECT DISTINCT brand FROM lensAarchive")
            lens_brands = {brand[0] for brand in self.c.fetchall()}
            unique_brands = cam_brands.union(lens_brands)

        return list(unique_brands)

    def get_brands_per_mode(self, arg0):
        self.query_db(arg0)
        return {brand[0] for brand in self.c.fetchall()}

    def get_categories(self, brand):
        cam_classes = []
        if self.app.lens_cam == 1:
            self.query_db_with_argument("SELECT DISTINCT Kameraklassen FROM camerAarchive WHERE brand = ?", brand)
            cam_classes = {cam_class[0] for cam_class in self.c.fetchall()}
        # self.query_db_with_argument("SELECT DISTINCT Kameraklassen FROM lensAarchive WHERE brand = ?", brand)
        # lens_classes = {lens_class[0] for lens_class in self.c.fetchall()}

        unique_classes = cam_classes if cam_classes is not None else []
        return list(unique_classes)

    def get_products_cam(self, cam_class, brand):
        brand = str(brand) if brand is not None else ''
        cam_class = str(cam_class) if cam_class is not None else ''
        print(f"Get Products called!"
              f"\nBrand: {brand}"
              f"\nCam_Class: {cam_class}")

        self.query_db_with_two_arguments("SELECT model FROM camerAarchive WHERE brand = ? AND Kameraklassen = ?", brand,
                                         cam_class)
        products = self.c.fetchall()
        print(f"SQL Used: "
              f"\nSELECT model FROM camerAarchive WHERE brand = {brand} AND Kameraklassen = {cam_class}")
        print(f"\nReturned products:"
              f"\n{list(products)}")

        return [product[0] for product in products]

    def get_products_lens(self, lens_class, brand):
        lens_class = str(lens_class) if lens_class is not None else ''
        brand = str(brand) if brand is not None else ''

        self.query_db_with_two_arguments("SELECT model FROM lensAarchive WHERE brand = ? AND Lensklassen = ?", brand,
                                         lens_class)
        lens_products = self.c.fetchall()
        print(f"SQL Used: "
              f"\nSELECT model FROM lensAarchive WHERE brand = {brand} AND Lensklassen = {lens_class}")
        print(f"\nReturned products:"
              f"\n{list(lens_products)}")

        return [product[0] for product in lens_products]


if __name__ == "__main__":
    app = QApplication([])

    # Create and show loading screen
    loading_screen = LoadingScreen()
    loading_screen.setWindowTitle('Loading')
    loading_screen.setGeometry(500, 300, 300, 200)
    loading_screen.show()

    # Create a worker thread to simulate loading
    worker = WorkerThread()

    # Connect worker thread to loading screen
    worker.progress_signal.connect(lambda value: None)  # Update this if needed
    worker.finished.connect(loading_screen.close_loading_screen)

    # Once loading is complete, show the main application window
    loading_screen.loading_complete.connect(lambda: ex.show())

    worker.start()

    ex = App()
    ex.setMinimumSize(400, 300)  # Set a minimum size for the window

    app.exec()
