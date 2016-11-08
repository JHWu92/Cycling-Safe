import pandas as pd
import geopandas as gp
import numpy as np
import shapely.geometry as shpgeo
from osmread import parse_file, Node, Way, Relation
import datetime
from shapely.ops import linemerge


def node2pt(node):
    return shpgeo.Point(node.lon,node.lat)


def way2line(osm_data, way):
    nodes = [osm_data.get_osm_node_by_id(nid) for nid in way.nodes]
    return shpgeo.LineString([(node.lon, node.lat) for node in nodes])


def rltn2poly(osm_data, relation):
    """
    work for only continuous lines. if the linestring is not closed, 
    a new line between the first and last node will be added
    """
    cltn = []
    for m in relation.members:
        if m.type==Way:
            way = osm_data.get_osm_way_by_id( m.member_id)
            ln = way2line(osm_data, way)
            cltn.append(ln)
    merged_line = linemerge(cltn)
    return shpgeo.Polygon(merged_line)

def rltn2cltn(osm_data, relation):
    cltn = []
    for m in relation.members:
        obj = osm_data.get_osm_obj_by_id(m.type, m.member_id)
        shpobj = way2line(osm_data, obj) if m.type==Way else node2pt(obj)
        cltn.append(shpobj)
    return shpgeo.GeometryCollection(cltn)


class osm_container:
    def __init__(self, osm_path):
        self.osm_path = osm_path
        self.osm_objs = self.read_osm()
        self.osm_objs_idx = self.build_idx()
    
    def read_osm(self):
        print 'begin reading osm', datetime.datetime.now()
        osm_objs = {Node: [], Way: [], Relation: []}
        for obj in parse_file(self.osm_path):
            osm_objs[type(obj)].append(obj)
        print 'finish reading osm', datetime.datetime.now()
        return osm_objs
    
    def data_size(self):
        return ['len of {} = {}'.format(key, len(v)) for key, v in self.osm_objs.items()]
        
    def build_idx(self):
        osm_objs_idx = {}
        for otype, objs in self.osm_objs.items():
            osm_objs_idx[otype] = {o.id:i for i, o in enumerate(objs)}
        return osm_objs_idx
        
    def get_osm_obj_by_id(self, otype, oid):
        idx = self.osm_objs_idx[otype][oid]
        return self.osm_objs[otype][idx]

    def get_osm_node_by_id(self, oid):
        return self.get_osm_obj_by_id(Node, oid)

    def get_osm_way_by_id(self, oid):
        return self.get_osm_obj_by_id(Way, oid)

    def get_osm_relation_by_id(self, oid):
        return self.get_osm_obj_by_id(Relation, oid)

