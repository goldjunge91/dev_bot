cmake_minimum_required(VERSION 3.5)
project(gubot_description)

find_package(ament_cmake REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()

  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_urdf_geometry
    tests/test_urdf_geometry.py
    TIMEOUT 30
  )
endif()

install(
  DIRECTORY urdf meshes rviz launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
