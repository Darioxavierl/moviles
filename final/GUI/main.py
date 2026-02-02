"""
GUI Main Application - UAV 5G NR Simulation Suite
Ventana principal con control panels, configuración y visualización 3D
"""
import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QSplitter, QTabWidget, QTextEdit, 
                            QPushButton, QGroupBox, QGridLayout, QLabel,
                            QScrollArea, QProgressBar, QStatusBar, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QPixmap, QFont, QPalette, QColor

# Matplotlib imports for interactive plots
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class SimulationWorker(QThread):
    """Worker thread para ejecutar simulaciones sin bloquear GUI"""
    finished = pyqtSignal(dict)
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, simulation_type, parameters):
        super().__init__()
        self.simulation_type = simulation_type
        self.parameters = parameters
    
    def run(self):
        """Ejecutar simulación en thread separado"""
        try:
            self.progress.emit(f"Iniciando simulación: {self.simulation_type}")
            
            if self.simulation_type == "mimo_beamforming":
                result = self.run_mimo_simulation()
            elif self.simulation_type == "height_analysis":
                result = self.run_height_simulation()
            elif self.simulation_type == "coverage_analysis":
                result = self.run_coverage_simulation()
            elif self.simulation_type == "mobility_analysis":
                result = self.run_mobility_simulation()
            elif self.simulation_type == "interference_analysis":
                result = self.run_interference_simulation()
            else:
                raise ValueError(f"Tipo de simulación no soportado: {self.simulation_type}")
            
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(f"Error en simulación: {str(e)}")

    def run_mimo_simulation(self):
        """Simulación MIMO real integrada"""
        
        # Import MIMO analysis
        try:
            from analysis.mimo_beamforming_gui import run_mimo_analysis_gui
            
            # Crear directorio outputs si no existe
            output_dir = os.path.join(os.path.dirname(__file__), "outputs")
            os.makedirs(output_dir, exist_ok=True)
            
            # Ejecutar análisis real
            result = run_mimo_analysis_gui(
                output_dir=output_dir, 
                progress_callback=lambda msg: self.progress.emit(msg)
            )
            
            return result
            
        except Exception as e:
            self.error.emit(f"Error en análisis MIMO: {str(e)}")
            return None

    def run_height_simulation(self):
        """Simulación de altura real integrada"""
        
        # Import height analysis
        try:
            from analysis.height_analysis_gui import run_height_analysis_gui
            
            # Crear directorio outputs si no existe
            output_dir = os.path.join(os.path.dirname(__file__), "outputs")
            os.makedirs(output_dir, exist_ok=True)
            
            # Ejecutar análisis real
            result = run_height_analysis_gui(
                output_dir=output_dir, 
                progress_callback=lambda msg: self.progress.emit(msg)
            )
            
            return result
            
        except Exception as e:
            self.error.emit(f"Error en análisis de altura: {str(e)}")
            return None

    def run_coverage_simulation(self):
        """Simulación de cobertura real integrada"""
        
        # Import coverage analysis
        try:
            from analysis.coverage_analysis_gui import run_coverage_analysis_gui
            
            # Crear directorio outputs si no existe
            output_dir = os.path.join(os.path.dirname(__file__), "outputs")
            os.makedirs(output_dir, exist_ok=True)
            
            # Ejecutar análisis real
            result = run_coverage_analysis_gui(
                output_dir=output_dir, 
                progress_callback=lambda msg: self.progress.emit(msg)
            )
            
            return result
            
        except Exception as e:
            self.error.emit(f"Error en análisis de cobertura: {str(e)}")
            return None

    def run_mobility_simulation(self):
        """Simulación de movilidad real integrada"""
        
        # Import mobility analysis
        try:
            from analysis.mobility_analysis_gui import run_mobility_analysis_gui
            
            # Crear directorio outputs si no existe
            output_dir = os.path.join(os.path.dirname(__file__), "outputs")
            os.makedirs(output_dir, exist_ok=True)
            
            # Ejecutar análisis real
            result = run_mobility_analysis_gui(
                output_dir=output_dir, 
                progress_callback=lambda msg: self.progress.emit(msg)
            )
            
            return result
            
        except Exception as e:
            self.error.emit(f"Error en análisis de movilidad: {str(e)}")
            return None

    def run_interference_simulation(self):
        """Simulación de interferencia real integrada"""
        
        # Import interference analysis
        try:
            from analysis.interference_analysis_gui import run_interference_analysis_gui
            
            # Crear directorio outputs si no existe
            output_dir = os.path.join(os.path.dirname(__file__), "outputs")
            os.makedirs(output_dir, exist_ok=True)
            
            # Ejecutar análisis real
            result = run_interference_analysis_gui(
                output_dir=output_dir, 
                progress_callback=lambda msg: self.progress.emit(msg)
            )
            
            return result
            
        except Exception as e:
            self.error.emit(f"Error en análisis de interferencia: {str(e)}")
            return None


class ControlPanel(QWidget):
    """Panel de control con botones para cada simulación"""
    
    simulation_requested = pyqtSignal(str, dict)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("🚀 Simulaciones UAV 5G NR")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Botones simulaciones
        self.create_simulation_buttons(layout)
        
        # Botones utilidades
        layout.addSpacing(20)
        self.create_utility_buttons(layout)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def create_simulation_buttons(self, layout):
        """Crear botones para cada tipo de simulación"""
        
        simulations_group = QGroupBox("Análisis Disponibles")
        sim_layout = QVBoxLayout()
        
        # MIMO Beamforming
        mimo_btn = QPushButton("MIMO Masivo + Beamforming")
        mimo_btn.setMinimumHeight(50)
        mimo_btn.clicked.connect(lambda: self.request_simulation("mimo_beamforming"))
        mimo_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        sim_layout.addWidget(mimo_btn)
        
        # Height Analysis (ACTIVO)
        height_btn = QPushButton("Analisis de Altura")
        height_btn.setMinimumHeight(50)
        height_btn.setEnabled(True)  # Ahora habilitado
        height_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        height_btn.clicked.connect(lambda: self.simulation_requested.emit("height_analysis", {}))
        sim_layout.addWidget(height_btn)
        
        # Coverage Analysis (ACTIVO)
        coverage_btn = QPushButton("Analisis de Cobertura")
        coverage_btn.setMinimumHeight(50)
        coverage_btn.setEnabled(True)  # Ahora habilitado
        coverage_btn.setStyleSheet("""
            QPushButton {
                background-color: #16a085;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138d75;
            }
        """)
        coverage_btn.clicked.connect(lambda: self.simulation_requested.emit("coverage_analysis", {}))
        sim_layout.addWidget(coverage_btn)
        
        # Mobility Analysis (ACTIVO)
        mobility_btn = QPushButton("Analisis de Movilidad")
        mobility_btn.setMinimumHeight(50)
        mobility_btn.setEnabled(True)  # Ahora habilitado
        mobility_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9b59b6;
            }
        """)
        mobility_btn.clicked.connect(lambda: self.simulation_requested.emit("mobility_analysis", {}))
        sim_layout.addWidget(mobility_btn)
        
        # Interference Analysis (ACTIVO)
        interference_btn = QPushButton("Analisis Interferencia")
        interference_btn.setMinimumHeight(50)
        interference_btn.setEnabled(True)  # Ahora habilitado
        interference_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        interference_btn.clicked.connect(lambda: self.simulation_requested.emit("interference_analysis", {}))
        sim_layout.addWidget(interference_btn)
        
        simulations_group.setLayout(sim_layout)
        layout.addWidget(simulations_group)
    
    def create_utility_buttons(self, layout):
        """Crear botones de utilidades"""
        
        utils_group = QGroupBox("Utilidades")
        utils_layout = QVBoxLayout()
        
        # Clear outputs
        clear_btn = QPushButton("Limpiar Resultados")
        clear_btn.clicked.connect(self.clear_outputs)
        utils_layout.addWidget(clear_btn)
        
        # Load config
        load_btn = QPushButton("Cargar Configuracion")
        load_btn.clicked.connect(self.load_config)
        utils_layout.addWidget(load_btn)
        
        # Save config
        save_btn = QPushButton("Guardar Configuracion")
        save_btn.clicked.connect(self.save_config)
        utils_layout.addWidget(save_btn)
        
        utils_group.setLayout(utils_layout)
        layout.addWidget(utils_group)
    
    def request_simulation(self, sim_type):
        """Solicitar ejecución de simulación"""
        parameters = {}  # Por ahora parámetros por defecto
        self.simulation_requested.emit(sim_type, parameters)
    
    def clear_outputs(self):
        """Limpiar directorio de outputs"""
        print("Limpiando outputs...")
        
        import os
        import shutil
        from PyQt6.QtWidgets import QMessageBox
        
        try:
            # Directorios a limpiar
            output_dirs = [
                'test_outputs',
                'test_viz', 
                'outputs',
                'results',
                'plots'
            ]
            
            cleaned_count = 0
            for output_dir in output_dirs:
                if os.path.exists(output_dir):
                    # Limpiar contenido del directorio pero mantener el directorio
                    for filename in os.listdir(output_dir):
                        file_path = os.path.join(output_dir, filename)
                        try:
                            if os.path.isfile(file_path) or os.path.islink(file_path):
                                os.unlink(file_path)
                                cleaned_count += 1
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                                cleaned_count += 1
                        except Exception as e:
                            print(f"Error eliminando {file_path}: {e}")
            
            # Mostrar mensaje de confirmación
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Limpieza Completa")
            msg.setText(f"Resultados limpiados exitosamente.\n\nArchivos eliminados: {cleaned_count}")
            msg.exec()
            
            print(f"Limpieza completada: {cleaned_count} archivos eliminados")
            
        except Exception as e:
            # Mostrar mensaje de error
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Error en Limpieza")
            msg.setText(f"Error durante la limpieza:\n{str(e)}")
            msg.exec()
            print(f"Error en clear_outputs: {e}")
    
    def load_config(self):
        """Cargar configuración personalizada"""
        print("Cargando configuración...")
        
        import json
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        
        try:
            # Abrir diálogo para seleccionar archivo de configuración
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar Archivo de Configuración",
                "",
                "Archivos JSON (*.json);;Archivos de Configuración (*.cfg *.conf);;Todos los archivos (*)"
            )
            
            if file_path:
                # Intentar cargar configuración JSON
                if file_path.endswith('.json'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    
                    # Aplicar configuración cargada
                    self.apply_loaded_config(config_data)
                    
                    # Mostrar mensaje de éxito
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Icon.Information)
                    msg.setWindowTitle("Configuración Cargada")
                    msg.setText(f"Configuración cargada exitosamente desde:\n{file_path}\n\nParametros aplicados: {len(config_data)} elementos")
                    msg.exec()
                    
                    print(f"Configuración cargada desde: {file_path}")
                    
                else:
                    # Para archivos .cfg o .conf, cargar como texto plano
                    with open(file_path, 'r', encoding='utf-8') as f:
                        config_text = f.read()
                    
                    # Mostrar configuración cargada
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Icon.Information) 
                    msg.setWindowTitle("Configuración Cargada")
                    msg.setText(f"Archivo de configuración cargado:\n{file_path}\n\nContenido mostrado en la consola.")
                    msg.exec()
                    
                    print(f"Configuración desde {file_path}:\n{config_text}")
        
        except json.JSONDecodeError as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Error de Formato")
            msg.setText(f"Error al leer el archivo JSON:\n{str(e)}")
            msg.exec()
            print(f"Error JSON: {e}")
            
        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Error de Carga")
            msg.setText(f"Error al cargar configuración:\n{str(e)}")
            msg.exec()
            print(f"Error en load_config: {e}")
    
    def apply_loaded_config(self, config_data):
        """Aplicar configuración cargada al sistema"""
        try:
            # Aquí se puede aplicar la configuración a los módulos del sistema
            print("Aplicando configuración cargada:")
            
            # Ejemplo de configuraciones que se pueden aplicar:
            if 'frequency' in config_data:
                print(f"  - Frecuencia: {config_data['frequency']} Hz")
            
            if 'power' in config_data:
                print(f"  - Potencia: {config_data['power']} dBm")
                
            if 'uav_position' in config_data:
                print(f"  - Posición UAV: {config_data['uav_position']}")
                
            if 'gnb_position' in config_data:
                print(f"  - Posición gNB: {config_data['gnb_position']}")
                
            if 'antenna_config' in config_data:
                print(f"  - Configuración antena: {config_data['antenna_config']}")
            
            # Actualizar panel de configuración si existe
            if hasattr(self, 'config_panel'):
                self.config_panel.update_config_display()
                
        except Exception as e:
            print(f"Error aplicando configuración: {e}")
    
    def save_config(self):
        """Guardar configuración actual del sistema"""
        print("Guardando configuración...")
        
        import json
        from datetime import datetime
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        
        try:
            # Crear configuración actual del sistema
            current_config = {
                "timestamp": datetime.now().isoformat(),
                "system_info": {
                    "version": "UAV 5G NR Analysis GUI v1.0",
                    "scenario": "Munich 3D Urban"
                },
                "rf_config": {
                    "frequency": "3.5e9",  # Hz
                    "bandwidth": "100e6",  # Hz
                    "tx_power": "30",      # dBm
                    "noise_figure": "7"    # dB
                },
                "positions": {
                    "gnb_position": [300, 200, 50],   # [x, y, z] metros - sobre edificio
                    "uav1_position": [100, 100, 50] # [x, y, z] metros
                },
                "antenna_config": {
                    "gnb_array": {
                        "num_rows": 16,
                        "num_cols": 16,
                        "element_spacing": 0.5,
                        "polarization": "dual"
                    },
                    "uav_array": {
                        "num_rows": 2,
                        "num_cols": 2,
                        "element_spacing": 0.5,
                        "polarization": "single"
                    }
                },
                "simulation_settings": {
                    "num_realizations": 100,
                    "max_reflection_order": 3,
                    "enable_los": True,
                    "enable_nlos": True
                }
            }
            
            # Abrir diálogo para guardar archivo
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar Configuración",
                f"config_uav_5g_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "Archivos JSON (*.json);;Todos los archivos (*)"
            )
            
            if file_path:
                # Guardar configuración en formato JSON
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(current_config, f, indent=4, ensure_ascii=False)
                
                # Mostrar mensaje de éxito
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("Configuración Guardada")
                msg.setText(f"Configuración guardada exitosamente en:\n{file_path}\n\nParámetros guardados: {len(current_config)} secciones")
                msg.exec()
                
                print(f"Configuración guardada en: {file_path}")
                
        except Exception as e:
            # Mostrar mensaje de error
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Error al Guardar")
            msg.setText(f"Error al guardar configuración:\n{str(e)}")
            msg.exec()
            print(f"Error en save_config: {e}")


class ConfigPanel(QWidget):
    """Panel para mostrar configuración actual del sistema"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_default_config()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("Configuración del Sistema")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Área de configuración
        self.config_text = QTextEdit()
        self.config_text.setReadOnly(True)
        self.config_text.setMaximumHeight(400)
        layout.addWidget(self.config_text)
        
        self.setLayout(layout)
    
    def load_default_config(self):
        """Cargar configuración por defecto"""
        default_config = {
            "System": {
                "Frequency": "3.5 GHz",
                "Bandwidth": "100 MHz",
                "Scenario": "Munich 3D Urban"
            },
            "MIMO": {
                "gNB_Antennas": "256 (16x16)",
                "UAV_Antennas": "4",
                "Beamforming": "SVD"
            },
            "UAVs": {
                "Count": "4",
                "Height_Range": "50-200m",
                "Mobility": "Dynamic trajectories"
            }
        }
        
        self.update_config_display(default_config)
    
    def update_config_display(self, config):
        """Actualizar display de configuración"""
        config_text = "CONFIGURACION ACTUAL\n"
        config_text += "=" * 40 + "\n\n"
        
        for section, params in config.items():
            config_text += f"{section}:\n"
            for key, value in params.items():
                config_text += f"  • {key.replace('_', ' ')}: {value}\n"
            config_text += "\n"
        
        self.config_text.setText(config_text)


class ResultsTabWidget(QTabWidget):
    """Widget con tabs para mostrar resultados: Gráficos + 3D Scene"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        # Tab 1: Gráficos de resultados
        self.graphs_tab = QWidget()
        self.init_graphs_tab()
        self.addTab(self.graphs_tab, "Graficos")
        
        # Tab 2: Escena 3D
        self.scene3d_tab = QWidget()
        self.init_scene3d_tab()
        self.addTab(self.scene3d_tab, "Escena 3D")
    
    def init_graphs_tab(self):
        """Inicializar tab de gráficos con matplotlib canvas interactivo"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Crear figura de matplotlib
        self.graphs_figure = Figure(figsize=(14, 10), facecolor='white')
        self.graphs_canvas = FigureCanvas(self.graphs_figure)
        self.graphs_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Toolbar de navegación (zoom, pan, etc.)
        self.graphs_toolbar = NavigationToolbar(self.graphs_canvas, self)
        self.graphs_toolbar.setStyleSheet("""
            QToolBar {
                background-color: #404040;
                border: 1px solid #555555;
                spacing: 2px;
            }
            QToolButton {
                background-color: #505050;
                color: white;
                border: 1px solid #666666;
                border-radius: 3px;
                padding: 5px;
                margin: 1px;
            }
            QToolButton:hover {
                background-color: #606060;
            }
        """)
        
        # Área scrolleable para múltiples gráficos
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.graphs_layout = QVBoxLayout(scroll_widget)
        self.graphs_layout.setContentsMargins(10, 10, 10, 10)
        self.graphs_layout.setSpacing(10)
        
        # Configuración de scroll area
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Mensaje inicial
        self.graphs_initial_msg = QLabel("Los graficos apareceran aqui despues de ejecutar una simulacion")
        self.graphs_initial_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.graphs_initial_msg.setStyleSheet("color: #cccccc; font-size: 14px; margin: 50px;")
        self.graphs_layout.addWidget(self.graphs_initial_msg)
        
        # Agregar componentes al layout principal
        layout.addWidget(self.graphs_toolbar)
        layout.addWidget(scroll_area)
        
        self.graphs_tab.setLayout(layout)
    
    def init_scene3d_tab(self):
        """Inicializar tab de escena 3D con matplotlib canvas interactivo"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Crear figura de matplotlib para escena 3D
        self.scene3d_figure = Figure(figsize=(12, 9), facecolor='white')
        self.scene3d_canvas = FigureCanvas(self.scene3d_figure)
        self.scene3d_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Toolbar de navegación 3D (zoom, rotación, etc.)
        self.scene3d_toolbar = NavigationToolbar(self.scene3d_canvas, self)
        self.scene3d_toolbar.setStyleSheet("""
            QToolBar {
                background-color: #404040;
                border: 1px solid #555555;
                spacing: 2px;
            }
            QToolButton {
                background-color: #505050;
                color: white;
                border: 1px solid #666666;
                border-radius: 3px;
                padding: 5px;
                margin: 1px;
            }
            QToolButton:hover {
                background-color: #606060;
            }
        """)
        
        # Mensaje inicial en la figura
        ax = self.scene3d_figure.add_subplot(111)
        ax.text(0.5, 0.5, 'Escena 3D aparecera aqui\n\nPodras hacer zoom y rotar\ncon los controles de arriba', 
                ha='center', va='center', transform=ax.transAxes, fontsize=14, 
                bbox=dict(boxstyle="round,pad=0.5", facecolor='lightblue', alpha=0.8))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        self.scene3d_figure.tight_layout()
        self.scene3d_canvas.draw()
        
        # Agregar componentes al layout
        layout.addWidget(self.scene3d_toolbar)
        layout.addWidget(self.scene3d_canvas)
        
        self.scene3d_tab.setLayout(layout)
    
    def update_graphs(self, graph_paths):
        """Actualizar tab de gráficos cargando plots de matplotlib directamente"""
        # Limpiar gráficos anteriores
        for i in reversed(range(self.graphs_layout.count())):
            widget = self.graphs_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Crear canvas para cada gráfico
        for graph_path in graph_paths:
            if os.path.exists(graph_path):
                try:
                    # Crear nueva figura y canvas para cada gráfico
                    figure = Figure(figsize=(14, 10), facecolor='white')
                    canvas = FigureCanvas(figure)
                    canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                    
                    # Toolbar individual para cada gráfico
                    toolbar = NavigationToolbar(canvas, self)
                    toolbar.setStyleSheet("""
                        QToolBar {
                            background-color: #404040;
                            border: 1px solid #555555;
                            spacing: 2px;
                            margin: 2px;
                        }
                        QToolButton {
                            background-color: #505050;
                            color: white;
                            border: 1px solid #666666;
                            border-radius: 3px;
                            padding: 3px;
                            margin: 1px;
                        }
                        QToolButton:hover {
                            background-color: #606060;
                        }
                    """)
                    
                    # Container para gráfico + toolbar
                    graph_container = QWidget()
                    graph_layout = QVBoxLayout(graph_container)
                    graph_layout.setContentsMargins(2, 2, 2, 2)
                    graph_layout.addWidget(toolbar)
                    graph_layout.addWidget(canvas)
                    
                    # Cargar imagen existente en la figura
                    img = plt.imread(graph_path)
                    ax = figure.add_subplot(111)
                    ax.imshow(img)
                    ax.axis('off')
                    figure.tight_layout()
                    canvas.draw()
                    
                    # Añadir al layout principal
                    self.graphs_layout.addWidget(graph_container)
                    
                except Exception as e:
                    print(f"Error cargando gráfico {graph_path}: {e}")
                    # Fallback: mostrar mensaje de error
                    error_label = QLabel(f"Error cargando: {os.path.basename(graph_path)}")
                    error_label.setStyleSheet("color: red; margin: 10px;")
                    self.graphs_layout.addWidget(error_label)
    
    def update_scene_3d(self, scene_path):
        """Actualizar escena 3D cargando directamente en matplotlib canvas"""
        if os.path.exists(scene_path):
            try:
                # Limpiar figura anterior
                self.scene3d_figure.clear()
                
                # Cargar imagen de escena 3D
                img = plt.imread(scene_path)
                ax = self.scene3d_figure.add_subplot(111)
                ax.imshow(img)
                ax.axis('off')
                
                # Ajustar layout y redibujar
                self.scene3d_figure.tight_layout()
                self.scene3d_canvas.draw()
                
            except Exception as e:
                print(f"Error cargando escena 3D {scene_path}: {e}")
                # Mostrar mensaje de error
                self.scene3d_figure.clear()
                ax = self.scene3d_figure.add_subplot(111)
                ax.text(0.5, 0.5, f'Error cargando escena 3D:\n{str(e)}', 
                        ha='center', va='center', transform=ax.transAxes, fontsize=12,
                        bbox=dict(boxstyle="round,pad=0.5", facecolor='lightcoral', alpha=0.8))
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.axis('off')
                self.scene3d_figure.tight_layout()
                self.scene3d_canvas.draw()


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación"""
    
    def __init__(self):
        super().__init__()
        self.simulation_worker = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("UAV 5G NR Simulation Suite")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal horizontal
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter principal
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel izquierdo: Control + Config
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.control_panel = ControlPanel()
        self.config_panel = ConfigPanel()
        
        left_layout.addWidget(self.control_panel, 1)
        left_layout.addWidget(self.config_panel, 1)
        left_panel.setFixedWidth(400)
        
        # Panel derecho: Results tabs
        self.results_tabs = ResultsTabWidget()
        
        # Añadir a splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(self.results_tabs)
        main_splitter.setSizes([400, 1200])
        
        main_layout.addWidget(main_splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Sistema listo - Seleccione una simulación")
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Conectar señales
        self.control_panel.simulation_requested.connect(self.run_simulation)
        
        # Aplicar estilo
        self.apply_style()
    
    def apply_style(self):
        """Aplicar estilo oscuro moderno para mejor legibilidad"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 10px;
                margin: 5px 0px;
                padding-top: 20px;
                background-color: #3a3a3a;
                color: #ffffff;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #ffffff;
            }
            
            QTextEdit {
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 10px;
                background-color: #404040;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
            
            QTabWidget::pane {
                border: 1px solid #555555;
                border-radius: 8px;
                background-color: #3a3a3a;
            }
            
            QTabBar::tab {
                background-color: #505050;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            
            QTabBar::tab:selected {
                background-color: #3a3a3a;
                border-bottom-color: #3a3a3a;
                color: #ffffff;
            }
            
            QLabel {
                color: #ffffff;
            }
            
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            
            QScrollArea {
                background-color: #2b2b2b;
                border: 1px solid #555555;
                border-radius: 8px;
            }
            
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 8px;
                background-color: #404040;
                color: #ffffff;
            }
            
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 6px;
            }
            
            QStatusBar {
                background-color: #404040;
                color: #ffffff;
                border-top: 1px solid #555555;
            }
        """)
    
    def run_simulation(self, sim_type, parameters):
        """Ejecutar simulación en worker thread"""
        if self.simulation_worker and self.simulation_worker.isRunning():
            self.status_bar.showMessage("Simulacion en curso, espere...")
            return
        
        # Crear y configurar worker
        self.simulation_worker = SimulationWorker(sim_type, parameters)
        self.simulation_worker.finished.connect(self.on_simulation_finished)
        self.simulation_worker.progress.connect(self.on_simulation_progress)
        self.simulation_worker.error.connect(self.on_simulation_error)
        
        # UI feedback
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_bar.showMessage(f"Ejecutando: {sim_type}")
        
        # Iniciar simulación
        self.simulation_worker.start()
    
    def on_simulation_progress(self, message):
        """Actualizar progreso de simulación"""
        self.status_bar.showMessage(f"{message}")
    
    def on_simulation_finished(self, result):
        """Simulación completada"""
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(f"Completado: {result['type']}")
        
        # Actualizar configuración mostrada
        if 'config' in result:
            self.config_panel.update_config_display(result['config'])
        
        # Actualizar gráficos
        if 'plots' in result and result['plots']:
            self.results_tabs.update_graphs(result['plots'])
            self.results_tabs.setCurrentIndex(0)  # Switch to graphs tab
        
        # Actualizar escena 3D
        if 'scene_3d' in result and result['scene_3d']:
            self.results_tabs.update_scene_3d(result['scene_3d'])
        
        print(f"Simulación completada: {result}")
    
    def on_simulation_error(self, error_message):
        """Error en simulación"""
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(f"Error: {error_message}")
        print(f"Error en simulacion: {error_message}")


def main():
    """Función principal de la aplicación"""
    app = QApplication(sys.argv)
    
    # Configurar aplicación
    app.setApplicationName("UAV 5G NR Simulation Suite")
    app.setApplicationVersion("1.0.0")
    
    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    
    print("GUI UAV 5G NR iniciada exitosamente!")
    print("Estructura GUI completa creada")
    print("Primer boton MIMO listo para implementacion")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()