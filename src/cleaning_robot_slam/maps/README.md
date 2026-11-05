# Saved maps

Save maps here after a mapping run, from the workspace root:

```bash
ros2 run nav2_map_server map_saver_cli -f src/cleaning_robot_slam/maps/indoor_house
```

That writes `indoor_house.pgm` (the occupancy image) and `indoor_house.yaml`
(resolution, origin, thresholds). Rebuild (`colcon build --packages-select cleaning_robot_slam`)
so the installed share directory picks up new maps.
