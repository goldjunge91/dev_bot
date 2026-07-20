cmake_minimum_required(VERSION 3.13)

# Pure Pico SDK CMake build (alternative to PlatformIO). Set PICO_SDK_PATH:
# export PICO_SDK_PATH=/path/to/pico-sdk
#
# Usage: mkdir build && cd build cmake .. -DPICO_SDK_PATH=$PICO_SDK_PATH make
# -j4
#
# Note: PlatformIO uses platformio.ini, not this file. This file is kept for
# pure-CMake / CI builds.

include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(mecanum_pico_firmware C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

# ---------------------------------------------------------------------------
# Sources — match PlatformIO layout: src/ lib/ include/
# ---------------------------------------------------------------------------
add_executable(
  mecanum_pico_firmware
  src/main.cpp
  lib/motor_driver.c
  lib/encoder_driver.c
  lib/mecanum_controller.c
  lib/imu_driver.cpp
  lib/icm20948_spi.cpp
  include/board_config.h
  include/motor.h)

target_compile_features(mecanum_pico_firmware PUBLIC cxx_std_17)

target_include_directories(
  mecanum_pico_firmware
  PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include # board_config.h
          ${CMAKE_CURRENT_SOURCE_DIR}/lib # motor_driver.h, encoder_driver.h,
                                          # ...
          ${CMAKE_CURRENT_SOURCE_DIR}/src # main.cpp (self-reference not needed
                                          # but harmless)
)

target_link_libraries(mecanum_pico_firmware pico_stdlib hardware_pwm
                      hardware_gpio hardware_spi pico_critical_section)

# USB-CDC stdio on, UART off
pico_enable_stdio_usb(mecanum_pico_firmware 1)
pico_enable_stdio_uart(mecanum_pico_firmware 0)

pico_add_extra_outputs(mecanum_pico_firmware)

target_compile_options(mecanum_pico_firmware PRIVATE -Wall -Wextra
                                                     -Wno-unused-parameter)
