import struct
import sys
import numpy as np


def parse_stl(filename):
    vertices = []
    try:
        with open(filename, "rb") as f:
            header = f.read(80)
            count_bytes = f.read(4)
            if len(count_bytes) < 4:
                return None
            count = struct.unpack("<I", count_bytes)[0]
            print(f"File {filename} has {count} triangles (Binary STL)")

            for _ in range(count):
                data = f.read(50)
                if len(data) < 50:
                    break
                floats = struct.unpack("<12f", data[:48])
                vertices.extend(floats[3:6])
                vertices.extend(floats[6:9])
                vertices.extend(floats[9:12])
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return None

    return np.array(vertices).reshape(-1, 3)


files = [
    "/home/ros/projects/my_new_robot/src/nerf_standalone/description/meshes/Dart_Pusher.stl"
]

for fn in files:
    verts = parse_stl(fn)
    if verts is not None and len(verts) > 0:
        min_xyz = np.min(verts, axis=0)
        max_xyz = np.max(verts, axis=0)
        center = (min_xyz + max_xyz) / 2.0
        dims = max_xyz - min_xyz
        print(f"--- {fn.split('/')[-1]} ---")
        print(f"  Min: {min_xyz}")
        print(f"  Max: {max_xyz}")
        print(f"  Geo Center: {center}")
        print(f"  Dims: {dims}")
