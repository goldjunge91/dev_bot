cmake_minimum_required(VERSION 3.5)
project(gubot_description)

find_package(ament_cmake REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()

  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_urdf_geometry
    test/test_urdf_geometry.py
    TIMEOUT 30
  )
  ament_add_pytest_test(test_urdf_variants
    test/test_urdf_variants.py
    TIMEOUT 60
  )
endif()

install(
  DIRECTORY urdf meshes rviz launch config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
