"""
Punto de entrada de la aplicación CDMA Simulator.
Inicializa la interfaz gráfica principal basada en PyQt5.
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# Importa la ventana principal
from ui.main_window import MainWindow  # Ajusta la ruta según tu estructura real

def main():
    """Función principal del simulador CDMA."""
    # Crear la aplicación Qt
    app = QApplication(sys.argv)

    # Estilo de la aplicación
    app.setStyle('Fusion')
    
    # (Opcional) Configurar metadatos y estilo
    app.setApplicationName("CDMA Simulator")
    app.setOrganizationName("CDMA Research Lab")
    app.setWindowIcon(QIcon("assets/icons/cdma_icon.png"))  # Opcional, si tienes un ícono
    
    # Crear y mostrar la ventana principal
    window = MainWindow()
    window.show()
    
    # Ejecutar el loop principal de la aplicación
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
