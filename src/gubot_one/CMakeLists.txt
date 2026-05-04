cmake_minimum_required(VERSION 3.5)
project(gubot_one)

# Default to C99
if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 99)
endif()

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
# uncomment the following section in order to fill in
# further dependencies manually.
# find_package(<dependency> REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  #set(ament_cmake_copyright_FOUND TRUE)
  #set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()

  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_tilt_controller_spawner
    tests/test_tilt_controller_spawner.py
    TIMEOUT 30
  )
  ament_add_pytest_test(test_controller_yaml
    tests/test_controller_yaml.py
    TIMEOUT 30
  )
  ament_add_pytest_test(test_urdf_geometry
    tests/test_urdf_geometry.py
    TIMEOUT 30
  )
  ament_add_pytest_test(test_launch_robot
    tests/test_launch_robot.py
    TIMEOUT 30
  )
endif()

install(
  DIRECTORY bringup controller description gazebo localization
  DESTINATION share/${PROJECT_NAME}
)

install(
  PROGRAMS
    scripts/teleop_twist_nerf_keyboard.py
    scripts/teleop__nerf_joystick.py
    scripts/debug_tilt.py
  DESTINATION lib/${PROJECT_NAME}
  PERMISSIONS
    OWNER_READ OWNER_WRITE OWNER_EXECUTE
    GROUP_READ GROUP_EXECUTE
    WORLD_READ WORLD_EXECUTE
)

ament_package()
