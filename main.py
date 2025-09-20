import sys
import os
import time
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit,
    QTextEdit, QCheckBox, QSpinBox, QGroupBox
)
from PyQt6.QtCore import QThread, pyqtSignal
from pywinauto import Desktop
from plyer import notification

# -------------------------------
# Monitoring Thread
# -------------------------------
class MonitorThread(QThread):
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, window_title, keywords, interval, action, custom_command, log_file):
        super().__init__()
        self.window_title = window_title
        self.keywords = keywords
        self.interval = interval
        self.action = action
        self.custom_command = custom_command
        self.log_file = log_file
        self.running = True

    def run(self):
        try:
            window = Desktop(backend="uia").window(title=self.window_title)
        except Exception as e:
            self.status_signal.emit(f"Error connecting to window: {e}")
            return

        while self.running:
            try:
                window.set_focus()
                texts = [ctrl.window_text() for ctrl in window.descendants()]
                detected = False
                for t in texts:
                    for keyword in self.keywords:
                        if keyword.lower() in t.lower():
                            detected = True
                            break
                    if detected:
                        break

                if detected:
                    self.status_signal.emit("✅ Installation Complete!")
                    self.perform_action()
                    self.finished_signal.emit()
                    break
                else:
                    self.status_signal.emit("⏳ Still installing...")
            except Exception as e:
                self.status_signal.emit(f"Error: {e}")
            time.sleep(self.interval)

    def perform_action(self):
        # Execute predefined actions
        if self.action == "Show Notification":
            notification.notify(title="ActionOnFinish", message="Installation Complete!", timeout=5)
        elif self.action == "Click Finish Button":
            try:
                finish_btn = Desktop(backend="uia").window(title=self.window_title).child_window(title="Finish", control_type="Button")
                if finish_btn.exists():
                    finish_btn.click_input()
                    self.status_signal.emit("Clicked Finish button.")
            except:
                self.status_signal.emit("Finish button not found.")
        elif self.action == "Shut Down PC":
            os.system("shutdown /s /t 5")
        elif self.action == "Restart PC":
            os.system("shutdown /r /t 5")
        elif self.action == "Run Custom Command" and self.custom_command:
            os.system(self.custom_command)

        # Log if needed
        if self.log_file:
            with open(self.log_file, "a") as f:
                f.write(f"Action '{self.action}' executed at {time.ctime()}\n")

    def stop(self):
        self.running = False
        self.quit()
        self.wait()

# -------------------------------
# Main GUI Window
# -------------------------------
class ActionOnFinishGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ActionOnFinish")
        self.setGeometry(200, 100, 650, 500)
        self.monitor_thread = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # --- Window Selection ---
        window_group = QGroupBox("Window Selection")
        window_layout = QHBoxLayout()
        window_layout.addWidget(QLabel("Select App/Window:"))

        self.window_dropdown = QComboBox()
        self.window_dropdown.setStyleSheet("padding:5px; font-size:14px;")
        window_layout.addWidget(self.window_dropdown)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_windows)
        window_layout.addWidget(refresh_btn)
        window_group.setLayout(window_layout)
        layout.addWidget(window_group)

        # --- Completion Keywords ---
        keyword_group = QGroupBox("Completion Detection")
        keyword_layout = QVBoxLayout()
        keyword_layout.addWidget(QLabel("Completion Keywords (comma separated):"))
        self.keywords_input = QLineEdit("finish, done, installation complete, success")
        keyword_layout.addWidget(self.keywords_input)

        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Check Interval (seconds):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setMinimum(1)
        self.interval_spin.setValue(2)
        interval_layout.addWidget(self.interval_spin)
        keyword_layout.addLayout(interval_layout)
        keyword_group.setLayout(keyword_layout)
        layout.addWidget(keyword_group)

        # --- Actions on Completion ---
        action_group = QGroupBox("Actions on Completion")
        action_layout = QVBoxLayout()
        self.action_dropdown = QComboBox()
        self.action_dropdown.addItems([
            "Do Nothing",
            "Show Notification",
            "Click Finish Button",
            "Shut Down PC",
            "Restart PC",
            "Run Custom Command"
        ])
        self.action_dropdown.currentTextChanged.connect(self.toggle_command_input)
        action_layout.addWidget(QLabel("Select Action:"))
        action_layout.addWidget(self.action_dropdown)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter custom command")
        self.command_input.setVisible(False)
        action_layout.addWidget(self.command_input)

        self.log_cb = QCheckBox("Log action to file")
        self.log_file_input = QLineEdit()
        self.log_file_input.setPlaceholderText("Log file path")
        action_layout.addWidget(self.log_cb)
        action_layout.addWidget(self.log_file_input)

        action_group.setLayout(action_layout)
        layout.addWidget(action_group)

        # --- Status Panel ---
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        status_layout.addWidget(self.status_display)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # --- Start / Stop Buttons ---
        buttons_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Monitoring")
        self.start_btn.clicked.connect(self.start_monitoring)
        buttons_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop Monitoring")
        self.stop_btn.clicked.connect(self.stop_monitoring)
        buttons_layout.addWidget(self.stop_btn)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        self.refresh_windows()

    # --- Functions ---
    def refresh_windows(self):
        self.window_dropdown.clear()
        windows = Desktop(backend="uia").windows()
        for w in windows:
            title = w.window_text().strip()
            if title:
                self.window_dropdown.addItem(title)

    def toggle_command_input(self, action):
        self.command_input.setVisible(action == "Run Custom Command")

    def start_monitoring(self):
        window_title = self.window_dropdown.currentText()
        if not window_title:
            self.status_display.append("❌ No window selected.")
            return

        keywords = [k.strip() for k in self.keywords_input.text().split(",") if k.strip()]
        interval = self.interval_spin.value()
        action = self.action_dropdown.currentText()
        custom_command = self.command_input.text() if action == "Run Custom Command" else None
        log_file = self.log_file_input.text() if self.log_cb.isChecked() else None

        self.monitor_thread = MonitorThread(window_title, keywords, interval, action, custom_command, log_file)
        self.monitor_thread.status_signal.connect(self.update_status)
        self.monitor_thread.finished_signal.connect(self.monitor_finished)
        self.monitor_thread.start()
        self.status_display.append(f"Started monitoring window: {window_title}")

    def stop_monitoring(self):
        if self.monitor_thread:
            self.monitor_thread.stop()
            self.status_display.append("Monitoring stopped.")

    def update_status(self, message):
        self.status_display.append(message)

    def monitor_finished(self):
        self.status_display.append("✅ Monitoring finished.")

# -------------------------------
# Run App
# -------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ActionOnFinishGUI()
    window.show()
    sys.exit(app.exec())
