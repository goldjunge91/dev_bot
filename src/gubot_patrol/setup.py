from setuptools import setup
from glob import glob

package_name = "gubot_patrol"

setup(
    name=package_name,
    version="0.0.1",
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
    description="Dead-reckoning patrol mode for Gubot One.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "patrol_node = gubot_patrol.patrol_node:main",
        ],
    },
)
