"""
Módulo para generación de mensajes para sistemas CDMA.
Soporta mensajes aleatorios, patrones de prueba y conversión de texto.
"""

import numpy as np
from typing import List, Union, Optional
import warnings


class MessageGenerator:
    """
    Clase para generar diferentes tipos de mensajes para simulaciones CDMA.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Inicializa el generador de mensajes.
        
        Args:
            seed: Semilla para reproducibilidad (opcional)
        """
        if seed is not None:
            np.random.seed(seed)
        self.seed = seed
    
    # ==================== Generación de mensajes aleatorios ====================
    
    def generate_random_bits(self, n_bits: int) -> np.ndarray:
        """
        Genera una secuencia aleatoria de bits.
        
        Args:
            n_bits: Número de bits a generar
        
        Returns:
            np.ndarray: Array de bits aleatorios {0, 1}
        
        Raises:
            ValueError: Si n_bits < 1
        
        Example:
            >>> gen = MessageGenerator(seed=42)
            >>> bits = gen.generate_random_bits(8)
            >>> bits.shape
            (8,)
        """
        if n_bits < 1:
            raise ValueError("n_bits debe ser al menos 1")
        
        return np.random.randint(0, 2, size=n_bits, dtype=np.int8)
    
    def generate_random_messages(self, 
                                 n_users: int, 
                                 n_bits: int) -> np.ndarray:
        """
        Genera mensajes aleatorios para múltiples usuarios.
        
        Args:
            n_users: Número de usuarios
            n_bits: Número de bits por mensaje
        
        Returns:
            np.ndarray: Matriz de mensajes (n_users, n_bits)
        
        Example:
            >>> gen = MessageGenerator(seed=42)
            >>> messages = gen.generate_random_messages(3, 4)
            >>> messages.shape
            (3, 4)
        """
        if n_users < 1:
            raise ValueError("n_users debe ser al menos 1")
        if n_bits < 1:
            raise ValueError("n_bits debe ser al menos 1")
        
        messages = np.random.randint(0, 2, size=(n_users, n_bits), dtype=np.int8)
        return messages
    
    def generate_random_message_with_probability(self,
                                                 n_bits: int,
                                                 p_one: float = 0.5) -> np.ndarray:
        """
        Genera mensaje aleatorio con probabilidad específica para bit '1'.
        
        Args:
            n_bits: Número de bits
            p_one: Probabilidad de bit '1' (0.0 a 1.0)
        
        Returns:
            np.ndarray: Array de bits
        
        Example:
            >>> gen = MessageGenerator(seed=42)
            >>> bits = gen.generate_random_message_with_probability(10, p_one=0.7)
            >>> # Aproximadamente 70% de unos
        """
        if not 0.0 <= p_one <= 1.0:
            raise ValueError("p_one debe estar entre 0.0 y 1.0")
        
        return (np.random.random(n_bits) < p_one).astype(np.int8)
    
    # ==================== Patrones de prueba ====================
    
    def generate_pattern(self, pattern_type: str, n_bits: int) -> np.ndarray:
        """
        Genera mensajes con patrones específicos para pruebas.
        
        Args:
            pattern_type: Tipo de patrón:
                - 'all_zeros': Todos ceros
                - 'all_ones': Todos unos
                - 'alternating': Alternante (0,1,0,1,...)
                - 'alternating_reverse': Alternante invertido (1,0,1,0,...)
                - 'block': Bloques (mitad 0, mitad 1)
                - 'ramp': Rampa (0...0,1...1)
            n_bits: Número de bits
        
        Returns:
            np.ndarray: Array con el patrón especificado
        
        Raises:
            ValueError: Si el patrón no es reconocido
        
        Example:
            >>> gen = MessageGenerator()
            >>> pattern = gen.generate_pattern('alternating', 8)
            >>> pattern
            array([0, 1, 0, 1, 0, 1, 0, 1])
        """
        if n_bits < 1:
            raise ValueError("n_bits debe ser al menos 1")
        
        pattern_type = pattern_type.lower()
        
        if pattern_type == 'all_zeros':
            return np.zeros(n_bits, dtype=np.int8)
        
        elif pattern_type == 'all_ones':
            return np.ones(n_bits, dtype=np.int8)
        
        elif pattern_type == 'alternating':
            return np.array([i % 2 for i in range(n_bits)], dtype=np.int8)
        
        elif pattern_type == 'alternating_reverse':
            return np.array([1 - (i % 2) for i in range(n_bits)], dtype=np.int8)
        
        elif pattern_type == 'block':
            half = n_bits // 2
            return np.concatenate([np.zeros(half, dtype=np.int8), 
                                  np.ones(n_bits - half, dtype=np.int8)])
        
        elif pattern_type == 'ramp':
            # Gradual de 0 a 1
            return (np.arange(n_bits) >= n_bits // 2).astype(np.int8)
        
        else:
            raise ValueError(
                f"Patrón '{pattern_type}' no reconocido. "
                f"Opciones: all_zeros, all_ones, alternating, "
                f"alternating_reverse, block, ramp"
            )
    
    def generate_test_patterns(self, n_users: int, n_bits: int) -> np.ndarray:
        """
        Genera diferentes patrones de prueba para cada usuario.
        
        Útil para testing y visualización de comportamiento del sistema.
        
        Args:
            n_users: Número de usuarios
            n_bits: Bits por mensaje
        
        Returns:
            np.ndarray: Matriz (n_users, n_bits) con diferentes patrones
        
        Example:
            >>> gen = MessageGenerator()
            >>> patterns = gen.generate_test_patterns(4, 8)
            >>> patterns.shape
            (4, 8)
        """
        patterns = ['all_zeros', 'all_ones', 'alternating', 'block', 'ramp', 'alternating_reverse']
        messages = []
        
        for i in range(n_users):
            pattern_type = patterns[i % len(patterns)]
            messages.append(self.generate_pattern(pattern_type, n_bits))
        
        return np.array(messages, dtype=np.int8)
    
    # ==================== Conversión de texto ====================
    
    def text_to_bits(self, text: str, encoding: str = 'ascii') -> np.ndarray:
        """
        Convierte texto a secuencia de bits.
        
        Args:
            text: Texto a convertir
            encoding: Codificación ('ascii' o 'utf-8')
        
        Returns:
            np.ndarray: Array de bits representando el texto
        
        Example:
            >>> gen = MessageGenerator()
            >>> bits = gen.text_to_bits('Hi')
            >>> len(bits)
            16  # 2 caracteres * 8 bits
        """
        if not text:
            raise ValueError("El texto no puede estar vacío")
        
        # Convertir texto a bytes
        try:
            text_bytes = text.encode(encoding)
        except UnicodeEncodeError:
            raise ValueError(f"No se puede codificar el texto con '{encoding}'")
        
        # Convertir cada byte a bits
        bits = []
        for byte in text_bytes:
            # Convertir byte a 8 bits
            bits.extend([int(b) for b in format(byte, '08b')])
        
        return np.array(bits, dtype=np.int8)
    
    def bits_to_text(self, bits: np.ndarray, encoding: str = 'ascii') -> str:
        """
        Convierte secuencia de bits a texto.
        
        Args:
            bits: Array de bits (longitud debe ser múltiplo de 8)
            encoding: Codificación ('ascii' o 'utf-8')
        
        Returns:
            str: Texto decodificado
        
        Raises:
            ValueError: Si la longitud de bits no es múltiplo de 8
        
        Example:
            >>> gen = MessageGenerator()
            >>> bits = np.array([0,1,0,0,1,0,0,0, 0,1,1,0,1,0,0,1])
            >>> text = gen.bits_to_text(bits)
            >>> text
            'Hi'
        """
        if len(bits) % 8 != 0:
            raise ValueError("La longitud de bits debe ser múltiplo de 8")
        
        # Convertir bits a bytes
        text_bytes = bytearray()
        for i in range(0, len(bits), 8):
            byte_bits = bits[i:i+8]
            byte_str = ''.join(map(str, byte_bits))
            byte_value = int(byte_str, 2)
            text_bytes.append(byte_value)
        
        # Convertir bytes a texto
        try:
            text = text_bytes.decode(encoding)
        except UnicodeDecodeError:
            raise ValueError(f"No se puede decodificar con '{encoding}'")
        
        return text
    
    def generate_text_messages(self, 
                              texts: List[str], 
                              pad_to_length: Optional[int] = None) -> np.ndarray:
        """
        Convierte múltiples textos a mensajes binarios.
        
        Args:
            texts: Lista de textos
            pad_to_length: Longitud objetivo (rellena con ceros si es necesario)
        
        Returns:
            np.ndarray: Matriz de mensajes binarios
        
        Example:
            >>> gen = MessageGenerator()
            >>> messages = gen.generate_text_messages(['Hi', 'OK'], pad_to_length=20)
            >>> messages.shape
            (2, 20)
        """
        bit_arrays = []
        
        for text in texts:
            bits = self.text_to_bits(text)
            
            # Padding si es necesario
            if pad_to_length is not None:
                if len(bits) > pad_to_length:
                    warnings.warn(
                        f"Texto '{text}' truncado de {len(bits)} a {pad_to_length} bits"
                    )
                    bits = bits[:pad_to_length]
                elif len(bits) < pad_to_length:
                    padding = np.zeros(pad_to_length - len(bits), dtype=np.int8)
                    bits = np.concatenate([bits, padding])
            
            bit_arrays.append(bits)
        
        return np.array(bit_arrays, dtype=np.int8)
    
    # ==================== Utilidades de análisis ====================
    
    def get_message_statistics(self, message: np.ndarray) -> dict:
        """
        Calcula estadísticas de un mensaje.
        
        Args:
            message: Array de bits
        
        Returns:
            dict: Diccionario con estadísticas
        
        Example:
            >>> gen = MessageGenerator()
            >>> msg = np.array([1, 0, 1, 1, 0, 1])
            >>> stats = gen.get_message_statistics(msg)
            >>> stats['ones_ratio']
            0.6666...
        """
        n_bits = len(message)
        n_ones = np.sum(message)
        n_zeros = n_bits - n_ones
        
        stats = {
            'n_bits': n_bits,
            'n_ones': n_ones,
            'n_zeros': n_zeros,
            'ones_ratio': n_ones / n_bits if n_bits > 0 else 0.0,
            'zeros_ratio': n_zeros / n_bits if n_bits > 0 else 0.0,
            'entropy': self._calculate_entropy(message)
        }
        
        return stats
    
    def _calculate_entropy(self, message: np.ndarray) -> float:
        """
        Calcula la entropía de Shannon del mensaje.
        
        Args:
            message: Array de bits
        
        Returns:
            float: Entropía en bits
        """
        if len(message) == 0:
            return 0.0
        
        n_ones = np.sum(message)
        n_zeros = len(message) - n_ones
        
        p_one = n_ones / len(message)
        p_zero = n_zeros / len(message)
        
        entropy = 0.0
        if p_one > 0:
            entropy -= p_one * np.log2(p_one)
        if p_zero > 0:
            entropy -= p_zero * np.log2(p_zero)
        
        return entropy
    
    def compare_messages(self, msg1: np.ndarray, msg2: np.ndarray) -> dict:
        """
        Compara dos mensajes y calcula métricas de similitud.
        
        Args:
            msg1: Primer mensaje
            msg2: Segundo mensaje
        
        Returns:
            dict: Métricas de comparación
        
        Example:
            >>> gen = MessageGenerator()
            >>> msg1 = np.array([1, 0, 1, 1])
            >>> msg2 = np.array([1, 0, 0, 1])
            >>> comp = gen.compare_messages(msg1, msg2)
            >>> comp['hamming_distance']
            1
        """
        if len(msg1) != len(msg2):
            raise ValueError("Los mensajes deben tener la misma longitud")
        
        # Distancia de Hamming
        hamming_dist = np.sum(msg1 != msg2)
        
        # Similitud
        similarity = 1.0 - (hamming_dist / len(msg1))
        
        comparison = {
            'hamming_distance': hamming_dist,
            'similarity': similarity,
            'differences': hamming_dist,
            'matches': len(msg1) - hamming_dist
        }
        
        return comparison
    
    # ==================== Generación de secuencias especiales ====================
    
    def generate_pn_sequence(self, length: int, taps: List[int]) -> np.ndarray:
        """
        Genera una secuencia pseudoaleatoria usando LFSR.
        
        Args:
            length: Longitud de la secuencia
            taps: Posiciones de feedback del LFSR
        
        Returns:
            np.ndarray: Secuencia pseudoaleatoria
        
        Example:
            >>> gen = MessageGenerator()
            >>> seq = gen.generate_pn_sequence(15, [4, 3])
            >>> len(seq)
            15
        """
        if length < 1:
            raise ValueError("length debe ser al menos 1")
        
        max_tap = max(taps) if taps else 0
        register_length = max_tap
        
        # Estado inicial
        register = np.ones(register_length, dtype=np.int8)
        sequence = np.zeros(length, dtype=np.int8)
        
        for i in range(length):
            sequence[i] = register[-1]
            
            # Calcular feedback
            feedback = 0
            for tap in taps:
                if tap <= register_length:
                    feedback ^= register[tap - 1]
            
            # Desplazar
            register = np.roll(register, 1)
            register[0] = feedback
        
        return sequence
    
    def generate_barker_sequence(self, length: int) -> np.ndarray:
        """
        Genera una secuencia de Barker (buenas propiedades de autocorrelación).
        
        Args:
            length: Longitud (2, 3, 4, 5, 7, 11, o 13)
        
        Returns:
            np.ndarray: Secuencia de Barker
        
        Raises:
            ValueError: Si la longitud no corresponde a una secuencia de Barker
        """
        barker_sequences = {
            2: [1, 0],
            3: [1, 1, 0],
            4: [1, 1, 0, 1],
            5: [1, 1, 1, 0, 1],
            7: [1, 1, 1, 0, 0, 1, 0],
            11: [1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0],
            13: [1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1]
        }
        
        if length not in barker_sequences:
            raise ValueError(
                f"No existe secuencia de Barker de longitud {length}. "
                f"Longitudes válidas: {list(barker_sequences.keys())}"
            )
        
        return np.array(barker_sequences[length], dtype=np.int8)


# ==================== Funciones de utilidad ====================

def generate_random_bits(n_bits: int, seed: Optional[int] = None) -> np.ndarray:
    """
    Función de conveniencia para generar bits aleatorios.
    
    Args:
        n_bits: Número de bits
        seed: Semilla opcional
    
    Returns:
        np.ndarray: Bits aleatorios
    """
    gen = MessageGenerator(seed=seed)
    return gen.generate_random_bits(n_bits)


def generate_random_messages(n_users: int, 
                            n_bits: int, 
                            seed: Optional[int] = None) -> np.ndarray:
    """
    Función de conveniencia para generar múltiples mensajes aleatorios.
    
    Args:
        n_users: Número de usuarios
        n_bits: Bits por mensaje
        seed: Semilla opcional
    
    Returns:
        np.ndarray: Matriz de mensajes
    """
    gen = MessageGenerator(seed=seed)
    return gen.generate_random_messages(n_users, n_bits)


if __name__ == "__main__":
    # Ejemplos de uso
    print("=== Generador de Mensajes CDMA ===\n")
    
    # Crear generador con semilla para reproducibilidad
    gen = MessageGenerator(seed=42)
    
    # Ejemplo 1: Mensajes aleatorios
    print("Ejemplo 1: Mensajes aleatorios")
    print("-" * 60)
    n_users = 3
    n_bits = 8
    
    messages = gen.generate_random_messages(n_users, n_bits)
    print(f"Generados {n_users} mensajes de {n_bits} bits:")
    for i, msg in enumerate(messages):
        print(f"  Usuario {i+1}: {msg}")
    
    # Estadísticas
    print("\nEstadísticas del Usuario 1:")
    stats = gen.get_message_statistics(messages[0])
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    
    # Ejemplo 2: Patrones de prueba
    print("\n" + "=" * 60)
    print("Ejemplo 2: Patrones de prueba")
    print("-" * 60)
    
    patterns = ['all_zeros', 'all_ones', 'alternating', 'block']
    for pattern_type in patterns:
        pattern = gen.generate_pattern(pattern_type, 8)
        print(f"  {pattern_type:20s}: {pattern}")
    
    # Ejemplo 3: Patrones de prueba para múltiples usuarios
    print("\n" + "=" * 60)
    print("Ejemplo 3: Patrones diferentes para cada usuario")
    print("-" * 60)
    
    test_messages = gen.generate_test_patterns(4, 8)
    for i, msg in enumerate(test_messages):
        print(f"  Usuario {i+1}: {msg}")
    
    # Ejemplo 4: Conversión de texto
    print("\n" + "=" * 60)
    print("Ejemplo 4: Conversión de texto a bits")
    print("-" * 60)
    
    text = "CDMA"
    bits = gen.text_to_bits(text)
    print(f"Texto: '{text}'")
    print(f"Bits ({len(bits)} bits): {bits}")
    print(f"En grupos de 8: ", end="")
    for i in range(0, len(bits), 8):
        print(f"{bits[i:i+8]} ", end="")
    print()
    
    # Recuperar texto
    recovered_text = gen.bits_to_text(bits)
    print(f"Texto recuperado: '{recovered_text}'")
    
    # Ejemplo 5: Múltiples textos
    print("\n" + "=" * 60)
    print("Ejemplo 5: Mensajes de texto para múltiples usuarios")
    print("-" * 60)
    
    texts = ['Hi', 'OK', 'Go']
    text_messages = gen.generate_text_messages(texts, pad_to_length=24)
    
    print(f"Textos originales: {texts}")
    print(f"Forma de matriz: {text_messages.shape}")
    for i, msg in enumerate(text_messages):
        print(f"  Usuario {i+1} ('{texts[i]}'): {msg[:16]}... ({len(msg)} bits)")
    
    # Ejemplo 6: Comparación de mensajes
    print("\n" + "=" * 60)
    print("Ejemplo 6: Comparación de mensajes")
    print("-" * 60)
    
    msg1 = gen.generate_random_bits(10)
    msg2 = gen.generate_random_bits(10)
    
    print(f"Mensaje 1: {msg1}")
    print(f"Mensaje 2: {msg2}")
    
    comparison = gen.compare_messages(msg1, msg2)
    print(f"\nComparación:")
    print(f"  Distancia de Hamming: {comparison['hamming_distance']}")
    print(f"  Similitud: {comparison['similarity']:.2%}")
    print(f"  Coincidencias: {comparison['matches']}/{len(msg1)}")
    
    # Ejemplo 7: Secuencias especiales
    print("\n" + "=" * 60)
    print("Ejemplo 7: Secuencias especiales")
    print("-" * 60)
    
    # Secuencia PN
    pn_seq = gen.generate_pn_sequence(15, taps=[4, 3])
    print(f"Secuencia PN (15 bits): {pn_seq}")
    
    # Secuencia de Barker
    barker = gen.generate_barker_sequence(7)
    print(f"Secuencia de Barker (7): {barker}")
    
    # Entropía
    print(f"\nEntropía de secuencias:")
    print(f"  Aleatorio: {gen._calculate_entropy(msg1):.4f} bits")
    print(f"  All zeros: {gen._calculate_entropy(gen.generate_pattern('all_zeros', 10)):.4f} bits")
    print(f"  Alternante: {gen._calculate_entropy(gen.generate_pattern('alternating', 10)):.4f} bits")