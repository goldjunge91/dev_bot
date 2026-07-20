cmake_minimum_required(VERSION 3.16)
project(mecanum_pico LANGUAGES CXX)

if(CMAKE_CXX_COMPILER_ID MATCHES "(GNU|Clang)")
  add_compile_options(-Wall -Wextra)
endif()

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------
set(THIS_PACKAGE_INCLUDE_DEPENDS
    diagnostic_msgs diagnostic_updater hardware_interface pluginlib rclcpp
    rclcpp_lifecycle)

find_package(ament_cmake REQUIRED)
foreach(Dependency IN ITEMS ${THIS_PACKAGE_INCLUDE_DEPENDS})
  find_package(${Dependency} REQUIRED)
endforeach()

# ---------------------------------------------------------------------------
# Compile the hardware interface shared library
# ---------------------------------------------------------------------------
add_library(mecanum_pico SHARED hardware/hardware_diagnostics.cpp
                                hardware/mecanum_pico.cpp)
target_compile_features(mecanum_pico PUBLIC cxx_std_17)
target_include_directories(
  mecanum_pico PUBLIC $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/hardware/include>
                      $<INSTALL_INTERFACE:include/mecanum_pico>)
ament_target_dependencies(mecanum_pico PUBLIC ${THIS_PACKAGE_INCLUDE_DEPENDS})

target_link_libraries(mecanum_pico PUBLIC serial)

# Visibility macro: export symbols when building the DLL
target_compile_definitions(${PROJECT_NAME} PRIVATE "MECANUM_PICO_BUILDING_DLL")

# Export hardware plugin descriptor
pluginlib_export_plugin_description_file(hardware_interface mecanum_pico.xml)

# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------
install(DIRECTORY hardware/include/ DESTINATION include/mecanum_pico)
install(DIRECTORY description/launch description/ros2_control description/urdf
                  description/rviz DESTINATION share/mecanum_pico)
install(DIRECTORY bringup/launch bringup/config DESTINATION share/mecanum_pico)
install(
  TARGETS mecanum_pico
  EXPORT export_mecanum_pico
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)

# ---------------------------------------------------------------------------
# Tests (Sprint 0: scaffolding only — zero tests, zero failures)
# ---------------------------------------------------------------------------
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)

  # Sprint 1 — Wheel data model tests
  ament_add_gtest(test_wheel test/test_wheel.cpp)
  target_include_directories(test_wheel
                             PRIVATE ${PROJECT_SOURCE_DIR}/hardware/include)
  # NOTE: test_wheel only uses header-only Wheel struct; no link to mecanum_pico
  # lib needed yet

  # IMU-Orientierungsfusion (Komplementärfilter, header-only wie Wheel)
  ament_add_gtest(test_imu_fusion test/test_imu_fusion.cpp)
  target_include_directories(test_imu_fusion
                             PRIVATE ${PROJECT_SOURCE_DIR}/hardware/include)

  # Sprint 2 — PicoComms serial protocol tests OLD:
  # ament_add_gtest(test_pico_comms test/test_pico_comms.cpp )
  # target_include_directories(test_pico_comms PRIVATE
  # ${PROJECT_SOURCE_DIR}/hardware/include ) NEW:
  ament_add_gtest(test_pico_comms test/test_pico_comms.cpp)
  target_include_directories(test_pico_comms
                             PRIVATE ${PROJECT_SOURCE_DIR}/hardware/include)
  target_link_libraries(test_pico_comms serial)

  # Sprint 3 — Hardware interface plugin load tests
  ament_add_gtest(test_hardware_interface test/test_hardware_interface.cpp)
  target_include_directories(test_hardware_interface
                             PRIVATE ${PROJECT_SOURCE_DIR}/hardware/include)
  target_link_libraries(test_hardware_interface mecanum_pico)
  ament_target_dependencies(test_hardware_interface hardware_interface
                            pluginlib rclcpp)

  # /diagnostics reporting (Pico serial connection + control-loop rate)
  ament_add_gtest(test_hardware_diagnostics test/test_hardware_diagnostics.cpp)
  target_include_directories(test_hardware_diagnostics
                             PRIVATE ${PROJECT_SOURCE_DIR}/hardware/include)
  target_link_libraries(test_hardware_diagnostics mecanum_pico)
  ament_target_dependencies(test_hardware_diagnostics diagnostic_msgs
                            diagnostic_updater rclcpp)
endif()

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------
ament_export_targets(export_mecanum_pico HAS_LIBRARY_TARGET)
ament_export_dependencies(${THIS_PACKAGE_INCLUDE_DEPENDS})
ament_package()
