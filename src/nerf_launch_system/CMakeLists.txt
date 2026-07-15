cmake_minimum_required(VERSION 3.8)

if(POLICY CMP0009)
  cmake_policy(SET CMP0009 NEW)
endif()

project(nerf_launch_system)
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(pluginlib REQUIRED)
find_package(diagnostic_msgs REQUIRED)
find_package(diagnostic_updater REQUIRED)
# libserial is a system library, usually found via PkgConfig or just linking
find_package(PkgConfig REQUIRED)
pkg_check_modules(SERIAL REQUIRED libserial)

# C++ Hardware Interface Library
add_library(nerf_system SHARED
  hardware/nerf_command_logic.cpp
  hardware/nerf_communication.cpp
  hardware/nerf_diagnostics.cpp
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
ament_target_dependencies(nerf_system
  diagnostic_msgs
  diagnostic_updater
)

pluginlib_export_plugin_description_file(hardware_interface nerf_launch_system_plugins.xml)

# Install C++ headers (hardware/include/nerf_launch_system/*.hpp already
# nests the package dir, so keep the plain include/ destination)
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
  nerf_launch_system/nerf_control_node.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME nerf_control_node
)

# Install launch, config, description, worlds, firmware
install(
  DIRECTORY launch config description firmware worlds
  DESTINATION share/${PROJECT_NAME}
)

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)

  # /diagnostics reporting (serial connection, armed state, control-loop rate)
  ament_add_gtest(test_nerf_diagnostics
    test/test_nerf_diagnostics.cpp
  )
  target_include_directories(test_nerf_diagnostics PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/hardware/include
  )
  target_link_libraries(test_nerf_diagnostics nerf_system)
  ament_target_dependencies(test_nerf_diagnostics
    diagnostic_msgs diagnostic_updater rclcpp
  )

  # Pure Tilt-/SHOT-Kommandologik (kein ROS/Serial) — Regressionstest für den
  # read()/write() Tilt-Mirror-Bug (A1).
  ament_add_gtest(test_nerf_command_logic
    test/test_nerf_command_logic.cpp
  )
  target_include_directories(test_nerf_command_logic PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/hardware/include
  )
  target_link_libraries(test_nerf_command_logic nerf_system)
endif()

ament_export_targets(export_nerf_system HAS_LIBRARY_TARGET)
ament_export_dependencies(
  rclcpp
  rclcpp_lifecycle
  hardware_interface
  pluginlib
  diagnostic_msgs
  diagnostic_updater
)

ament_package()
