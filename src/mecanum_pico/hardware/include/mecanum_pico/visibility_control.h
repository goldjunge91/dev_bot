// MIGRATION STATUS: COMPLETE
// Copyright 2024 mecanum_pico Development
// SPDX-License-Identifier: Apache-2.0
//
// Visibility macros for mecanum_pico shared library symbol export/import.

#ifndef MECANUM_PICO__VISIBILITY_CONTROL_H_
#define MECANUM_PICO__VISIBILITY_CONTROL_H_

#if defined _WIN32 || defined __CYGWIN__
  #ifdef __GNUC__
    #define MECANUM_PICO_EXPORT __attribute__((dllexport))
    #define MECANUM_PICO_IMPORT __attribute__((dllimport))
  #else
    #define MECANUM_PICO_EXPORT __declspec(dllexport)
    #define MECANUM_PICO_IMPORT __declspec(dllimport)
  #endif
  #ifdef MECANUM_PICO_BUILDING_DLL
    #define MECANUM_PICO_PUBLIC MECANUM_PICO_EXPORT
  #else
    #define MECANUM_PICO_PUBLIC MECANUM_PICO_IMPORT
  #endif
  #define MECANUM_PICO_PUBLIC_TYPE MECANUM_PICO_PUBLIC
  #define MECANUM_PICO_LOCAL
#else
  #define MECANUM_PICO_EXPORT __attribute__((visibility("default")))
  #define MECANUM_PICO_IMPORT
  #if __GNUC__ >= 4
    #define MECANUM_PICO_PUBLIC __attribute__((visibility("default")))
    #define MECANUM_PICO_LOCAL  __attribute__((visibility("hidden")))
  #else
    #define MECANUM_PICO_PUBLIC
    #define MECANUM_PICO_LOCAL
  #endif
  #define MECANUM_PICO_PUBLIC_TYPE
#endif

#endif  // MECANUM_PICO__VISIBILITY_CONTROL_H_
