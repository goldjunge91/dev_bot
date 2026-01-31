from setuptools import find_packages, setup

package_name = "nerf_dart_launcher"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),

        ("share/" + package_name + "/firmware", [
            "firmware/nerf_launcher_firmware.ino",
            "firmware/README.md",
        ]),
        ("share/" + package_name + "/urdf", [
            "urdf/nerf_launcher.urdf.xacro",
            "urdf/nerf_launcher_minimal.urdf.xacro",
            "urdf/nerf_launcher_ros2_control.xacro",
            "urdf/nerf_launcher_standalone.urdf.xacro"
        ]),
        ("share/" + package_name + "/config", [
            "config/nerf_controllers.yaml",
            "config/nerf_launcher_view.rviz"
        ]),
        ("share/" + package_name + "/launch", [
            "launch/nerf_launcher.launch.py", 
            "launch/nerf_controllers.launch.py",
            "launch/test_launcher_standalone.launch.py"
        ]),
        ("share/" + package_name + "/description/meshes", [
            "description/meshes/Dart-Tray.stl",
            "description/meshes/Dart_Pusher.stl",
            "description/meshes/Launcher_wheel.stl",
            "description/meshes/Launcher_wheel_v1.stl",
            "description/meshes/Montageplatte.stl",
            "description/meshes/Motor_und_Magazinplatte.stl",
            "description/meshes/Racerstar-BR2205-2300KV.stl",
            "description/meshes/Racerstar-BR2205-2300KV1.stl",
            "description/meshes/Servo-TD8320MG-TD8325MG.stl",
            "description/meshes/Turret.stl",
            "description/meshes/esc_halterung.stl",
        ]),
    ],
    install_requires=["setuptools", "pyserial"],
    zip_safe=True,
    maintainer="marco",
    maintainer_email="30201929+goldjunge91@users.noreply.github.com",
    description="Nerf launcher control and interfaces for my_steel robot",
    license="Apache-2.0",
    extras_require={
        "test": [
            "pytest",
        ],
    },
    entry_points={
        "console_scripts": [
            "nerf_launcher_node=nerf_dart_launcher.nerf_launcher_node:main",
        ],
    },
)