cmake_minimum_required(VERSION 3.8)
project(gubot_gazebo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)

  ament_add_pytest_test(test_harmonic_launch_args test/test_harmonic_launch_args.py)
endif()

install(DIRECTORY
  launch
  worlds
  config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
