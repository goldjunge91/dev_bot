cmake_minimum_required(VERSION 3.5)
project(gubot_gazebo)

find_package(ament_cmake REQUIRED)

# Modell-Suchpfad für Ignition/Gazebo (wie husarion_gz_worlds):
# stellt models/ (construction_cone, construction_barrel für
# obstacles.world) über IGN_GAZEBO_RESOURCE_PATH bereit
ament_environment_hooks(
  "${CMAKE_CURRENT_SOURCE_DIR}/env-hooks/${PROJECT_NAME}.sh.in")

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

install(
  DIRECTORY launch config worlds models
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
