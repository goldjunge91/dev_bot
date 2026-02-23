cmake_minimum_required(VERSION 3.8)

if(POLICY CMP0009)
  cmake_policy(SET CMP0009 NEW)
endif()

project(nerf_standalone)
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(pluginlib REQUIRED)
# libserial is a system library, usually found via PkgConfig or just linking
find_package(PkgConfig REQUIRED)
pkg_check_modules(SERIAL REQUIRED libserial)

# C++ Hardware Interface Library
add_library(nerf_system SHARED
  hardware/nerf_system.cpp
)

target_include_directories(nerf_system PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/hardware/include>
  $<INSTALL_INTERFACE:include>
  ${SERIAL_INCLUDE_DIRS}
)

target_link_libraries(nerf_system
  rclcpp::rclcpp
  rclcpp_lifecycle::rclcpp_lifecycle
  hardware_interface::hardware_interface
  pluginlib::pluginlib
  ${SERIAL_LIBRARIES}
)

pluginlib_export_plugin_description_file(hardware_interface nerf_standalone_plugins.xml)

# Install C++ headers
install(
  DIRECTORY hardware/include/
  DESTINATION include
)

# Install C++ library
install(
  TARGETS nerf_system
  EXPORT export_nerf_system
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

# Install Python modules
ament_python_install_package(${PROJECT_NAME})

# Install Python scripts (entry points)
install(PROGRAMS
  nerf_standalone/nerf_control_node.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME nerf_control_node
)

# Install launch, config, description, worlds, firmware
install(
  DIRECTORY launch config description firmware worlds
  DESTINATION share/${PROJECT_NAME}
)

ament_export_include_directories(include)
ament_export_libraries(nerf_system)
ament_export_dependencies(
  rclcpp
  rclcpp_lifecycle
  hardware_interface
  pluginlib
)

ament_package()
