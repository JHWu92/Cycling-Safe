import pandas as pd
import geopandas as gp
import numpy as np
import shapely.geometry as shpgeo
from osmread import parse_file, Node, Way, Relation
import datetime
from shapely.ops import linemerge
from geofunc import remove_equal_shpobj, merge_within_by_list_shp

def have_tag_value(obj, tag='*', value='*'):
    if not obj.tags: # have no tag, discard it whatever query is
        return False
    if tag=='*': # True for having any tag
        return True
    if not tag in obj.tags:
        return False
    if value=='*':
        return True
    return obj.tags[tag] in value

def filter_obj(obj, have_one=[('*','*')], donthave=[]):
    for tag, value in donthave:
        if have_tag_value(obj,tag, value):
            return False

    for tag, value in have_one:
        if have_tag_value(obj, tag,value):
            return True
    return False

def filter_osm_data(osm_objs,have_one=[('*','*')], donthave=[], special_filters=None):
    objs = []
    if special_filters:
        for o in osm_objs:
            pass_filter = True
            for filt in special_filters:
                if not filt(o):
                    pass_filter=False
                    break
            if pass_filter:
                objs.append(o)
    else:
        for o in osm_objs:
            if filter_obj(o, have_one, donthave):
                objs.append(o)
    return objs

def filter_osm_data_to_df(osm_objs,have_one=[('*','*')], donthave=[], special_filters=None):
    objs = filter_osm_data(osm_objs,have_one, donthave, special_filters=None)
    attr =[x[0] for x in have_one]
    objs = [[o.id]+[o.tags.get(k,'') for k in attr] for o in objs]
    df_objs = pd.DataFrame(objs, columns=['id']+attr)
    return df_objs
    
    
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

def rltn2cltn(osm_data, relation, sub_rltn=False):
    nodes, ways, sub_nodes, sub_ways = [],[], [], []
    for m in relation.members:
        obj = osm_data.get_osm_obj_by_id(m.type, m.member_id)
        if m.type == Node:
            nodes.append(obj)
        elif m.type==Way:    
            ways.append(obj)
        elif m.type==Relation: 
            r_nodes, r_ways = rltn2cltn(osm_data, obj, True)
            sub_nodes.extend(r_nodes)
            sub_ways.extend(r_ways)
    if sub_rltn:
        return nodes, ways
    
    nodes.extend([node for node in sub_nodes])
    ways.extend([way for way in sub_ways])

    nodes = [node2pt(node) for node in nodes]
    ways = [way2line(osm_data, way) for way in ways]
    
    nodes = remove_equal_shpobj(nodes)
    ways = remove_equal_shpobj(ways)
    
    shpcltn = {'Point':nodes, 'LineString':[], 'Polygon':[]}
    if ways:
        merged = linemerge(ways)
        if merged.type == 'LineString':
            merged = [merged]
        else:
            merged = list(merged)
        for ln in merged:
            if ln.is_ring:
                shpcltn['Polygon'].append(shpgeo.Polygon(ln))
            else: 
                shpcltn['LineString'].append(ln)
    return shpcltn

def rltn2mergedCltn(osm_data,relation):
    try:
        shpcltn = rltn2cltn(osm_data,relation)
    except Exception as e:
        print relation.id, "relation's member out of osm bound, no need to consider", e
        return None, 'error'
    list_shp = []
    for l in shpcltn.values():
        list_shp+=l
    merge_shpcltn = merge_within_by_list_shp(list_shp)
    return merge_shpcltn, 'ok'
    

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

