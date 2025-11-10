"""
Módulo para generación de códigos ortogonales para CDMA.
Soporta códigos Walsh-Hadamard y códigos Gold.
"""

import numpy as np
from typing import List, Tuple, Optional
import warnings


class CodeGenerator:
    """
    Clase para generar códigos de esparcimiento ortogonales para sistemas CDMA.
    """
    
    @staticmethod
    def generate_walsh_codes(n_users: int) -> np.ndarray:
        """
        Genera códigos Walsh-Hadamard ortogonales usando la construcción recursiva.
        
        Los códigos Walsh son perfectamente ortogonales y se generan usando la
        matriz de Hadamard. El número de usuarios debe ser una potencia de 2.
        
        Args:
            n_users: Número de usuarios (debe ser potencia de 2)
            
        Returns:
            np.ndarray: Matriz de códigos Walsh de forma (n_users, n_users)
                       Cada fila es un código de esparcimiento para un usuario
                       
        Raises:
            ValueError: Si n_users no es una potencia de 2 o es menor que 1
            
        Example:
            >>> codes = CodeGenerator.generate_walsh_codes(4)
            >>> codes.shape
            (4, 4)
        """
        if n_users < 1:
            raise ValueError("El número de usuarios debe ser al menos 1")
        
        # Verificar si es potencia de 2
        if not CodeGenerator._is_power_of_2(n_users):
            # Redondear a la siguiente potencia de 2
            next_power = CodeGenerator._next_power_of_2(n_users)
            warnings.warn(
                f"El número de usuarios {n_users} no es potencia de 2. "
                f"Se generarán {next_power} códigos y se tomarán los primeros {n_users}."
            )
            n_users_actual = next_power
        else:
            n_users_actual = n_users
        
        # Generar matriz de Hadamard recursivamente
        hadamard = CodeGenerator._generate_hadamard_matrix(n_users_actual)
        
        # Convertir de {1, -1} a {1, -1} normalizado
        # Los códigos Walsh se mantienen en formato bipolar {-1, +1}
        codes = hadamard.astype(np.float64)
        
        # Si se solicitaron menos códigos que la potencia de 2, recortar
        if n_users < n_users_actual:
            codes = codes[:n_users, :]
        
        return codes
    
    
    @staticmethod
    def verify_orthogonality(codes: np.ndarray, threshold: float = 1e-10) -> Tuple[bool, np.ndarray]:
        """
        Verifica la ortogonalidad de un conjunto de códigos.
        
        Calcula la matriz de correlación cruzada y verifica que los códigos
        sean ortogonales (correlación cero excepto en la diagonal).
        
        Args:
            codes: Matriz de códigos (n_users, code_length)
            threshold: Umbral para considerar correlación como cero
            
        Returns:
            Tuple[bool, np.ndarray]: 
                - bool: True si los códigos son ortogonales
                - np.ndarray: Matriz de correlación normalizada
                
        Example:
            >>> codes = CodeGenerator.generate_walsh_codes(4)
            >>> is_ortho, corr_matrix = CodeGenerator.verify_orthogonality(codes)
            >>> is_ortho
            True
        """
        n_users, code_length = codes.shape
        
        # Calcular matriz de correlación
        correlation_matrix = np.zeros((n_users, n_users))
        
        for i in range(n_users):
            for j in range(n_users):
                # Correlación normalizada
                correlation = np.dot(codes[i], codes[j]) / code_length
                correlation_matrix[i, j] = correlation
        
        # Verificar ortogonalidad
        # Los códigos son ortogonales si la matriz de correlación es la identidad
        is_orthogonal = True
        for i in range(n_users):
            for j in range(n_users):
                if i == j:
                    # Diagonal debe ser 1 (autocorrelación)
                    if abs(correlation_matrix[i, j] - 1.0) > threshold:
                        is_orthogonal = False
                else:
                    # Fuera de diagonal debe ser 0 (ortogonalidad)
                    if abs(correlation_matrix[i, j]) > threshold:
                        is_orthogonal = False
        
        return is_orthogonal, correlation_matrix
    
    @staticmethod
    def get_code_properties(codes: np.ndarray) -> dict:
        """
        Calcula propiedades estadísticas de los códigos.
        
        Args:
            codes: Matriz de códigos
            
        Returns:
            dict: Diccionario con propiedades de los códigos
        """
        is_ortho, corr_matrix = CodeGenerator.verify_orthogonality(codes)
        
        # Extraer correlaciones cruzadas (fuera de diagonal)
        n_users = codes.shape[0]
        cross_correlations = []
        for i in range(n_users):
            for j in range(i+1, n_users):
                cross_correlations.append(abs(corr_matrix[i, j]))
        
        properties = {
            'n_codes': codes.shape[0],
            'code_length': codes.shape[1],
            'is_orthogonal': is_ortho,
            'max_cross_correlation': max(cross_correlations) if cross_correlations else 0.0,
            'avg_cross_correlation': np.mean(cross_correlations) if cross_correlations else 0.0,
            'correlation_matrix': corr_matrix
        }
        
        return properties
    
    # ==================== Métodos auxiliares ====================
    
    @staticmethod
    def _is_power_of_2(n: int) -> bool:
        """Verifica si un número es potencia de 2."""
        return n > 0 and (n & (n - 1)) == 0
    
    @staticmethod
    def _next_power_of_2(n: int) -> int:
        """Calcula la siguiente potencia de 2."""
        return 2 ** int(np.ceil(np.log2(n)))
    
    @staticmethod
    def _generate_hadamard_matrix(n: int) -> np.ndarray:
        """
        Genera matriz de Hadamard de orden n usando construcción de Sylvester.
        
        Args:
            n: Orden de la matriz (debe ser potencia de 2)
            
        Returns:
            np.ndarray: Matriz de Hadamard de tamaño (n, n)
        """
        if n == 1:
            return np.array([[1]])
        
        # Construcción recursiva: H(2n) = [H(n)  H(n)]
        #                                 [H(n) -H(n)]
        half = n // 2
        h_half = CodeGenerator._generate_hadamard_matrix(half)
        
        # Construir matriz de Hadamard de orden n
        h = np.zeros((n, n), dtype=np.int8)
        h[:half, :half] = h_half
        h[:half, half:] = h_half
        h[half:, :half] = h_half
        h[half:, half:] = -h_half
        
        return h
    
    

# ==================== Funciones de utilidad ====================

def generate_codes(n_users: int, code_type: str = 'walsh') -> np.ndarray:
    """
    Función de conveniencia para generar códigos.
    
    Args:
        n_users: Número de usuarios
        code_type: Tipo de código ('walsh' o 'gold')
        
    Returns:
        np.ndarray: Matriz de códigos
    """
    generator = CodeGenerator()
    
    if code_type.lower() == 'walsh':
        return generator.generate_walsh_codes(n_users)
    else:
        raise ValueError(f"Tipo de código '{code_type}' no reconocido. Use 'walsh' o 'gold'.")


if __name__ == "__main__":
    # Ejemplo de uso
    print("=== Generador de Códigos CDMA ===\n")
    
    # Generar códigos Walsh
    n_users = 4
    print(f"Generando {n_users} códigos Walsh-Hadamard...")
    walsh_codes = CodeGenerator.generate_walsh_codes(n_users)
    print(f"Forma de la matriz: {walsh_codes.shape}")
    print(f"Códigos:\n{walsh_codes}\n")
    
    # Verificar ortogonalidad
    is_ortho, corr_matrix = CodeGenerator.verify_orthogonality(walsh_codes)
    print(f"¿Son ortogonales? {is_ortho}")
    print(f"Matriz de correlación:\n{corr_matrix}\n")
    
    # Propiedades
    props = CodeGenerator.get_code_properties(walsh_codes)
    print("Propiedades de los códigos Walsh:")
    print(f"  - Número de códigos: {props['n_codes']}")
    print(f"  - Longitud: {props['code_length']}")
    print(f"  - Ortogonales: {props['is_orthogonal']}")
    print(f"  - Correlación cruzada máxima: {props['max_cross_correlation']:.6f}\n")
    
    # Generar códigos Gold
    print(f"Generando {n_users} códigos Gold...")
    gold_codes = CodeGenerator.generate_gold_codes(n_users, length=7)
    print(f"Forma de la matriz: {gold_codes.shape}")
    print(f"Códigos:\n{gold_codes}\n")
    
    # Propiedades Gold
    props_gold = CodeGenerator.get_code_properties(gold_codes)
    print("Propiedades de los códigos Gold:")
    print(f"  - Número de códigos: {props_gold['n_codes']}")
    print(f"  - Longitud: {props_gold['code_length']}")
    print(f"  - Ortogonales: {props_gold['is_orthogonal']}")
    print(f"  - Correlación cruzada máxima: {props_gold['max_cross_correlation']:.6f}")
    print(f"  - Correlación cruzada promedio: {props_gold['avg_cross_correlation']:.6f}")