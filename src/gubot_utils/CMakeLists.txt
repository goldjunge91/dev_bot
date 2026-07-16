cmake_minimum_required(VERSION 3.5)
project(gubot_utils)

find_package(ament_cmake REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

install(
  DIRECTORY autostart cycloneDDS docs scripts
  DESTINATION share/${PROJECT_NAME}
)

install(
  PROGRAMS
    scripts/teleop_twist_nerf_keyboard.py
    scripts/teleop__nerf_joystick.py
    scripts/debug_tilt.py
    scripts/imu_hw_test.py
  DESTINATION lib/${PROJECT_NAME}
  PERMISSIONS
    OWNER_READ OWNER_WRITE OWNER_EXECUTE
    GROUP_READ GROUP_EXECUTE
    WORLD_READ WORLD_EXECUTE
)

ament_package()
