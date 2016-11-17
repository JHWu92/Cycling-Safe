import sys
import os

import shapely.geometry as shpgeo
from shapely.ops import linemerge
sys.path.insert(0, os.path.abspath('../../../'))
from Cycling_Safe.utils.geofunc import remove_equal_shpobj, merge_within_by_list_shp
from osmread import Node, Way, Relation


def node2pt(node):
    return shpgeo.Point(node.lon, node.lat)


def way2line(osm_container, way):
    nodes = [osm_container.get_osm_node_by_id(nid) for nid in way.nodes]
    return shpgeo.LineString([(node.lon, node.lat) for node in nodes])


def lon_lats_closed(lon_lats):
    return lon_lats[0] == lon_lats[-1]


def way2lineOrpoly(osm_container, way):
    import warnings
    nodes = [osm_container.get_osm_node_by_id(nid) for nid in way.nodes]
    lon_lats = [(node.lon, node.lat) for node in nodes]
    obj = shpgeo.Polygon(lon_lats) if lon_lats_closed(lon_lats) and len(lon_lats) > 3 else shpgeo.LineString(lon_lats)
    if not obj.is_valid:
        warnings.warn("way id={} is not valid as a {}".format(way.id, type(obj)))
        obj = obj.buffer(0)
    return obj


def rltn2poly(osm_container, relation):
    """
    work for only continuous lines. if the linestring is not closed, 
    a new line between the first and last node will be added
    """
    cltn = []
    for m in relation.members:
        if m.type == Way:
            way = osm_container.get_osm_way_by_id(m.member_id)
            ln = way2line(osm_container, way)
            cltn.append(ln)
    merged_line = linemerge(cltn)
    return shpgeo.Polygon(merged_line)


def rltn2dictShp(osm_container, relation, sub_rltn=False):
    nodes, ways, sub_nodes, sub_ways = [], [], [], []
    for m in relation.members:
        obj = osm_container.get_osm_obj_by_id(m.type, m.member_id)
        if m.type == Node:
            nodes.append(obj)
        elif m.type == Way:
            ways.append(obj)
        elif m.type == Relation:
            r_nodes, r_ways = rltn2dictShp(osm_container, obj, True)
            sub_nodes.extend(r_nodes)
            sub_ways.extend(r_ways)
    if sub_rltn:
        return nodes, ways
    nodes.extend([node for node in sub_nodes])
    ways.extend([way for way in sub_ways])

    points = [node2pt(node) for node in nodes]
    keep_pts_idx, _ = remove_equal_shpobj(points)
    points = [p for cnt, p in enumerate(points) if cnt in keep_pts_idx]

    lines = [way2line(osm_container, way) for way in ways]
    keep_lines_idx, _ = remove_equal_shpobj(lines)
    lines = [l for cnt, l in enumerate(lines) if cnt in keep_lines_idx]


    dict_shp= {'Point': points, 'LineString': [], 'Polygon': []}
    if lines:
        merged = linemerge(lines)
        if merged.type == 'LineString':
            merged = [merged]
        else:
            merged = list(merged)
        for ln in merged:
            if ln.is_ring:
                dict_shp['Polygon'].append(shpgeo.Polygon(ln))
            else:
                dict_shp['LineString'].append(ln)
    return dict_shp


def rltn2mergedListShp(osm_container, relation):
    try:
        shpcltn = rltn2dictShp(osm_container, relation)
    except Exception as e:
        print relation.id, "relation's member out of osm bound, no need to consider", e
        return None, 'error'
    list_shp = []
    for l in shpcltn.values():
        list_shp += l
    merge_list_shp = merge_within_by_list_shp(list_shp)
    return merge_list_shp, 'ok'


def rltn2mergedFlattenListShp(osm_container, relation):
    merge_list_shp, message = rltn2mergedListShp(osm_container, relation)
    if message=='ok':
        flat_shpcltn = []
        for shpobjs in merge_list_shp:
            flat_shpcltn.extend(shpobjs)
        return flat_shpcltn
    else: return None


def test_rltn2merged(path_test_osm_data):
    from container import OSMContainer
    osm_data = OSMContainer(path_test_osm_data)
    rltns = osm_data.osm_objs['Relation']
    shpobjs_from_rltns = [(rltn.id,rltn2mergedFlattenListShp(osm_data,rltn)) for rltn in rltns]
    shpobjs_from_rltns = [r for r in shpobjs_from_rltns if r[1]]
    shpobjs_from_rltns = [(rid, 'Relation', shpobj) for (rid,shpobjs) in shpobjs_from_rltns for shpobj in shpobjs]
    print len(rltns), len(shpobjs_from_rltns)

if __name__ == '__main__':
    path_test_osm_data = '../../data/test/map.osm'
    test_rltn2merged(path_test_osm_data)