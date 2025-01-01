from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtGui import QPixmap, QKeyEvent, QKeySequence, QShortcut
from PySide6.QtCore import QTimer, Qt, QUrl, QSysInfo
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, 
    QWidget, QFileDialog, QPushButton, QDialog, 
    QHBoxLayout, QSpinBox, QFormLayout)
from PIL.ImageQt import ImageQt
from PIL import Image, ExifTags
from pathlib import Path
import random
import sys
import os

class SlideshowApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Slideshow")
        self.resize(1200, 800)

        # Set black background
        self.setStyleSheet("background-color: black;")
        
        # Setup main widget and layout
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: black;")
        self.setCentralWidget(main_widget)
        self.layout = QVBoxLayout(main_widget)

        # Create initial buttons layout
        buttons_layout = QHBoxLayout()
        
        # Create open folder button
        self.open_folder_button = QPushButton("Open Folder")
        self.open_folder_button.setStyleSheet(self.get_button_style())
        self.open_folder_button.clicked.connect(self.select_folder)
        
        # Create settings button
        self.settings_button = QPushButton("Settings")
        self.settings_button.setStyleSheet(self.get_button_style())
        self.settings_button.clicked.connect(self.show_settings)
        
        # Add buttons to layout
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.open_folder_button)
        buttons_layout.addSpacing(10)  # Add some space between buttons
        buttons_layout.addWidget(self.settings_button)
        buttons_layout.addStretch()
        
        # Update prompt label
        self.prompt_label = QLabel("Drag and drop folder here\nor click 'Open Folder'")
        self.prompt_label.setStyleSheet("color: white; font-size: 24px;")
        self.prompt_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.prompt_label)
        
        # Add buttons layout to main layout
        self.layout.addLayout(buttons_layout)

        # Create display widgets
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: black;")
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)

        # Add widgets to layout
        self.layout.addWidget(self.image_label)
        self.layout.addWidget(self.video_widget)
        self.video_widget.hide()
        self.image_label.hide()  # Hide initially

        self.is_playing = True
        self.folder_path = None
        self.files = []
        self.current_index = -1
        self.display_duration = 5000
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.gif', 
                                '.mp4', '.mov', '.avi']

        # Timer for slideshow
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_item)

        # Create audio output
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)

        self.history = []  # Store history of shown items
        self.history_position = -1  # Current position in history
        self.future_queue = []  # Store items that were shown after current position

        # Add video finished signal handler
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)

        # Add cursor hide timer
        self.cursor_timer = QTimer()
        self.cursor_timer.timeout.connect(self.hide_cursor)
        self.cursor_timer.setSingleShot(True)
        
        # Track cursor visibility
        self.cursor_visible = True
        self.cursor_timer.start(2000)

        # Enable drop events
        self.setAcceptDrops(True)

        # Initialize settings
        self.display_duration = 5000  # 5 seconds default

        # Add settings shortcut based on platform
        if QSysInfo.productType() == "macos":
            # Command+, for macOS
            self.settings_shortcut = QShortcut(QKeySequence("Ctrl+,"), self)
        else:
            # Ctrl+, for Windows/Linux
            self.settings_shortcut = QShortcut(QKeySequence("Ctrl+,"), self)
        
        self.settings_shortcut.activated.connect(self.show_settings)

        # Track slideshow state
        self.slideshow_active = False

    def get_button_style(self):
        """Return consistent button style"""
        return """
            QPushButton {
                color: white;
                background-color: rgba(60, 60, 60, 180);
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: rgba(80, 80, 80, 180);
            }
        """

    def dragEnterEvent(self, event):
        """Handle drag enter events"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle drop events"""
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if os.path.isdir(path):
                self.folder_path = path
                self.files = self.get_media_files()
                if self.files:
                    self.start_slideshow()
                else:
                    self.prompt_label.setText("No supported media files found\nTry another folder")
            else:
                self.prompt_label.setText("Please drop a folder\nnot a file")

    def start_slideshow(self):
        """Start the slideshow with current files"""
        self.prompt_label.hide()
        self.open_folder_button.hide()
        self.settings_button.hide()
        self.image_label.show()
        self.slideshow_active = True  # Set slideshow as active
        random.shuffle(self.files)
        self.current_index = -1
        self.history = []
        self.history_position = -1
        self.future_queue = []
        self.next_item()

    def select_folder(self):
        """Handle folder selection"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.folder_path = folder_path
            self.files = self.get_media_files()
            if self.files:
                self.start_slideshow()
            else:
                self.prompt_label.setText("No supported media files found\nTry another folder")

    def get_media_files(self):
        files = []
        for ext in self.supported_formats:
            files.extend(Path(self.folder_path).glob(f'*{ext}'))
        return sorted(files)

    def is_video_file(self, file_path):
        return str(file_path).lower().endswith(('.mp4', '.mov', '.avi'))

    def show_image(self, file_path):
        self.video_widget.hide()
        self.image_label.show()
        self.media_player.stop()
        
        # Load and rotate image if needed using PIL
        image = Image.open(str(file_path))
        
        try:
            # Check for EXIF orientation tag
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break
            
            exif = image._getexif()
            if exif is not None:
                orientation_value = exif.get(orientation)
                if orientation_value is not None:
                    # Rotate image according to EXIF orientation
                    if orientation_value == 3:
                        image = image.rotate(180, expand=True)
                    elif orientation_value == 6:
                        image = image.rotate(270, expand=True)
                    elif orientation_value == 8:
                        image = image.rotate(90, expand=True)
        except (AttributeError, KeyError, IndexError):
            # No EXIF data or orientation tag found
            pass
        
        # Convert PIL image to QPixmap
        qim = ImageQt(image)
        pixmap = QPixmap.fromImage(qim)
        
        scaled_pixmap = pixmap.scaled(self.image_label.size(), 
                                    Qt.KeepAspectRatio, 
                                    Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)
        if self.is_playing:
            self.timer.start(self.display_duration)

    def show_video(self, file_path):
        self.image_label.hide()
        self.video_widget.show()
        
        
        self.media_player.setSource(QUrl.fromLocalFile(str(file_path)))
        self.media_player.play()
        
        # Don't start the timer for videos
        self.timer.stop()

    def next_item(self):
        if not self.files:
            return
            
        # If we have items in future_queue (after going back), use those
        if self.future_queue:
            self.current_index = self.future_queue.pop(0)
            self.history.append(self.current_index)
            self.history_position = len(self.history) - 1
        else:
            # Pick a random index that's different from the current one
            new_index = self.current_index
            while new_index == self.current_index and len(self.files) > 1:
                new_index = random.randint(0, len(self.files) - 1)
            
            self.current_index = new_index
            self.history.append(self.current_index)
            self.history_position = len(self.history) - 1
            
        self.show_current_item()

    def previous_item(self):
        if not self.files or self.history_position <= 0:
            return
            
        # Store current item in future queue before going back
        if self.history_position == len(self.history) - 1:
            self.future_queue.insert(0, self.history[self.history_position])
            
        self.history_position -= 1
        self.current_index = self.history[self.history_position]
        self.show_current_item()

    def show_current_item(self):
        current_file = self.files[self.current_index]
        if self.is_video_file(current_file):
            self.show_video(current_file)
        else:
            self.show_image(current_file)

    def toggle_play_pause(self):
        self.is_playing = not self.is_playing
        
        if self.is_playing:
            if self.is_video_file(self.files[self.current_index]):
                self.media_player.play()
            else:
                self.timer.start(self.display_duration)
        else:
            if self.is_video_file(self.files[self.current_index]):
                self.media_player.pause()
            else:
                self.timer.stop()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.image_label.pixmap():
            current_file = self.files[self.current_index]
            if not self.is_video_file(current_file):
                # Use the same image loading logic as show_image
                image = Image.open(str(current_file))
                
                try:
                    for orientation in ExifTags.TAGS.keys():
                        if ExifTags.TAGS[orientation] == 'Orientation':
                            break
                    
                    exif = image._getexif()
                    if exif is not None:
                        orientation_value = exif.get(orientation)
                        if orientation_value is not None:
                            if orientation_value == 3:
                                image = image.rotate(180, expand=True)
                            elif orientation_value == 6:
                                image = image.rotate(270, expand=True)
                            elif orientation_value == 8:
                                image = image.rotate(90, expand=True)
                except (AttributeError, KeyError, IndexError):
                    pass
                
                qim = ImageQt(image)
                pixmap = QPixmap.fromImage(qim)
                scaled_pixmap = pixmap.scaled(self.image_label.size(), 
                                            Qt.KeepAspectRatio, 
                                            Qt.SmoothTransformation)
                self.image_label.setPixmap(scaled_pixmap)

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard events"""
        if event.key() == Qt.Key_Left:
            self.previous_item()
        elif event.key() == Qt.Key_Right:
            self.next_item()
        elif event.key() == Qt.Key_Space:
            self.toggle_play_pause()
        elif event.key() == Qt.Key_O:
            self.select_folder()
        # Add Cmd+, (macOS) or Ctrl+, (Windows/Linux) shortcut
        elif (event.key() == Qt.Key_Comma and 
              ((QSysInfo.productType() == "macos" and event.modifiers() == Qt.MetaModifier) or
               (QSysInfo.productType() != "macos" and event.modifiers() == Qt.ControlModifier))):
            self.show_settings()
        event.accept()

    def handle_media_status(self, status):
        
        # When video reaches the end, move to next item
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.next_item()

    def mouseMoveEvent(self, event):
        """Show cursor when mouse moves and restart the timer"""
        if self.slideshow_active:  # Only manage cursor if slideshow is active
            if not self.cursor_visible:
                self.setCursor(Qt.ArrowCursor)
                self.cursor_visible = True
            
            self.cursor_timer.start(2000)
        super().mouseMoveEvent(event)

    def hide_cursor(self):
        """Hide the cursor after timer expires"""
        if self.slideshow_active:  # Only hide cursor if slideshow is active
            self.setCursor(Qt.BlankCursor)
            self.cursor_visible = False

    def leaveEvent(self, event):
        """Show cursor when leaving window"""
        self.setCursor(Qt.ArrowCursor)
        self.cursor_visible = True
        super().leaveEvent(event)

    def enterEvent(self, event):
        """Start timer when entering window"""
        if self.slideshow_active:  # Only start timer if slideshow is active
            self.cursor_timer.start(2000)
        super().enterEvent(event)

    def show_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedWidth(300)
        
        # Use system palette for background
        self.setStyleSheet("")  # Remove any custom styling to use system style
        
        # Create layout
        layout = QFormLayout(self)
        layout.setSpacing(20)
        
        # Display duration spinner
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 60)
        self.duration_spin.setValue(parent.display_duration // 1000)
        
        # Create a horizontal layout for spinner and label
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(self.duration_spin)
        duration_layout.addWidget(QLabel("seconds"))
        duration_layout.addStretch()
        
        # Add widgets to layout
        layout.addRow("Display Duration:", duration_layout)
        
        # Update apply button style to match main window buttons
        self.apply_button = QPushButton("Apply")
        self.apply_button.setStyleSheet(parent.get_button_style())
        self.apply_button.clicked.connect(self.apply_settings)
        
        # Center the apply button
        apply_layout = QHBoxLayout()
        apply_layout.addStretch()
        apply_layout.addWidget(self.apply_button)
        apply_layout.addStretch()
        
        layout.addRow("", apply_layout)
        
        self.setLayout(layout)
        
        # Store parent reference
        self.parent = parent
        
    def apply_settings(self):
        self.parent.display_duration = self.duration_spin.value() * 1000
        self.close()

def main():
    app = QApplication(sys.argv)
    window = SlideshowApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()