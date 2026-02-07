import numpy as np
import tensorflow as tf
import sionna
from sionna.rt import Camera, PathSolver
import matplotlib.pyplot as plt
from GUI2.config.system_config import ScenarioConfig, AntennaConfig, RFConfig


scene = sionna.rt.load_scene(sionna.rt.scene.munich)

tx = sionna.rt.Transmitter(
    name="gNB", 
    position=ScenarioConfig.GNB_POSITION
)

rx = sionna.rt.Receiver(
        name="UAV1", 
        position=ScenarioConfig.UAV1_POSITION
)

scene.add(tx)
scene.add(rx)

scene.tx_array = sionna.rt.PlanarArray(
            num_rows=AntennaConfig.GNB_ARRAY['num_rows'],
            num_cols=AntennaConfig.GNB_ARRAY['num_cols'],
            vertical_spacing=AntennaConfig.GNB_ARRAY['vertical_spacing'],
            horizontal_spacing=AntennaConfig.GNB_ARRAY['horizontal_spacing'],
            pattern=AntennaConfig.GNB_ARRAY['pattern'],
            polarization=AntennaConfig.GNB_ARRAY['polarization']
        )

scene.rx_array = sionna.rt.PlanarArray(
            num_rows=AntennaConfig.UAV_ARRAY['num_rows'],
            num_cols=AntennaConfig.UAV_ARRAY['num_cols'],
            vertical_spacing=AntennaConfig.UAV_ARRAY['vertical_spacing'],
            horizontal_spacing=AntennaConfig.UAV_ARRAY['horizontal_spacing'],
            pattern=AntennaConfig.UAV_ARRAY['pattern'],
            polarization=AntennaConfig.UAV_ARRAY['polarization']
        )

cam_pos = (ScenarioConfig.GNB_POSITION[0]+300, ScenarioConfig.GNB_POSITION[1]+300, ScenarioConfig.GNB_POSITION[2]+100)
cam = Camera(position=cam_pos)
cam.look_at(rx)

# Compute paths
solver = PathSolver()
paths = solver(scene)


img = scene.render(camera=cam,paths=paths)
plt.axis("off")
plt.show()