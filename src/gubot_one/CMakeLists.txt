cmake_minimum_required(VERSION 3.5)
project(gubot_one)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY gubot_hardware.repos gubot_simulation.repos
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_package_structure
    test/test_package_structure.py
    TIMEOUT 30
  )
endif()

ament_package()
