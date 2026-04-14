"""
Test: URDF Geometrie Symmetrie (Mecanum)

Prueft gemäß Plan 02:
- Alle 4 Räder muessen symmetrisch um base_link angeordnet sein.
- front_left/right muessen einen X-Offset > 0 haben.
- rear_left/right muessen einen negativen X-Offset haben.
- Die Beträge der X-Offsets muessen gleich sein (Symmetrie).
"""

import os
import subprocess
import xml.etree.ElementTree as ET
import pytest

# Pfad relativ zu diesem Test-Skript
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
XACRO_PATH = os.path.join(
    _TEST_DIR, "..", "description", "gubot_one_main.urdf.xacro"
)


def get_urdf_xml():
    """Rendert das XACRO zu URDF und gibt den XML-String zurueck."""
    # drive_type=mecanum ist noetig damit Hinterrad-Joints gerendert werden
    result = subprocess.run(
        ['xacro', XACRO_PATH, 'drive_type:=mecanum'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        pytest.fail(f"XACRO rendering failed: {result.stderr}")
    return result.stdout

def test_wheel_joints_symmetry():
    """Prueft die X-Positionen der Rad-Joints im URDF."""
    urdf_content = get_urdf_xml()
    root = ET.fromstring(urdf_content)
    
    joints = {
        'front_left_wheel_joint': None,
        'front_right_wheel_joint': None,
        'rear_left_wheel_joint': None,
        'rear_right_wheel_joint': None
    }
    
    for joint in root.findall('joint'):
        name = joint.get('name')
        if name in joints:
            origin = joint.find('origin')
            if origin is not None:
                xyz = origin.get('xyz', '0 0 0').split()
                joints[name] = [float(x) for x in xyz]
    
    # Sicherstellen dass alle gefunden wurden
    for name, pos in joints.items():
        assert pos is not None, f"Joint {name} nicht im URDF gefunden"

    fl = joints['front_left_wheel_joint']
    fr = joints['front_right_wheel_joint']
    rl = joints['rear_left_wheel_joint']
    rr = joints['rear_right_wheel_joint']

    # 1. Front-Raeder muessen X > 0 haben (Bug: aktuell X=0)
    assert fl[0] > 0, f"front_left_wheel_joint X ist {fl[0]}, muss > 0 sein"
    assert fr[0] > 0, f"front_right_wheel_joint X ist {fr[0]}, muss > 0 sein"
    
    # 2. Rear-Raeder muessen X < 0 haben
    assert rl[0] < 0, f"rear_left_wheel_joint X ist {rl[0]}, muss < 0 sein"
    assert rr[0] < 0, f"rear_right_wheel_joint X ist {rr[0]}, muss < 0 sein"
    
    # 3. Symmetrie-Check X (Betrag front == Betrag rear)
    assert abs(abs(fl[0]) - abs(rl[0])) < 0.001, f"Asymmetrie X: front={fl[0]}, rear={rl[0]}"
    assert abs(abs(fr[0]) - abs(rr[0])) < 0.001, f"Asymmetrie X: front={fr[0]}, rear={rr[0]}"
    
    print(f"\nGefundene X-Positionen: Front={fl[0]}, Rear={rl[0]}")
