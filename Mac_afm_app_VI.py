#!/usr/bin/env python3

import subprocess
import queue
import numpy as np
from PyQt5.QtGui import QIcon, QCursor, QColor, QPalette, QFont
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QInputDialog, 
                             QFileDialog, QMainWindow, QAction, QLabel, QLineEdit, QHBoxLayout, 
                             QGroupBox, QMessageBox, QSlider, QMenu, QFrame)

# Import the modified modules for macOS
from mac_com_monitor import ComMonitorThread
from mac_serial_utils import full_port_name, enumerate_serial_ports, list_ports_info

# Matplotlib for plotting
import matplotlib
matplotlib.use('Qt5Agg')
matplotlib.rc('font', family='Optima')
matplotlib.rcParams['savefig.format'] = 'png'
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

# Import seaborn for ggplot-style visualization
import seaborn as sns
sns.set_theme(style="whitegrid")

# The Main Application Window
class AFMApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Main Window Setup
        self.setWindowTitle("DIY AFM Control on MacBook Pro MacOS 2025")
        self.setMinimumSize(1280, 800)
        
        # Font setup
        font = QFont("Optima")
        font.setStyleHint(QFont.Serif)
        QApplication.setFont(font)
        
        # Main widget setup with modern styling
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Set clean white background for the main widget
        self.main_widget.setStyleSheet("""
            background-color: #ffffff;
            color: #121212;
        """)
        
        # Modern button style - black rounded buttons with white text
        self.button_style = """
            QPushButton {
                background-color: #000000;
                color: white;
                border: none;
                padding: 14px 24px;
                border-radius: 25px;
                font-size: 16px;
                font-family: "Optima", "Segoe UI", "Helvetica Neue", sans-serif;
                min-width: 120px;
                text-align: center;
            }
            
            QPushButton:hover {
                background-color: #333333;
            }
    
            QPushButton:disabled {
                background-color: #666666;
                opacity: 0.6;
            }
        """
        
        # Frame style for panel sections
        self.panel_style = """
            QFrame {
                background-color: #f2f2f2;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """
        
        # Group box style for clean, modern look
        self.group_style = """
            QGroupBox {
                font-weight: 500;
                font-size: 16px;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                margin-top: 15px;
                background-color: #f2f2f2;
                padding: 15px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #121212;
            }
        """
        
        # Slider style
        self.slider_style = """
            QSlider::groove:horizontal {
                height: 8px;
                background: #f2f2f2;
                border-radius: 4px;
                border: 1px solid #e0e0e0;
            }
            
            QSlider::handle:horizontal {
                background: #000000;
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            
            QSlider::handle:horizontal:hover {
                background: #333333;
            }
        """
        
        # Label style
        self.label_style = """
            QLabel {
                font-size: 16px;
                color: #121212;
            }
        """
        
        # Application title
        self.title_label = QLabel("DIY AFM on MacBook Pro MacOS 15.3.1")
        self.title_label.setStyleSheet("""
            font-size: 28px;
            font-weight: 500;
            color: #121212;
            letter-spacing: -0.5px;
            margin-bottom: 10px;
        """)
        self.main_layout.addWidget(self.title_label)
        
        # Setup components
        self.setup_serial_connection()
        self.setup_scan_controls()
        self.setup_figure()
        self.setup_controls()
        
        # Initialize variables
        self.acquiring = False
        self.data = []
        
        # Show the window
        self.show()
        
    def setup_serial_connection(self):
        """Setup the serial connection controls in a modern panel"""
        serial_frame = QFrame()
        serial_frame.setStyleSheet(self.panel_style)
        serial_layout = QHBoxLayout(serial_frame)
        serial_layout.setContentsMargins(20, 20, 20, 20)
        serial_layout.setSpacing(15)
        
        # Status label
        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 500;
            padding: 8px 16px;
            border-radius: 25px;
            background-color: #f2f2f2;
            border: 1px solid #e0e0e0;
        """)
        serial_layout.addWidget(self.status_label)
        
        # Port selection
        port_label = QLabel("Port:")
        port_label.setStyleSheet(self.label_style)
        serial_layout.addWidget(port_label)
        
        self.port_combo = QPushButton("Select Port")
        self.port_combo.setStyleSheet(self.button_style)
        self.port_combo.clicked.connect(self.select_port)
        serial_layout.addWidget(self.port_combo)
        
        # Connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.setStyleSheet(self.button_style)
        self.connect_button.clicked.connect(self.toggle_connection)
        serial_layout.addWidget(self.connect_button)
        
        # Add stretch to push all elements to the left
        serial_layout.addStretch(1)
        
        self.main_layout.addWidget(serial_frame)
        
        # Initialize serial connection variables
        self.serial_connected = False
        self.com_monitor = None
        self.data_q = queue.Queue()
        self.error_q = queue.Queue()
        self.port = None
        
    def setup_scan_controls(self):
        """Setup AFM scan parameters controls with modern styling"""
        scan_frame = QFrame()
        scan_frame.setStyleSheet(self.panel_style)
        scan_layout = QHBoxLayout(scan_frame)
        scan_layout.setContentsMargins(20, 20, 20, 20)
        scan_layout.setSpacing(20)
        
        # Scan size
        size_label = QLabel("Scan Size (nm):")
        size_label.setStyleSheet(self.label_style)
        scan_layout.addWidget(size_label)
        
        self.scan_size_input = QLineEdit("1000")
        self.scan_size_input.setStyleSheet("""
            padding: 8px;
            border-radius: 5px;
            border: 1px solid #e0e0e0;
            background-color: white;
            font-size: 16px;
        """)
        self.scan_size_input.setFixedWidth(100)
        scan_layout.addWidget(self.scan_size_input)
        
        # Resolution
        res_label = QLabel("Resolution (pixels):")
        res_label.setStyleSheet(self.label_style)
        scan_layout.addWidget(res_label)
        
        self.resolution_input = QLineEdit("256")
        self.resolution_input.setStyleSheet("""
            padding: 8px;
            border-radius: 5px;
            border: 1px solid #e0e0e0;
            background-color: white;
            font-size: 16px;
        """)
        self.resolution_input.setFixedWidth(100)
        scan_layout.addWidget(self.resolution_input)
        
        # Scan speed with slider
        speed_label = QLabel("Scan Speed:")
        speed_label.setStyleSheet(self.label_style)
        scan_layout.addWidget(speed_label)
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 10)
        self.speed_slider.setValue(2)
        self.speed_slider.setStyleSheet(self.slider_style)
        self.speed_slider.setFixedWidth(150)
        scan_layout.addWidget(self.speed_slider)
        
        self.speed_value = QLabel("2 Hz")
        self.speed_value.setStyleSheet(self.label_style + "min-width: 60px;")
        self.speed_slider.valueChanged.connect(
            lambda v: self.speed_value.setText(f"{v} Hz"))
        scan_layout.addWidget(self.speed_value)
        
        # Set parameters button
        self.set_params_button = QPushButton("Set Parameters")
        self.set_params_button.setStyleSheet(self.button_style)
        self.set_params_button.clicked.connect(self.set_scan_parameters)
        scan_layout.addWidget(self.set_params_button)
        
        self.main_layout.addWidget(scan_frame)
        
    def setup_figure(self):
        """Setup the matplotlib figure with Seaborn styling for visualization"""
        figure_frame = QFrame()
        figure_frame.setStyleSheet(self.panel_style)
        figure_layout = QVBoxLayout(figure_frame)
        figure_layout.setContentsMargins(15, 15, 15, 15)
        
        # Figure title
        figure_title = QLabel("DIY AFM Data Visualisation")
        figure_title.setStyleSheet("""
            font-size: 18px;
            font-weight: 500;
            margin-bottom: 10px;
        """)
        figure_layout.addWidget(figure_title)
        
        # Create figure and canvas with Seaborn styling
        self.figure = Figure(figsize=(12, 6), dpi=100, facecolor='#f2f2f2')
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Style the toolbar
        self.toolbar.setStyleSheet("""
            background-color: white;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            margin-bottom: 10px;
        """)
        
        figure_layout.addWidget(self.toolbar)
        figure_layout.addWidget(self.canvas)
        
        # Setup the plots - topography as heatmap
        self.ax_topo = self.figure.add_subplot(121)
        self.ax_topo.set_title('Topography', fontsize=14, fontweight='medium')
        self.ax_topo.set_facecolor('#f8f8f8')
        # Using Seaborn color palette
        self.topo_image = self.ax_topo.imshow(np.zeros((10, 10)), 
                                             cmap=sns.color_palette("viridis", as_cmap=True),
                                             interpolation='nearest', aspect='equal')
        self.figure.colorbar(self.topo_image, ax=self.ax_topo, label='Height (nm)')
        
        # FES as line plot instead of image
        self.ax_fes = self.figure.add_subplot(122)
        self.ax_fes.set_title('Frequency Shift (FES)', fontsize=14, fontweight='medium')
        self.ax_fes.set_facecolor('#f8f8f8')
        # Initialize with empty data
        self.fes_line, = self.ax_fes.plot([], [], lw=2, color=sns.color_palette()[0])
        self.ax_fes.set_xlabel('Scan Position (pixels)')
        self.ax_fes.set_ylabel('Frequency Shift (Hz)')
        self.ax_fes.grid(False)
        
        self.figure.tight_layout()
        self.canvas.draw()
        
        self.main_layout.addWidget(figure_frame)
        
        # Initialize data arrays
        self.scan_size = (256, 256)  # Default scan size
        self.topo_data = np.zeros(self.scan_size)
        self.fes_data = np.zeros(self.scan_size)
        self.current_line = 0
        
        # Setup timer for updating the plot
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        
    def setup_controls(self):
        """Setup the control buttons with consistent styling"""
        controls_frame = QFrame()
        controls_frame.setStyleSheet(self.panel_style)
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(20, 20, 20, 20)
        controls_layout.setSpacing(15)
        
        # Start Acquisition Button
        self.start_button = QPushButton("Start Acquisition")
        self.start_button.setEnabled(False)
        self.start_button.setStyleSheet(self.button_style)
        self.start_button.clicked.connect(self.toggle_acquisition)
        controls_layout.addWidget(self.start_button)
        
        # Stop Acquisition Button
        self.stop_button = QPushButton("Stop Acquisition")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet(self.button_style)
        self.stop_button.clicked.connect(self.toggle_acquisition)
        controls_layout.addWidget(self.stop_button)
        
        # Clear Button
        self.clear_button = QPushButton("Clear Plot")
        self.clear_button.setStyleSheet(self.button_style)
        self.clear_button.clicked.connect(self.clear_plot)
        controls_layout.addWidget(self.clear_button)
        
        # Save Button
        self.save_button = QPushButton("Save Data")
        self.save_button.setStyleSheet(self.button_style)
        self.save_button.clicked.connect(self.save_data)
        controls_layout.addWidget(self.save_button)
        
        self.main_layout.addWidget(controls_frame)
        
    def select_port(self):
        """Select a serial port from available ports"""
        ports = enumerate_serial_ports()
        if not ports:
            QMessageBox.warning(self, "No Ports", "No serial ports found. Please connect your device.")
            return
        
        port, ok = QInputDialog.getItem(self, "Select Port", "Port:", ports, 0, False)
        if ok and port:
            self.port = port
            self.port_combo.setText(port)
            
    def toggle_connection(self):
        """Connect or disconnect from the serial port"""
        if not self.serial_connected:
            if not self.port:
                QMessageBox.warning(self, "No Port Selected", "Please select a serial port first.")
                return
            
            # Start serial monitor thread
            self.com_monitor = ComMonitorThread(self.data_q, self.error_q, self.port, port_baud=115200)
            self.com_monitor.start()
            
            # Update UI
            self.connect_button.setText("Disconnect")
            self.start_button.setEnabled(True)
            self.serial_connected = True
            self.status_label.setText("Status: Connected")
            self.status_label.setStyleSheet("""
                font-size: 16px;
                font-weight: 500;
                padding: 8px 16px;
                border-radius: 25px;
                background-color: #f0f8ff;
                border: 1px solid #4682B4;
                color: #4682B4;
            """)
        else:
            if self.com_monitor:
                # Fix for AttributeError - use close() method instead of stop()
                self.com_monitor.close()
                
            if self.acquiring:
                self.toggle_acquisition()
                
            # Update UI
            self.connect_button.setText("Connect")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.serial_connected = False
            self.status_label.setText("Status: Disconnected")
            self.status_label.setStyleSheet("""
                font-size: 16px;
                font-weight: 500;
                padding: 8px 16px;
                border-radius: 25px;
                background-color: #f2f2f2;
                border: 1px solid #e0e0e0;
                color: #121212;
            """)
            
    def toggle_acquisition(self):
        """Start or stop data acquisition"""
        if not self.acquiring:
            self.timer.start(100)  # Start updating the plot
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.acquiring = True
            self.status_label.setText("Status: Scanning")
            self.status_label.setStyleSheet("""
                font-size: 16px;
                font-weight: 500;
                padding: 8px 16px;
                border-radius: 25px;
                background-color: #f0fff0;
                border: 1px solid #2e8b57;
                color: #2e8b57;
            """)
        else:
            self.timer.stop()  # Stop updating the plot
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.acquiring = False
            self.status_label.setText("Status: Connected")
            self.status_label.setStyleSheet("""
                font-size: 16px;
                font-weight: 500;
                padding: 8px 16px;
                border-radius: 25px;
                background-color: #f0f8ff;
                border: 1px solid #4682B4;
                color: #4682B4;
            """)
            
    def set_scan_parameters(self):
        """Send scan parameters to the Stromline Nano controller"""
        if not self.serial_connected:
            QMessageBox.warning(self, "Not Connected", "Please connect to the controller first.")
            return
        
        try:
            # Get parameters from inputs
            scan_size = float(self.scan_size_input.text())
            resolution = int(self.resolution_input.text())
            scan_speed = self.speed_slider.value()
            
            # Reset data arrays
            self.scan_size = (resolution, resolution)
            self.topo_data = np.zeros(self.scan_size)
            self.fes_data = np.zeros(self.scan_size)
            self.current_line = 0
            
            # Reset axes for line plot
            self.ax_fes.set_xlim(0, resolution)
            self.ax_fes.set_ylim(-10, 10)  # Default range, will adjust dynamically
            
            # Send parameters to controller
            # Format command based on Stromline Nano specifications
            cmd = f"SCAN_PARAMS,{scan_size},{resolution},{scan_speed}\n"
            self.com_monitor.send_serial(cmd)
            
            QMessageBox.information(self, "Success", "Scan parameters set successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to set parameters: {str(e)}")
            
    def update_plot(self):
        """Update the AFM visualization with incoming data"""
        # Check for errors
        if not self.error_q.empty():
            error = self.error_q.get()
            QMessageBox.critical(self, "Error", f"Serial communication error: {error}")
            self.toggle_connection()
            return
        
        # Get data from queue
        data_updated = False
        while not self.data_q.empty():
            data, timestamp = self.data_q.get()
            try:
                # Parse data - expected format: x,y,topography,fes
                values = [float(v) for v in data.split(',')]
                x, y, topo, fes = int(values[0]), int(values[1]), values[2], values[3]
                
                # Update data arrays
                if x < self.scan_size[0] and y < self.scan_size[1]:
                    self.topo_data[y, x] = topo
                    self.fes_data[y, x] = fes
                    data_updated = True
                    
                    # Update current line for progress tracking
                    if y > self.current_line:
                        self.current_line = y
            except Exception as e:
                print(f"Error processing data: {e}")
                
        # Update visualizations if data has changed
        if data_updated:
            # Update topography heatmap
            self.topo_image.set_data(self.topo_data)
            self.topo_image.set_clim(np.min(self.topo_data), np.max(self.topo_data))
            
            # Update FES line plot - plot the current scan line
            if self.current_line < self.scan_size[1]:
                x_data = np.arange(self.scan_size[0])
                y_data = self.fes_data[self.current_line, :]
                
                # Remove NaN and zero values for better visualization
                valid_indices = ~np.isnan(y_data) & (y_data != 0)
                if np.any(valid_indices):
                    x_valid = x_data[valid_indices]
                    y_valid = y_data[valid_indices]
                    
                    # Update line data
                    self.fes_line.set_data(x_valid, y_valid)
                    
                    # Dynamically adjust y-axis limits if needed
                    if len(y_valid) > 0:
                        y_min, y_max = np.min(y_valid), np.max(y_valid)
                        # Add some padding
                        y_range = max(1, y_max - y_min)  # Ensure non-zero range
                        self.ax_fes.set_ylim(y_min - 0.1*y_range, y_max + 0.1*y_range)
                        
            # Redraw the canvas
            self.canvas.draw()
            
            # Check if scan is complete
            if self.current_line >= self.scan_size[1] - 1:
                QMessageBox.information(self, "Scan Complete", "AFM scan completed successfully.")
                self.toggle_acquisition()
                
    def clear_plot(self):
        """Clear the plot and data"""
        # Reset data arrays
        self.topo_data = np.zeros(self.scan_size)
        self.fes_data = np.zeros(self.scan_size)
        self.current_line = 0
        
        # Update the plots
        self.topo_image.set_data(self.topo_data)
        self.fes_line.set_data([], [])
        
        # Redraw the canvas
        self.canvas.draw()
        
        QMessageBox.information(self, "Plot Cleared", "Plot data has been cleared.")
        
    def save_data(self):
        """Save the AFM data to files"""
        if np.all(self.topo_data == 0) and np.all(self.fes_data == 0):
            QMessageBox.warning(self, "No Data", "There is no scan data available to save.")
            return
        
        try:
            # Save dialog
            base_filename, _ = QFileDialog.getSaveFileName(
                self, "Save AFM Data", "", "NumPy Files (*.npy);;CSV Files (*.csv);;All Files (*)"
            )
            
            if not base_filename:
                return
            
            # Save topography data
            topo_filename = f"{base_filename}_topography"
            if base_filename.endswith('.npy'):
                np.save(topo_filename, self.topo_data)
            else:
                np.savetxt(f"{topo_filename}.csv", self.topo_data, delimiter=',')
                
            # Save frequency shift data
            fes_filename = f"{base_filename}_fes"
            if base_filename.endswith('.npy'):
                np.save(fes_filename, self.fes_data)
            else:
                np.savetxt(f"{fes_filename}.csv", self.fes_data, delimiter=',')
                
            # Save the image figures with Seaborn styling
            with sns.plotting_context("paper", font_scale=1.2):
                self.figure.savefig(f"{base_filename}_image.png", dpi=300, bbox_inches='tight')
                
            QMessageBox.information(self, "Success", f"AFM data saved successfully.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save data: {str(e)}")
            
if __name__ == '__main__':
    app = QApplication([])
    app.setStyle('Fusion')  # Use Fusion style for a more modern look
    window = AFMApp()
    app.exec_()