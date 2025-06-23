from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt, QTimer

class LoadingDialog(QDialog):
    def __init__(self, message="Importing PDF files"):
        super().__init__()
        self.setWindowTitle("Please wait")
        self.setFixedSize(320, 100)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)

        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QProgressBar {
                border: 1px solid #333;
                border-radius: 5px;
                background-color: #2d2d2d;
                height: 16px;
            }
            QProgressBar::chunk {
                background-color: #8e44ad;
                width: 20px;
            }
        """)

        layout = QVBoxLayout()
        self.base_message = message
        self.dots = 0

        self.label = QLabel(self.base_message)
        self.label.setAlignment(Qt.AlignCenter)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate

        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate_text)
        self.timer.start(500)

    def animate_text(self):
        self.dots = (self.dots + 1) % 4
        self.label.setText(self.base_message + "." * self.dots)
