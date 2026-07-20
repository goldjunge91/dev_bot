cmake_minimum_required(VERSION 3.5)
project(gubot_gazebo)

find_package(ament_cmake REQUIRED)

# Modell-Suchpfad für Ignition/Gazebo (wie husarion_gz_worlds): stellt models/
# (construction_cone, construction_barrel für obstacles.world) über
# IGN_GAZEBO_RESOURCE_PATH bereit
ament_environment_hooks(
  "${CMAKE_CURRENT_SOURCE_DIR}/env-hooks/${PROJECT_NAME}.sh.in")

option(GUBOT_E2E "E2E-Simulationstests registrieren (langsam, startet Gazebo)"
       OFF)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  find_package(ament_cmake_pytest REQUIRED)
  ament_lint_auto_find_test_dependencies()
  ament_add_pytest_test(test_bridge_config test/test_bridge_config.py TIMEOUT
                        120)

  if(GUBOT_E2E)
    find_package(launch_testing_ament_cmake REQUIRED)
    add_launch_test(
      test/test_e2e_sim_drive.py
      TARGET
      test_e2e_sim_drive
      TIMEOUT
      300
      ENV
      GUBOT_E2E=1
      ROS_DOMAIN_ID=77)
    set_tests_properties(test_e2e_sim_drive PROPERTIES LABELS "e2e")
  endif()
endif()

install(DIRECTORY launch config worlds models DESTINATION share/${PROJECT_NAME})

ament_package()
