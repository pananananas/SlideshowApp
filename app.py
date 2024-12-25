import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, 
                              QVBoxLayout, QWidget, QPushButton, QHBoxLayout,
                              QFileDialog)
from PySide6.QtCore import QTimer, Qt, QSize
from PySide6.QtGui import QPixmap, QImage, QPalette, QColor, QKeyEvent
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
import random  # Add this import at the top
from PIL import Image, ExifTags
from PIL.ImageQt import ImageQt

class SlideshowApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Slideshow Viewer")
        self.resize(800, 600)

        # Set black background
        self.setStyleSheet("background-color: black;")
        
        # Setup main widget and layout
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: black;")
        self.setCentralWidget(main_widget)
        self.layout = QVBoxLayout(main_widget)

        # Create initial prompt label
        self.prompt_label = QLabel("Press 'O' to open a folder")
        self.prompt_label.setStyleSheet("color: white; font-size: 24px;")
        self.prompt_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.prompt_label)

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

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.folder_path = folder_path
            self.files = self.get_media_files()
            if self.files:
                self.prompt_label.hide()
                self.image_label.show()
                random.shuffle(self.files)
                self.current_index = -1
                self.next_item()
            else:
                self.prompt_label.setText("No supported media files found\nPress 'O' to select another folder")

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
        self.timer.start(self.display_duration)

    def show_video(self, file_path):
        self.image_label.hide()
        self.video_widget.show()
        
        from PySide6.QtCore import QUrl
        self.media_player.setSource(QUrl.fromLocalFile(str(file_path)))
        self.media_player.play()
        
        # Start the timer for videos as well
        self.timer.start(self.display_duration)

    def next_item(self):
        if not self.files:
            return
            
        # Instead of cycling through, pick a random index
        self.current_index = random.randint(0, len(self.files) - 1)
        self.show_current_item()

    def previous_item(self):
        if not self.files:
            return
            
        # Also pick a random index for previous
        self.current_index = random.randint(0, len(self.files) - 1)
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
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = SlideshowApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()