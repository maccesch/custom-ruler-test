"""Write a standalone 3MF from one or more groups of STL parts.

Each group is laid out side by side on the bed; parts within a group keep
their relative positions, which is what the two-colour beam needs.

Stdlib only, so it runs in Pyodide.
"""

from __future__ import annotations

import struct
import zipfile
from xml.sax.saxutils import escape, quoteattr

GAP_MM = 5.0          # clear space between parts on the bed

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>
"""

RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""

HEAD = ('<?xml version="1.0" encoding="UTF-8"?>\n'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n')


def read_stl(path):
    """Binary STL -> (vertices, triangles), vertices de-duplicated."""
    with open(path, "rb") as f:
        data = f.read()
    count = struct.unpack_from("<I", data, 80)[0]
    index = {}
    vertices = []
    triangles = []
    for i in range(count):
        off = 84 + i * 50
        v = struct.unpack_from("<12f", data, off)
        tri = []
        for k in (3, 6, 9):
            p = (round(v[k], 4), round(v[k + 1], 4), round(v[k + 2], 4))
            j = index.get(p)
            if j is None:
                j = index[p] = len(vertices)
                vertices.append(p)
            tri.append(j)
        triangles.append(tri)
    return vertices, triangles


def _bounds(vertices):
    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    zs = [v[2] for v in vertices]
    return min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)


def _chunks(f, items):
    buf = []
    for s in items:
        buf.append(s)
        if len(buf) >= 4096:
            f.write("".join(buf).encode("utf-8"))
            buf.clear()
    if buf:
        f.write("".join(buf).encode("utf-8"))


def write_3mf(path, groups, description=""):
    """groups: [[(name, stl_path), ...], ...].

    Each group is laid out side by side on the bed; parts within a group keep
    their relative positions, which is what the two-colour beam needs.
    """
    loaded = []
    for group in groups:
        meshes = [(name, *read_stl(stl)) for name, stl in group]
        x0 = min(_bounds(v)[0] for _, v, _ in meshes)
        y0 = min(_bounds(v)[1] for _, v, _ in meshes)
        z0 = min(_bounds(v)[2] for _, v, _ in meshes)
        width = max(_bounds(v)[3] for _, v, _ in meshes) - x0
        loaded.append((meshes, (x0, y0, z0, width)))

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        with z.open("3D/3dmodel.model", "w") as f:
            f.write(HEAD.encode("utf-8"))
            if description:
                f.write(f'<metadata name="Description">'
                        f'{escape(description)}</metadata>'.encode("utf-8"))
            f.write(b"<resources>")
            cursor = 0.0
            objects = []
            for meshes, (x0, y0, z0, width) in loaded:
                dx, dy, dz = cursor - x0, -y0, -z0
                for name, vertices, triangles in meshes:
                    oid = len(objects) + 1
                    objects.append(oid)
                    f.write(f'<object id="{oid}" type="model" '
                            f'name={quoteattr(name)}><mesh><vertices>'.encode("utf-8"))
                    _chunks(f, (f'<vertex x="{x + dx:g}" y="{y + dy:g}" z="{z + dz:g}"/>'
                                for x, y, z in vertices))
                    f.write(b"</vertices><triangles>")
                    _chunks(f, (f'<triangle v1="{a}" v2="{b}" v3="{c}"/>'
                                for a, b, c in triangles))
                    f.write(b"</triangles></mesh></object>")
                cursor += width + GAP_MM
            f.write(b"</resources><build>")
            for oid in objects:
                f.write(f'<item objectid="{oid}"/>'.encode("utf-8"))
            f.write(b"</build></model>")
    return path
