"""
Ventana principal de la aplicación CDMA Simulator.
Interfaz gráfica con PyQt5 para simulación y visualización de CDMA.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QLabel, QGroupBox, QPushButton,
    QSpinBox, QDoubleSpinBox, QComboBox, QTableWidget,
    QTableWidgetItem, QSplitter, QMessageBox, QStatusBar,
    QProgressBar
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
import numpy as np
from typing import Optional
import traceback

# Imports del proyecto (ajustar según estructura)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from src.core.code_generator import CodeGenerator
    from src.core.encoder import Encoder
    from src.core.decoder import Decoder
    from src.core.message_generator import MessageGenerator
    from src.core.signal_processor import SignalProcessor
    from src.models.simulation import Simulation
except ImportError:
    # Fallback para imports relativos
    from core.code_generator import CodeGenerator
    from core.encoder import Encoder
    from core.decoder import Decoder
    from core.message_generator import MessageGenerator
    from core.signal_processor import SignalProcessor
    from models.simulation import Simulation

# Imports de widgets de UI (se implementarán después)
from ui.widgets.signal_plot import SignalPlotWidget
#from ui.widgets.spectrum_plot import SpectrumPlotWidget


class MainWindow(QMainWindow):
    """
    Ventana principal del simulador CDMA.
    """
    
    def __init__(self):
        super().__init__()
        
        # Datos de la simulación
        self.simulation: Optional[Simulation] = None
        self.code_generator = CodeGenerator()
        self.message_generator = MessageGenerator()
        self.encoder = Encoder()
        self.decoder = Decoder()
        self.signal_processor = SignalProcessor()
        
        # Configuración de la ventana
        self.setWindowTitle("CDMA Simulator - Sistema de Acceso Múltiple por División de Código")
        self.setGeometry(100, 100, 1400, 900)
        
        # Inicializar UI
        self._init_ui()
        
        # Conectar señales
        self._connect_signals()
        
        # Barra de estado
        self.statusBar().showMessage("Listo para simular")
    
    def _init_ui(self):
        """Inicializa todos los componentes de la interfaz."""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal (horizontal)
        main_layout = QHBoxLayout(central_widget)
        
        # Panel izquierdo: Configuración y control
        left_panel = self._create_left_panel()
        
        # Panel derecho: Visualización (tabs)
        right_panel = self._create_right_panel()
        
        # Splitter para redimensionar
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)  # Panel izquierdo
        splitter.setStretchFactor(1, 3)  # Panel derecho (más grande)
        
        main_layout.addWidget(splitter)
    
    def _create_left_panel(self) -> QWidget:
        """Crea el panel izquierdo con controles de configuración."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Título
        title = QLabel("Configuración de Simulación")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Grupo: Parámetros básicos
        params_group = self._create_parameters_group()
        layout.addWidget(params_group)

        self._default_decoder_threshold = 0.0   # Más estricto
        self._default_snr_db = 20.0             # Menos ruido
        
        # Grupo: Opciones de codificación
        #encoding_group = self._create_encoding_group()
        #layout.addWidget(encoding_group)
        
        # Grupo: Opciones de ruido
        #noise_group = self._create_noise_group()
        #layout.addWidget(noise_group)
        
        # Botones de control
        buttons_group = self._create_buttons_group()
        layout.addWidget(buttons_group)
        
        # Grupo: Información de simulación
        info_group = self._create_info_group()
        layout.addWidget(info_group)
        
        # Espaciador
        layout.addStretch()
        
        return panel
    
    def _create_parameters_group(self) -> QGroupBox:
        """Crea el grupo de parámetros básicos."""
        group = QGroupBox("Parámetros Básicos")
        layout = QVBoxLayout()
        
        # Número de usuarios
        users_layout = QHBoxLayout()
        users_layout.addWidget(QLabel("Número de Usuarios:"))
        self.spin_users = QSpinBox()
        self.spin_users.setRange(1, 32)
        self.spin_users.setValue(4)
        self.spin_users.setToolTip("Número de usuarios simultáneos en el sistema CDMA")
        users_layout.addWidget(self.spin_users)
        layout.addLayout(users_layout)
        
        # Número de bits por mensaje
        bits_layout = QHBoxLayout()
        bits_layout.addWidget(QLabel("Bits por Mensaje:"))
        self.spin_bits = QSpinBox()
        self.spin_bits.setRange(4, 128)
        self.spin_bits.setValue(8)
        self.spin_bits.setToolTip("Número de bits en cada mensaje")
        bits_layout.addWidget(self.spin_bits)
        layout.addLayout(bits_layout)
        
        # Longitud del código (chips por bit)
        code_len_layout = QHBoxLayout()
        code_len_layout.addWidget(QLabel("Longitud de Código:"))
        self.spin_code_length = QSpinBox()
        self.spin_code_length.setRange(2, 1024)
        self.spin_code_length.setValue(8)
        self.spin_code_length.setToolTip("Número de chips por bit (factor de esparcimiento)")
        code_len_layout.addWidget(self.spin_code_length)
        layout.addLayout(code_len_layout)
        
        # Tipo de código
        #code_layout = QHBoxLayout()
        #code_layout.addWidget(QLabel("Tipo de Código:"))
        #self.combo_code_type = QComboBox()
        #self.combo_code_type.addItems(["Walsh"])
        #self.combo_code_type.setToolTip("Walsh: Códigos Hadamard ortogonales (potencia de 2)\n"
        #    "Gold: Buena correlación cruzada\n"
        #    "PN Sequence: Secuencias pseudoaleatorias (LFSR/m-sequences)\n"
        #    "OVSF: Orthogonal Variable Spreading Factor")
        #code_layout.addWidget(self.combo_code_type)
        #layout.addLayout(code_layout)
        self.combo_code_type = "Walsh"
        
        # Conectar cambios de usuarios/longitud para ajustar automáticamente
        self.spin_users.valueChanged.connect(self._on_users_changed)
        #self.combo_code_type.currentTextChanged.connect(self._on_code_type_changed)
        
        group.setLayout(layout)
        return group
    
    def _create_encoding_group(self) -> QGroupBox:
        """Crea el grupo de opciones de codificación."""
        group = QGroupBox("Opciones de Decodificación")
        layout = QVBoxLayout()
        
        # Decoder rate (umbral)
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("Umbral de Decisión:"))
        self.spin_decoder_rate = QDoubleSpinBox()
        self.spin_decoder_rate.setRange(-1.0, 1.0)
        self.spin_decoder_rate.setValue(0.0)
        self.spin_decoder_rate.setSingleStep(0.1)
        self.spin_decoder_rate.setDecimals(2)
        self.spin_decoder_rate.setToolTip("Umbral para decisión de bits en el decodificador")
        rate_layout.addWidget(self.spin_decoder_rate)
        layout.addLayout(rate_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_noise_group(self) -> QGroupBox:
        """Crea el grupo de opciones de ruido."""
        group = QGroupBox("Canal con Ruido (Opcional)")
        layout = QVBoxLayout()
        
        # Checkbox para habilitar ruido
        # self.check_enable_noise = QCheckBox("Agregar Ruido AWGN")
        # layout.addWidget(self.check_enable_noise)
        
        # SNR
        snr_layout = QHBoxLayout()
        snr_layout.addWidget(QLabel("SNR (dB):"))
        self.spin_snr = QDoubleSpinBox()
        self.spin_snr.setRange(-10.0, 50.0)
        self.spin_snr.setValue(10.0)
        self.spin_snr.setSingleStep(1.0)
        self.spin_snr.setDecimals(1)
        self.spin_snr.setToolTip("Relación señal-ruido en decibeles")
        # self.spin_snr.setEnabled(False)
        snr_layout.addWidget(self.spin_snr)
        layout.addLayout(snr_layout)
        
        # Conectar checkbox con SNR spinbox
        # self.check_enable_noise.stateChanged.connect(
        #     lambda state: self.spin_snr.setEnabled(state == Qt.Checked)
        # )
        
        group.setLayout(layout)
        return group
    
    def _create_buttons_group(self) -> QGroupBox:
        """Crea el grupo de botones de control."""
        group = QGroupBox("Control")
        layout = QVBoxLayout()
        
        # Botón: Generar Códigos
        self.btn_generate_codes = QPushButton("1. Generar Códigos")
        self.btn_generate_codes.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.btn_generate_codes.setMinimumHeight(40)
        layout.addWidget(self.btn_generate_codes)
        
        # Botón: Generar Mensajes
        self.btn_generate_messages = QPushButton("2. Generar Mensajes")
        self.btn_generate_messages.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.btn_generate_messages.setMinimumHeight(40)
        self.btn_generate_messages.setEnabled(False)
        layout.addWidget(self.btn_generate_messages)
        
        # Botón: Codificar
        self.btn_encode = QPushButton("3. Codificar Señales")
        self.btn_encode.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        self.btn_encode.setMinimumHeight(40)
        self.btn_encode.setEnabled(False)
        layout.addWidget(self.btn_encode)
        
        # Botón: Decodificar
        self.btn_decode = QPushButton("4. Decodificar Señales")
        self.btn_decode.setStyleSheet("background-color: #9C27B0; color: white; font-weight: bold;")
        self.btn_decode.setMinimumHeight(40)
        self.btn_decode.setEnabled(False)
        layout.addWidget(self.btn_decode)
        
        # Separador
        layout.addSpacing(20)
        
        # Botón: Simulación completa
        self.btn_run_all = QPushButton("▶ Ejecutar Simulación Completa")
        self.btn_run_all.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        self.btn_run_all.setMinimumHeight(50)
        layout.addWidget(self.btn_run_all)
        
        # Botón: Reset
        self.btn_reset = QPushButton("🔄 Reiniciar")
        self.btn_reset.setMinimumHeight(35)
        layout.addWidget(self.btn_reset)
        
        group.setLayout(layout)
        return group
    
    def _create_info_group(self) -> QGroupBox:
        """Crea el grupo de información de la simulación."""
        group = QGroupBox("Estado de la Simulación")
        layout = QVBoxLayout()
        
        # Labels de información
        self.label_status = QLabel("Estado: Sin iniciar")
        self.label_code_length = QLabel("Longitud de código: -")
        self.label_signal_length = QLabel("Longitud de señal: -")
        self.label_time_info = QLabel("Tiempo: - chips = - bits")
        self.label_spreading_factor = QLabel("Factor de esparcimiento: -")
        self.label_ber = QLabel("BER promedio: -")
        
        layout.addWidget(self.label_status)
        layout.addWidget(self.label_code_length)
        layout.addWidget(self.label_signal_length)
        layout.addWidget(self.label_time_info)
        layout.addWidget(self.label_spreading_factor)
        layout.addWidget(self.label_ber)
        
        group.setLayout(layout)
        return group
    
    def _create_right_panel(self) -> QWidget:
        """Crea el panel derecho con visualizaciones."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Tabs para diferentes vistas
        self.tabs = QTabWidget()
        
        # Tab 1: Señales codificadas
        tab_encoded = self._create_encoded_signals_tab()
        self.tabs.addTab(tab_encoded, "📊 Señales Codificadas")
        
        # Tab 2: Espectros
        #tab_spectrum = self._create_spectrum_tab()
        #self.tabs.addTab(tab_spectrum, "📈 Espectros de Frecuencia")
        
        # Tab 3: Resultados (tabla comparativa)
        tab_results = self._create_results_tab()
        self.tabs.addTab(tab_results, "📋 Resultados y Comparación")
        
        # Tab 4: Análisis
        tab_analysis = self._create_analysis_tab()
        #self.tabs.addTab(tab_analysis, "🔍 Análisis Detallado")
        
        layout.addWidget(self.tabs)
        
        return panel
    
    def _create_encoded_signals_tab(self) -> QWidget:
        """Crea la pestaña de señales codificadas."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Placeholder para gráfico de señales
        # TODO: Reemplazar con SignalPlotWidget cuando esté implementado
        self.plot_encoded_signals = SignalPlotWidget()  # ← Widget real
        
        #layout.addWidget(QLabel("<b>Señales Individuales y Señal Total:</b>"))
        layout.addWidget(self.plot_encoded_signals)
        
        return widget
    
    def _create_spectrum_tab(self) -> QWidget:
        """Crea la pestaña de espectros."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Placeholder para gráfico de espectros
        # TODO: Reemplazar con SpectrumPlotWidget cuando esté implementado
        self.plot_spectrum = SpectrumPlotWidget()
        
        layout.addWidget(QLabel("<b>Análisis Espectral (FFT):</b>"))
        layout.addWidget(self.plot_spectrum)
        
        return widget
    
    def _create_results_tab(self) -> QWidget:
        """Crea la pestaña de resultados."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Tabla de comparación
        layout.addWidget(QLabel("<b>Comparación de Mensajes Original vs Decodificado:</b>"))
        
        self.table_results = QTableWidget()
        self.table_results.setColumnCount(5)
        self.table_results.setHorizontalHeaderLabels([
            "Usuario", "Mensaje Original", "Mensaje Decodificado", "Codigo", "Estado"
        ])
        self.table_results.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.table_results)
        
        return widget
    
    def _create_analysis_tab(self) -> QWidget:
        """Crea la pestaña de análisis detallado."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Información detallada
        self.text_analysis = QLabel("Análisis detallado aparecerá aquí después de la simulación.")
        self.text_analysis.setWordWrap(True)
        self.text_analysis.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.text_analysis.setStyleSheet("background-color: white; padding: 10px; border: 1px solid #ccc;")
        
        layout.addWidget(QLabel("<b>Análisis de la Simulación:</b>"))
        layout.addWidget(self.text_analysis)
        
        return widget
    
    def _connect_signals(self):
        """Conecta señales de los widgets con sus slots."""
        # Botones de control
        self.btn_generate_codes.clicked.connect(self.on_generate_codes)
        self.btn_generate_messages.clicked.connect(self.on_generate_messages)
        self.btn_encode.clicked.connect(self.on_encode)
        self.btn_decode.clicked.connect(self.on_decode)
        self.btn_run_all.clicked.connect(self.on_run_all)
        self.btn_reset.clicked.connect(self.on_reset)
    
    # ==================== Slots (event handlers) ====================
    
    def on_generate_codes(self):
        """Genera códigos de esparcimiento ortogonales."""
        try:
            n_users = self.spin_users.value()
            code_length = self.spin_code_length.value()
            code_type = self.combo_code_type.lower()
            
            self.statusBar().showMessage("Generando códigos...")
            
            # Generar códigos con longitud específica
            if code_type == 'walsh':
                # Walsh requiere potencia de 2, ajustar si es necesario
                codes = self.code_generator.generate_walsh_codes(max(n_users, code_length))
                # Recortar a n_users y code_length
                codes = codes[:n_users, :code_length]
            
            # Verificar ortogonalidad
            is_ortho, corr_matrix = self.code_generator.verify_orthogonality(codes)
            
            # Crear simulación
            n_bits = self.spin_bits.value()
            #decoder_rate = self.spin_decoder_rate.value()
            decoder_rate = self._default_decoder_threshold
            
            self.simulation = Simulation(
                n_users=n_users,
                n_bits=n_bits,
                code_type=code_type,
                decoder_rate=decoder_rate
            )
            
            self.simulation.initialize_users(codes)
            
            # Actualizar UI
            self.label_status.setText("Estado: Códigos generados")
            self.label_code_length.setText(f"Longitud de código: {codes.shape[1]} chips/bit")
            self.label_spreading_factor.setText(f"Factor de esparcimiento: {codes.shape[1]}x")
            
            ortho_text = "✓ Ortogonales" if is_ortho else "⚠ No ortogonales"
            max_corr = np.max(np.abs(corr_matrix - np.eye(n_users)))
            self.statusBar().showMessage(
                f"Códigos generados: {n_users} códigos {code_type.upper()} "
                f"({codes.shape[1]} chips/bit) - {ortho_text} "
                f"(Max correlación cruzada: {max_corr:.4f})"
            )
            
            # Habilitar siguiente paso
            self.btn_generate_messages.setEnabled(True)
            
        except Exception as e:
            self._show_error("Error generando códigos", e)
    
    def on_generate_messages(self):
        """Genera mensajes aleatorios para los usuarios."""
        try:
            if self.simulation is None:
                QMessageBox.warning(self, "Advertencia", "Primero debe generar los códigos")
                return
            
            self.statusBar().showMessage("Generando mensajes...")
            
            # Generar mensajes aleatorios
            messages = self.message_generator.generate_random_messages(
                self.simulation.n_users,
                self.simulation.n_bits
            )
            
            self.simulation.set_messages(messages)
            
            # Actualizar UI
            self.label_status.setText("Estado: Mensajes generados")
            self.statusBar().showMessage(
                f"Mensajes generados: {self.simulation.n_users} usuarios con {self.simulation.n_bits} bits cada uno"
            )
            
            # Habilitar siguiente paso
            self.btn_encode.setEnabled(True)
            
        except Exception as e:
            self._show_error("Error generando mensajes", e)
    
    def on_encode(self):
        """Codifica los mensajes de todos los usuarios."""
        try:
            if self.simulation is None or not self.simulation.users[0].has_message:
                QMessageBox.warning(self, "Advertencia", "Primero debe generar mensajes")
                return
            
            self.statusBar().showMessage("Codificando señales...")
            
            # Obtener mensajes y códigos
            messages = self.simulation.get_all_original_messages()
            codes = self.simulation.codes
            
            # Codificar
            signals, total_signal = self.encoder.encode_and_combine(messages, codes)
            
            # Guardar en simulación
            self.simulation.set_encoded_signals(signals, total_signal)
            
            # Actualizar UI
            signal_length = len(total_signal)
            code_length = self.simulation.codes.shape[1]
            n_bits = self.simulation.n_bits

            self.label_status.setText("Estado: Señales codificadas")
            self.label_signal_length.setText(f"Longitud de señal: {signal_length} chips")
            self.label_time_info.setText(f"Tiempo: {signal_length} chips = {n_bits} bits")
            self.label_spreading_factor.setText(f"Factor de esparcimiento: {code_length}x")
            self.statusBar().showMessage(
                f"Codificación completa: {self.simulation.n_users} señales combinadas"
                f"({n_bits} bits × {code_length} chips/bit = {signal_length} chips)"
            )
            
            # TODO: Actualizar gráficos de señales y espectros
            # Actualizar gráfico de señales
            self.plot_encoded_signals.plot_signals(
                individual_signals=signals,
                total_signal=total_signal,
                user_labels=[user.label for user in self.simulation.users],
                code_length=self.simulation.codes.shape[1],
                original_messages=messages
            )
            
            # Actualizar gráfico de espectros
            #self.plot_spectrum.plot_spectra(
            #    individual_signals=signals,
            #    total_signal=total_signal,
            #    user_labels=[user.label for user in self.simulation.users],
            #    sampling_rate=100.0  # Ajustar según necesidad
            #)
            
            # Habilitar siguiente paso
            self.btn_decode.setEnabled(True)
            
        except Exception as e:
            self._show_error("Error codificando señales", e)
    
    def on_decode(self):
        """Decodifica la señal total para recuperar los mensajes."""
        try:
            if self.simulation is None or not self.simulation.is_encoded:
                QMessageBox.warning(self, "Advertencia", "Primero debe codificar las señales")
                return
            
            self.statusBar().showMessage("Decodificando señales...")
            
            # Obtener señal para decodificar
            signal_to_decode = self.simulation.total_signal.data
            
            # Aplicar ruido si está habilitado
            # if self.check_enable_noise.isChecked():
            #snr_db = self.spin_snr.value()
            snr_db = self._default_snr_db
            #noisy_signal = self.encoder.add_noise(signal_to_decode, snr_db)
            #self.simulation.set_noisy_signal(noisy_signal, snr_db)
            #signal_to_decode = noisy_signal
            
            # Actualizar umbral del decodificador
            #self.decoder.set_decision_threshold(self.spin_decoder_rate.value())
            self.decoder.set_decision_threshold(self._default_decoder_threshold)
            
            # Decodificar
            decoded_messages = self.decoder.decode_all_users(
                signal_to_decode,
                self.simulation.codes,
                self.simulation.n_bits
            )
            
            self.simulation.set_decoded_messages(decoded_messages)
            
            # Actualizar UI
            avg_ber = self.simulation.metrics.get('average_ber', 0.0)
            self.label_status.setText("Estado: Decodificación completa")
            self.label_ber.setText(f"BER promedio: {avg_ber:.4f}")
            
            self.statusBar().showMessage(
                f"Decodificación completa - BER promedio: {avg_ber:.4f}"
            )
            
            # Actualizar tabla de resultados
            self._update_results_table()
            
            # Actualizar análisis
            #self._update_analysis()
            
        except Exception as e:
            self._show_error("Error decodificando señales", e)
    
    def on_run_all(self):
        """Ejecuta la simulación completa (todos los pasos)."""
        try:
            self.statusBar().showMessage("Ejecutando simulación completa...")
            
            # Ejecutar todos los pasos
            self.on_generate_codes()
            self.on_generate_messages()
            self.on_encode()
            self.on_decode()
            
            self.statusBar().showMessage("Simulación completa ejecutada exitosamente")
            
            # Cambiar a tab de resultados
            self.tabs.setCurrentIndex(1)
            
        except Exception as e:
            self._show_error("Error en simulación completa", e)
    
    def on_reset(self):
        """Reinicia la simulación."""
        reply = QMessageBox.question(
            self,
            "Confirmar Reset",
            "¿Está seguro de que desea reiniciar la simulación?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reiniciar simulación
            if self.simulation:
                self.simulation.reset()
            self.simulation = None
            
            # Reiniciar UI
            self.label_status.setText("Estado: Sin iniciar")
            self.label_code_length.setText("Longitud de código: -")
            self.label_signal_length.setText("Longitud de señal: -")
            self.label_ber.setText("BER promedio: -")
            
            # Deshabilitar botones
            self.btn_generate_messages.setEnabled(False)
            self.btn_encode.setEnabled(False)
            self.btn_decode.setEnabled(False)
            
            # Limpiar tabla
            self.table_results.setRowCount(0)
            
            # Limpiar análisis
            self.text_analysis.setText("Análisis detallado aparecerá aquí después de la simulación.")
            self.plot_encoded_signals.clear_plot()
            #self.plot_spectrum.clear_plot()
            
            self.statusBar().showMessage("Simulación reiniciada")
    
    # ==================== Métodos auxiliares ====================
    
    def _update_results_table(self):
        """Actualiza la tabla de resultados."""
        if not self.simulation or not self.simulation.is_decoded:
            return
        
        self.table_results.setRowCount(self.simulation.n_users)
        
        for i, user in enumerate(self.simulation.users):
            # Usuario
            self.table_results.setItem(i, 0, QTableWidgetItem(user.label))
            
            # Mensaje original
            orig_msg = ''.join(map(str, user.original_message))
            self.table_results.setItem(i, 1, QTableWidgetItem(orig_msg))
            
            # Mensaje decodificado
            dec_msg = ''.join(map(str, user.decoded_message))
            self.table_results.setItem(i, 2, QTableWidgetItem(dec_msg))
            
            # BER
            ber = user.calculate_ber()
            ber_item = QTableWidgetItem(f"{ber:.4f}")
            if ber == 0.0:
                ber_item.setBackground(QColor(200, 255, 200))  # Verde claro
            elif ber < 0.1:
                ber_item.setBackground(QColor(255, 255, 200))  # Amarillo
            else:
                ber_item.setBackground(QColor(255, 200, 200))  # Rojo claro
            #self.table_results.setItem(i, 3, ber_item)
            self.table_results.setItem(i,3,QTableWidgetItem(''.join('1' if x > 0 else '0' for x in user.code)))
            
            # Estado
            status = "✓ Perfecto" if ber == 0.0 else f"⚠ {int(ber * user.message_length)} errores"
            status_item = QTableWidgetItem(status)
            self.table_results.setItem(i, 4, status_item)
        
        # Ajustar columnas
        self.table_results.resizeColumnsToContents()
    
    def _update_analysis(self):
        """Actualiza el análisis detallado."""
        if not self.simulation or not self.simulation.is_decoded:
            return
        
        summary = self.simulation.get_summary()
        
        analysis_text = f"""
<h3>Resumen de la Simulación</h3>

<b>Parámetros:</b><br>
• Número de usuarios: {summary['parameters']['n_users']}<br>
• Bits por mensaje: {summary['parameters']['n_bits']}<br>
• Tipo de código: {summary['parameters']['code_type'].upper()}<br>
• Longitud de código: {summary['parameters']['code_length']} chips<br>

<b>Resultados:</b><br>
• Total de bits: {summary['metrics']['total_bits']}<br>
• Total de errores: {summary['metrics']['total_errors']}<br>
• Usuarios sin errores: {summary['metrics']['perfect_users']}/{summary['parameters']['n_users']}<br>

<b>Análisis por Usuario:</b><br>
"""
        
        for user in self.simulation.users:
            ber = user.calculate_ber()
            errors = np.sum(user.get_errors())
            analysis_text += f"• {user.label}: BER={ber:.4f} ({errors} errores)<br>"
        
        self.text_analysis.setText(analysis_text)
    
    def _show_error(self, title: str, exception: Exception):
        """Muestra un mensaje de error."""
        error_msg = f"{str(exception)}\n\n{traceback.format_exc()}"
        QMessageBox.critical(self, title, error_msg)
        self.statusBar().showMessage(f"Error: {str(exception)}")
    
    def _on_users_changed(self, value):
        """Callback cuando cambia el número de usuarios."""
        # Para Walsh, sugerir longitud de código >= n_users
        code_type = self.combo_code_type.lower()
        if code_type == 'walsh':
            # Sugerir la siguiente potencia de 2
            suggested_length = 2 ** int(np.ceil(np.log2(max(value, self.spin_code_length.value()))))
            if self.spin_code_length.value() < value:
                self.spin_code_length.setValue(suggested_length)
    
    def _on_code_type_changed(self, text):
        """Callback cuando cambia el tipo de código."""
        code_type = text.lower()
        n_users = self.spin_users.value()
        
        if code_type == 'walsh':
            # Walsh necesita potencia de 2
            suggested_length = 2 ** int(np.ceil(np.log2(max(n_users, 4))))
            self.spin_code_length.setValue(suggested_length)
            self.spin_code_length.setToolTip(
                "Walsh requiere potencia de 2. Se ajustará automáticamente."
            )
        else:
            # Gold puede ser más flexible
            self.spin_code_length.setToolTip(
                "Longitud del código (chips por bit). Para Gold: 2^n - 1 es óptimo."
            )


def main():
    """Función principal para ejecutar la aplicación."""
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Estilo de la aplicación
    app.setStyle('Fusion')
    
    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()