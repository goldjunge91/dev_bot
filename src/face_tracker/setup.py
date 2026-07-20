# Copyright 2026 goldjunge91
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from glob import glob

from setuptools import setup

package_name = "face_tracker"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*launch.py")),
        ("share/" + package_name + "/config", glob("config/*.yaml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="ros",
    maintainer_email="30201929+goldjunge91@users.noreply.github.com",
    description="Face detection, recognition, and tracking for Gubot One robot.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "detect_face = face_tracker.detect_face:main",
            "follow_face = face_tracker.follow_face:main",
            "fire_at_face = face_tracker.fire_at_face:main",
            "register_face = face_tracker.register_face:main",
            "udp_cam_receiver = face_tracker.udp_cam_receiver:main",
            "udp_cam_sender = face_tracker.udp_cam_sender:main",
            "fake_face_publisher = face_tracker.fake_face_publisher:main",
        ],
    },
)
