cmake_minimum_required(VERSION 3.8)
project(spirit_high_msgs)

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(std_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)


set(msg_files
  "msg/SpatialMeasurement.msg"
  "msg/ExtrapolatedMap.msg"
  "msg/MeasurementArray.msg"
)
rosidl_generate_interfaces(${PROJECT_NAME}
  ${msg_files}
  DEPENDENCIES std_msgs nav_msgs
)
ament_export_dependencies(rosidl_default_generators std_msgs nav_msgs geometry_msgs)
ament_package()
