"""
Visualizaciones 3D - Sistema UAV 5G NR
Genera las vistas 3D del escenario Munich con UAVs, gNB y análisis de cobertura
"""
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import json
import os

class UAV3DVisualizer:
    """Generador de visualizaciones 3D para sistema UAV 5G NR"""
    
    def __init__(self):
        """Inicializar visualizador 3D"""
        
        print("="*70)
        print("🎨 GENERADOR DE VISUALIZACIONES 3D - UAV 5G NR")
        print("="*70)
        
        # Ensure output directory exists
        self.output_dir = "UAV/dashboard_output/visualizations_3d"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Munich scenario parameters
        self.munich_config = {
            'area_size_m': 500,
            'building_heights': [20, 35, 45, 30, 25, 40],
            'building_positions': [
                [100, 100, 20], [200, 150, 35], [300, 200, 45],
                [150, 300, 30], [350, 350, 25], [250, 50, 40]
            ],
            'gnb_position': [0, 0, 30],
            'uav_positions': {
                'user_uav': [200, 200, 50],
                'relay_uav': [125, 140, 75],  # Optimized position
                'mesh_uav_1': [150, 50, 55],
                'mesh_uav_2': [50, 150, 55]
            }
        }
        
        print("✅ Visualizador 3D inicializado")
        print(f"📁 Directorio de salida: {self.output_dir}")
    
    def create_3d_scenario_view(self):
        """Crear vista 3D completa del escenario Munich con mapa urbano realista"""
        
        fig = plt.figure(figsize=(18, 14))
        ax = fig.add_subplot(111, projection='3d')
        
        area = self.munich_config['area_size_m']
        
        # ===== TERRENO URBANO MUNICH =====
        # Crear un mapa base más realista
        x_ground = np.linspace(0, area, 50)
        y_ground = np.linspace(0, area, 50)
        X_ground, Y_ground = np.meshgrid(x_ground, y_ground)
        
        # Terreno con variaciones (simulando calles y parques)
        Z_ground = 2 * np.sin(X_ground/100) * np.cos(Y_ground/100) + 1
        ax.plot_surface(X_ground, Y_ground, Z_ground, alpha=0.3, color='lightgreen', 
                       linewidth=0, antialiased=True)
        
        # ===== EDIFICIOS URBANOS MUNICH =====
        building_colors = ['#8B4513', '#696969', '#708090', '#2F4F4F', '#8FBC8F', '#CD853F']
        building_names = ['Edificio A', 'Edificio B', 'Edificio C', 'Edificio D', 'Edificio E', 'Edificio F']
        
        for i, (x, y, h) in enumerate(self.munich_config['building_positions']):
            building_size = 35  # Edificios más grandes
            
            # Crear edificio como prisma rectangular más realista
            # Base del edificio
            xx = [x-building_size/2, x+building_size/2, x+building_size/2, x-building_size/2, x-building_size/2]
            yy = [y-building_size/2, y-building_size/2, y+building_size/2, y+building_size/2, y-building_size/2]
            
            # Cara inferior y superior
            for z_level in [0, h]:
                ax.plot(xx, yy, [z_level]*5, 'k-', alpha=0.8, linewidth=2)
            
            # Aristas verticales
            for j in range(4):
                ax.plot([xx[j], xx[j]], [yy[j], yy[j]], [0, h], 'k-', alpha=0.8, linewidth=2)
            
            # Edificio sólido con color distintivo
            ax.bar3d(x-building_size/2, y-building_size/2, 0, building_size, building_size, h, 
                    alpha=0.7, color=building_colors[i], edgecolor='black', linewidth=1)
            
            # Etiqueta del edificio
            ax.text(x, y, h+5, f'{building_names[i]}\n{h}m', fontsize=9, ha='center', va='bottom',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        # ===== ESTACIÓN BASE gNB =====
        gnb_x, gnb_y, gnb_z = self.munich_config['gnb_position']
        
        # Torre gNB más visible y realista
        ax.scatter([gnb_x], [gnb_y], [gnb_z], c='red', s=400, marker='^', 
                  label='gNB Base Station (Torre 5G)', alpha=1.0, edgecolors='darkred', linewidth=3)
        
        # Torre de comunicación (mástil)
        ax.plot([gnb_x, gnb_x], [gnb_y, gnb_y], [0, gnb_z], 'darkred', linewidth=6, alpha=0.9)
        
        # Patrón de cobertura gNB (sector beam más realista)
        sector_angles = np.linspace(-np.pi/3, np.pi/3, 20)  # 120° sector
        sector_radius = 150
        for angle in sector_angles:
            end_x = gnb_x + sector_radius * np.cos(angle + np.pi/4)  # 45° azimuth
            end_y = gnb_y + sector_radius * np.sin(angle + np.pi/4)
            ax.plot([gnb_x, end_x], [gnb_y, end_y], [gnb_z, gnb_z-10], 'r-', alpha=0.3, linewidth=1)
        
        # ===== UAVs CON REPRESENTACIÓN REALISTA =====
        uav_configs = {
            'user_uav': {'color': 'blue', 'marker': 'o', 'label': 'UAV Usuario', 'size': 200},
            'relay_uav': {'color': 'green', 'marker': 's', 'label': 'UAV Relay', 'size': 250}, 
            'mesh_uav_1': {'color': 'orange', 'marker': 'D', 'label': 'UAV Mesh 1', 'size': 180},
            'mesh_uav_2': {'color': 'purple', 'marker': 'v', 'label': 'UAV Mesh 2', 'size': 180}
        }
        
        for uav_type, (x, y, z) in self.munich_config['uav_positions'].items():
            config = uav_configs[uav_type]
            
            # UAV principal
            ax.scatter([x], [y], [z], c=config['color'], s=config['size'], 
                      marker=config['marker'], label=config['label'], alpha=0.9, 
                      edgecolors='black', linewidth=2)
            
            # Hélices del UAV (4 rotores)
            rotor_offset = 8
            rotor_positions = [(x+rotor_offset, y+rotor_offset, z), (x-rotor_offset, y+rotor_offset, z),
                             (x+rotor_offset, y-rotor_offset, z), (x-rotor_offset, y-rotor_offset, z)]
            
            for rx, ry, rz in rotor_positions:
                ax.scatter([rx], [ry], [rz], c=config['color'], s=30, marker='o', alpha=0.6)
            
            # Línea vertical desde el suelo (indicar altura)
            ax.plot([x, x], [y, y], [0, z], '--', color=config['color'], alpha=0.5, linewidth=2)
            
            # Etiqueta de posición
            ax.text(x, y, z+8, f'{config["label"]}\n[{x},{y},{z}m]', 
                   fontsize=8, ha='center', va='bottom',
                   bbox=dict(boxstyle="round,pad=0.2", facecolor=config['color'], alpha=0.7, edgecolor='black'))
        
        # ===== ENLACES DE COMUNICACIÓN 5G =====
        # Enlaces directos gNB-UAVs
        for uav_type, (x, y, z) in self.munich_config['uav_positions'].items():
            if uav_type == 'user_uav':
                # Enlace directo usuario (rojo punteado)
                ax.plot([gnb_x, x], [gnb_y, y], [gnb_z, z], 'r--', linewidth=4, 
                       alpha=0.8, label='Enlace Directo 5G')
            elif uav_type == 'relay_uav':
                # Enlaces relay (verde sólido) 
                ax.plot([gnb_x, x], [gnb_y, y], [gnb_z, z], 'g-', linewidth=5, alpha=0.9)
                user_x, user_y, user_z = self.munich_config['uav_positions']['user_uav']
                ax.plot([x, user_x], [y, user_y], [z, user_z], 'g-', linewidth=5, 
                       alpha=0.9, label='Enlaces Relay')
        
        # Enlaces mesh (naranja)
        mesh_uavs = ['mesh_uav_1', 'mesh_uav_2']
        user_pos = self.munich_config['uav_positions']['user_uav']
        
        for i, uav_type in enumerate(mesh_uavs):
            x, y, z = self.munich_config['uav_positions'][uav_type]
            
            # Mesh a gNB
            ax.plot([gnb_x, x], [gnb_y, y], [gnb_z, z], 'orange', linewidth=3, alpha=0.7)
            # Mesh a usuario
            ax.plot([x, user_pos[0]], [y, user_pos[1]], [z, user_pos[2]], 'orange', 
                   linewidth=3, alpha=0.7, label='Red Mesh' if i == 0 else '')
        
        # Interconnexión mesh
        mesh1_pos = self.munich_config['uav_positions']['mesh_uav_1']
        mesh2_pos = self.munich_config['uav_positions']['mesh_uav_2']
        ax.plot([mesh1_pos[0], mesh2_pos[0]], [mesh1_pos[1], mesh2_pos[1]], 
               [mesh1_pos[2], mesh2_pos[2]], 'purple', linewidth=4, alpha=0.8,
               label='Interconexión Mesh')
        
        # ===== CONFIGURACIÓN DE LA VISTA =====
        ax.set_xlabel('Coordenada X (metros)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Coordenada Y (metros)', fontsize=12, fontweight='bold')
        ax.set_zlabel('Altura Z (metros)', fontsize=12, fontweight='bold')
        ax.set_title('MAPA 3D MUNICH - Sistema UAV 5G NR\nEscenario Urbano Realista con Torres, Edificios y UAVs', 
                    fontsize=16, fontweight='bold', pad=20)
        
        # Límites y aspecto
        ax.set_xlim(-50, area+50)
        ax.set_ylim(-50, area+50)
        ax.set_zlim(0, 120)
        
        # Leyenda mejorada
        ax.legend(loc='upper left', bbox_to_anchor=(0.02, 0.98), fontsize=10, 
                 framealpha=0.9, fancybox=True, shadow=True)
        
        # Grid 3D más visible
        ax.grid(True, alpha=0.4)
        ax.xaxis.pane.fill = False
        ax.yaxis.pane.fill = False
        ax.zaxis.pane.fill = False
        
        # Ángulo de vista óptimo para ver todo el escenario
        ax.view_init(elev=30, azim=45)
        
        # Color de fondo
        fig.patch.set_facecolor('white')
        
        plt.tight_layout()
        plot_path = f"{self.output_dir}/scenario_3d_complete.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return plot_path
    
    def create_coverage_heatmap_3d(self):
        """Crear mapa de calor 3D de cobertura"""
        
        fig = plt.figure(figsize=(14, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # Create coverage grid
        area = self.munich_config['area_size_m']
        x = np.linspace(0, area, 50)
        y = np.linspace(0, area, 50)
        X, Y = np.meshgrid(x, y)
        
        # Simulate coverage based on distance from gNB and UAVs
        gnb_pos = np.array(self.munich_config['gnb_position'])
        relay_pos = np.array(self.munich_config['uav_positions']['relay_uav'])
        
        # Coverage calculation
        Z_coverage = np.zeros_like(X)
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                point = np.array([X[i,j], Y[i,j], 1.5])  # 1.5m user height
                
                # Distance to gNB (direct)
                dist_gnb = np.linalg.norm(point - gnb_pos)
                power_direct = 1000 / (dist_gnb**2 + 1)  # Simple path loss model
                
                # Distance via relay
                dist_to_relay = np.linalg.norm(point - relay_pos)
                dist_relay_gnb = np.linalg.norm(relay_pos - gnb_pos)
                power_relay = 800 / ((dist_to_relay**2 + 1) * (dist_relay_gnb**2 + 1))
                
                # Combined coverage (simplified)
                Z_coverage[i,j] = max(power_direct, power_relay * 1.5)  # Relay gain
        
        # Normalize to throughput-like values
        Z_coverage = Z_coverage / np.max(Z_coverage) * 250  # Max 250 Mbps
        
        # 3D surface plot
        surf = ax.plot_surface(X, Y, Z_coverage, cmap='viridis', alpha=0.8, 
                              linewidth=0, antialiased=True)
        
        # Add buildings as obstacles (lower coverage)
        for x, y, h in self.munich_config['building_positions']:
            # Create coverage shadow
            shadow_size = 40
            x_shadow = np.linspace(x-shadow_size, x+shadow_size, 5)
            y_shadow = np.linspace(y-shadow_size, y+shadow_size, 5)
            X_shadow, Y_shadow = np.meshgrid(x_shadow, y_shadow)
            Z_shadow = np.ones_like(X_shadow) * 10  # Low coverage
            
            ax.plot_surface(X_shadow, Y_shadow, Z_shadow, alpha=0.3, color='red')
        
        # UAV positions
        for uav_type, (x, y, z) in self.munich_config['uav_positions'].items():
            ax.scatter([x], [y], [z], c='white', s=100, marker='o', 
                      edgecolors='black', linewidth=2)
        
        # gNB position
        gnb_x, gnb_y, gnb_z = self.munich_config['gnb_position']
        ax.scatter([gnb_x], [gnb_y], [gnb_z], c='red', s=200, marker='^')
        
        # Styling
        ax.set_xlabel('X (metros)')
        ax.set_ylabel('Y (metros)')
        ax.set_zlabel('Throughput (Mbps)')
        ax.set_title('Mapa de Cobertura 3D - Throughput Estimado', fontsize=16, fontweight='bold')
        
        # Color bar
        fig.colorbar(surf, shrink=0.5, aspect=20, label='Throughput (Mbps)')
        
        # View angle
        ax.view_init(elev=35, azim=-45)
        
        plt.tight_layout()
        plot_path = f"{self.output_dir}/coverage_heatmap_3d.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return plot_path
    
    def create_mimo_beamforming_3d(self):
        """Visualización 3D de patrones MIMO y beamforming"""
        
        fig = plt.figure(figsize=(16, 12))
        
        # Create subplots for different antenna configurations
        ax1 = fig.add_subplot(221, projection='3d')
        ax2 = fig.add_subplot(222, projection='3d')
        ax3 = fig.add_subplot(223, projection='3d')
        ax4 = fig.add_subplot(224, projection='3d')
        
        axes = [ax1, ax2, ax3, ax4]
        configs = ['SISO (1x1)', 'MIMO 2x2', 'MIMO 4x4', 'MIMO 8x4']
        
        for idx, (ax, config) in enumerate(zip(axes, configs)):
            # Create antenna pattern (simplified radiation pattern)
            theta = np.linspace(0, 2*np.pi, 50)
            phi = np.linspace(0, np.pi, 25)
            THETA, PHI = np.meshgrid(theta, phi)
            
            # Different patterns for different MIMO configs
            if idx == 0:  # SISO - omnidirectional
                R = 1 + 0.3 * np.cos(PHI)
            elif idx == 1:  # 2x2 - slight directivity
                R = 1 + 0.5 * np.cos(2*THETA) * np.sin(PHI)
            elif idx == 2:  # 4x4 - more focused
                R = 1 + 0.7 * np.cos(4*THETA) * np.sin(PHI)**2
            else:  # 8x4 - highly directional
                R = 1 + 1.2 * np.cos(8*THETA) * np.sin(PHI)**3
            
            # Convert to Cartesian coordinates
            X = R * np.sin(PHI) * np.cos(THETA)
            Y = R * np.sin(PHI) * np.sin(THETA)
            Z = R * np.cos(PHI)
            
            # Plot surface
            surf = ax.plot_surface(X, Y, Z, cmap='plasma', alpha=0.7, 
                                  linewidth=0, antialiased=True)
            
            # Center point (antenna)
            ax.scatter([0], [0], [0], c='black', s=50, marker='o')
            
            ax.set_title(config, fontweight='bold')
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            
            # Equal aspect ratio
            max_range = 2
            ax.set_xlim(-max_range, max_range)
            ax.set_ylim(-max_range, max_range)
            ax.set_zlim(-max_range, max_range)
            
            ax.view_init(elev=20, azim=45)
        
        plt.suptitle('Patrones de Radiación 3D - Configuraciones MIMO', 
                    fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        plot_path = f"{self.output_dir}/mimo_patterns_3d.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return plot_path
    
    def create_network_topology_3d(self):
        """Crear visualización 3D de topologías de red"""
        
        fig = plt.figure(figsize=(20, 12))
        
        topologies = ['Direct', 'Relay', 'Mesh 2-hop', 'Mesh 3-hop', 'Cooperative']
        
        for idx, topology in enumerate(topologies):
            ax = fig.add_subplot(2, 3, idx+1, projection='3d')
            
            # Base positions
            gnb_pos = self.munich_config['gnb_position']
            uav_positions = self.munich_config['uav_positions']
            
            # Plot all nodes
            ax.scatter(*gnb_pos, c='red', s=200, marker='^', label='gNB')
            
            colors = ['blue', 'green', 'orange', 'purple']
            for i, (uav_type, pos) in enumerate(uav_positions.items()):
                ax.scatter(*pos, c=colors[i], s=100, marker='o', 
                          label=uav_type.replace('_', ' ').title())
            
            # Draw connections based on topology
            user_pos = uav_positions['user_uav']
            relay_pos = uav_positions['relay_uav']
            mesh1_pos = uav_positions['mesh_uav_1']
            mesh2_pos = uav_positions['mesh_uav_2']
            
            if topology == 'Direct':
                # Only gNB to User
                ax.plot([gnb_pos[0], user_pos[0]], [gnb_pos[1], user_pos[1]], 
                       [gnb_pos[2], user_pos[2]], 'b-', linewidth=3, alpha=0.8)
                
            elif topology == 'Relay':
                # gNB -> Relay -> User
                ax.plot([gnb_pos[0], relay_pos[0]], [gnb_pos[1], relay_pos[1]], 
                       [gnb_pos[2], relay_pos[2]], 'g-', linewidth=3, alpha=0.8)
                ax.plot([relay_pos[0], user_pos[0]], [relay_pos[1], user_pos[1]], 
                       [relay_pos[2], user_pos[2]], 'g-', linewidth=3, alpha=0.8)
                
            elif topology == 'Mesh 2-hop':
                # gNB -> Mesh1 -> User
                ax.plot([gnb_pos[0], mesh1_pos[0]], [gnb_pos[1], mesh1_pos[1]], 
                       [gnb_pos[2], mesh1_pos[2]], 'orange', linewidth=3, alpha=0.8)
                ax.plot([mesh1_pos[0], user_pos[0]], [mesh1_pos[1], user_pos[1]], 
                       [mesh1_pos[2], user_pos[2]], 'orange', linewidth=3, alpha=0.8)
                
            elif topology == 'Mesh 3-hop':
                # gNB -> Mesh1 -> Mesh2 -> User
                ax.plot([gnb_pos[0], mesh1_pos[0]], [gnb_pos[1], mesh1_pos[1]], 
                       [gnb_pos[2], mesh1_pos[2]], 'purple', linewidth=2, alpha=0.8)
                ax.plot([mesh1_pos[0], mesh2_pos[0]], [mesh1_pos[1], mesh2_pos[1]], 
                       [mesh1_pos[2], mesh2_pos[2]], 'purple', linewidth=2, alpha=0.8)
                ax.plot([mesh2_pos[0], user_pos[0]], [mesh2_pos[1], user_pos[1]], 
                       [mesh2_pos[2], user_pos[2]], 'purple', linewidth=2, alpha=0.8)
                
            elif topology == 'Cooperative':
                # Multiple paths
                # gNB -> Relay -> User
                ax.plot([gnb_pos[0], relay_pos[0]], [gnb_pos[1], relay_pos[1]], 
                       [gnb_pos[2], relay_pos[2]], 'g-', linewidth=2, alpha=0.8)
                ax.plot([relay_pos[0], user_pos[0]], [relay_pos[1], user_pos[1]], 
                       [relay_pos[2], user_pos[2]], 'g-', linewidth=2, alpha=0.8)
                # gNB -> Mesh1 -> User
                ax.plot([gnb_pos[0], mesh1_pos[0]], [gnb_pos[1], mesh1_pos[1]], 
                       [gnb_pos[2], mesh1_pos[2]], 'orange', linewidth=2, alpha=0.6)
                ax.plot([mesh1_pos[0], user_pos[0]], [mesh1_pos[1], user_pos[1]], 
                       [mesh1_pos[2], user_pos[2]], 'orange', linewidth=2, alpha=0.6)
                # Cooperation links
                ax.plot([relay_pos[0], mesh1_pos[0]], [relay_pos[1], mesh1_pos[1]], 
                       [relay_pos[2], mesh1_pos[2]], 'cyan', linewidth=1, alpha=0.5, linestyle='--')
            
            ax.set_title(f'{topology} Topology', fontweight='bold')
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            ax.set_zlabel('Z (m)')
            
            # Set limits
            ax.set_xlim(0, 400)
            ax.set_ylim(0, 400)
            ax.set_zlim(0, 100)
            
            ax.view_init(elev=25, azim=45)
            
            if idx == 0:  # Only show legend for first plot
                ax.legend(bbox_to_anchor=(0.02, 0.98), loc='upper left', fontsize=8)
        
        plt.suptitle('Topologías de Red 3D - Sistema Multi-UAV', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        plot_path = f"{self.output_dir}/network_topologies_3d.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return plot_path
    
    def generate_all_3d_visualizations(self):
        """Generar todas las visualizaciones 3D"""
        
        print("\n🎨 GENERANDO VISUALIZACIONES 3D COMPLETAS...")
        
        generated_files = {}
        
        # Scenario overview
        print("📍 Vista 3D del escenario...")
        generated_files['scenario'] = self.create_3d_scenario_view()
        
        # Coverage heatmap
        print("🗺️  Mapa de cobertura 3D...")
        generated_files['coverage'] = self.create_coverage_heatmap_3d()
        
        # MIMO patterns
        print("📡 Patrones MIMO 3D...")
        generated_files['mimo'] = self.create_mimo_beamforming_3d()
        
        # Network topologies
        print("🕸️  Topologías de red 3D...")
        generated_files['topologies'] = self.create_network_topology_3d()
        
        print(f"\n✅ VISUALIZACIONES 3D COMPLETADAS!")
        print(f"📁 Archivos guardados en: {self.output_dir}")
        
        for name, path in generated_files.items():
            print(f"  🎨 {name}: {path}")
        
        return generated_files

def main():
    """Función principal para generar visualizaciones 3D"""
    
    print("🎨 INICIANDO GENERACIÓN DE VISUALIZACIONES 3D...")
    
    visualizer = UAV3DVisualizer()
    files = visualizer.generate_all_3d_visualizations()
    
    print(f"\n" + "="*70)
    print("🎊 VISUALIZACIONES 3D COMPLETADAS EXITOSAMENTE!")
    print(f"Total: {len(files)} archivos 3D generados")
    print("="*70)
    
    return visualizer, files

if __name__ == "__main__":
    viz_system, viz_files = main()