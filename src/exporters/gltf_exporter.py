"""GLTF/GLB exporter for NeoEng-D-Trace.

Implementation preserved in the single ``src`` source tree.
Geometry, metadata, buffer construction, error handling and persistence behavior
are intentionally preserved.
"""

# src/exporters/gltf_exporter.py
import os
import tempfile
from typing import List

import numpy as np

try:
    from pygltflib import (
        GLTF2,
        Accessor,
        Asset,
        Buffer,
        BufferView,
        Mesh,
        Node,
        Primitive,
        Scene,
    )

    _HAS_PYGLTF = True
except ImportError:
    _HAS_PYGLTF = False

from src.core.app_identity import GLTF_GENERATOR
from src.core.logger import logger
from src.models.scene import Scene as PolygonScene
from src.physics.convex_decomp import triangulate_to_convex


def _save_glb(gltf, output_path: str) -> None:
    """Persist a GLB without allowing ``GLTF2.save`` to replace ``asset``.

    ``pygltflib`` 1.16.5 assigns the default ``Asset`` argument inside
    ``GLTF2.save``. Calling ``save_binary`` directly preserves the generator
    selected by NeoEng-D-Trace. A ``save`` fallback is retained for compatible
    test doubles and alternative backends that do not expose ``save_binary``.
    """
    save_binary = getattr(gltf, "save_binary", None)
    result = (
        save_binary(output_path) if callable(save_binary) else gltf.save(output_path)
    )
    if result is False:
        raise OSError("GLTF backend reported a failed save operation")


def export_scene_to_gltf(
    scene: PolygonScene, output_path: str, include_metadata: bool = True
) -> bool:
    """
    Export the entire scene to a GLTF .glb file with triangulated
    meshes and metadata.

    Args:
        scene: The NeoEng-D-Trace scene to export
        output_path: Path to save the .glb file
        include_metadata: Whether to include scene metadata as extras

    Returns:
        True if successful, False otherwise
    """
    if not _HAS_PYGLTF:
        logger.error("pygltflib not available, cannot export GLTF")
        return False

    gltf = GLTF2()
    gltf.asset = Asset(version="2.0", generator=GLTF_GENERATOR)

    # Prepare buffers for geometry
    all_positions: List[float] = []
    all_indices: List[int] = []

    nodes = []
    meshes = []

    for obj_id, obj in scene.objects.items():
        if not obj.polygon or len(obj.polygon) < 3:
            continue

        # Triangulate the polygon
        # Ensure float coordinates
        poly_float = [(float(x), float(y)) for x, y in obj.polygon]
        triangles = triangulate_to_convex(poly_float)

        if not triangles:
            continue

        # RE-WRITE LOOP FOR CLARITY AND CORRECTNESS

        # 1. Collect all vertices for this object first to minimize duplicates?
        #    convex_decomp returns list of polygons.
        obj_verts = []
        obj_indices = []

        current_obj_offset = 0  # Local offset for this object

        for poly in triangles:  # poly is a list of (x,y)
            if len(poly) < 3:
                continue

            # Add vertices
            for x, y in poly:
                obj_verts.extend([x, y, 0.0])

            # Add fan indices
            # Center is 0 relative to this poly
            # Indices are relative to the Accessor start, so they should
            # start at 0, 1, 2...
            # Multiple objects in one buffer usually use an Accessor
            # byteOffset.

            # Use absolute indices relative to the Accessor that is about
            # to be created.
            # If we create one Accessor per object, indices should start at 0.

            base = current_obj_offset
            for i in range(1, len(poly) - 1):
                obj_indices.extend([base + 0, base + i, base + i + 1])

            current_obj_offset += len(poly)

        if not obj_verts:
            continue

        # We have geometry for this object.
        # Now we need to append it to the GLOBAL buffer, but manage offsets correctly.

        # Global Byte Offsets
        pos_byte_offset = len(all_positions) * 4  # 4 bytes per float

        # Append to global lists
        all_positions.extend(obj_verts)
        # Indices in buffer must be global if we use a single big Accessor?
        # NO. We will create one Accessor per object.
        # The accessor will point to a specific byteOffset in the BufferView.
        # Indices inside that accessor are relative to the start of the
        # position accessor (0-based).
        # So 'obj_indices' as calculated (0-based) is correct.

        # BUT wait, all_indices accumulates everything.
        # A single index BufferView cannot easily expose separate accessors
        # for chunks unless BufferViews are split or Accessor byteOffset is used.
        # Accessor byteOffset must be aligned.

        # Let's define the Accessors now relative to the buffers we will create later.

        # Accessor for Positions
        pos_accessor_idx = len(gltf.accessors)
        gltf.accessors.append(
            Accessor(
                bufferView=0,  # We will assign 0 to positions BufferView
                byteOffset=pos_byte_offset,
                componentType=5126,  # FLOAT
                count=len(obj_verts) // 3,
                type="VEC3",
                min=[min(obj_verts[0::3]), min(obj_verts[1::3]), 0.0],
                max=[max(obj_verts[0::3]), max(obj_verts[1::3]), 0.0],
            )
        )

        # Accessor for Indices
        # Indices need to be appended to a separate list or handle offset
        # Concatenated indices require the starting offset for each object.
        current_indices_start = len(all_indices)
        all_indices.extend(obj_indices)

        idx_accessor_idx = len(gltf.accessors)
        gltf.accessors.append(
            Accessor(
                bufferView=1,  # We will assign 1 to indices BufferView
                byteOffset=current_indices_start * 2,  # 2 bytes per index
                componentType=5123,  # UNSIGNED_SHORT
                count=len(obj_indices),
                type="SCALAR",
                min=[min(obj_indices)],
                max=[max(obj_indices)],
            )
        )

        primitive = Primitive(
            attributes={"POSITION": pos_accessor_idx},
            indices=idx_accessor_idx,
            mode=4,  # TRIANGLES
        )

        mesh = Mesh(primitives=[primitive])
        if include_metadata:
            mesh.extras = {
                "object_id": obj_id,
                "layer": obj.layer_id,
                "groups": [g.id for g in scene.groups if obj_id in g.members],
            }

        mesh_idx = len(gltf.meshes)
        gltf.meshes.append(mesh)
        meshes.append(mesh)

        node = Node(mesh=mesh_idx)
        if include_metadata:
            node.extras = {"object_id": obj_id}

        node_idx = len(gltf.nodes)
        gltf.nodes.append(node)
        nodes.append(node_idx)  # Save index

    if not all_positions:
        logger.warning("No valid polygons to export")
        return False

    # Create buffers
    positions_bytes = np.array(all_positions, dtype=np.float32).tobytes()

    # Pad indices to 4-byte boundary for GLTF alignment if necessary?
    # GLTF requires Accessor byteOffset to be multiple of componentType size.
    # We used 2 bytes (ushort). So multiples of 2 is fine.
    indices_bytes = np.array(all_indices, dtype=np.uint16).tobytes()

    # We create ONE buffer with 2 Views: [Positions | Indices]
    # Positions are Float32 (4 bytes), so length is always multiple of 4.
    # Indices start immediately after.

    buffer_data = positions_bytes + indices_bytes

    buffer = Buffer(byteLength=len(buffer_data))
    gltf.buffers.append(buffer)

    # BufferView 0: Positions
    gltf.bufferViews.append(
        BufferView(
            buffer=0,
            byteOffset=0,
            byteLength=len(positions_bytes),
            target=34962,  # ARRAY_BUFFER
            byteStride=12,  # 3 floats
        )
    )

    # BufferView 1: Indices
    gltf.bufferViews.append(
        BufferView(
            buffer=0,
            byteOffset=len(positions_bytes),
            byteLength=len(indices_bytes),
            target=34963,  # ELEMENT_ARRAY_BUFFER
        )
    )

    # Create scene
    scene_node = Scene(nodes=nodes)  # nodes is list of indices
    if include_metadata:
        scene_node.extras = {
            "layers": [
                {"id": layer.id, "name": layer.name, "visible": layer.visible}
                for layer in scene.layers
            ],
            "groups": [
                {"id": g.id, "name": g.name, "members": list(g.members)}
                for g in scene.groups
            ],
        }
    gltf.scenes.append(scene_node)
    gltf.scene = 0

    # Set buffer data
    gltf.set_binary_blob(buffer_data)

    # Save atomically
    dirn = os.path.dirname(output_path)
    if dirn and not os.path.exists(dirn):
        os.makedirs(dirn, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(suffix=".glb", dir=dirn)
    os.close(fd)
    try:
        _save_glb(gltf, tmp_path)
        # os.replace atomically replaces an existing destination on Windows
        # and POSIX. Pre-deleting the destination would create a data-loss gap.
        os.replace(tmp_path, output_path)
        logger.info(f"Exported GLTF to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save GLTF: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False


def export_object_to_gltf(
    obj_id: str,
    scene: PolygonScene,
    output_path: str,
    include_metadata: bool = True,
) -> bool:
    """
    Export a single object to GLTF .glb file.
    """
    if obj_id not in scene.objects:
        logger.error(f"Object {obj_id} not found")
        return False

    obj = scene.objects[obj_id]
    if not obj.polygon or len(obj.polygon) < 3:
        logger.error(f"Object {obj_id} has invalid polygon")
        return False

    # Create a temporary scene with just this object
    temp_scene = PolygonScene()
    temp_scene.objects[obj_id] = obj
    # Include only relevant groups
    temp_scene.groups = [g for g in scene.groups if obj_id in g.members]
    # Include layers info anyway for context
    temp_scene.layers = scene.layers

    return export_scene_to_gltf(temp_scene, output_path, include_metadata)
