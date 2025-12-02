"""
Simulador OFDM con Especificaciones LTE
Archivo principal para ejecutar la aplicación
"""
import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import OFDMSimulatorGUI


def main():
    """Función principal"""
    app = QApplication(sys.argv)
    app.setApplicationName("Simulador OFDM - LTE")
    
    # Crear y mostrar ventana principal
    window = OFDMSimulatorGUI()
    window.show()
    
    # Configuración inicial
    window.update_config()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()