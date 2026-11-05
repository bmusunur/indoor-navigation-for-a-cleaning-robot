cmake_minimum_required(VERSION 3.8)
project(cleaning_robot_slam)

find_package(ament_cmake REQUIRED)

install(DIRECTORY config launch rviz maps
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
