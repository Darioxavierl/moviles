"""
Motor de simulación para ejecutar experimentos OFDM
"""
import numpy as np
import time
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from core.ofdm_system import OFDMSystem
from config.lte_params import LTEConfig


@dataclass
class SimulationConfig:
    """Configuración para una simulación"""
    bandwidth: float
    delta_f: float
    modulation: str
    cp_type: str
    n_bits: int
    snr_db: Optional[float] = None


@dataclass
class SimulationResults:
    """Resultados de una simulación"""
    ber: float
    errors: int
    evm: float
    snr_db: Optional[float]
    n_bits: int
    transmission_time: Optional[float] = None
    transmitted_symbols: Optional[np.ndarray] = None
    received_symbols: Optional[np.ndarray] = None
    transmitted_bits: Optional[np.ndarray] = None
    received_bits: Optional[np.ndarray] = None


class OFDMSimulator:
    """
    Simulador de sistema OFDM
    Proporciona interfaz de alto nivel para ejecutar simulaciones
    """
    
    def __init__(self):
        """Inicializa el simulador"""
        self.system = None
        self.config = None
        self.last_results = None
    
    def configure(self, sim_config: SimulationConfig):
        """
        Configura el simulador con parámetros específicos
        
        Args:
            sim_config: Configuración de simulación
        """
        lte_config = LTEConfig(
            bandwidth=sim_config.bandwidth,
            delta_f=sim_config.delta_f,
            modulation=sim_config.modulation,
            cp_type=sim_config.cp_type
        )
        
        self.config = sim_config
        self.system = OFDMSystem(lte_config)
    
    def run_single(self, bits: Optional[np.ndarray] = None, 
                   measure_time: bool = True) -> SimulationResults:
        """
        Ejecuta una simulación única
        
        Args:
            bits: Array de bits a transmitir (None = generar aleatorios)
            measure_time: Si True, mide el tiempo de transmisión
            
        Returns:
            SimulationResults con los resultados
        """
        if self.system is None:
            raise RuntimeError("Sistema no configurado. Llame a configure() primero.")
        
        # Generar bits si no se proporcionan
        if bits is None:
            bits = np.random.randint(0, 2, self.config.n_bits)
        
        # Ejecutar simulación usando el método simulate
        results = self.system.simulate(bits, snr_db=self.config.snr_db)
        
        # Crear objeto de resultados
        sim_results = SimulationResults(
            ber=results['BER'],
            errors=results['bit_errors'],
            evm=0.0,  # Calcular EVM si es necesario
            snr_db=results['SNR_dB'],
            n_bits=results['transmitted_bits'],
            transmission_time=results['transmission_time'],
            transmitted_symbols=results['symbols_tx'],
            received_symbols=results['symbols_rx'],
            transmitted_bits=results['bits_tx'],
            received_bits=results['bits_rx']
        )
        
        self.last_results = sim_results
        return sim_results
    
    def snr_sweep(self,
                  snr_values: List[float],
                  num_bits: int = 1000,
                  num_runs: int = 10,
                  progress_callback: Optional[Callable] = None) -> Dict:
        """
        Realiza un barrido de SNR calculando BER vs SNR
        
        Args:
            snr_values: Array con valores de SNR en dB
            num_bits: Número de bits por corrida
            num_runs: Número de corridas por SNR
            progress_callback: Función para reportar progreso
            
        Returns:
            dict: Resultados del barrido (BER, SER, intervalos de confianza)
        """
        snr_values = np.atleast_1d(snr_values).astype(float)
        results = {
            'snr_values': snr_values,
            'ber_mean': [],
            'ber_std': [],
            'ber_ci_lower': [],
            'ber_ci_upper': [],
            'ser_mean': [],
            'ser_std': [],
            'ber_runs': [],
            'ser_runs': []
        }
        
        total_steps = len(snr_values)
        
        for idx, snr_db in enumerate(snr_values):
            ber_values = []
            ser_values = []
            
            # Ejecutar num_runs corridas para cada SNR
            for run in range(num_runs):
                # Generar bits aleatorios
                bits = np.random.randint(0, 2, num_bits)
                
                # Establecer SNR en config
                self.config.snr_db = snr_db
                
                # Simular
                sim_results = self.run_single(bits, measure_time=False)
                
                ber_values.append(sim_results.ber)
                ser_values.append(0.0)  # TODO: Implementar cálculo de SER
            
            # Calcular estadísticas
            ber_array = np.array(ber_values)
            ser_array = np.array(ser_values)
            
            ber_mean = np.mean(ber_array)
            ber_std = np.std(ber_array)
            ser_mean = np.mean(ser_array)
            ser_std = np.std(ser_array)
            
            # Calcular intervalo de confianza (95%)
            ber_ci = self._calculate_confidence_interval(ber_array)
            
            results['ber_mean'].append(ber_mean)
            results['ber_std'].append(ber_std)
            results['ber_ci_lower'].append(ber_ci[0] if ber_ci else ber_mean)
            results['ber_ci_upper'].append(ber_ci[1] if ber_ci else ber_mean)
            results['ser_mean'].append(ser_mean)
            results['ser_std'].append(ser_std)
            results['ber_runs'].append(ber_values)
            results['ser_runs'].append(ser_values)
            
            # Reportar progreso
            if progress_callback:
                progress_callback(idx + 1, total_steps, float(snr_db), ber_mean, ser_mean)
        
        # Convertir a arrays numpy
        for key in results:
            if key != 'ber_runs' and key != 'ser_runs':
                results[key] = np.array(results[key])
        
        return results
    
    def _calculate_confidence_interval(self, data, confidence=0.95):
        """
        Calcula el intervalo de confianza de los datos
        
        Args:
            data: Array de datos
            confidence: Nivel de confianza (default 95%)
            
        Returns:
            tuple: (lower_bound, upper_bound)
        """
        if len(data) == 0:
            return None
        
        from scipy import stats
        
        n = len(data)
        mean = np.mean(data)
        std = np.std(data, ddof=1)
        
        # Usar la distribución t de Student
        t_value = stats.t.ppf((1 + confidence) / 2, n - 1)
        margin_of_error = t_value * std / np.sqrt(n)
        
        return (mean - margin_of_error, mean + margin_of_error)
    
    def run_ber_sweep(self, 
                      snr_start: float,
                      snr_end: float,
                      snr_step: float,
                      n_iterations: int = 10,
                      progress_callback: Optional[Callable] = None) -> Dict:
        """
        Ejecuta un barrido de SNR para generar curva BER
        
        Args:
            snr_start: SNR inicial en dB
            snr_end: SNR final en dB
            snr_step: Paso de SNR en dB
            n_iterations: Número de iteraciones por SNR
            progress_callback: Función de callback para progreso
            
        Returns:
            Dict con resultados del barrido
        """
        if self.system is None:
            raise RuntimeError("Sistema no configurado. Llame a configure() primero.")
        
        snr_range = np.arange(snr_start, snr_end + snr_step, snr_step)
        
        results = self.system.run_ber_sweep(
            self.config.n_bits,
            snr_range,
            n_iterations,
            progress_callback
        )
        
        return results
    
    def run_batch(self, 
                  snr_values: List[float],
                  n_runs: int = 1) -> List[SimulationResults]:
        """
        Ejecuta múltiples simulaciones con diferentes SNRs
        
        Args:
            snr_values: Lista de valores SNR a simular
            n_runs: Número de corridas por SNR
            
        Returns:
            Lista de SimulationResults
        """
        if self.system is None:
            raise RuntimeError("Sistema no configurado. Llame a configure() primero.")
        
        all_results = []
        
        for snr in snr_values:
            self.config.snr_db = snr
            
            for _ in range(n_runs):
                result = self.run_single(measure_time=False)
                all_results.append(result)
        
        return all_results
    
    def get_system_info(self) -> Dict:
        """
        Obtiene información del sistema configurado
        
        Returns:
            Dict con información del sistema
        """
        if self.system is None:
            return {}
        
        return self.system.config.get_info()
    
    def get_throughput_info(self) -> Dict:
        """
        Calcula información de throughput del sistema
        
        Returns:
            Dict con métricas de throughput
        """
        if self.system is None:
            return {}
        
        return self.system.calculate_transmission_metrics(self.config.n_bits)


class BatchSimulator:
    """
    Simulador por lotes para comparar múltiples configuraciones
    """
    
    def __init__(self):
        """Inicializa el simulador por lotes"""
        self.simulators = []
        self.results = []
    
    def add_configuration(self, sim_config: SimulationConfig):
        """
        Agrega una configuración al lote
        
        Args:
            sim_config: Configuración de simulación
        """
        simulator = OFDMSimulator()
        simulator.configure(sim_config)
        self.simulators.append({
            'config': sim_config,
            'simulator': simulator
        })
    
    def run_all(self, progress_callback: Optional[Callable] = None) -> List[Dict]:
        """
        Ejecuta todas las configuraciones
        
        Args:
            progress_callback: Función de callback para progreso
            
        Returns:
            Lista de resultados
        """
        results = []
        total = len(self.simulators)
        
        for idx, sim_dict in enumerate(self.simulators):
            config = sim_dict['config']
            simulator = sim_dict['simulator']
            
            if progress_callback:
                progress = ((idx + 1) / total) * 100
                progress_callback(progress, f"Configuración {idx+1}/{total}")
            
            result = simulator.run_single()
            
            results.append({
                'config': config,
                'results': result
            })
        
        self.results = results
        return results
    
    def compare_modulations(self, 
                           bandwidth: float,
                           delta_f: float,
                           snr_db: float,
                           n_bits: int) -> Dict:
        """
        Compara diferentes esquemas de modulación
        
        Args:
            bandwidth: Ancho de banda en MHz
            delta_f: Separación de subportadoras en kHz
            snr_db: SNR en dB
            n_bits: Número de bits a transmitir
            
        Returns:
            Dict con comparación de resultados
        """
        modulations = ['QPSK', '16-QAM', '64-QAM']
        comparison = {}
        
        for mod in modulations:
            config = SimulationConfig(
                bandwidth=bandwidth,
                delta_f=delta_f,
                modulation=mod,
                cp_type='normal',
                n_bits=n_bits,
                snr_db=snr_db
            )
            
            simulator = OFDMSimulator()
            simulator.configure(config)
            result = simulator.run_single()
            
            comparison[mod] = {
                'ber': result.ber,
                'evm': result.evm,
                'errors': result.errors,
                'bits_per_symbol': simulator.system.config.bits_per_symbol
            }
        
        return comparison
    
    def compare_bandwidths(self,
                          modulation: str,
                          delta_f: float,
                          snr_db: float,
                          n_bits: int) -> Dict:
        """
        Compara diferentes anchos de banda LTE
        
        Args:
            modulation: Esquema de modulación
            delta_f: Separación de subportadoras en kHz
            snr_db: SNR en dB
            n_bits: Número de bits a transmitir
            
        Returns:
            Dict con comparación de resultados
        """
        bandwidths = [1.25, 2.5, 5.0, 10.0, 15.0, 20.0]
        comparison = {}
        
        for bw in bandwidths:
            config = SimulationConfig(
                bandwidth=bw,
                delta_f=delta_f,
                modulation=modulation,
                cp_type='normal',
                n_bits=n_bits,
                snr_db=snr_db
            )
            
            simulator = OFDMSimulator()
            simulator.configure(config)
            result = simulator.run_single()
            throughput = simulator.get_throughput_info()
            
            comparison[bw] = {
                'ber': result.ber,
                'evm': result.evm,
                'throughput_mbps': throughput['throughput_mbps'],
                'n_ofdm_symbols': throughput['n_ofdm_symbols']
            }
        
        return comparison


class MonteCarloSimulator:
    """
    Simulador Monte Carlo para análisis estadístico
    """
    
    def __init__(self, simulator: OFDMSimulator):
        """
        Inicializa el simulador Monte Carlo
        
        Args:
            simulator: Simulador OFDM configurado
        """
        self.simulator = simulator
    
    def run(self, 
            n_iterations: int,
            snr_db: float,
            progress_callback: Optional[Callable] = None) -> Dict:
        """
        Ejecuta simulación Monte Carlo
        
        Args:
            n_iterations: Número de iteraciones
            snr_db: SNR en dB
            progress_callback: Función de callback para progreso
            
        Returns:
            Dict con estadísticas
        """
        self.simulator.config.snr_db = snr_db
        
        ber_values = []
        evm_values = []
        
        for i in range(n_iterations):
            if progress_callback:
                progress = ((i + 1) / n_iterations) * 100
                progress_callback(progress, f"Iteración {i+1}/{n_iterations}")
            
            result = self.simulator.run_single(measure_time=False)
            ber_values.append(result.ber)
            evm_values.append(result.evm)
        
        # Calcular estadísticas
        ber_array = np.array(ber_values)
        evm_array = np.array(evm_values)
        
        return {
            'snr_db': snr_db,
            'n_iterations': n_iterations,
            'ber_mean': np.mean(ber_array),
            'ber_std': np.std(ber_array),
            'ber_min': np.min(ber_array),
            'ber_max': np.max(ber_array),
            'ber_median': np.median(ber_array),
            'evm_mean': np.mean(evm_array),
            'evm_std': np.std(evm_array),
            'confidence_interval_95': 1.96 * np.std(ber_array) / np.sqrt(n_iterations)
        }