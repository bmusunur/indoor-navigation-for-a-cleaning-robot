#!/usr/bin/env python3
"""Generate src/cleaning_robot_gazebo/worlds/indoor_house.sdf.

Floor plan (10 m x 8 m, origin at the centre, robot spawns at (-2, 0)):

    y=+4 +-----------------------+--------------------+
         |                       |      BEDROOM       |
         |                       |  bed, nightstands, |
         |      LIVING ROOM      |  wardrobe, desk    |
         |  sofa, coffee table,  +------+    +--------+  y=0  (door x 2.5..3.5)
         |  TV stand, armchair,  door              |
         |  bookshelf, plant     |      KITCHEN /     |
         |                       |      DINING        |
         |                       |  table + 4 chairs, |
         |                       |  counter, fridge   |
    y=-4 +-----------------------+--------------------+
        x=-5                    x=1 (door y -0.5..0.5) x=5

All furniture is built from primitives (no meshes), so the world has no
external dependencies. Tables and chairs are modelled with legs so the
robot's low LiDAR sees them the way a real robot vacuum would.

Edit the layout below and re-run:
    python3 tools/generate_indoor_world.py
"""

import os

WALL_T = 0.15      # wall thickness (m)
WALL_H = 1.0       # wall height (m) - kept low so you can look inside from above

WALL_COLOR = '0.85 0.82 0.75 1'
WOOD = '0.55 0.36 0.20 1'
FABRIC = '0.25 0.35 0.55 1'
WHITE = '0.95 0.95 0.95 1'
GREY = '0.45 0.45 0.48 1'
GREEN = '0.20 0.55 0.25 1'
BED = '0.80 0.75 0.85 1'


def material(rgba):
    return (f'<material><ambient>{rgba}</ambient><diffuse>{rgba}</diffuse>'
            f'<specular>0.1 0.1 0.1 1</specular></material>')


def box_link(name, x, y, z, sx, sy, sz, rgba):
    geom = f'<geometry><box><size>{sx} {sy} {sz}</size></box></geometry>'
    return f"""
      <link name="{name}">
        <pose>{x} {y} {z} 0 0 0</pose>
        <collision name="collision">{geom}</collision>
        <visual name="visual">{geom}{material(rgba)}</visual>
      </link>"""


def cyl_link(name, x, y, z, r, h, rgba):
    geom = f'<geometry><cylinder><radius>{r}</radius><length>{h}</length></cylinder></geometry>'
    return f"""
      <link name="{name}">
        <pose>{x} {y} {z} 0 0 0</pose>
        <collision name="collision">{geom}</collision>
        <visual name="visual">{geom}{material(rgba)}</visual>
      </link>"""


def model(name, x, y, links, yaw=0.0):
    return f"""
    <model name="{name}">
      <static>true</static>
      <pose>{x} {y} 0 0 0 {yaw}</pose>{''.join(links)}
    </model>"""


def solid_box(name, x, y, sx, sy, sz, rgba, yaw=0.0):
    """Furniture that reaches the floor (sofa, bed, cabinet...)."""
    return model(name, x, y, [box_link('body', 0, 0, sz / 2, sx, sy, sz, rgba)], yaw)


def table(name, x, y, sx, sy, h, rgba, leg=0.05, top_t=0.04):
    """Table top + 4 legs (the robot can drive underneath)."""
    lx, ly = sx / 2 - leg, sy / 2 - leg
    links = [box_link('top', 0, 0, h - top_t / 2, sx, sy, top_t, rgba)]
    for i, (dx, dy) in enumerate([(lx, ly), (lx, -ly), (-lx, ly), (-lx, -ly)]):
        links.append(box_link(f'leg_{i}', dx, dy, (h - top_t) / 2, leg, leg, h - top_t, rgba))
    return model(name, x, y, links)


def chair(name, x, y, yaw, rgba=WOOD, s=0.42, seat_h=0.45, back_h=0.45, leg=0.04):
    """Chair with 4 legs, seat and backrest. Backrest is on the local -x side."""
    l = s / 2 - leg / 2
    links = [box_link('seat', 0, 0, seat_h - 0.02, s, s, 0.04, rgba),
             box_link('back', -s / 2 + 0.02, 0, seat_h + back_h / 2, 0.04, s, back_h, rgba)]
    for i, (dx, dy) in enumerate([(l, l), (l, -l), (-l, l), (-l, -l)]):
        links.append(box_link(f'leg_{i}', dx, dy, (seat_h - 0.04) / 2, leg, leg, seat_h - 0.04, rgba))
    return model(name, x, y, links, yaw)


def plant(name, x, y):
    return model(name, x, y, [
        cyl_link('pot', 0, 0, 0.15, 0.18, 0.30, GREY),
        cyl_link('leaves', 0, 0, 0.55, 0.28, 0.50, GREEN),
    ])


def walls():
    t, h = WALL_T, WALL_H
    segs = [
        # name, x, y, sx, sy
        ('north', 0.0, 4.0, 10.0 + t, t),
        ('south', 0.0, -4.0, 10.0 + t, t),
        ('east', 5.0, 0.0, t, 8.0 + t),
        ('west', -5.0, 0.0, t, 8.0 + t),
        # living room | bedroom+kitchen, 1 m doorway at y in [-0.5, 0.5]
        ('divider_x_upper', 1.0, 2.25, t, 3.5),
        ('divider_x_lower', 1.0, -2.25, t, 3.5),
        # bedroom | kitchen, 1 m doorway at x in [2.5, 3.5]
        ('divider_y_left', 1.75, 0.0, 1.5, t),
        ('divider_y_right', 4.25, 0.0, 1.5, t),
    ]
    links = [box_link(n, x, y, h / 2, sx, sy, h, WALL_COLOR) for n, x, y, sx, sy in segs]
    return model('house_walls', 0, 0, links)


def furniture():
    items = []
    # ---- Living room (x -5..1) ----
    items.append(solid_box('sofa', -4.45, 1.5, 0.85, 2.0, 0.8, FABRIC))
    items.append(table('coffee_table', -3.3, 1.5, 0.6, 1.0, 0.45, WOOD))
    items.append(solid_box('tv_stand', 0.7, 1.8, 0.4, 1.6, 0.5, GREY))
    items.append(solid_box('armchair', -3.6, -2.4, 0.8, 0.8, 0.8, FABRIC, yaw=0.5))
    items.append(solid_box('bookshelf', -1.8, -3.7, 1.2, 0.3, 1.8, WOOD))
    items.append(plant('plant', 0.45, -3.45))
    # ---- Bedroom (x 1..5, y 0..4) ----
    items.append(solid_box('bed', 3.0, 2.9, 1.6, 2.0, 0.5, BED))
    items.append(solid_box('nightstand_left', 1.85, 3.6, 0.4, 0.4, 0.5, WOOD))
    items.append(solid_box('nightstand_right', 4.15, 3.6, 0.4, 0.4, 0.5, WOOD))
    items.append(solid_box('wardrobe', 4.6, 1.0, 0.6, 1.5, 2.0, WOOD))
    items.append(table('desk', 1.45, 1.2, 0.6, 1.2, 0.75, WHITE))
    # ---- Kitchen / dining (x 1..5, y -4..0) ----
    items.append(solid_box('kitchen_counter', 4.6, -1.95, 0.6, 2.5, 0.9, WHITE))
    items.append(solid_box('fridge', 4.55, -3.55, 0.7, 0.7, 1.8, GREY))
    items.append(table('dining_table', 2.6, -2.2, 1.4, 0.9, 0.75, WOOD))
    # chairs face the table; backrest on the far side
    for i, cx in enumerate([2.25, 2.95]):
        items.append(chair(f'chair_n{i}', cx, -1.4, -1.5708))   # north side
        items.append(chair(f'chair_s{i}', cx, -3.0, 1.5708))    # south side
    items.append(model('trash_bin', 1.4, -3.6, [cyl_link('bin', 0, 0, 0.3, 0.18, 0.6, GREY)]))
    return ''.join(items)


def world():
    return f"""<?xml version="1.0"?>
<!-- AUTO-GENERATED by tools/generate_indoor_world.py - edit that script, not this file. -->
<sdf version="1.9">
  <world name="indoor_house">

    <physics name="1ms" type="ignored">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>

    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    <plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu"/>

    <gui fullscreen="0">
      <camera name="user_camera">
        <pose>0 -9 11 0 0.9 1.5708</pose>
      </camera>
    </gui>

    <scene>
      <ambient>0.6 0.6 0.6 1</ambient>
      <background>0.8 0.85 0.9 1</background>
      <shadows>true</shadows>
    </scene>

    <light type="directional" name="sun">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.9 0.9 0.9 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
      <direction>-0.4 0.3 -0.9</direction>
    </light>

    <model name="floor">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry><plane><normal>0 0 1</normal><size>30 30</size></plane></geometry>
          <surface><friction><ode><mu>1.0</mu><mu2>1.0</mu2></ode></friction></surface>
        </collision>
        <visual name="visual">
          <geometry><plane><normal>0 0 1</normal><size>30 30</size></plane></geometry>
          {material('0.70 0.65 0.58 1')}
        </visual>
      </link>
    </model>
{walls()}
{furniture()}
  </world>
</sdf>
"""


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, '..', 'src', 'cleaning_robot_gazebo', 'worlds', 'indoor_house.sdf')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w') as f:
        f.write(world())
    print(f'wrote {os.path.normpath(out)}')
