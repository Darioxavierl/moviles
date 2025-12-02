"""
Ventana principal de la interfaz gráfica PyQt6
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
                             QGroupBox, QFileDialog, QTextEdit, QTabWidget, QProgressBar,
                             QGridLayout, QMessageBox, QSplitter)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
import numpy as np
import sys
import os

# Imports del sistema OFDM
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.lte_params import LTEConfig, MODULATION_SCHEMES, SUBCARRIER_SPACING
from core.ofdm_system import OFDMSystem
from utils.image_processing import ImageProcessor
from utils.signal_processing import SignalAnalyzer, PlotGenerator

# Matplotlib para PyQt6
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class SimulationWorker(QThread):
    """Worker thread para ejecutar simulaciones sin bloquear la GUI"""
    
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    
    def __init__(self, ofdm_system, mode, params):
        super().__init__()
        self.ofdm_system = ofdm_system
        self.mode = mode
        self.params = params
    
    def run(self):
        """Ejecuta la simulación según el modo"""
        try:
            if self.mode == 'single':
                self._run_single_simulation()
            elif self.mode == 'sweep':
                self._run_sweep_simulation()
        except Exception as e:
            self.finished.emit({'error': str(e)})
    
    def _run_single_simulation(self):
        """Ejecuta simulación única"""
        self.progress.emit(10, "Preparando datos...")
        
        if 'image_path' in self.params:
            # Transmisión de imagen
            bits, metadata = ImageProcessor.image_to_bits(self.params['image_path'])
            self.params['metadata'] = metadata
        else:
            # Bits aleatorios
            bits = np.random.randint(0, 2, self.params['n_bits'])
        
        self.progress.emit(30, "Transmitiendo...")
        
        results = self.ofdm_system.transmit(bits, 
                                           snr_db=self.params['snr_db'],
                                           return_time=True)
        
        self.progress.emit(70, "Procesando resultados...")
        
        if 'metadata' in self.params:
            # Reconstruir imagen usando el array de bits recibidos
            reconstructed_img = ImageProcessor.bits_to_image(
                results['bits_rx'], 
                self.params['metadata']
            )
            results['reconstructed_image'] = reconstructed_img
            results['metadata'] = self.params['metadata']
        
        self.progress.emit(100, "Completado")
        self.finished.emit(results)
    
    def _run_sweep_simulation(self):
        """Ejecuta barrido de SNR con todas las modulaciones"""
        self.progress.emit(5, "Preparando datos...")
        
        # Extraer bits (de imagen o generar aleatorios)
        bits_to_sweep = None
        if 'image_path' in self.params:
            self.progress.emit(10, "Cargando imagen...")
            bits_to_sweep, metadata = ImageProcessor.image_to_bits(self.params['image_path'])
            self.params['metadata'] = metadata
            self.progress.emit(15, f"Imagen cargada: {len(bits_to_sweep)} bits")
        
        def progress_callback(progress, message):
            # Asegurar que sea un entero válido
            try:
                prog_int = int(progress)
                if prog_int < 0:
                    prog_int = 0
                elif prog_int > 100:
                    prog_int = 100
                self.progress.emit(prog_int, str(message))
            except:
                pass
        
        # Calcular número de bits
        num_bits = len(bits_to_sweep) if bits_to_sweep is not None else 50000
        
        self.progress.emit(20, f"Iniciando barrido SNR ({len(self.params['snr_range'])} valores)...")
        
        # Usar nuevo método que barre todas las modulaciones
        all_results = self.ofdm_system.run_ber_sweep_all_modulations(
            num_bits,
            self.params['snr_range'],
            self.params['n_iterations'],
            progress_callback,
            bits=bits_to_sweep  # Pasar los bits específicos si existen
        )
        
        # Si se transmitió imagen, agregar información de la imagen
        if 'metadata' in self.params:
            all_results['metadata'] = self.params['metadata']
        
        self.progress.emit(100, "Barrido completado")
        self.finished.emit(all_results)


class OFDMSimulatorGUI(QMainWindow):
    """Ventana principal del simulador OFDM"""
    
    def __init__(self):
        super().__init__()
        self.ofdm_system = None
        self.current_image_path = None
        self.init_ui()
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        self.setWindowTitle('Simulador OFDM - Especificaciones LTE')
        self.setGeometry(100, 100, 1400, 900)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Panel izquierdo: controles
        left_panel = self.create_control_panel()
        
        # Panel derecho: resultados
        right_panel = self.create_results_panel()
        
        # Agregar paneles con splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
    
    def create_control_panel(self):
        """Crea el panel de controles"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # Parámetros LTE
        lte_group = self.create_lte_parameters_group()
        layout.addWidget(lte_group)
        
        # Parámetros de simulación
        sim_group = self.create_simulation_parameters_group()
        layout.addWidget(sim_group)
        
        # Transmisión de imagen
        image_group = self.create_image_group()
        layout.addWidget(image_group)
        
        # Botones de simulación
        buttons_group = self.create_simulation_buttons()
        layout.addWidget(buttons_group)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("Listo")
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)
        
        # Info de configuración
        self.config_info = QTextEdit()
        self.config_info.setReadOnly(True)
        self.config_info.setMaximumHeight(200)
        layout.addWidget(QLabel("Información de Configuración:"))
        layout.addWidget(self.config_info)
        
        layout.addStretch()
        
        return panel
    
    def create_lte_parameters_group(self):
        """Crea grupo de parámetros LTE"""
        group = QGroupBox("Parámetros LTE")
        layout = QGridLayout()
        
        # Modulación
        layout.addWidget(QLabel("Modulación:"), 0, 0)
        self.modulation_combo = QComboBox()
        self.modulation_combo.addItems(MODULATION_SCHEMES)
        self.modulation_combo.currentTextChanged.connect(self.update_config)
        layout.addWidget(self.modulation_combo, 0, 1)
        
        # Ancho de banda
        layout.addWidget(QLabel("Ancho de banda (MHz):"), 1, 0)
        self.bandwidth_combo = QComboBox()
        self.bandwidth_combo.addItems(['1.25', '2.5', '5', '10', '15', '20'])
        self.bandwidth_combo.setCurrentText('5')
        self.bandwidth_combo.currentTextChanged.connect(self.update_config)
        layout.addWidget(self.bandwidth_combo, 1, 1)
        
        # Separación subportadoras
        layout.addWidget(QLabel("Δf (kHz):"), 2, 0)
        self.delta_f_combo = QComboBox()
        self.delta_f_combo.addItems(['15.0', '7.5'])
        self.delta_f_combo.currentTextChanged.connect(self.update_config)
        layout.addWidget(self.delta_f_combo, 2, 1)
        
        # Tipo de CP
        layout.addWidget(QLabel("Prefijo Cíclico:"), 3, 0)
        self.cp_combo = QComboBox()
        self.cp_combo.addItems(['normal', 'extended'])
        self.cp_combo.currentTextChanged.connect(self.update_config)
        layout.addWidget(self.cp_combo, 3, 1)
        
        group.setLayout(layout)
        return group
    
    def create_simulation_parameters_group(self):
        """Crea grupo de parámetros de simulación"""
        group = QGroupBox("Parámetros de Simulación")
        layout = QGridLayout()
        
        # SNR
        layout.addWidget(QLabel("SNR (dB):"), 0, 0)
        self.snr_spin = QDoubleSpinBox()
        self.snr_spin.setRange(-10, 40)
        self.snr_spin.setValue(10)
        self.snr_spin.setSingleStep(1)
        layout.addWidget(self.snr_spin, 0, 1)
        
        # Barrido SNR - inicio
        layout.addWidget(QLabel("SNR inicio (dB):"), 1, 0)
        self.snr_start_spin = QDoubleSpinBox()
        self.snr_start_spin.setRange(-10, 40)
        self.snr_start_spin.setValue(0)
        layout.addWidget(self.snr_start_spin, 1, 1)
        
        # Barrido SNR - fin
        layout.addWidget(QLabel("SNR fin (dB):"), 2, 0)
        self.snr_end_spin = QDoubleSpinBox()
        self.snr_end_spin.setRange(-10, 40)
        self.snr_end_spin.setValue(20)
        layout.addWidget(self.snr_end_spin, 2, 1)
        
        # Barrido SNR - paso
        layout.addWidget(QLabel("SNR paso (dB):"), 3, 0)
        self.snr_step_spin = QDoubleSpinBox()
        self.snr_step_spin.setRange(0.5, 5)
        self.snr_step_spin.setValue(2)
        layout.addWidget(self.snr_step_spin, 3, 1)
        
        # Iteraciones
        layout.addWidget(QLabel("Iteraciones por SNR:"), 4, 0)
        self.iterations_spin = QSpinBox()
        self.iterations_spin.setRange(1, 100)
        self.iterations_spin.setValue(10)
        layout.addWidget(self.iterations_spin, 4, 1)
        
        group.setLayout(layout)
        return group
    
    def create_image_group(self):
        """Crea grupo para transmisión de imagen"""
        group = QGroupBox("Transmisión de Imagen")
        layout = QVBoxLayout()
        
        self.load_image_btn = QPushButton("Cargar Imagen")
        self.load_image_btn.clicked.connect(self.load_image)
        layout.addWidget(self.load_image_btn)
        
        self.image_label = QLabel("No hay imagen cargada")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(150)
        self.image_label.setStyleSheet("border: 1px solid gray")
        layout.addWidget(self.image_label)
        
        group.setLayout(layout)
        return group
    
    def create_simulation_buttons(self):
        """Crea botones de simulación"""
        group = QGroupBox("Simulación")
        layout = QVBoxLayout()
        
        self.single_sim_btn = QPushButton("Simulación Única")
        self.single_sim_btn.clicked.connect(self.run_single_simulation)
        layout.addWidget(self.single_sim_btn)
        
        self.sweep_sim_btn = QPushButton("Barrido en SNR")
        self.sweep_sim_btn.clicked.connect(self.run_sweep_simulation)
        layout.addWidget(self.sweep_sim_btn)
        
        group.setLayout(layout)
        return group
    
    def create_results_panel(self):
        """Crea panel de resultados"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # Tabs para diferentes vistas
        self.tabs = QTabWidget()
        
        # Tab 1: Métricas
        self.metrics_tab = QTextEdit()
        self.metrics_tab.setReadOnly(True)
        self.tabs.addTab(self.metrics_tab, "Métricas")
        
        # Tab 2: Gráficos
        self.plots_tab = QWidget()
        self.plots_layout = QVBoxLayout()
        self.plots_tab.setLayout(self.plots_layout)
        self.tabs.addTab(self.plots_tab, "Gráficos")
        
        # Tab 3: Imagen
        self.image_tab = QWidget()
        self.image_layout = QHBoxLayout()
        self.image_tab.setLayout(self.image_layout)
        self.tabs.addTab(self.image_tab, "Imagen")
        
        layout.addWidget(self.tabs)
        
        return panel
    
    def update_config(self):
        """Actualiza la configuración del sistema"""
        try:
            bandwidth = float(self.bandwidth_combo.currentText())
            delta_f = float(self.delta_f_combo.currentText())
            modulation = self.modulation_combo.currentText()
            cp_type = self.cp_combo.currentText()
            
            config = LTEConfig(bandwidth, delta_f, modulation, cp_type)
            self.ofdm_system = OFDMSystem(config)
            
            # Mostrar info
            info = config.get_info()
            info_text = "Configuración Actual:\n" + "-"*40 + "\n"
            for key, value in info.items():
                info_text += f"{key}: {value}\n"
            
            self.config_info.setText(info_text)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al actualizar configuración: {str(e)}")
    
    def load_image(self):
        """Carga una imagen para transmitir"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Imagen", "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            self.current_image_path = file_path
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)
            self.image_label.setPixmap(scaled_pixmap)
    
    def run_single_simulation(self):
        """Ejecuta simulación única"""
        if not self.ofdm_system:
            self.update_config()
        
        # Requiere imagen cargada
        if not self.current_image_path:
            QMessageBox.warning(self, "Advertencia", 
                              "Por favor carga una imagen para realizar la simulación")
            return
        
        # Preparar parámetros
        params = {
            'snr_db': self.snr_spin.value(),
            'image_path': self.current_image_path
        }
        
        # Deshabilitar botones
        self.set_buttons_enabled(False)
        
        # Crear y ejecutar worker
        self.worker = SimulationWorker(self.ofdm_system, 'single', params)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_single_simulation_finished)
        self.worker.start()
    
    def run_sweep_simulation(self):
        """Ejecuta barrido de SNR"""
        if not self.ofdm_system:
            self.update_config()
        
        # Preparar parámetros
        snr_start = self.snr_start_spin.value()
        snr_end = self.snr_end_spin.value()
        snr_step = self.snr_step_spin.value()
        
        params = {
            'snr_range': np.arange(snr_start, snr_end + snr_step, snr_step),
            'n_iterations': self.iterations_spin.value()
        }
        
        # Si hay imagen cargada, usar sus bits; si no, requiere imagen
        if self.current_image_path:
            params['image_path'] = self.current_image_path
        else:
            QMessageBox.warning(self, "Advertencia", 
                              "Por favor carga una imagen para realizar el barrido")
            return
        
        # Deshabilitar botones
        self.set_buttons_enabled(False)
        
        # Crear y ejecutar worker
        self.worker = SimulationWorker(self.ofdm_system, 'sweep', params)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_sweep_simulation_finished)
        self.worker.start()
    
    def update_progress(self, value, message):
        """Actualiza barra de progreso"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
    
    def on_single_simulation_finished(self, results):
        """Maneja finalización de simulación única"""
        self.set_buttons_enabled(True)
        
        if 'error' in results:
            QMessageBox.critical(self, "Error", results['error'])
            return
        
        # Mostrar métricas
        metrics_text = "Resultados de la Simulación:\n" + "="*50 + "\n"
        metrics_text += f"SNR: {results['snr_db']:.2f} dB\n"
        metrics_text += f"Bits transmitidos: {results['n_bits']}\n"
        metrics_text += f"BER: {results['ber']:.6e}\n"
        metrics_text += f"Errores: {results['errors']}\n"
        metrics_text += f"EVM: {results['evm']:.2f}%\n"
        
        if 'transmission_time' in results:
            metrics_text += f"Tiempo de transmisión: {results['transmission_time']*1000:.3f} ms\n"
        
        self.metrics_tab.setText(metrics_text)
        
        # Graficar constelación
        self.clear_plots()
        self.plot_constellation_comparison(
            results['transmitted_symbols'],
            results['received_symbols']
        )
        
        # Mostrar imagen si aplica
        if 'reconstructed_image' in results:
            self.show_image_comparison(results)
    
    def on_sweep_simulation_finished(self, results):
        """Maneja finalización de barrido SNR (con todas las modulaciones)"""
        self.set_buttons_enabled(True)
        
        if 'error' in results:
            QMessageBox.critical(self, "Error", results['error'])
            return
        
        # Mostrar métricas
        metrics_text = "Resultados del Barrido SNR (Todas las Modulaciones):\n" + "="*60 + "\n"
        
        # Procesar resultados por modulación
        for modulation, mod_results in results.items():
            if modulation == 'metadata':
                continue
            
            metrics_text += f"\n{modulation}:\n" + "-"*40 + "\n"
            metrics_text += f"Bits por corrida: {mod_results['n_bits']}\n"
            metrics_text += f"Iteraciones por SNR: {mod_results['n_iterations']}\n"
            metrics_text += f"Rango SNR: {mod_results['snr_db'][0]:.1f} - {mod_results['snr_db'][-1]:.1f} dB\n\n"
            
            for snr, ber, std in zip(mod_results['snr_db'], mod_results['ber_mean'], mod_results['ber_std']):
                metrics_text += f"  SNR {snr:.1f} dB: BER = {ber:.6e} ± {std:.6e}\n"
        
        self.metrics_tab.setText(metrics_text)
        
        # Graficar BER vs SNR para todas las modulaciones
        self.clear_plots()
        self.plot_ber_curve_all_modulations(results)
    
    def plot_constellation_comparison(self, tx_symbols, rx_symbols):
        """Grafica comparación de constelaciones"""
        fig = Figure(figsize=(12, 5))
        
        # Símbolos transmitidos
        ax1 = fig.add_subplot(121)
        ax1.scatter(tx_symbols[:1000].real, tx_symbols[:1000].imag, alpha=0.5, s=10)
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='k', linewidth=0.5)
        ax1.axvline(x=0, color='k', linewidth=0.5)
        ax1.set_title('Símbolos Transmitidos')
        ax1.set_xlabel('I')
        ax1.set_ylabel('Q')
        ax1.set_aspect('equal')
        
        # Símbolos recibidos
        ax2 = fig.add_subplot(122)
        ax2.scatter(rx_symbols[:1000].real, rx_symbols[:1000].imag, alpha=0.5, s=10)
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='k', linewidth=0.5)
        ax2.axvline(x=0, color='k', linewidth=0.5)
        ax2.set_title('Símbolos Recibidos')
        ax2.set_xlabel('I')
        ax2.set_ylabel('Q')
        ax2.set_aspect('equal')
        
        fig.tight_layout()
        
        canvas = FigureCanvas(fig)
        self.plots_layout.addWidget(canvas)
    
    def plot_ber_curve(self, results):
        """Grafica curva BER vs SNR"""
        fig = Figure(figsize=(10, 7))
        ax = fig.add_subplot(111)
        
        # BER simulado
        ax.semilogy(results['snr_db'], results['ber_mean'], 'o-', 
                   label='BER Simulado', linewidth=2, markersize=8)
        
        # Intervalo de confianza
        ax.fill_between(results['snr_db'],
                       np.array(results['ber_ci_lower']),
                       np.array(results['ber_ci_upper']),
                       alpha=0.3, label='IC 95%')
        
        ax.grid(True, alpha=0.3, which='both')
        ax.set_xlabel('SNR (dB)', fontsize=12)
        ax.set_ylabel('BER', fontsize=12)
        ax.set_title('BER vs SNR', fontsize=14)
        ax.legend(fontsize=10)
        
        fig.tight_layout()
        
        canvas = FigureCanvas(fig)
        self.plots_layout.addWidget(canvas)
    
    def plot_ber_curve_all_modulations(self, all_results):
        """Grafica curva BER vs SNR para todas las modulaciones con IC"""
        fig = Figure(figsize=(12, 8))
        ax = fig.add_subplot(111)
        
        # Colores para cada modulación
        colors = {'QPSK': 'blue', '16-QAM': 'red', '64-QAM': 'green'}
        markers = {'QPSK': 'o', '16-QAM': 's', '64-QAM': '^'}
        
        # Para cada modulación
        for modulation in ['QPSK', '16-QAM', '64-QAM']:
            if modulation not in all_results:
                continue
            
            results = all_results[modulation]
            snr_db = results['snr_db']
            ber_mean = results['ber_mean']
            ber_ci_lower = results['ber_ci_lower']
            ber_ci_upper = results['ber_ci_upper']
            
            color = colors[modulation]
            marker = markers[modulation]
            
            # BER simulado con marcadores
            ax.semilogy(snr_db, ber_mean, marker=marker, linestyle='-', 
                       color=color, label=modulation, linewidth=2.5, markersize=10)
            
            # Intervalo de confianza como banda sombreada
            ax.fill_between(snr_db,
                           np.array(ber_ci_lower),
                           np.array(ber_ci_upper),
                           alpha=0.2, color=color)
        
        ax.grid(True, alpha=0.4, which='both')
        ax.set_xlabel('SNR (dB)', fontsize=13, fontweight='bold')
        ax.set_ylabel('BER', fontsize=13, fontweight='bold')
        ax.set_title('BER vs SNR - Comparación de Modulaciones', fontsize=15, fontweight='bold')
        ax.legend(fontsize=11, loc='upper right')
        ax.set_ylim([1e-6, 1])
        
        fig.tight_layout()
        
        # Crear canvas con toolbar para guardar
        canvas = FigureCanvas(fig)
        
        # Agregar toolbar para permitir guardar imagen
        toolbar = NavigationToolbar(canvas, self)
        
        # Widget contenedor para canvas + toolbar
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.addWidget(toolbar)
        container_layout.addWidget(canvas)
        container.setLayout(container_layout)
        
        self.plots_layout.addWidget(container)
    
    def show_image_comparison(self, results):
        """Muestra comparación de imágenes"""
        # Limpiar layout
        for i in reversed(range(self.image_layout.count())):
            self.image_layout.itemAt(i).widget().setParent(None)
        
        # Imagen original
        original_label = QLabel("Original")
        original_pixmap = QPixmap(self.current_image_path)
        original_label.setPixmap(original_pixmap.scaled(400, 400, 
                                                        Qt.AspectRatioMode.KeepAspectRatio))
        
        # Imagen recibida
        received_label = QLabel("Recibida")
        received_img = results['reconstructed_image']
        
        # Convertir PIL a QPixmap
        received_img_rgb = received_img.convert('RGB')
        data = received_img_rgb.tobytes('raw', 'RGB')
        bytes_per_line = received_img_rgb.width * 3  # RGB = 3 bytes per pixel
        qimage = QImage(data, received_img_rgb.width, received_img_rgb.height, 
                       bytes_per_line, QImage.Format.Format_RGB888)
        received_pixmap = QPixmap.fromImage(qimage)
        received_label.setPixmap(received_pixmap.scaled(400, 400,
                                                       Qt.AspectRatioMode.KeepAspectRatio))
        
        self.image_layout.addWidget(original_label)
        self.image_layout.addWidget(received_label)
    
    def clear_plots(self):
        """Limpia gráficos anteriores"""
        for i in reversed(range(self.plots_layout.count())):
            widget = self.plots_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
    
    def set_buttons_enabled(self, enabled):
        """Habilita/deshabilita botones"""
        self.single_sim_btn.setEnabled(enabled)
        self.sweep_sim_btn.setEnabled(enabled)
        self.load_image_btn.setEnabled(enabled)