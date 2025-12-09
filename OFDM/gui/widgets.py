"""
Widgets personalizados para la interfaz gráfica
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np


class PlotWidget(QWidget):
    """Widget para mostrar gráficos de matplotlib"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Inicializa el widget"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Crear figura de matplotlib
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
    
    def clear(self):
        """Limpia la figura"""
        self.figure.clear()
        self.canvas.draw()
    
    def plot_constellation(self, symbols, title="Constelación"):
        """
        Grafica constelación de símbolos
        
        Args:
            symbols: Array de símbolos complejos
            title: Título del gráfico
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        ax.scatter(symbols.real, symbols.imag, alpha=0.5, s=20)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='k', linewidth=0.5)
        ax.axvline(x=0, color='k', linewidth=0.5)
        ax.set_xlabel('In-Phase (I)')
        ax.set_ylabel('Quadrature (Q)')
        ax.set_title(title)
        ax.set_aspect('equal')
        
        self.canvas.draw()
    
    def plot_ber_curve(self, snr_db, ber_mean, ber_std=None, theoretical_ber=None):
        """
        Grafica curva BER vs SNR
        
        Args:
            snr_db: Array de valores SNR
            ber_mean: BER promedio
            ber_std: Desviación estándar del BER (opcional)
            theoretical_ber: BER teórico (opcional)
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # BER simulado
        ax.semilogy(snr_db, ber_mean, 'o-', label='BER Simulado', linewidth=2)
        
        # Barras de error si hay desviación estándar
        if ber_std is not None:
            confidence = 1.96 * np.array(ber_std) / np.sqrt(10)
            ax.fill_between(snr_db, 
                           np.maximum(np.array(ber_mean) - confidence, 1e-6),
                           np.array(ber_mean) + confidence,
                           alpha=0.3, label='IC 95%')
        
        # BER teórico
        if theoretical_ber is not None:
            theoretical_ber = np.array(theoretical_ber)
            valid_idx = ~np.isnan(theoretical_ber)
            if np.any(valid_idx):
                ax.semilogy(np.array(snr_db)[valid_idx], 
                           theoretical_ber[valid_idx], 
                           's--', label='BER Teórico', linewidth=2, markersize=8)
        
        ax.grid(True, alpha=0.3, which='both')
        ax.set_xlabel('SNR (dB)', fontsize=12)
        ax.set_ylabel('BER', fontsize=12)
        ax.set_title('BER vs SNR', fontsize=14)
        ax.legend(fontsize=10)
        
        self.canvas.draw()
    
    def plot_comparison(self, tx_symbols, rx_symbols):
        """
        Grafica comparación de constelaciones transmitidas y recibidas
        
        Args:
            tx_symbols: Símbolos transmitidos
            rx_symbols: Símbolos recibidos
        """
        self.figure.clear()
        
        # Limitar a 1000 símbolos para visualización
        tx_symbols = tx_symbols[:1000]
        rx_symbols = rx_symbols[:1000]
        
        # Símbolos transmitidos
        ax1 = self.figure.add_subplot(121)
        ax1.scatter(tx_symbols.real, tx_symbols.imag, alpha=0.5, s=10)
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='k', linewidth=0.5)
        ax1.axvline(x=0, color='k', linewidth=0.5)
        ax1.set_title('Símbolos Transmitidos')
        ax1.set_xlabel('I')
        ax1.set_ylabel('Q')
        ax1.set_aspect('equal')
        
        # Símbolos recibidos
        ax2 = self.figure.add_subplot(122)
        ax2.scatter(rx_symbols.real, rx_symbols.imag, alpha=0.5, s=10)
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='k', linewidth=0.5)
        ax2.axvline(x=0, color='k', linewidth=0.5)
        ax2.set_title('Símbolos Recibidos')
        ax2.set_xlabel('I')
        ax2.set_ylabel('Q')
        ax2.set_aspect('equal')
        
        self.figure.tight_layout()
        self.canvas.draw()


class MetricsPanel(QWidget):
    """Panel para mostrar métricas de simulación"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Inicializa el widget"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Crear etiquetas para métricas
        self.metrics_labels = {}
        
        metrics = [
            ('SNR', 'dB'),
            ('BER', ''),
            ('Errores', 'bits'),
            #('EVM', '%'),
            ('Bits Transmitidos', ''),
            ('Tiempo TX', 'ms')
        ]
        
        for metric_name, unit in metrics:
            group = self.create_metric_group(metric_name, unit)
            layout.addWidget(group)
        
        layout.addStretch()
    
    def create_metric_group(self, name, unit):
        """Crea un grupo para una métrica"""
        group = QGroupBox(name)
        layout = QHBoxLayout()
        
        value_label = QLabel("--")
        value_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if unit:
            unit_label = QLabel(unit)
            unit_label.setFont(QFont("Arial", 10))
            layout.addWidget(value_label)
            layout.addWidget(unit_label)
        else:
            layout.addWidget(value_label)
        
        group.setLayout(layout)
        
        self.metrics_labels[name] = value_label
        return group
    
    def update_metrics(self, results):
        """
        Actualiza los valores de las métricas
        
        Args:
            results: Diccionario con resultados de la simulación
        """
        if 'snr_db' in results and results['snr_db'] is not None:
            self.metrics_labels['SNR'].setText(f"{results['snr_db']:.2f}")
        
        if 'ber' in results:
            self.metrics_labels['BER'].setText(f"{results['ber']:.6e}")
        
        if 'errors' in results:
            self.metrics_labels['Errores'].setText(f"{results['errors']}")
        
        if 'evm' in results:
            self.metrics_labels['EVM'].setText(f"{results['evm']:.2f}")
        
        if 'n_bits' in results:
            self.metrics_labels['Bits Transmitidos'].setText(f"{results['n_bits']}")
        
        if 'transmission_time' in results:
            time_ms = results['transmission_time'] * 1000
            self.metrics_labels['Tiempo TX'].setText(f"{time_ms:.3f}")
    
    def clear(self):
        """Limpia todas las métricas"""
        for label in self.metrics_labels.values():
            label.setText("--")


class ConfigInfoPanel(QWidget):
    """Panel para mostrar información de configuración"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Inicializa el widget"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Título
        title = QLabel("Configuración del Sistema")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # Grid para parámetros
        grid = QGridLayout()
        
        self.param_labels = {}
        
        params = [
            'Ancho de banda (MHz)',
            'Separación subportadoras (kHz)',
            'Modulación',
            'Tipo CP',
            'Subportadoras útiles (Nc)',
            'Puntos FFT (N)',
            'Frecuencia muestreo (MHz)',
            'Duración CP (μs)',
            'Bits por símbolo'
        ]
        
        for i, param in enumerate(params):
            label = QLabel(f"{param}:")
            value = QLabel("--")
            value.setStyleSheet("color: blue;")
            
            grid.addWidget(label, i, 0)
            grid.addWidget(value, i, 1)
            
            self.param_labels[param] = value
        
        layout.addLayout(grid)
        layout.addStretch()
    
    def update_config(self, config_info):
        """
        Actualiza la información de configuración
        
        Args:
            config_info: Diccionario con información de configuración
        """
        for key, value in config_info.items():
            if key in self.param_labels:
                self.param_labels[key].setText(str(value))


class StatusBar(QWidget):
    """Barra de estado personalizada"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Inicializa el widget"""
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        self.status_label = QLabel("Listo")
        self.status_label.setStyleSheet("padding: 5px;")
        
        layout.addWidget(self.status_label)
        layout.addStretch()
    
    def set_status(self, message, color="black"):
        """
        Establece el mensaje de estado
        
        Args:
            message: Mensaje a mostrar
            color: Color del texto
        """
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; padding: 5px;")
    
    def set_error(self, message):
        """Muestra un mensaje de error"""
        self.set_status(f"Error: {message}", "red")
    
    def set_success(self, message):
        """Muestra un mensaje de éxito"""
        self.set_status(message, "green")
    
    def set_warning(self, message):
        """Muestra un mensaje de advertencia"""
        self.set_status(f"Advertencia: {message}", "orange")


class ImageComparisonWidget(QWidget):
    """Widget para comparar imágenes"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Inicializa el widget"""
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        # Panel izquierdo - Original
        left_panel = QVBoxLayout()
        left_title = QLabel("Imagen Original")
        left_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        self.original_label = QLabel()
        self.original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.original_label.setMinimumSize(300, 300)
        self.original_label.setStyleSheet("border: 1px solid gray;")
        
        left_panel.addWidget(left_title)
        left_panel.addWidget(self.original_label)
        
        # Panel derecho - Recibida
        right_panel = QVBoxLayout()
        right_title = QLabel("Imagen Recibida")
        right_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        self.received_label = QLabel()
        self.received_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.received_label.setMinimumSize(300, 300)
        self.received_label.setStyleSheet("border: 1px solid gray;")
        
        right_panel.addWidget(right_title)
        right_panel.addWidget(self.received_label)
        
        # Métricas de calidad
        metrics_panel = QVBoxLayout()
        self.psnr_label = QLabel("PSNR: --")
        self.ssim_label = QLabel("SSIM: --")
        
        metrics_panel.addWidget(self.psnr_label)
        metrics_panel.addWidget(self.ssim_label)
        metrics_panel.addStretch()
        
        right_panel.addLayout(metrics_panel)
        
        # Agregar paneles al layout principal
        layout.addLayout(left_panel)
        layout.addLayout(right_panel)
    
    def set_images(self, original_pixmap, received_pixmap, psnr=None, ssim=None):
        """
        Establece las imágenes a comparar
        
        Args:
            original_pixmap: QPixmap de la imagen original
            received_pixmap: QPixmap de la imagen recibida
            psnr: Valor PSNR (opcional)
            ssim: Valor SSIM (opcional)
        """
        # Escalar imágenes manteniendo aspecto
        scaled_original = original_pixmap.scaled(
            300, 300, 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        scaled_received = received_pixmap.scaled(
            300, 300,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.original_label.setPixmap(scaled_original)
        self.received_label.setPixmap(scaled_received)
        
        # Actualizar métricas
        if psnr is not None:
            self.psnr_label.setText(f"PSNR: {psnr:.2f} dB")
        
        if ssim is not None:
            self.ssim_label.setText(f"SSIM: {ssim:.4f}")
    
    def clear(self):
        """Limpia las imágenes"""
        self.original_label.clear()
        self.received_label.clear()
        self.psnr_label.setText("PSNR: --")
        self.ssim_label.setText("SSIM: --")