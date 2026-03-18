# Copyright 2026 gubot_one contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""
Phase 2 – Orphan-Dateien-Test für gubot_one_description.

Stellt sicher dass veraltete / verwaiste Dateien deaktiviert sind:
- robot_core_bak.xml  (manuelles Backup, gehört nicht ins Repo)
- gazebo_control.xacro (libgazebo_ros_diff_drive, bypasses ros2_control)
"""

import os

DESC = os.path.join(os.path.dirname(__file__), "..", "description")


def test_no_active_backup_xml():
    """robot_core_bak.xml darf nicht aktiv (nicht leer / nicht deaktiviert) sein."""
    bak = os.path.join(DESC, "robot_core_bak.xml")
    if not os.path.exists(bak):
        return  # bereits gelöscht – Test besteht
    content = open(bak).read().strip()
    assert content.startswith("<!--") and "DEAKTIVIERT" in content, (
        "robot_core_bak.xml ist noch aktiv. "
        "Inhalt durch DEAKTIVIERT-Kommentar ersetzen oder Datei löschen."
    )


def test_no_active_gazebo_control_xacro():
    """gazebo_control.xacro (libgazebo_ros_diff_drive) darf nicht aktiv sein.

    libgazebo_ros_diff_drive bypasses ros2_control vollständig –
    unvereinbar mit der Zielarchitektur (alle 4 Modi über ros2_control).
    """
    path = os.path.join(DESC, "gazebo_control.xacro")
    if not os.path.exists(path):
        return  # bereits gelöscht – Test besteht
    content = open(path).read().strip()
    assert content.startswith("<!--") and "DEAKTIVIERT" in content, (
        "gazebo_control.xacro ist noch aktiv (enthält libgazebo_ros_diff_drive.so). "
        "Inhalt durch DEAKTIVIERT-Kommentar ersetzen oder Datei löschen."
    )
