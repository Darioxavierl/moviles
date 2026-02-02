"""
Coverage Analysis - Análisis de Cobertura 2D con LoS/NLoS
Genera mapas de cobertura, throughput y análisis estadístico LoS vs NLoS
"""
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import sys
import os

# Importar configuraciones y sistema
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.system_config import *
from systems.basic_system import BasicUAVSystem

class CoverageAnalysis:
    """
    Análisis completo de cobertura 2D con mapas de throughput y LoS/NLoS
    """
    
    def __init__(self, grid_resolution=15, coverage_range=300, optimal_height=50):
        """
        Inicializar análisis de cobertura
        
        Args:
            grid_resolution: Número de puntos por dimensión (15x15 = 225 puntos)
            coverage_range: Rango de cobertura en metros (±range)
            optimal_height: Altura UAV fija (de Fase 2)
        """
        self.grid_resolution = grid_resolution
        self.coverage_range = coverage_range
        self.optimal_height = optimal_height
        
        print("="*70)
        print("ANÁLISIS DE COBERTURA 2D - LoS vs NLoS")
        print("="*70)
        
        # Generate grid
        self._generate_grid()
        
        # Initialize system
        print("🔧 Inicializando sistema UAV...")
        self.system = BasicUAVSystem()
        
        print(f"🗺️  Grid: {grid_resolution}x{grid_resolution} = {grid_resolution**2} puntos")
        print(f"📏 Área: {2*coverage_range}m x {2*coverage_range}m")
        print(f"🚁 Altura fija: {optimal_height}m (óptima de Fase 2)")
        
        # Storage for results
        self.results = None
    
    def _generate_grid(self):
        """Generar grid 2D de posiciones"""
        x_positions = np.linspace(-self.coverage_range, self.coverage_range, self.grid_resolution)
        y_positions = np.linspace(-self.coverage_range, self.coverage_range, self.grid_resolution)
        
        # Create meshgrid
        self.X, self.Y = np.meshgrid(x_positions, y_positions)
        
        # Flatten for iteration
        self.x_flat = self.X.flatten()
        self.y_flat = self.Y.flatten()
        
        print(f"🗺️  Grid generado: {len(self.x_flat)} posiciones")
    
    def run_coverage_sweep(self, fixed_snr_db=20):
        """Ejecutar sweep completo de cobertura 2D"""
        print(f"\n🗺️  INICIANDO SWEEP DE COBERTURA...")
        print(f"📡 SNR fijo: {fixed_snr_db} dB")
        
        # Initialize results
        throughput_grid = np.zeros(len(self.x_flat))
        los_grid = np.zeros(len(self.x_flat))
        path_loss_grid = np.zeros(len(self.x_flat))
        num_paths_grid = np.zeros(len(self.x_flat))
        spectral_efficiency_grid = np.zeros(len(self.x_flat))
        
        # Original position backup
        original_pos = ScenarioConfig.UAV1_POSITION.copy()
        
        total_points = len(self.x_flat)
        print_interval = max(1, total_points // 10)  # Print every 10%
        
        for i, (x, y) in enumerate(zip(self.x_flat, self.y_flat)):
            if i % print_interval == 0:
                progress = (i / total_points) * 100
                print(f"  Progreso: {progress:.0f}% ({i}/{total_points})")
            
            # Move UAV to new position
            new_position = [x, y, self.optimal_height]
            success = self.system.scenario.move_uav("UAV1", new_position)
            
            if not success:
                continue
            
            # Recalculate paths
            paths = self.system.scenario.get_paths(max_depth=5)
            self.system.paths = paths
            
            # Simulate at fixed SNR
            metrics = self.system._simulate_single_snr(fixed_snr_db)
            
            # Store results
            throughput_grid[i] = metrics['throughput_mbps']
            path_loss_grid[i] = -metrics['channel_gain_db']  # Convert to path loss
            spectral_efficiency_grid[i] = metrics['spectral_efficiency']
            
            # LoS analysis
            if metrics['channel_condition'] and metrics['channel_condition']['is_los']:
                los_grid[i] = 1.0
            else:
                los_grid[i] = 0.0
            
            # Number of paths
            if metrics['channel_condition']:
                num_paths_grid[i] = metrics['channel_condition']['total_paths']
        
        # Restore original position
        self.system.scenario.move_uav("UAV1", original_pos)
        
        # Reshape results to grid
        self.results = {
            'throughput_map': throughput_grid.reshape(self.grid_resolution, self.grid_resolution),
            'los_map': los_grid.reshape(self.grid_resolution, self.grid_resolution),
            'path_loss_map': path_loss_grid.reshape(self.grid_resolution, self.grid_resolution),
            'spectral_efficiency_map': spectral_efficiency_grid.reshape(self.grid_resolution, self.grid_resolution),
            'num_paths_map': num_paths_grid.reshape(self.grid_resolution, self.grid_resolution),
            'X': self.X,
            'Y': self.Y,
            'fixed_snr_db': fixed_snr_db,
            'optimal_height': self.optimal_height
        }
        
        print(f"✅ Sweep completado: {total_points} posiciones")
        return self.results
    
    def analyze_coverage_statistics(self):
        """Analizar estadísticas de cobertura"""
        if self.results is None:
            print("❌ No hay resultados. Ejecute run_coverage_sweep() primero.")
            return None
        
        print(f"\n📊 ESTADÍSTICAS DE COBERTURA:")
        
        # Extract data
        throughput = self.results['throughput_map'].flatten()
        los = self.results['los_map'].flatten()
        path_loss = self.results['path_loss_map'].flatten()
        
        # Overall statistics
        stats = {
            'total_points': len(throughput),
            'avg_throughput_mbps': np.mean(throughput),
            'max_throughput_mbps': np.max(throughput),
            'min_throughput_mbps': np.min(throughput),
            'coverage_area_km2': (2 * self.coverage_range / 1000) ** 2,
            
            # LoS statistics
            'los_percentage': np.mean(los) * 100,
            'los_points': int(np.sum(los)),
            'nlos_points': int(np.sum(1 - los)),
            
            # LoS vs NLoS performance
            'avg_throughput_los': np.mean(throughput[los == 1]) if np.any(los == 1) else 0,
            'avg_throughput_nlos': np.mean(throughput[los == 0]) if np.any(los == 0) else 0,
            
            # Coverage reliability
            'coverage_above_10mbps': np.mean(throughput > 10) * 100,
            'coverage_above_20mbps': np.mean(throughput > 20) * 100,
            'coverage_above_50mbps': np.mean(throughput > 50) * 100,
            
            # Path loss statistics
            'avg_path_loss_db': np.mean(path_loss),
            'path_loss_range_db': np.max(path_loss) - np.min(path_loss)
        }
        
        # Performance advantage
        if stats['avg_throughput_los'] > 0 and stats['avg_throughput_nlos'] > 0:
            stats['los_advantage_db'] = 10 * np.log10(stats['avg_throughput_los'] / stats['avg_throughput_nlos'])
        else:
            stats['los_advantage_db'] = 0
        
        # Print statistics
        print(f"  🗺️  Área total: {stats['coverage_area_km2']:.1f} km²")
        print(f"  📊 Throughput promedio: {stats['avg_throughput_mbps']:.1f} Mbps")
        print(f"  📈 Throughput máximo: {stats['max_throughput_mbps']:.1f} Mbps")
        print(f"  📉 Throughput mínimo: {stats['min_throughput_mbps']:.1f} Mbps")
        print(f"  ")
        print(f"  👁️  Condiciones de propagación:")
        print(f"     • LoS: {stats['los_percentage']:.1f}% ({stats['los_points']} puntos)")
        print(f"     • NLoS: {100-stats['los_percentage']:.1f}% ({stats['nlos_points']} puntos)")
        print(f"  ")
        print(f"  📡 Desempeño por condición:")
        print(f"     • Throughput LoS: {stats['avg_throughput_los']:.1f} Mbps")
        print(f"     • Throughput NLoS: {stats['avg_throughput_nlos']:.1f} Mbps")
        print(f"     • Ventaja LoS: {stats['los_advantage_db']:.1f} dB")
        print(f"  ")
        print(f"  📶 Cobertura de calidad:")
        print(f"     • >10 Mbps: {stats['coverage_above_10mbps']:.1f}%")
        print(f"     • >20 Mbps: {stats['coverage_above_20mbps']:.1f}%")
        print(f"     • >50 Mbps: {stats['coverage_above_50mbps']:.1f}%")
        
        return stats
    
    def generate_coverage_maps(self, save_path="./UAV/outputs/coverage_maps.png"):
        """Generar mapas de cobertura 2D"""
        if self.results is None:
            print("❌ No hay resultados para graficar.")
            return
        
        print(f"\n🗺️  GENERANDO MAPAS DE COBERTURA...")
        
        # Create output directory
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 14))
        
        # Custom colormap for throughput (blue to red)
        colors_throughput = ['#000080', '#0000FF', '#00FFFF', '#FFFF00', '#FF8000', '#FF0000']
        cmap_throughput = LinearSegmentedColormap.from_list('throughput', colors_throughput, N=256)
        
        # 1. Throughput Heatmap (MAIN MAP)
        im1 = ax1.contourf(self.results['X'], self.results['Y'], self.results['throughput_map'], 
                          levels=20, cmap=cmap_throughput)
        ax1.set_xlabel('Posición X [m]', fontweight='bold')
        ax1.set_ylabel('Posición Y [m]', fontweight='bold')
        ax1.set_title(f'Mapa de Throughput @ {self.optimal_height}m altura\n(SNR = {self.results["fixed_snr_db"]} dB)', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        cbar1 = plt.colorbar(im1, ax=ax1)
        cbar1.set_label('Throughput [Mbps]', fontweight='bold')
        
        # Add gNB position
        ax1.scatter(0, 0, s=200, c='white', marker='s', edgecolors='black', linewidth=3, label='gNB')
        ax1.legend()
        
        # 2. LoS/NLoS Map
        im2 = ax2.contourf(self.results['X'], self.results['Y'], self.results['los_map'], 
                          levels=[0, 0.5, 1], colors=['red', 'green'], alpha=0.7)
        ax2.set_xlabel('Posición X [m]', fontweight='bold')
        ax2.set_ylabel('Posición Y [m]', fontweight='bold')
        ax2.set_title('Mapa de Propagación LoS/NLoS', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.scatter(0, 0, s=200, c='white', marker='s', edgecolors='black', linewidth=3)
        
        # Custom legend for LoS/NLoS
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor='green', alpha=0.7, label='LoS'),
                          Patch(facecolor='red', alpha=0.7, label='NLoS'),
                          plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='white', 
                                   markeredgecolor='black', markersize=10, label='gNB')]
        ax2.legend(handles=legend_elements)
        
        # 3. Path Loss Map
        im3 = ax3.contourf(self.results['X'], self.results['Y'], self.results['path_loss_map'], 
                          levels=20, cmap='viridis_r')
        ax3.set_xlabel('Posición X [m]', fontweight='bold')
        ax3.set_ylabel('Posición Y [m]', fontweight='bold')
        ax3.set_title('Mapa de Path Loss', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        cbar3 = plt.colorbar(im3, ax=ax3)
        cbar3.set_label('Path Loss [dB]', fontweight='bold')
        ax3.scatter(0, 0, s=200, c='white', marker='s', edgecolors='black', linewidth=3)
        
        # 4. Spectral Efficiency Map
        im4 = ax4.contourf(self.results['X'], self.results['Y'], self.results['spectral_efficiency_map'], 
                          levels=20, cmap='plasma')
        ax4.set_xlabel('Posición X [m]', fontweight='bold')
        ax4.set_ylabel('Posición Y [m]', fontweight='bold')
        ax4.set_title('Eficiencia Espectral', fontweight='bold')
        ax4.grid(True, alpha=0.3)
        cbar4 = plt.colorbar(im4, ax=ax4)
        cbar4.set_label('SE [bits/s/Hz]', fontweight='bold')
        ax4.scatter(0, 0, s=200, c='white', marker='s', edgecolors='black', linewidth=3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=VisualizationConfig.DPI, bbox_inches='tight')
        
        print(f"✅ Mapas guardados: {save_path}")
        return fig
    
    def save_results(self, data_path="./UAV/outputs/coverage_analysis_data.npz"):
        """Guardar resultados de cobertura"""
        if self.results is None:
            print("❌ No hay resultados para guardar.")
            return
        
        # Create output directory
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        
        # Save all results
        np.savez(data_path,
                throughput_map=self.results['throughput_map'],
                los_map=self.results['los_map'],
                path_loss_map=self.results['path_loss_map'],
                spectral_efficiency_map=self.results['spectral_efficiency_map'],
                num_paths_map=self.results['num_paths_map'],
                X=self.results['X'],
                Y=self.results['Y'],
                fixed_snr_db=self.results['fixed_snr_db'],
                optimal_height=self.results['optimal_height'],
                coverage_range=self.coverage_range,
                grid_resolution=self.grid_resolution)
        
        print(f"✅ Datos guardados: {data_path}")
    
    def generate_report(self):
        """Generar reporte completo de cobertura"""
        if self.results is None:
            print("❌ Ejecute el análisis primero.")
            return
        
        stats = self.analyze_coverage_statistics()
        
        print(f"\n" + "="*70)
        print("REPORTE DE ANÁLISIS DE COBERTURA 2D")
        print("="*70)
        
        # Configuration
        info = self.system.get_system_info()
        print(f"\n📊 CONFIGURACIÓN:")
        print(f"  • Escenario: {info['scene']} (3D)")
        print(f"  • Área: {stats['coverage_area_km2']:.1f} km² ({2*self.coverage_range}m x {2*self.coverage_range}m)")
        print(f"  • Resolución: {self.grid_resolution}x{self.grid_resolution} = {stats['total_points']} puntos")
        print(f"  • Altura UAV: {self.optimal_height}m (óptima)")
        print(f"  • gNB: {info['gnb_antennas']} antenas @ {info['gnb_position']}")
        print(f"  • SNR: {self.results['fixed_snr_db']} dB")
        
        # Coverage performance
        print(f"\n📈 DESEMPEÑO DE COBERTURA:")
        print(f"  🎯 Throughput promedio: {stats['avg_throughput_mbps']:.1f} Mbps")
        print(f"  📊 Rango: {stats['min_throughput_mbps']:.1f} - {stats['max_throughput_mbps']:.1f} Mbps")
        print(f"  📶 Cobertura de calidad:")
        print(f"     • >10 Mbps: {stats['coverage_above_10mbps']:.1f}% del área")
        print(f"     • >20 Mbps: {stats['coverage_above_20mbps']:.1f}% del área") 
        print(f"     • >50 Mbps: {stats['coverage_above_50mbps']:.1f}% del área")
        
        # LoS vs NLoS analysis
        print(f"\n👁️  ANÁLISIS LoS vs NLoS:")
        print(f"  📡 Distribución:")
        print(f"     • LoS: {stats['los_percentage']:.1f}% del área")
        print(f"     • NLoS: {100-stats['los_percentage']:.1f}% del área")
        print(f"  📈 Desempeño:")
        print(f"     • Throughput LoS: {stats['avg_throughput_los']:.1f} Mbps")
        print(f"     • Throughput NLoS: {stats['avg_throughput_nlos']:.1f} Mbps")
        print(f"     • Ventaja LoS: {stats['los_advantage_db']:.1f} dB")
        
        # Recommendations
        print(f"\n💡 RECOMENDACIONES:")
        
        if stats['los_percentage'] > 70:
            print(f"  ✅ Excelente cobertura LoS ({stats['los_percentage']:.0f}%)")
        elif stats['los_percentage'] > 40:
            print(f"  ⚠️  Cobertura LoS moderada ({stats['los_percentage']:.0f}%)")
        else:
            print(f"  ❌ Baja cobertura LoS ({stats['los_percentage']:.0f}%) - optimizar posición gNB")
        
        if stats['coverage_above_20mbps'] > 50:
            print(f"  ✅ Buena cobertura de alta velocidad (>20 Mbps en {stats['coverage_above_20mbps']:.0f}%)")
        else:
            print(f"  ⚠️  Cobertura de alta velocidad limitada")
        
        if stats['los_advantage_db'] > 3:
            print(f"  ✅ Clara ventaja LoS ({stats['los_advantage_db']:.1f} dB)")
        elif stats['los_advantage_db'] > 1:
            print(f"  ⚠️  Ventaja LoS moderada ({stats['los_advantage_db']:.1f} dB)")
        else:
            print(f"  ❌ Ventaja LoS mínima - revisar configuración MIMO")
        
        print("="*70)
        
        return stats

def run_coverage_analysis():
    """Ejecutar análisis completo de cobertura"""
    # Create analysis (reduced grid for speed)
    analysis = CoverageAnalysis(grid_resolution=12, coverage_range=250, optimal_height=50)
    
    # Run coverage sweep
    results = analysis.run_coverage_sweep()
    
    # Analyze statistics
    stats = analysis.analyze_coverage_statistics()
    
    # Generate maps
    analysis.generate_coverage_maps()
    
    # Save data
    analysis.save_results()
    
    # Generate report
    analysis.generate_report()
    
    return analysis, results, stats

if __name__ == "__main__":
    analysis, results, stats = run_coverage_analysis()