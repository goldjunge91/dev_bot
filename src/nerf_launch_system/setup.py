from setuptools import find_packages, setup
import os
from glob import glob

package_name = "nerf_launch_system"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "config"), glob("config/*")),
        (
            os.path.join("share", package_name, "description", "urdf"),
            glob("description/urdf/*"),
        ),
        (
            os.path.join("share", package_name, "description", "meshes"),
            glob("description/meshes/*"),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="ros",
    maintainer_email="30201929+goldjunge91@users.noreply.github.com",
    description="ROS2 hardware interface and control node for the Nerf dart launcher on Gubot One.",
    license="Apache-2.0",
    extras_require={
        "test": [
            "pytest",
        ],
    },
    entry_points={
        "console_scripts": [
            "nerf_control_node = nerf_launch_system.nerf_control_node:main",
        ],
    },
)
