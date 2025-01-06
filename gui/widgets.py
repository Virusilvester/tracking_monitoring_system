# File: gui/widgets.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, 
                               QListWidget, QFileDialog, QProgressBar, QLineEdit, QCheckBox)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent
import shutil
import os
import time
from PySide6.QtWidgets import QApplication
import yaml
from pathlib import Path
import torch
from lib.yolov5 import train as yolo_train
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class AlertWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        # Alert list
        self.alert_list = QListWidget()
        self.alert_list.setStyleSheet("background-color: #2a2a2a; color: white; border: none;")
        layout.addWidget(self.alert_list)
        
        # Email notification settings
        email_group = QVBoxLayout()
        email_group.addWidget(QLabel("Email Notification Settings"))
        
        # Email toggle
        self.email_toggle = QCheckBox("Enable Email Notifications")
        email_group.addWidget(self.email_toggle)
        
        # Email settings
        self.email_settings = {
            'recipient': QLineEdit(),
            'smtp_server': QLineEdit(),
            'port': QSpinBox(),
            'sender_email': QLineEdit(),
            'sender_password': QLineEdit()
        }
        
        # Configure widgets
        self.email_settings['port'].setRange(1, 65535)
        self.email_settings['port'].setValue(587)  # Default SMTP port
        self.email_settings['sender_password'].setEchoMode(QLineEdit.Password)
        
        # Add widgets to layout
        for label, widget in [
            ("Recipient Email:", self.email_settings['recipient']),
            ("SMTP Server:", self.email_settings['smtp_server']),
            ("Port:", self.email_settings['port']),
            ("Sender Email:", self.email_settings['sender_email']),
            ("Password:", self.email_settings['sender_password'])
        ]:
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            row.addWidget(widget)
            email_group.addLayout(row)
        
        # Save button
        self.save_email_button = QPushButton("Save Email Settings")
        self.save_email_button.clicked.connect(self.save_email_settings)
        email_group.addWidget(self.save_email_button)
        
        layout.addLayout(email_group)
        self.setLayout(layout)
        
        # Load existing email settings
        self.load_email_settings()

    def save_email_settings(self):
        """Save email settings to config file"""
        config = {
            'enabled': self.email_toggle.isChecked(),
            'recipient_email': self.email_settings['recipient'].text(),
            'smtp_server': self.email_settings['smtp_server'].text(),
            'port': self.email_settings['port'].value(),
            'sender_email': self.email_settings['sender_email'].text(),
            'sender_password': self.email_settings['sender_password'].text()
        }
        
        config_path = Path('configs/email_config.yaml')
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        self.add_alert("Email settings saved successfully")

    def load_email_settings(self):
        """Load email settings from config file"""
        config_path = Path('configs/email_config.yaml')
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            self.email_toggle.setChecked(config.get('enabled', False))
            self.email_settings['recipient'].setText(config.get('recipient_email', ''))
            self.email_settings['smtp_server'].setText(config.get('smtp_server', ''))
            self.email_settings['port'].setValue(config.get('port', 587))
            self.email_settings['sender_email'].setText(config.get('sender_email', ''))
            self.email_settings['sender_password'].setText(config.get('sender_password', ''))

    def add_alert(self, message):
        """Add an alert to the list"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        alert_item = f"[{timestamp}] {message}"
        self.alert_list.addItem(alert_item)
        self.alert_list.scrollToBottom()
        
        # Send email for gun detection, person with phone alerts, or anomalies if enabled
        if self.email_toggle.isChecked() and (
            "gun detected" in message.lower() or 
            "person with cell phone detected" in message.lower() or
            "anomaly detected" in message.lower()
        ):
            self.send_email_alert(message)

    def send_email_alert(self, message):
        """Send an email alert"""
        config_path = Path('configs/email_config.yaml')
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            recipient_email = config.get('recipient_email', '')
            smtp_server = config.get('smtp_server', '')
            port = config.get('port', 587)
            sender_email = config.get('sender_email', '')
            sender_password = config.get('sender_password', '')
            
            if recipient_email and smtp_server and sender_email and sender_password:
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = recipient_email
                
                # Set subject based on alert type
                if "gun detected" in message.lower():
                    msg['Subject'] = 'Gun Detection Alert'
                elif "person with cell phone detected" in message.lower():
                    msg['Subject'] = 'Person with Cell Phone Alert'
                elif "anomaly detected" in message.lower():
                    msg['Subject'] = 'Anomaly Detection Alert'
                else:
                    msg['Subject'] = 'Security Alert'
                
                body = f"SECURITY ALERT\n\nTime: {time.strftime('%Y-%m-%d %H:%M:%S')}\nAlert: {message}"
                msg.attach(MIMEText(body, 'plain'))
                
                server = smtplib.SMTP(smtp_server, port)
                server.starttls()
                server.login(sender_email, sender_password)
                text = msg.as_string()
                server.sendmail(sender_email, recipient_email, text)
                server.quit()
                
                self.add_alert("Email alert sent successfully")
            else:
                self.add_alert("Email alert failed: incomplete email settings")

    def add_anomaly_alert(self, anomaly_type, details=None):
        """Add an anomaly alert with specific type and details"""
        message = f"Anomaly detected: {anomaly_type}"
        if details:
            message += f" - {details}"
        self.add_alert(message)

class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        # Camera Settings
        camera_group = QVBoxLayout()
        camera_group.addWidget(QLabel("Camera Settings"))
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["640x480", "1280x720", "1920x1080"])
        camera_group.addWidget(QLabel("Resolution:"))
        camera_group.addWidget(self.resolution_combo)
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(1, 60)
        self.fps_spinbox.setValue(30)
        camera_group.addWidget(QLabel("FPS:"))
        camera_group.addWidget(self.fps_spinbox)

        # Camera Source
        self.source_combo = QComboBox()
        self.source_combo.addItems([
            "Webcam (0)", "Image File", "Video File", "Screenshot", 
            "Directory", "Image List", "Stream List", "Glob Pattern",
            "YouTube URL", "RTSP/RTMP/HTTP Stream"
        ])
        camera_group.addWidget(QLabel("Camera Source:"))
        camera_group.addWidget(self.source_combo)

        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Enter source path or URL")
        camera_group.addWidget(self.source_input)

        self.source_combo.currentIndexChanged.connect(self.update_source_input_placeholder)
        layout.addLayout(camera_group)

        # Model Settings
        model_group = QVBoxLayout()
        model_group.addWidget(QLabel("Model Settings"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["YOLOv5", "SSD", "Faster R-CNN"])
        model_group.addWidget(QLabel("Detection Model:"))
        model_group.addWidget(self.model_combo)
        self.confidence_spinbox = QDoubleSpinBox()
        self.confidence_spinbox.setRange(0.1, 1.0)
        self.confidence_spinbox.setValue(0.5)
        self.confidence_spinbox.setSingleStep(0.1)
        model_group.addWidget(QLabel("Confidence Threshold:"))
        model_group.addWidget(self.confidence_spinbox)
        layout.addLayout(model_group)

        # Apply Button
        self.apply_button = QPushButton("Apply Settings")
        layout.addWidget(self.apply_button)

        self.setLayout(layout)

    def update_source_input_placeholder(self, index):
        placeholders = [
            "Enter device number (e.g., 0 for webcam)",
            "Enter image file path",
            "Enter video file path",
            "Type 'screen' for screenshot",
            "Enter directory path",
            "Enter path to list of images",
            "Enter path to list of streams",
            "Enter glob pattern (e.g., 'path/*.jpg')",
            "Enter YouTube URL",
            "Enter RTSP, RTMP, or HTTP stream URL"
        ]
        self.source_input.setPlaceholderText(placeholders[index])

class TrainingWidget(QWidget):
    training_started = Signal(str)
    training_progress = Signal(int, dict)  # Progress percentage and metrics
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        
        layout = QVBoxLayout()
        
        # Training Settings Group
        settings_group = QVBoxLayout()
        settings_group.addWidget(QLabel("Training Settings"))
        
        # Model settings
        model_layout = QHBoxLayout()
        self.weights_input = QLineEdit()
        self.weights_input.setPlaceholderText("Path to initial weights (e.g., yolov5s.pt)")
        self.weights_browse = QPushButton("Browse")
        self.weights_browse.clicked.connect(self.browse_weights)
        model_layout.addWidget(QLabel("Weights:"))
        model_layout.addWidget(self.weights_input)
        model_layout.addWidget(self.weights_browse)
        settings_group.addLayout(model_layout)
        
        # Training parameters
        params_layout = QHBoxLayout()
        
        # Epochs
        self.epochs_spin = QSpinBox()
        self.epochs_spin.setRange(1, 1000)
        self.epochs_spin.setValue(100)
        params_layout.addWidget(QLabel("Epochs:"))
        params_layout.addWidget(self.epochs_spin)
        
        # Batch size
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 128)
        self.batch_size_spin.setValue(16)
        params_layout.addWidget(QLabel("Batch Size:"))
        params_layout.addWidget(self.batch_size_spin)
        
        # Image size
        self.img_size_spin = QSpinBox()
        self.img_size_spin.setRange(320, 1280)
        self.img_size_spin.setValue(640)
        self.img_size_spin.setSingleStep(32)
        params_layout.addWidget(QLabel("Image Size:"))
        params_layout.addWidget(self.img_size_spin)
        
        settings_group.addLayout(params_layout)
        
        # Advanced options
        advanced_layout = QHBoxLayout()
        
        self.cache_combo = QComboBox()
        self.cache_combo.addItems(["No Cache", "RAM", "Disk"])
        advanced_layout.addWidget(QLabel("Cache:"))
        advanced_layout.addWidget(self.cache_combo)
        
        self.device_input = QLineEdit()
        self.device_input.setPlaceholderText("cuda device (e.g., 0 or 0,1,2,3)")
        advanced_layout.addWidget(QLabel("Device:"))
        advanced_layout.addWidget(self.device_input)
        
        settings_group.addLayout(advanced_layout)
        
        # Checkboxes for additional options
        options_layout = QHBoxLayout()
        self.rect_check = QCheckBox("Rectangular")
        self.multi_scale_check = QCheckBox("Multi-Scale")
        self.sync_bn_check = QCheckBox("Sync BatchNorm")
        options_layout.addWidget(self.rect_check)
        options_layout.addWidget(self.multi_scale_check)
        options_layout.addWidget(self.sync_bn_check)
        settings_group.addLayout(options_layout)
        
        layout.addLayout(settings_group)
        
        # Existing drag and drop area
        self.drop_label = QLabel("Drag and drop training data folder here")
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setStyleSheet("""
            background-color: #2a2a2a;
            border: 2px dashed #3a3a3a;
            padding: 20px;
            font-size: 16px;
        """)
        layout.addWidget(self.drop_label)
        
        # Training data list
        self.data_list = QListWidget()
        self.data_list.setStyleSheet("background-color: #2a2a2a; color: white; border: none;")
        layout.addWidget(self.data_list)
        
        # Training controls
        controls_layout = QHBoxLayout()
        self.train_button = QPushButton("Start Training")
        self.train_button.clicked.connect(self.start_training)
        controls_layout.addWidget(self.train_button)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        controls_layout.addWidget(self.progress_bar)
        
        layout.addLayout(controls_layout)
        
        self.setLayout(layout)
        
    def browse_weights(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Weights File", "", "Weight Files (*.pt);;All Files (*.*)"
        )
        if file_name:
            self.weights_input.setText(file_name)
    
    def prepare_training_config(self):
        """Prepare training configuration from GUI settings"""
        # Create data configuration
        data_yaml = {
            'path': str(Path.cwd() / 'training_data'),
            'train': 'images/train',
            'val': 'images/val',
            'test': 'images/test',
            'nc': 1,  # number of classes (modify based on your dataset)
            'names': ['object']  # class names (modify based on your dataset)
        }
        
        # Save data configuration
        data_path = Path.cwd() / 'training_data' / 'data.yaml'
        with open(data_path, 'w') as f:
            yaml.dump(data_yaml, f)
        
        # Prepare training options
        opt = yolo_train.parse_opt(True)
        opt.weights = self.weights_input.text() or 'yolov5s.pt'
        opt.data = str(data_path)
        opt.epochs = self.epochs_spin.value()
        opt.batch_size = self.batch_size_spin.value()
        opt.imgsz = self.img_size_spin.value()
        opt.rect = self.rect_check.isChecked()
        opt.multi_scale = self.multi_scale_check.isChecked()
        opt.sync_bn = self.sync_bn_check.isChecked()
        
        # Handle cache setting
        cache_setting = self.cache_combo.currentText().lower()
        opt.cache = cache_setting if cache_setting != "no cache" else None
        
        # Handle device setting
        opt.device = self.device_input.text() or ''
        
        return opt
    
    def start_training(self):
        """Start the training process"""
        if not Path('training_data').exists():
            self.training_started.emit("No training data available!")
            return
        
        try:
            opt = self.prepare_training_config()
            self.training_started.emit(f"Starting training with {opt.weights}")
            self.train_button.setEnabled(False)
            
            # Create a custom callback to update progress
            class ProgressCallback:
                def __init__(self, widget):
                    self.widget = widget
                
                def on_train_epoch_end(self, epoch, epochs):
                    progress = int((epoch + 1) / epochs * 100)
                    self.widget.progress_bar.setValue(progress)
                    QApplication.processEvents()
            
            # Start training
            callbacks = ProgressCallback(self)
            results = yolo_train.train(opt.hyp, opt, torch.device(opt.device), callbacks)
            
            self.training_started.emit("Training completed!")
            
        except Exception as e:
            self.training_started.emit(f"Training error: {str(e)}")
        finally:
            self.train_button.setEnabled(True)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isdir(file_path):
                self.copy_training_data(file_path)
    
    def copy_training_data(self, source_dir):
        target_dir = os.path.join(os.getcwd(), "training_data")
        os.makedirs(target_dir, exist_ok=True)
        
        try:
            shutil.copytree(source_dir, os.path.join(target_dir, os.path.basename(source_dir)))
            self.update_data_list()
        except Exception as e:
            print(f"Error copying training data: {e}")
    
    def update_data_list(self):
        self.data_list.clear()
        target_dir = os.path.join(os.getcwd(), "training_data")
        for item in os.listdir(target_dir):
            self.data_list.addItem(item)
