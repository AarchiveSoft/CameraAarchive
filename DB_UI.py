"""
gui for interaction with the database
based on pyqt6
"""
import time

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QMovie
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout

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
        brand_label = QLabel("Marke")
        input_layout.addWidget(brand_label)

        brand_input = QLineEdit()
        input_layout.addWidget(brand_input)

        in_out_layout.addLayout(input_layout)

        output_layout = QVBoxLayout()

        in_out_layout.addLayout(output_layout)

        main_layout.addLayout(in_out_layout)

        main_layout.addStretch()

        # Connect the resize event
        self.resizeEvent = self.on_resize

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
