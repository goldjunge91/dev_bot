cmake_minimum_required(VERSION 3.5)
project(gubot_navigation)

find_package(ament_cmake REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  find_package(ament_cmake_pytest REQUIRED)
  ament_lint_auto_find_test_dependencies()
  ament_add_pytest_test(test_nav2_config test/test_nav2_config.py TIMEOUT 30)
  ament_add_pytest_test(test_nav_launch_args test/test_nav_launch_args.py
                        TIMEOUT 120)
endif()

install(DIRECTORY launch config maps DESTINATION share/${PROJECT_NAME})

ament_package()
