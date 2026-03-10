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
  # find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # uncomment the line when a copyright and license is not present in all source files
  #set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # uncomment the line when this package is not in a git repo
  #set(ament_cmake_cpplint_FOUND TRUE)
  # ament_lint_auto_find_test_dependencies()

  find_package(ament_cmake_pytest REQUIRED)

  # Logic to discover workspace prefixes in the install folder
  get_filename_component(INSTALL_ROOT "${CMAKE_INSTALL_PREFIX}" DIRECTORY)
  file(GLOB WS_PREFIXES LIST_DIRECTORIES true "${INSTALL_ROOT}/*")

  set(WS_AMENT_PREFIX_PATH "")
  set(WS_PYTHONPATH "")
  foreach(WS_PREFIX ${WS_PREFIXES})
    if(IS_DIRECTORY "${WS_PREFIX}")
      set(WS_AMENT_PREFIX_PATH "${WS_PREFIX}:${WS_AMENT_PREFIX_PATH}")
      set(WS_PYTHONPATH "${WS_PREFIX}/local/lib/python3.10/dist-packages:${WS_PREFIX}/lib/python3.10/site-packages:${WS_PYTHONPATH}")
    endif()
  endforeach()

  ament_add_pytest_test(test_launch_args test/test_launch_args.py
    APPEND_ENV 
      "AMENT_PREFIX_PATH=${WS_AMENT_PREFIX_PATH}:$ENV{AMENT_PREFIX_PATH}"
      "PYTHONPATH=${WS_PYTHONPATH}:$ENV{PYTHONPATH}"
  )
  ament_add_pytest_test(test_imu_orientation test/test_imu_orientation.py
    APPEND_ENV 
      "AMENT_PREFIX_PATH=${WS_AMENT_PREFIX_PATH}:$ENV{AMENT_PREFIX_PATH}"
      "PYTHONPATH=${WS_PYTHONPATH}:$ENV{PYTHONPATH}"
  )
endif()

install(
  DIRECTORY config description launch worlds meshes
  DESTINATION share/${PROJECT_NAME}
)

install(
  PROGRAMS scripts/nerf_teleop.py scripts/nerf_joy.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
