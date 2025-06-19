import sys
import json
import ctypes
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QSlider, QColorDialog, QCheckBox, QPushButton,
                             QSystemTrayIcon, QMenu, QTabWidget, QFileDialog)
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QColor, QPainter, QPen, QIcon, QCursor

class CrosshairOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Window setup
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.X11BypassWindowManagerHint |
            Qt.WindowTransparentForInput |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Cursor control
        self.user32 = ctypes.windll.user32
        self.cursor_visible = True
        self.cursor_timer = QTimer()
        self.cursor_timer.timeout.connect(self.manage_cursor)
        self.cursor_timer.start(50)  # 50ms refresh rate
        
        # Default settings
        self.settings = {
            'size': 20,
            'thickness': 2,
            'gap': 5,
            'color': QColor(255, 0, 0),
            'outline': True,
            'outline_thickness': 1,
            'outline_color': QColor(0, 0, 0),
            'center_dot': True,
            'dot_size': 3,
            'opacity': 1.0
        }
        
        self.update_position()
    
    def manage_cursor(self):
        """Hide cursor only when over our overlay and not over GUI"""
        cursor_pos = QCursor.pos()
        
        # Get reference to main GUI window
        main_window = QApplication.instance().activeWindow()
        
        # Check if cursor is over the main GUI window
        if main_window and main_window.geometry().contains(cursor_pos):
            # Show cursor when over GUI
            if not self.cursor_visible:
                self.user32.ShowCursor(True)
                self.cursor_visible = True
        else:
            # Hide cursor when over game area
            if self.cursor_visible:
                self.user32.ShowCursor(False)
                self.cursor_visible = False
    
    def update_position(self):
        screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(0, 0, screen_geometry.width(), screen_geometry.height())
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setOpacity(self.settings['opacity'])
        
        center = self.rect().center()
        size = self.settings['size']
        thickness = self.settings['thickness']
        gap = self.settings['gap']
        color = self.settings['color']
        
        # Draw outline if enabled
        if self.settings['outline']:
            outline_pen = QPen(self.settings['outline_color'])
            outline_pen.setWidth(self.settings['outline_thickness'] * 2 + thickness)
            painter.setPen(outline_pen)
            
            # Horizontal line
            painter.drawLine(
                QPoint(center.x() - size - gap, center.y()),
                QPoint(center.x() - gap, center.y())
            )
            painter.drawLine(
                QPoint(center.x() + gap, center.y()),
                QPoint(center.x() + size + gap, center.y())
            )
            
            # Vertical line
            painter.drawLine(
                QPoint(center.x(), center.y() - size - gap),
                QPoint(center.x(), center.y() - gap)
            )
            painter.drawLine(
                QPoint(center.x(), center.y() + gap),
                QPoint(center.x(), center.y() + size + gap)
            )
        
        # Draw main crosshair
        pen = QPen(color)
        pen.setWidth(thickness)
        painter.setPen(pen)
        
        # Horizontal line
        painter.drawLine(
            QPoint(center.x() - size - gap, center.y()),
            QPoint(center.x() - gap, center.y())
        )
        painter.drawLine(
            QPoint(center.x() + gap, center.y()),
            QPoint(center.x() + size + gap, center.y())
        )
        
        # Vertical line
        painter.drawLine(
            QPoint(center.x(), center.y() - size - gap),
            QPoint(center.x(), center.y() - gap)
        )
        painter.drawLine(
            QPoint(center.x(), center.y() + gap),
            QPoint(center.x(), center.y() + size + gap)
        )
        
        # Draw center dot
        if self.settings['center_dot']:
            dot_size = self.settings['dot_size']
            if self.settings['outline']:
                painter.setPen(QPen(self.settings['outline_color']))
                painter.setBrush(self.settings['outline_color'])
                painter.drawEllipse(center, dot_size + 1, dot_size + 1)
            
            painter.setPen(QPen(color))
            painter.setBrush(color)
            painter.drawEllipse(center, dot_size, dot_size)
        
        painter.end()
    
    def closeEvent(self, event):
        """Ensure cursor is restored when closing"""
        self.user32.ShowCursor(True)
        event.accept()

class CrosshairApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.loading_profile = False
        self.overlay = CrosshairOverlay()
        self.overlay.show()
        
        self.init_ui()
        self.init_tray_icon()
        
        # Ensure GUI always shows cursor
        self.setCursor(Qt.ArrowCursor)
    
    def init_ui(self):
        self.setWindowTitle("Crosshair Overlay")
        self.setWindowIcon(QIcon("crosshair.png"))
        self.setFixedSize(400, 450)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        crosshair_tab = QWidget()
        crosshair_layout = QVBoxLayout(crosshair_tab)
        
        # Create sliders
        self.size_slider, self.size_value_label = self.create_slider("Size:", 5, 100, self.overlay.settings['size'])
        self.thickness_slider, self.thickness_value_label = self.create_slider("Thickness:", 1, 10, self.overlay.settings['thickness'])
        self.gap_slider, self.gap_value_label = self.create_slider("Gap:", 0, 20, self.overlay.settings['gap'])
        self.outline_thickness_slider, self.outline_thickness_value_label = self.create_slider("Outline Thickness:", 1, 5, self.overlay.settings['outline_thickness'])
        self.dot_size_slider, self.dot_size_value_label = self.create_slider("Dot Size:", 1, 10, self.overlay.settings['dot_size'])
        self.opacity_slider, self.opacity_value_label = self.create_slider("Opacity:", 10, 100, int(self.overlay.settings['opacity'] * 100))
        
        # Add to layout
        crosshair_layout.addLayout(self.size_slider)
        crosshair_layout.addLayout(self.thickness_slider)
        crosshair_layout.addLayout(self.gap_slider)
        
        # Color selection
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        self.color_btn = QPushButton()
        self.color_btn.setStyleSheet(f"background-color: {self.overlay.settings['color'].name()}")
        self.color_btn.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_btn)
        crosshair_layout.addLayout(color_layout)
        
        # Outline checkbox
        self.outline_check = QCheckBox("Outline")
        self.outline_check.setChecked(self.overlay.settings['outline'])
        self.outline_check.stateChanged.connect(self.update_outline)
        crosshair_layout.addWidget(self.outline_check)
        
        crosshair_layout.addLayout(self.outline_thickness_slider)
        
        # Outline color
        outline_color_layout = QHBoxLayout()
        outline_color_layout.addWidget(QLabel("Outline Color:"))
        self.outline_color_btn = QPushButton()
        self.outline_color_btn.setStyleSheet(f"background-color: {self.overlay.settings['outline_color'].name()}")
        self.outline_color_btn.clicked.connect(self.choose_outline_color)
        outline_color_layout.addWidget(self.outline_color_btn)
        crosshair_layout.addLayout(outline_color_layout)
        
        # Center dot
        self.dot_check = QCheckBox("Center Dot")
        self.dot_check.setChecked(self.overlay.settings['center_dot'])
        self.dot_check.stateChanged.connect(self.update_dot)
        crosshair_layout.addWidget(self.dot_check)
        
        crosshair_layout.addLayout(self.dot_size_slider)
        crosshair_layout.addLayout(self.opacity_slider)
        
        tabs.addTab(crosshair_tab, "Crosshair")
        
        # Save/Load buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Profile")
        save_btn.clicked.connect(self.save_profile)
        btn_layout.addWidget(save_btn)
        
        load_btn = QPushButton("Load Profile")
        load_btn.clicked.connect(self.load_profile)
        btn_layout.addWidget(load_btn)
        
        layout.addLayout(btn_layout)
        
        # System tray options
        self.close_to_tray_check = QCheckBox("Close to system tray")
        self.close_to_tray_check.setChecked(True)
        layout.addWidget(self.close_to_tray_check)
        
        # Connect signals after UI setup
        self.connect_sliders()
    
    def create_slider(self, label_text, min_val, max_val, default_val):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        layout.addWidget(label)
        
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(default_val)
        
        value_label = QLabel(str(default_val))
        value_label.setFixedWidth(30)
        
        layout.addWidget(slider)
        layout.addWidget(value_label)
        
        return layout, value_label
    
    def connect_sliders(self):
        self.size_slider.itemAt(1).widget().valueChanged.connect(self.update_crosshair)
        self.thickness_slider.itemAt(1).widget().valueChanged.connect(self.update_crosshair)
        self.gap_slider.itemAt(1).widget().valueChanged.connect(self.update_crosshair)
        self.outline_thickness_slider.itemAt(1).widget().valueChanged.connect(self.update_crosshair)
        self.dot_size_slider.itemAt(1).widget().valueChanged.connect(self.update_crosshair)
        self.opacity_slider.itemAt(1).widget().valueChanged.connect(self.update_crosshair)
    
    def update_crosshair(self):
        if not self.loading_profile:
            self.overlay.settings['size'] = self.size_slider.itemAt(1).widget().value()
            self.overlay.settings['thickness'] = self.thickness_slider.itemAt(1).widget().value()
            self.overlay.settings['gap'] = self.gap_slider.itemAt(1).widget().value()
            self.overlay.settings['outline_thickness'] = self.outline_thickness_slider.itemAt(1).widget().value()
            self.overlay.settings['dot_size'] = self.dot_size_slider.itemAt(1).widget().value()
            self.overlay.settings['opacity'] = self.opacity_slider.itemAt(1).widget().value() / 100
            self.overlay.update()
    
    def choose_color(self):
        color = QColorDialog.getColor(self.overlay.settings['color'], self, "Choose Crosshair Color")
        if color.isValid():
            self.overlay.settings['color'] = color
            self.color_btn.setStyleSheet(f"background-color: {color.name()}")
            self.overlay.update()
    
    def choose_outline_color(self):
        color = QColorDialog.getColor(self.overlay.settings['outline_color'], self, "Choose Outline Color")
        if color.isValid():
            self.overlay.settings['outline_color'] = color
            self.outline_color_btn.setStyleSheet(f"background-color: {color.name()}")
            self.overlay.update()
    
    def update_outline(self, state):
        self.overlay.settings['outline'] = state == Qt.Checked
        self.overlay.update()
    
    def update_dot(self, state):
        self.overlay.settings['center_dot'] = state == Qt.Checked
        self.overlay.update()
    
    def save_profile(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Profile", "", "JSON Files (*.json)")
        if filename:
            settings_to_save = self.overlay.settings.copy()
            settings_to_save['color'] = settings_to_save['color'].name()
            settings_to_save['outline_color'] = settings_to_save['outline_color'].name()
            
            with open(filename, 'w') as f:
                json.dump(settings_to_save, f)
    
    def load_profile(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Profile", "", "JSON Files (*.json)")
        if filename:
            with open(filename, 'r') as f:
                loaded_settings = json.load(f)
                
                # Convert colors
                loaded_settings['color'] = QColor(loaded_settings['color'])
                loaded_settings['outline_color'] = QColor(loaded_settings['outline_color'])
                
                # Update settings
                self.overlay.settings = loaded_settings
                
                # Update UI without triggering events
                self.loading_profile = True
                self.update_ui_from_settings()
                self.loading_profile = False
                
                self.overlay.update()
    
    def update_ui_from_settings(self):
        # Update sliders
        self.size_slider.itemAt(1).widget().setValue(self.overlay.settings['size'])
        self.thickness_slider.itemAt(1).widget().setValue(self.overlay.settings['thickness'])
        self.gap_slider.itemAt(1).widget().setValue(self.overlay.settings['gap'])
        self.outline_thickness_slider.itemAt(1).widget().setValue(self.overlay.settings['outline_thickness'])
        self.dot_size_slider.itemAt(1).widget().setValue(self.overlay.settings['dot_size'])
        self.opacity_slider.itemAt(1).widget().setValue(int(self.overlay.settings['opacity'] * 100))
        
        # Update labels
        self.size_value_label.setText(str(self.overlay.settings['size']))
        self.thickness_value_label.setText(str(self.overlay.settings['thickness']))
        self.gap_value_label.setText(str(self.overlay.settings['gap']))
        self.outline_thickness_value_label.setText(str(self.overlay.settings['outline_thickness']))
        self.dot_size_value_label.setText(str(self.overlay.settings['dot_size']))
        self.opacity_value_label.setText(str(int(self.overlay.settings['opacity'] * 100)))
        
        # Update colors
        self.color_btn.setStyleSheet(f"background-color: {self.overlay.settings['color'].name()}")
        self.outline_color_btn.setStyleSheet(f"background-color: {self.overlay.settings['outline_color'].name()}")
        
        # Update checkboxes
        self.outline_check.setChecked(self.overlay.settings['outline'])
        self.dot_check.setChecked(self.overlay.settings['center_dot'])
    
    def init_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("crosshair.png"))
        
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show)
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_app)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.tray_icon_activated)
    
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
    
    def closeEvent(self, event):
        if self.close_to_tray_check.isChecked():
            event.ignore()
            self.hide()
        else:
            self.quit_app()
    
    def quit_app(self):
        self.overlay.close()
        self.tray_icon.hide()
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Crosshair Overlay")
    app.setApplicationDisplayName("Crosshair Overlay")
    
    main_window = CrosshairApp()
    main_window.show()
    
    sys.exit(app.exec_())