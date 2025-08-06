# gui_qt.py

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QStackedLayout, QSizePolicy, QFrame, QComboBox
)
from PySide6.QtCore import Qt, QTimer, QSize
from audio_input import PitchDetector
import sys
import numpy as np

from PySide6.QtGui import QPainter, QPen, QColor



class SidebarButton(QPushButton):
    def __init__(self, text, icon=""):
        super().__init__(text)
        self.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: #2e2e2e;
                border: none;
                padding: 12px;
                text-align: left;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

class Sidebar(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setFixedWidth(180)
        self.setStyleSheet("background-color: #2b2b2b;")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.tuner_btn = SidebarButton("Tuner")
        self.tuner_btn.clicked.connect(lambda: parent.set_page("tuner"))
        layout.addWidget(self.tuner_btn)

        self.metronome_btn = SidebarButton("Metronome")
        self.metronome_btn.clicked.connect(lambda: parent.set_page("metronome"))
        layout.addWidget(self.metronome_btn)

        self.scales_btn = SidebarButton("Scales")
        self.scales_btn.clicked.connect(lambda: parent.set_page("scales"))
        layout.addWidget(self.scales_btn)

        layout.addStretch()
        self.setLayout(layout)

class TunerPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #1e1e1e; color: white;")
        layout = QVBoxLayout()

        self.note_label = QLabel("---")
        self.note_label.setAlignment(Qt.AlignCenter)
        self.note_label.setStyleSheet("font-size: 60px; color: lime;")
        layout.addWidget(self.note_label)

        self.freq_label = QLabel("")
        self.freq_label.setAlignment(Qt.AlignCenter)
        self.freq_label.setStyleSheet("font-size: 18px;")
        layout.addWidget(self.freq_label)

        self.tuning_meter = TuningMeter()
        layout.addWidget(self.tuning_meter)

        self.setLayout(layout)

        self.current_note = None
        self.current_freq = None

        self.detector = PitchDetector(callback=self.update_pitch)
        self.detector.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_ui)
        self.timer.start(50)

    def update_pitch(self, note, freq):
        self.current_note = note
        self.current_freq = freq

    def refresh_ui(self):
        if self.current_note:
            self.note_label.setText(self.current_note)
            self.freq_label.setText(f"{self.current_freq:.1f} Hz")

            from audio_input import note_to_freq
            expected = note_to_freq(self.current_note)
            if expected:
                cents = 1200 * np.log2(self.current_freq / expected)
                self.tuning_meter.set_cents(cents)
        else:
            self.note_label.setText("---")
            self.freq_label.setText("")
            self.tuning_meter.set_cents(0)

    def close(self):
        self.detector.stop()
        super().close()


class TuningMeter(QWidget):
    def __init__(self):
        super().__init__()
        self.cents = None
        self.setMinimumHeight(30)

    def set_cents(self, cents):
        self.cents = max(-50, min(50, cents))  # Clamp to [-50, 50]
        self.update()

    def paintEvent(self, event):
        if self.cents is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        center_x = w / 2
        meter_width = w * 0.9
        bar_width = 4

        # Draw background line
        painter.setPen(QPen(Qt.gray, 2))
        painter.drawLine(center_x - meter_width/2, h/2, center_x + meter_width/2, h/2)

        # Draw center mark
        painter.setPen(QPen(Qt.white, 2))
        painter.drawLine(center_x, h/4, center_x, 3*h/4)

        # Draw tuning bar
        x_offset = (self.cents / 100) * meter_width
        bar_x = center_x + x_offset - bar_width/2

        color = QColor("lime") if abs(self.cents) <= 5 else QColor("orange")
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawRect(bar_x, h/4, bar_width, h/2)


class MetronomePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #1e1e1e; color: white;")
        layout = QVBoxLayout()
        label = QLabel("🕒 Metronome (Coming Soon)")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 24px;")
        layout.addWidget(label)
        self.setLayout(layout)

class ScalesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

        # UI Elements
        self.root_selector = QComboBox()
        self.root_selector.addItems(['C', 'C#', 'D', 'D#', 'E', 'F',
                                     'F#', 'G', 'G#', 'A', 'A#', 'B'])
        self.root_selector.setStyleSheet("padding: 6px; font-size: 16px;")

        self.scale_selector = QComboBox()
        self.scale_selector.addItems(['Major', 'Natural Minor',
                                      'Major Pentatonic', 'Minor Pentatonic'])
        self.scale_selector.setStyleSheet("padding: 6px; font-size: 16px;")

        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet("font-size: 20px; padding: 12px; color: lime;")

        self.played_note_label = QLabel("Current Note: ---")
        self.played_note_label.setAlignment(Qt.AlignCenter)
        self.played_note_label.setStyleSheet("font-size: 22px; color: orange; padding: 12px;")

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Select Root Note:"))
        layout.addWidget(self.root_selector)
        layout.addWidget(QLabel("Select Scale Type:"))
        layout.addWidget(self.scale_selector)
        layout.addStretch()
        layout.addWidget(QLabel("Scale Notes:"))
        layout.addWidget(self.result_label)
        layout.addStretch()
        layout.addWidget(self.played_note_label)
        self.setLayout(layout)

        # State
        self.current_note = None
        self.scale_notes = []

        # Logic
        self.root_selector.currentIndexChanged.connect(self.update_scale)
        self.scale_selector.currentIndexChanged.connect(self.update_scale)

        self.update_scale()

        # Start pitch detection
        self.detector = PitchDetector(callback=self.update_pitch)
        self.detector.start()

        # Timer to refresh UI
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_ui)
        self.timer.start(50)

    def update_scale(self):
        root = self.root_selector.currentText()
        scale_type = self.scale_selector.currentText()
        self.scale_notes = self.generate_scale(root, scale_type)
        self.result_label.setText("  •  ".join(self.scale_notes))

    def generate_scale(self, root, scale_type):
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F',
                      'F#', 'G', 'G#', 'A', 'A#', 'B']
        patterns = {
            'Major': [2, 2, 1, 2, 2, 2, 1],
            'Natural Minor': [2, 1, 2, 2, 1, 2, 2],
            'Major Pentatonic': [2, 2, 3, 2, 3],
            'Minor Pentatonic': [3, 2, 2, 3, 2]
        }

        pattern = patterns.get(scale_type, [])
        idx = note_names.index(root)
        scale = [note_names[idx]]

        for step in pattern:
            idx = (idx + step) % 12
            scale.append(note_names[idx])

        return scale

    def update_pitch(self, note, freq):
        self.current_note = note

    def refresh_ui(self):
        if self.current_note:
            note_name = self.current_note[:-1]  # Remove octave
            if note_name in self.scale_notes:
                color = "lime"
            else:
                color = "red"
            self.played_note_label.setText(f"Current Note: {self.current_note}")
            self.played_note_label.setStyleSheet(f"font-size: 22px; color: {color}; padding: 12px;")
        else:
            self.played_note_label.setText("Current Note: ---")
            self.played_note_label.setStyleSheet("font-size: 22px; color: orange; padding: 12px;")

    def close(self):
        self.detector.stop()
        super().close()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎸 Guitar Trainer")
        self.setMinimumSize(800, 500)
        self.setStyleSheet("background-color: #1e1e1e;")

        # Layouts
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Sidebar
        self.sidebar = Sidebar(self)
        main_layout.addWidget(self.sidebar)

        # Pages
        self.stack = QStackedLayout()
        self.pages = {
            "tuner": TunerPage(),
            "metronome": MetronomePage(),
            "scales": ScalesPage(),
        }

        for page in self.pages.values():
            self.stack.addWidget(page)

        content = QWidget()
        content.setLayout(self.stack)
        main_layout.addWidget(content)

        self.set_page("tuner")

    def set_page(self, page_name):
        index = list(self.pages.keys()).index(page_name)
        self.stack.setCurrentIndex(index)

    def closeEvent(self, event):
        self.pages["tuner"].close()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
