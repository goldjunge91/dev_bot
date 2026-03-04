from setuptools import setup
from glob import glob

package_name = "face_tracker"

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
