import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QPushButton, QFileDialog, QWidget, QHBoxLayout, QFrame
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QSplitter, QAbstractItemView
from PyQt6.QtGui import QPixmap, QImageReader, QKeySequence, QColor, QIcon
from PyQt6.QtCore import Qt
import shutil

WIDTH = 1000
HEIGHT = 600

class ImageSorterApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.image_label = QLabel()
        self.image_list_widget = QListWidget()
        self.current_folder = None
        self.image_filenames = []
        self.current_index = 0
        
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        central_widget.setLayout(self.setup_central_widget())
        self.setCentralWidget(central_widget)
        self.image_list_widget.itemClicked.connect(self.list_item_clicked)
        self.setWindowTitle('Image Sorter')
        self.setWindowIcon(QIcon("assets/icon.png"))
        self.setGeometry(100, 100, WIDTH, HEIGHT)
        self.show_default_image()

    
    def setup_central_widget(self):
        layout = QHBoxLayout()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        

        left_layout = QVBoxLayout()
        
        self.image_label.setMinimumSize(640, 480)
        left_layout.addWidget(self.image_label)

        button_layout = QHBoxLayout()

        select_folder_button = QPushButton('Select Folder(S)', self)
        select_folder_button.clicked.connect(self.select_folder)
        button_layout.addWidget(select_folder_button)

        prev_button = QPushButton('Previous', self)
        prev_button.clicked.connect(self.show_previous_image)
        prev_button.setShortcut(QKeySequence(Qt.Key.Key_Left))
        button_layout.addWidget(prev_button)

        next_button = QPushButton('Next', self)
        next_button.clicked.connect(self.show_next_image)
        next_button.setShortcut(QKeySequence(Qt.Key.Key_Right))
        button_layout.addWidget(next_button)

        delete_button = QPushButton('Delete', self)
        delete_button.clicked.connect(self.delete_image)
        delete_button.setShortcut(QKeySequence(Qt.Key.Key_Delete))
        button_layout.addWidget(delete_button)
        
        left_layout.addLayout(button_layout)

        right_layout = QVBoxLayout()

        subdirectories = self.get_subdirectories('sortedimg')
        for i,subdir in enumerate(subdirectories):
            subdir_button = QPushButton(f"{subdir.title()} ({i})", self)
            subdir_button.clicked.connect(lambda checked, subdir=subdir: self.copy_to_subdirectory(subdir))
            subdir_button.setShortcut(f'{i}')
            right_layout.addWidget(subdir_button)

        right_layout.addWidget(QFrame(frameShape=QFrame.Shape.HLine))
        self.image_list_widget = QListWidget()
        self.image_list_widget.setStyleSheet("color: black;")
        self.image_list_widget.setAutoScroll(True)
        image_list_layout = QVBoxLayout()
        image_list_layout.addWidget(self.image_list_widget)
        right_layout.addLayout(image_list_layout)
        
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStyleSheet("QSplitter::handle { background-color: black; }")
        splitter.setSizes([int(splitter.size().width()*0.8), int(splitter.size().width()*0.2)])
        splitter.splitterMoved.connect(self.splitter_move)
        layout.addWidget(splitter)
        
        return layout


    def load_images_from_folder(self):
        if self.current_folder:
            image_files = [f for f in os.listdir(self.current_folder) if QImageReader.supportedImageFormats().__contains__(f.split('.')[-1])]
            self.image_filenames = [os.path.join(self.current_folder, f) for f in image_files]
            # Update the image list widget
            self.image_list_widget.clear()
            for image_file in self.image_filenames:
                item = QListWidgetItem(os.path.basename(image_file))
                self.image_list_widget.addItem(item)


    def get_subdirectories(self, directory):
        return [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]

    def show_default_image(self):
        default_image_path = 'assets/download.jpg'
        if os.path.exists(default_image_path):
            self.display_image(default_image_path)
        else:
            print(f"Default image '{default_image_path}' not found.")

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder_path:
            self.current_folder = folder_path
            self.load_images_from_folder()

            # Clear checkmarks in the list widget
            for i in range(self.image_list_widget.count()):
                item = self.image_list_widget.item(i)
                if item:
                    item.setCheckState(Qt.CheckState.Unchecked)

            # Load checked images from file            
            self.load_checked_images()

            # Find the index of the first unchecked image
            first_unchecked_index = self.find_first_unchecked_index()
            if first_unchecked_index is not None:
                self.show_image(first_unchecked_index)
                self.current_index = first_unchecked_index
            else:
                # If all images are checked, show the first image
                self.show_image(0)

    def find_first_unchecked_index(self):
        for i, image_file in enumerate(self.image_filenames):
            item = self.image_list_widget.item(i)
            if item and item.checkState() != Qt.CheckState.Checked:
                return i
        return None

    def list_item_clicked(self, item):
        index = self.image_list_widget.row(item)
        if index >= 0:
            self.current_index = index
            self.show_image(index)

    def load_checked_images(self):
        script_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        checked_images_file = os.path.join(script_dir, 'checked_images.txt')

        if os.path.exists(checked_images_file):
            with open(checked_images_file, 'r') as file:
                checked_images = [line.strip() for line in file]
               
                for i in range(self.image_list_widget.count()):
                    item = self.image_list_widget.item(i)
                    if item and self.image_filenames[i] in checked_images:
                        item.setCheckState(Qt.CheckState.Checked)

    def save_checked_images(self):
        script_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        checked_images_file = os.path.join(script_dir, 'checked_images.txt')

        # Read existing filenames from the file
        existing_filenames = set()
        if os.path.exists(checked_images_file):
            with open(checked_images_file, 'r') as file:
                existing_filenames = {line.strip() for line in file}

        current_item = self.image_list_widget.item(self.current_index)
        if current_item and current_item.checkState() == Qt.CheckState.Checked:
            current_filename = self.image_filenames[self.current_index]
            if current_filename not in existing_filenames:
                # Append the filename to the file only if it's not already present
                with open(checked_images_file, 'a') as file:
                    file.write(current_filename + '\n')

    def show_next_image(self):
        if self.image_filenames:
            # Get the current item in the list widget
            current_item = self.image_list_widget.item(self.current_index)
            if current_item:
                # Set checkmark for the current item
                current_item.setCheckState(Qt.CheckState.Checked)

            # Save checked images to file
            self.save_checked_images()

            # Move to the next image
            self.current_index = (self.current_index + 1) % len(self.image_filenames)
            self.show_image(self.current_index)
            


    def show_previous_image(self):
        if self.image_filenames:
            self.current_index = (self.current_index - 1) % len(self.image_filenames)
            self.show_image(self.current_index)

    def delete_image(self):
        try:
            deleted_filename = self.image_filenames[self.current_index]
            os.remove(deleted_filename)
            # Show the next image
            self.show_next_image()

            for i in range(self.image_list_widget.count()):
                item = self.image_list_widget.item(i)
                if item and item.text() == os.path.basename(deleted_filename):
                    item.setForeground(QColor(Qt.GlobalColor.red))

        except OSError as e:
            print(f"Error: {e.filename} - {e.strerror}")

    def show_image(self, index):
        if self.image_filenames:
            # Update the current index
            self.current_index = index

            # Display the image
            image_path = self.image_filenames[self.current_index]
            self.display_image(image_path)

            # Highlight the current file in the list
            for i in range(self.image_list_widget.count()):
                item = self.image_list_widget.item(i)
                if item:
                    item.setSelected(i == self.current_index)

            # Scroll to the current item in the list widget
            current_item = self.image_list_widget.item(self.current_index)
            if current_item:
                self.image_list_widget.scrollToItem(current_item, QAbstractItemView.ScrollHint.PositionAtCenter)

    def display_image(self, image_path):
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                self.image_label.setPixmap(pixmap)
                self.scale_image()
            else:
                # Handle the case where the image couldn't be loaded
                # print(f"Error: Unable to load image from {image_path}")
                self.show_deleted_image_placeholder()
        else:
            # Handle the case where the image file does not exist
            # print(f"Error: Image file not found at {image_path}")
            self.show_deleted_image_placeholder()

    def show_deleted_image_placeholder(self):
        # You can customize this function to display a placeholder or message
        placeholder_text = "Deleted Image"
        self.image_label.setText(placeholder_text)
        # Optionally, you can set the text color, font, etc. to make it stand out

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scale_image()
        
    def splitter_move(self, pos, index):
        self.scale_image()
        
    def scale_image(self):
        if not self.image_label.pixmap():
            return

        pixmap = self.image_label.pixmap()
        scaled_pixmap = pixmap.scaled(self.image_label.size(), aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
                                      transformMode=Qt.TransformationMode.SmoothTransformation)
        
        x_offset = int((self.image_label.width() - scaled_pixmap.width()) / 2)
        y_offset = int((self.image_label.height() - scaled_pixmap.height()) / 2)

        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setContentsMargins(x_offset, y_offset, x_offset, y_offset)

    def copy_to_subdirectory(self, subdir):
        if self.current_folder:
            current_image_path = self.image_filenames[self.current_index]
            destination_folder = os.path.join('sortedimg', subdir)

            # Create the destination folder if it doesn't exist
            os.makedirs(destination_folder, exist_ok=True)
            

            # Copy the image to the destination folder
            destination_path = os.path.join(destination_folder, os.path.basename(current_image_path))
            try:
                shutil.copy2(current_image_path, destination_path)
            except FileNotFoundError:
                pass

def main():
    app = QApplication(sys.argv)
    viewer = ImageSorterApp()
    viewer.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
