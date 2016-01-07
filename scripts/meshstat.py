#!/usr/bin/env python

"""
Print out useful info about an input mesh.
"""

import argparse
import json
import numpy as np
import pymesh
import os.path

from print_utils import print_bold, print_header, print_green, print_red

def print_property(name, val, expected=None):
    if expected is not None and val != expected:
        print_red("{:-<35}: {}".format(name, val));
    else:
        print("{:-<35}: {}".format(name, val));

def print_section_header(val):
    print_green("{:_^45}".format(val));

def print_basic_info(mesh, info):
    print_section_header("Basic information");
    print("dim: {}".format(mesh.dim));

    num_vertices = mesh.num_vertices;
    num_faces = mesh.num_faces;
    num_voxels = mesh.num_voxels;
    print("#v: {}\t#f: {}\t#V: {}".format(
        num_vertices, num_faces, num_voxels));
    print("vertex per face : {}".format(mesh.vertex_per_face));
    print("vertex per voxel: {}".format(mesh.vertex_per_voxel));

    info["num_vertices"] = num_vertices;
    info["num_faces"] = num_faces;
    info["num_voxels"] = num_voxels;
    info["vertex_per_face"] = mesh.vertex_per_face;
    info["vertex_per_voxel"] = mesh.vertex_per_voxel;

def print_bbox(mesh, info):
    print_section_header("Boundding box");
    if mesh.num_vertices == 0:
        print_red("Cannot compute bbox on empty mesh.");
        return;
    bbox_min, bbox_max = mesh.bbox;
    if mesh.dim == 3:
        print_format = "[{v[0]:^10.6g} {v[1]:^10.6g} {v[2]:^10.6g}]";
    elif mesh.dim == 2:
        print_format = "[{v[0]:^10.6g} {v[1]:^10.6g}]";
    print("bbox_min:  " + print_format.format(v=bbox_min));
    print("bbox_max:  " + print_format.format(v=bbox_max));
    print("bbox_size: " + print_format.format(v=bbox_max - bbox_min));

    info["bbox_min"] = bbox_min.tolist();
    info["bbox_max"] = bbox_max.tolist();

def print_percentage(data):
    p0, p25, p50, p75, p100= np.percentile(data, [0, 25, 50, 75, 100]);
    table_format = "{:^7.3}  {:^7.3}  {:^7.3}  {:^7.3}  {:^7.3}";
    print(table_format.format("min", "25%", "50%", "75%", "max"));
    print(table_format.format(p0, p25, p50, p75, p100));
    return p0, p25, p50, p75, p100;

def print_face_info(mesh, info):
    if (mesh.num_faces == 0): return;
    print_section_header("Face info");
    mesh.add_attribute("face_area");
    face_areas = mesh.get_attribute("face_area");
    total_area = np.sum(face_areas);
    ave_area = np.mean(face_areas);

    print("ave: {:.6g}         total: {:.6g}".format(
        ave_area, total_area));
    min_area, p25_area, median_area, p75_area, max_area = \
            print_percentage(face_areas);

    info["total_face_area"] = total_area;
    info["max_face_area"] = max_area;
    info["min_face_area"] = min_area;
    info["ave_face_area"] = ave_area;
    info["median_face_area"] = median_area;

def print_voxel_info(mesh, info):
    if (mesh.num_voxels == 0): return;

    print_section_header("Voxel info");
    mesh.add_attribute("voxel_volume");
    voxel_volume = mesh.get_attribute("voxel_volume");

    total_volume = np.sum(voxel_volume);
    ave_volume = np.mean(voxel_volume);
    print("ave: {:.6g}         total: {:.6g}".format(
        ave_volume, total_volume));

    min_volume, p25_volume, median_volume, p75_volume, max_volume = \
            print_percentage(voxel_volume);

    info["total_voxel_volume"] = total_volume;
    info["max_voxel_volume"] = max_volume;
    info["min_voxel_volume"] = min_volume;
    info["ave_voxel_volume"] = ave_volume;
    info["median_voxel_volume"] = median_volume;

def print_extended_info(mesh, info):
    print_section_header("Extended info");

    num_cc = mesh.num_components;
    num_f_cc = mesh.num_surface_components;
    if mesh.num_voxels > 0:
        num_v_cc = mesh.num_volume_components;
    else:
        num_v_cc = 0;
    isolated_vertices = mesh.num_isolated_vertices;
    duplicated_faces = mesh.num_duplicated_faces;

    degenerated_indices = pymesh.get_degenerated_faces(mesh);
    num_degenerated = len(degenerated_indices);

    if num_degenerated > 0:
        degenerated_faces = mesh.faces[degenerated_indices];
        combinatorially_degenerated_faces = \
                [f for f in degenerated_faces if len(set(f)) != len(f) ];
        num_combinatorial_degenerated_faces =\
                len(combinatorially_degenerated_faces);
    else:
        num_combinatorial_degenerated_faces = 0;

    print_property("num connected components", num_cc);
    print_property("num connected surface components", num_f_cc);
    print_property("num connected volume components", num_v_cc);
    print_property("num isolated vertices", isolated_vertices, 0);
    print_property("num duplicated faces", duplicated_faces, 0);
    print_property("num boundary edges", mesh.num_boundary_edges);
    print_property("num boundary loops", mesh.num_boundary_loops);
    print_property("num degenerated faces", num_degenerated, 0)
    if num_degenerated > 0:
        print_property("  combinatorially degenerated",
                num_combinatorial_degenerated_faces, 0);
        print_property("  geometrically degenerated",
                num_degenerated - num_combinatorial_degenerated_faces, 0);

    info["num_connected_components"] = num_cc;
    info["num_connected_surface_components"] = num_f_cc;
    info["num_connected_volume_components"] = num_v_cc;
    info["num_isolated_vertices"] = isolated_vertices;
    info["num_duplicated_faces"] = duplicated_faces;
    info["num_boundary_edges"] = mesh.num_boundary_edges;
    info["num_boundary_loops"] = mesh.num_boundary_loops;
    info["num_degenerated_faces"] = num_degenerated;
    info["num_combinatorial_degenerated_faces"] =\
            num_combinatorial_degenerated_faces;
    info["num_geometrical_degenerated_faces"] =\
            num_degenerated - num_combinatorial_degenerated_faces;

    is_closed = mesh.is_closed();
    is_edge_manifold = mesh.is_edge_manifold();
    is_vertex_manifold = mesh.is_vertex_manifold();
    is_oriented = mesh.is_oriented();
    euler = mesh.euler_characteristic;
    print_property("oriented", is_oriented, True);
    print_property("closed", is_closed, True)
    print_property("edge manifold", is_edge_manifold, True);
    print_property("vertex manifold", is_vertex_manifold, True);
    print_property("euler characteristic", euler);
    info["oriented"] = is_oriented;
    info["closed"] = is_closed;
    info["vertex_manifold"] = is_vertex_manifold;
    info["edge_manifold"] = is_edge_manifold;
    info["euler_characteristic"] = euler;

def coplanar_analysis(mesh, intersecting_faces):
    intersect_and_coplanar = set();
    vertices = mesh.vertices;
    faces = mesh.faces;
    for fi, fj in intersecting_faces:
        p0 = vertices[faces[fi, 0]];
        p1 = vertices[faces[fi, 1]];
        p2 = vertices[faces[fi, 2]];
        q0 = vertices[faces[fj, 0]];
        q1 = vertices[faces[fj, 1]];
        q2 = vertices[faces[fj, 2]];
        if pymesh.orient_3D(p0, p1, p2, q0) == 0 and \
           pymesh.orient_3D(p0, p1, p2, q1) == 0 and \
           pymesh.orient_3D(p0, p1, p2, q2) == 0:
               intersect_and_coplanar.add(fi);
               intersect_and_coplanar.add(fj);
    return intersect_and_coplanar;

def print_self_intersection_info(mesh, info):
    if mesh.vertex_per_face == 4:
        print_red("Converting quad to tri for self-intersection check.");
        mesh = pymesh.quad_to_tri(mesh);

    if mesh.num_vertices == 0 or mesh.num_faces == 0:
        num_intersections = 0;
        num_coplanar_intersecting_faces = 0;
    else:
        intersecting_faces = pymesh.detect_self_intersection(mesh);
        num_intersections = len(intersecting_faces);
        intersect_and_coplanar = coplanar_analysis(mesh, intersecting_faces);
        num_coplanar_intersecting_faces = len(intersect_and_coplanar);
    info["self_intersect"] = num_intersections > 0;
    info["num_self_intersections"] = num_intersections;
    info["num_coplanar_intersecting_faces"] = num_coplanar_intersecting_faces;
    print_property("self intersect", info["self_intersect"], False);
    if num_intersections > 0:
        print_property("num self intersections", num_intersections, 0);
        print_property("num coplanar intersecting faces",
                num_coplanar_intersecting_faces, 0);

def load_info(mesh_file):
    basename, ext = os.path.splitext(mesh_file);
    info_file = basename + ".info";
    info = {};
    if os.path.exists(info_file):
        with open(info_file, 'r') as fin:
            try:
                info = json.load(fin);
            except ValueError:
                print_red("Cannot parse {}, overwriting it".format(info_file));
    return info;

def dump_info(mesh_file, info):
    basename, ext = os.path.splitext(mesh_file);
    info_file = basename + ".info";

    with open(info_file, 'w') as fout:
        json.dump(info, fout, indent=4, sort_keys=True);

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__);
    parser.add_argument("--extended", "-x", action="store_true",
            help="check for manifold, closedness, connected components and more ");
    parser.add_argument("--self-intersection", "-s", action="store_true",
            help="check for self-intersection, maybe slow");
    parser.add_argument("--export", "-e", action="store_true",
            help="export stats into a .info file");
    parser.add_argument("input_mesh", help="input mesh file");
    return parser.parse_args();

def main():
    args = parse_args();
    mesh = pymesh.load_mesh(args.input_mesh);
    info = load_info(args.input_mesh);

    header = "Summary of {}".format(args.input_mesh);
    print_header("{:=^45}".format(header));
    print_basic_info(mesh, info);
    print_bbox(mesh, info);
    print_face_info(mesh, info);
    print_voxel_info(mesh, info);
    if (args.extended):
        print_extended_info(mesh, info);
    if (args.self_intersection):
        print_self_intersection_info(mesh, info);

    if (args.export):
        dump_info(args.input_mesh, info);


if __name__ == "__main__":
    main();
