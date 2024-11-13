"""
gui for interaction with the database
based on pyqt6
"""
import sqlite3
import time

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QMovie
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
                             QComboBox,
                             QGridLayout)
from PyQt6_SwitchControl import SwitchControl

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
        __init__(): Constructor to initialize the LoadingScreen widget with a banner image and
        loading icon.
        close_loading_screen(): Closes the loading screen and emits the loading_complete signal.
    """
    loading_complete = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SplashScreen)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Banner Image
        self.logo_label = QLabel()
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        screen_width = screen_geometry.width()
        pixmap = QPixmap(image)
        scaled_pixmap = pixmap.scaledToWidth(screen_width // 4,
                                             Qt.TransformationMode.SmoothTransformation)  # Scale
        # to a quarter of the
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
        self.toggle_state = False

        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout for central widget
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 10, 10,
                                            10)  # Set a small margin for the entire layout
        central_widget.setLayout(self.main_layout)

        # Logo QLabel setup
        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.pixmap = QPixmap(image)
        self.update_pixmap()

        # Image layout (logo at the top)
        image_layout = QVBoxLayout()
        image_layout.addWidget(self.logo,
                               alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        image_layout.setContentsMargins(0, 0, 0,
                                        0)  # Minimal buffer at the top (between status bar and
        # logo)
        self.main_layout.addLayout(image_layout)

        in_out_layout = QHBoxLayout()

        # Connect the resize event
        self.resizeEvent = self.on_resize

        input_layout = QVBoxLayout()

        parent_layout = QHBoxLayout()
        toggle_layout = QGridLayout()
        self.select_type_Label = QLabel("Modus Wählen")
        self.select_type_Label.setStyleSheet(
            "font-size: 16px;"
        )
        self.select_type_Label.setMargin(5)
        toggle_layout.addWidget(self.select_type_Label, 0, 1)

        self.toggle_left = QLabel("<b>Kameras</b>")
        self.toggle_left.setStyleSheet(
            "color: #006c8c;"
            "font-size: 15px;"
        )
        self.toggle_left.setAlignment(Qt.AlignmentFlag.AlignRight)
        toggle_layout.addWidget(self.toggle_left, 1, 0)
        self.toggle_right = QLabel("<b>Objektive</b>")
        self.toggle_right.setStyleSheet(
            "color: #9a9a9c;"
            "font-size: 15px;"
        )
        self.toggle_right.setAlignment(Qt.AlignmentFlag.AlignLeft)
        toggle_layout.addWidget(self.toggle_right, 1, 2)
        self.mode_toggle = SwitchControl(active_color="#9a9a9c", bg_color="#006c8c",
                                         circle_color="#ffffff")
        self.mode_toggle.stateChanged.connect(self.on_toggle)
        self.toggle_state = self.mode_toggle.isChecked()
        toggle_layout.addWidget(self.mode_toggle, 1, 1, alignment=Qt.AlignmentFlag.AlignCenter)

        parent_layout.addStretch(1)
        parent_layout.addLayout(toggle_layout)
        parent_layout.addStretch(1)
        input_layout.addLayout(parent_layout)
        self.main_layout.addLayout(input_layout)

        print("Toggle state: ", self.mode_toggle.isChecked())

        self.dynamic_layout = QVBoxLayout()

        if self.toggle_state:
            print("Lens Mode enabled")
        else:
            print("Camera Mode enabled")
            self.dynamic_layout.addLayout(self.setup_camera_mode())

        self.main_layout.addLayout(self.dynamic_layout)

        self.main_layout.addStretch(1)

        self.setLayout(self.main_layout)

    def on_toggle(self):
        self.toggle_state = self.mode_toggle.isChecked()
        print("Toggle State Updated: ", self.toggle_state)

        self.clear_layout(self.dynamic_layout)

        if self.toggle_state:
            self.dynamic_layout.addLayout(self.setup_lens_mode())
        else:
            self.dynamic_layout.addLayout(self.setup_camera_mode())

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                sub_layout = item.layout()
                if sub_layout is not None:
                    self.clear_layout(sub_layout)

    def setup_camera_mode(self):
        self.setWindowTitle("GraphicArchive - CamerArchive")
        camera_mode_layout = QVBoxLayout()

        brand_input_label = QLabel("Marke")
        camera_mode_layout.addWidget(brand_input_label)

        # get brands from db
        conn = sqlite3.connect("CamerAarchive.db")
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT brand FROM camerAarchive")
        brands = [brand[0] for brand in cursor.fetchall()]
        conn.close()

        self.brand_input = QComboBox()
        self.brand_input.clear()
        self.brand_input.addItems(brands)
        self.brand_input.currentIndexChanged.connect(self.on_cam_brand_changed)
        camera_mode_layout.addWidget(self.brand_input)

        category_input_label = QLabel("Kategorie")
        camera_mode_layout.addWidget(category_input_label)

        self.category_input = QComboBox()
        self.category_input.currentIndexChanged.connect(self.on_cam_category_changed)
        camera_mode_layout.addWidget(self.category_input)

        product_input_label = QLabel("Produkt")
        camera_mode_layout.addWidget(product_input_label)

        self.product_input = QComboBox()
        self.product_input.currentIndexChanged.connect(self.on_cam_product_changed)
        camera_mode_layout.addWidget(self.product_input)

        self.on_cam_brand_changed()
        self.on_cam_category_changed()

        return camera_mode_layout

    def setup_lens_mode(self):
        self.setWindowTitle("GraphicArchive - LensArchive")
        lens_mode_layout = QVBoxLayout()
        return lens_mode_layout

    def on_cam_brand_changed(self):
        self.selected_brand = self.brand_input.currentText()
        print(self.selected_brand)

        conn = sqlite3.connect("CamerAarchive.db")
        cursor = conn.cursor()

        # Retrieve all categories for the selected brand
        cursor.execute("SELECT DISTINCT Kameraklassen FROM camerAarchive WHERE brand = ?",
                       (self.selected_brand,))
        raw_categories = cursor.fetchall()

        # Split categories by comma and filter them
        individual_categories = set()
        for entry in raw_categories:
            categories = entry[0].split(",")  # Split by comma
            for category in categories:
                individual_categories.add(
                    category.strip())  # Add each category, stripped of extra spaces

        print(individual_categories)

        self.category_input.clear()
        self.category_input.addItems(sorted(individual_categories))  # Sort for readability
        conn.close()

    def on_cam_category_changed(self):
        selected_category = self.category_input.currentText()

        conn = sqlite3.connect("CamerAarchive.db")
        cursor = conn.cursor()

        cursor.execute("SELECT model FROM camerAarchive WHERE brand = ? AND Kameraklassen LIKE ?",
                       (self.selected_brand,
                        selected_category))
        products = {product[0] for product in cursor.fetchall()}

        conn.close()

        self.product_input.clear()
        self.product_input.addItems(products)

    def on_cam_product_changed(self):
        return

    def update_pixmap(self):
        # Limit the width of the pixmap to a quarter of the full screen width
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        screen_width = screen_geometry.width()
        label_width = screen_width // 4
        scaled_pixmap = self.pixmap.scaledToWidth(label_width,
                                                  Qt.TransformationMode.SmoothTransformation)
        self.logo.setPixmap(scaled_pixmap)

    def on_resize(self, event):
        self.update_pixmap()
        super().resizeEvent(event)


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
