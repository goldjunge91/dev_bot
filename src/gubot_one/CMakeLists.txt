cmake_minimum_required(VERSION 3.5)
project(gubot_one)

# find dependencies
find_package(ament_cmake REQUIRED)

install(
  DIRECTORY gubot_hardware.repos gubot_simulation.repos
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
