import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import qtawesome as qta
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Import phase-specific tabs
from edflowsimulator.Phase_1 import Phase1Tab
from edflowsimulator.Phase_2 import Phase2Tab
from edflowsimulator.Phase_3 import Phase3Tab
from edflowsimulator.Phase_4 import Phase4Tab

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        return os.path.join(os.path.dirname(__file__), relative_path)

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Emergency Department Flow Simulation - Sta. Cruz Provincial Hospital")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon(resource_path("resources/EDFlowSimulator.png")))
        
        # Set up the main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Initialize tabs
        self.phase1_tab = Phase1Tab()
        self.phase2_tab = Phase2Tab()
        self.phase3_tab = Phase3Tab()
        self.phase4_tab = Phase4Tab()

        # Add tabs with icons
        self.tabs.addTab(self.phase1_tab, qta.icon('fa5s.hospital', color='#E6D5F5'), "Phase 1")
        self.tabs.addTab(self.phase2_tab, qta.icon('fa5s.chart-line', color='#E6D5F5'), "Phase 2")
        self.tabs.addTab(self.phase3_tab, qta.icon('fa5s.cogs', color='#E6D5F5'), "Phase 3")
        self.tabs.addTab(self.phase4_tab, qta.icon('fa5s.file-alt', color='#E6D5F5'), "Phase 4")

        # Add separator (horizontal line)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #4A3B6A;")
        layout.addWidget(separator)

        # Add footer
        footer_label = QLabel('Developed by @VoxDroid - <a href="https://github.com/VoxDroid" style="color: white;">github.com/VoxDroid</a> | CSEL 303 & CMSC 313 Final Project | Emergency Department Flow Simulation')
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_label.setTextFormat(Qt.TextFormat.RichText)
        footer_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        footer_label.setOpenExternalLinks(True)
        footer_label.setStyleSheet("""
            QLabel {
                color: #E6D5F5;
                font-family: 'Poppins', Arial, sans-serif;
                font-size: 12px;
                padding: 10px;
                background-color: #34294F;
            }
        """)
        layout.addWidget(footer_label)

        # Apply styles
        self.apply_styles()

    def apply_styles(self):
        """Apply the purplish-white dark theme to the application."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2A1B3D;
            }
            QTabWidget::pane {
                border: 1px solid #4A3B6A;
                background-color: #34294F;
            }
            QTabBar::tab {
                background-color: #4A3B6A;
                color: #E6D5F5;
                padding: 10px;
                font-family: 'Poppins', Arial, sans-serif;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: #6B5A8D;
                color: #FFFFFF;
            }
            QTabBar::tab:hover {
                background-color: #5A4B7A;
            }
            QWidget {
                font-family: 'Poppins', Arial, sans-serif;
                font-size: 14px;
                color: #E6D5F5;
            }
        """)

def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()