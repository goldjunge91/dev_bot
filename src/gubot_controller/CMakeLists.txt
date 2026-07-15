cmake_minimum_required(VERSION 3.5)
project(gubot_controller)

find_package(ament_cmake REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
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
  ament_add_pytest_test(test_controller_launch
    tests/test_controller_launch.py
    TIMEOUT 30
  )
endif()

install(
  DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
