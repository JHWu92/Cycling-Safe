from osmread import parse_file, Node, Way, Relation
import datetime


class OSMContainer:

    def __init__(self, osm_path):
        self.osm_path = osm_path
        self.osm_type2str = {Node: 'Node', Way:'Way', Relation:'Relation'}
        self.osm_objs = self.read_osm()
        self.osm_objs_idx = self.build_idx()

    def get_type_str(self,t):
        if isinstance(t, str):
            return t
        return self.osm_type2str[t]

    def read_osm(self):
        print 'begin reading osm', datetime.datetime.now()
        osm_objs = {'Node': [], 'Way': [], 'Relation': []}
        for obj in parse_file(self.osm_path):
            type_str = self.get_type_str(type(obj))
            osm_objs[type_str].append(obj)
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
        otype = self.get_type_str(otype)
        idx = self.osm_objs_idx[otype][oid]
        return self.osm_objs[otype][idx]

    def get_osm_node_by_id(self, oid):
        return self.get_osm_obj_by_id('Node', oid)

    def get_osm_way_by_id(self, oid):
        return self.get_osm_obj_by_id('Way', oid)

    def get_osm_relation_by_id(self, oid):
        return self.get_osm_obj_by_id('Relation', oid)