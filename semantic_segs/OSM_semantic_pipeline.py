# coding=utf-8
__author__ = 'JHW'

import datetime
import sys
import logging
import os

import geopandas as gp

sys.path.insert(0, os.path.abspath('../../'))
from Cycling_Safe.utils.osm.container import OSMContainer
from Cycling_Safe.utils.osm.osm2shp import *
from Cycling_Safe.utils.osm.osmFliter import *
from seg_nearby import get_osm_ids_near_dc_seg, bfr_20m
from Cycling_Safe.utils.geofunc import merge_within
import pandas as pd
from collections import defaultdict, Counter

START_TIME = datetime.datetime.now()


def set_Logger(log_name='log_%s_%s.txt' % (START_TIME.strftime('%Y%m%d'), os.path.basename(sys.argv[0])[:-3]),
               format_log='%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'):
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_name)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(format_log)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def costs(start_time=START_TIME):
    dnow = datetime.datetime.now()
    secs = int((dnow - start_time).total_seconds())
    return 'now = %s, costs = %d days %02d:%02d:%02d = %d seconds' % (dnow.strftime('%Y-%m-%d %H:%M:%S'),
                                                                      secs / 3600 / 24, secs / 3600 % 24,
                                                                      secs / 60 % 60, secs % 60, secs)


def build_gpdf_list_from_osm(osm_data, nodes, ways, rltns):
    columns = ['id', 'type', 'geometry']
    shpobjs_from_nodes = [(node.id, 'Node', node2pt(node)) for node in nodes]
    shpobjs_from_ways = [(way.id, 'Way', way2lineOrpoly(osm_data, way)) for way in ways]
    shpobjs_from_rltns = [(rltn.id,rltn2mergedFlattenListShp(osm_data,rltn)) for rltn in rltns]
    shpobjs_from_rltns = [r for r in shpobjs_from_rltns if r[1]]
    shpobjs_from_rltns = [(rid, 'Relation', shpobj) for (rid,shpobjs) in shpobjs_from_rltns for shpobj in shpobjs]
    print 'build_gpdf_list len(shpobjs_from_nodes)={},len(shpobjs_from_ways)={},len(shpobjs_from_rltns)={}'.format(
        len(shpobjs_from_nodes), len(shpobjs_from_ways), len(shpobjs_from_rltns))
    shpobjs = []
    shpobjs.extend(shpobjs_from_nodes)
    shpobjs.extend(shpobjs_from_ways)
    shpobjs.extend(shpobjs_from_rltns)
    gpdf = gp.GeoDataFrame(shpobjs, columns=columns)
    return gpdf


def main():
    # LOGGER.info('test')

    print 'begin OSM POI pipeline', costs()
    data_dir = '../data/'
    osm_data_dir = data_dir + 'osm/'

    # 1. read OSM data
    start_time = datetime.datetime.now()
    path_osm_dc_bbox = osm_data_dir + 'osm_dc_bbox.osm'
    osm_dc_bbox = OSMContainer(path_osm_dc_bbox)
    print 'finished reading osm data', costs(start_time)

    # 2. retrieve osm within dc polygon - from/data_prepro/getOSM_within_dc_poly
    print '2.'
    start_time = datetime.datetime.now()
    path_osm_ids_in_dc = osm_data_dir + 'osm_ids_within_dc_polygon.txt'
    with open(path_osm_ids_in_dc) as f:
        osm_ids_in_dc = eval(f.readlines()[0])
    dc_nodes = filter_objs_by_ids(osm_dc_bbox.osm_objs['Node'], osm_ids_in_dc['Node'])
    dc_ways = filter_objs_by_ids(osm_dc_bbox.osm_objs['Way'], osm_ids_in_dc['Way'])
    dc_rltns = filter_objs_by_ids(osm_dc_bbox.osm_objs['Relation'], osm_ids_in_dc['Relation'])
    print 'retrieve osm within dc polygon', costs(start_time)

    # 3. get osm ids which has tags and near open dc street segments
    # OSM_near_segments.ipynb
    # 3.1 get osm which has tags
    print '3.'
    dc_nodes_with_tag = filter_osm_data(dc_nodes)
    dc_ways_with_tag = filter_osm_data(dc_ways)
    dc_rltns_with_tag = filter_osm_data(dc_rltns)
    print 'len with tags: node={}, way={}, relation={}'.format(
        len(dc_nodes_with_tag), len(dc_ways_with_tag), len(dc_rltns_with_tag))

    # 3.2 from osm to geopandas geodataframe
    osm_gpdf = build_gpdf_list_from_osm(osm_dc_bbox, dc_nodes_with_tag, dc_ways_with_tag, dc_rltns_with_tag)

    # 3.3 sjoin to get osm ids
    path_opendc_segs = data_dir + 'opendc_segments.geojson'
    segs = gp.read_file(path_opendc_segs)
    osm_ids_near = get_osm_ids_near_dc_seg(segs, osm_gpdf, bfr_20m)

    # 3.4 store ids near
    path_osm_ids_has_tag_near_segs = osm_data_dir + 'osm_ids_has_tag_near_segs.txt'
    dump_obj(path_osm_ids_has_tag_near_segs, osm_ids_near)

    # 4. merge overlapping place.ipynb
    print '4.'
    # TODO: use the osm_tree_all_parents to explore which to exclude or not merge
    # TODO: check this: relation/5147841; http://www.openstreetmap.org/relation/5170966#map=12/38.9299/-77.0246 and http://www.openstreetmap.org/relation/5147841#map=12/38.8886/-77.0145
    # TODO: path_manually_defined_not_merge_osm_ids = osm_data_dir + 'osm_ids_not_merge.txt'
    # TODO: path_manually_defined_exclude_osm_ids = osm_data_dir + 'osm_ids_exclude.txt'
    # TODO: filter by ids: in (has_tag.txt) not in (not_merge, exclude)
    osm_ids_for_merge = osm_ids_near
    # filter osm for merge
    dc_nodes_for_merge = filter_objs_by_ids(dc_nodes, osm_ids_for_merge['Node'])
    dc_ways_for_merge = filter_objs_by_ids(dc_ways, osm_ids_for_merge['Way'])
    dc_rltns_for_merge = filter_objs_by_ids(dc_rltns, osm_ids_for_merge['Relation'])
    print 'filter by id len ways = {}, relations = {}'.format(len(dc_ways_for_merge), len(dc_rltns_for_merge))

    filter_for_ways = [filter_isnot_admin, filter_isnot_motorway, filter_isnot_landuse]
    dc_ways_for_merge = filter_osm_data(dc_ways_for_merge, special_filters=filter_for_ways)
    filter_for_rltns = [filter_isnot_admin, filter_isnot_restriction, filter_isnot_landuse]
    dc_rltns_for_merge = filter_osm_data(dc_rltns_for_merge, special_filters=filter_for_rltns)
    print 'filter by tag len ways = {}, relations = {}'.format(len(dc_ways_for_merge), len(dc_rltns_for_merge))

    ## do merge on filtered by ids
    gpdf_for_merge = build_gpdf_list_from_osm(osm_dc_bbox, dc_nodes_for_merge, dc_ways_for_merge, dc_rltns_for_merge)
    _, all_parents, direct_parent, osm_ids_equal_pair = merge_within(gpdf_for_merge)

    # 4.2 store merged result
    path_osm_tree_all_parents = osm_data_dir + 'osm_tree_all_parents.csv'
    dump_tree(path_osm_tree_all_parents, all_parents, gpdf_for_merge, ['node', 'parent','node_oid', 'node_otype', 'parent_oid', 'parent_otype'])
    path_osm_tree_direct_parent = osm_data_dir + 'osm_tree_direct_parent.csv'
    direct_parent_df = dump_tree(path_osm_tree_direct_parent, direct_parent, gpdf_for_merge,  ['node', 'parent', 'lv', 'node_oid', 'node_otype', 'parent_oid', 'parent_otype'])
    path_osm_ids_equal_pair = osm_data_dir + 'osm_ids_equal_pair.csv'
    equal_pair = [(gpdf_for_merge.loc[i].id, gpdf_for_merge.loc[i]['type'],
                   gpdf_for_merge.loc[j].id, gpdf_for_merge.loc[j]['type']) for i, j in osm_ids_equal_pair]
    columns = ['node_oid', 'node_otype', 'parent_oid', 'parent_otype']
    equal_pair_df = pd.DataFrame(equal_pair, columns=columns)
    equal_pair_df.to_csv(path_osm_ids_equal_pair)

    # 5 get all tags for each subtree to avoid re-counting tags.
    print '5.'
    # 5.1 get subtree
    nodes_have_children = direct_parent_df[
        (direct_parent_df.node.apply(str).isin(direct_parent_df.parent.value_counts().index.tolist()))
        & (direct_parent_df.parent == -1)].node.tolist()
    print datetime.datetime.now()
    sub_trees = []
    shape_error = []
    assert_error = []
    for node_id in nodes_have_children:
        try:
            subtree, shape = get_sub_tree(direct_parent_df, node_id)
        except Exception as e:
            assert_error.append((node_id, e))
            continue
        if shape != (1, 7):
            shape_error.append((node_id, subtree, shape))
        sub_trees.append(subtree)
    print datetime.datetime.now()
    sub_trees_root = direct_parent_df[direct_parent_df.parent == -1].node
    nodes_have_no_child = set(sub_trees_root) - set(nodes_have_children)
    nodes_have_no_child = direct_parent_df[direct_parent_df.node.isin(nodes_have_no_child)]
    one_node_subtrees = nodes_have_no_child.apply(lambda x: set([(int(x.node_oid), x.node_otype)]), axis=1).tolist()
    sub_trees.extend(one_node_subtrees)
    # 5.1.2 store subtree
    path_osm_tree_subtrees = osm_data_dir + 'osm_tree_subtrees.txt'
    dump_obj(path_osm_tree_subtrees, sub_trees)

    # 5.2 get subtree tags
    print datetime.datetime.now()
    subtree_tags = []
    for subtree in sub_trees:
        tags = defaultdict(list)
        cnt = 0
        for oid, otype in subtree:
            obj = osm_dc_bbox.get_osm_obj_by_id(otype, oid)
            cnt+=1
            for tag, value in obj.tags.items():
                tags[tag].append(value)
        print 'len of objs in subtree', cnt
        subtree_tags.append(tags)
    print datetime.datetime.now()

    path_osm_tags_in_subtrees = osm_data_dir + 'osm_tags_in_subtrees.txt'
    dump_obj(path_osm_tags_in_subtrees, [dict(d) for d in subtree_tags])

    # 6. plot tags
    path_tags_of_interest = osm_data_dir + 'osm_tags_of_interest.txt'
    tags_of_interest = load_obj(path_tags_of_interest)

    finial_tags_value = defaultdict(int)
    for tags in subtree_tags:
        for tag, duplicate_value in tags.items():
            for v, cnt in Counter(duplicate_value).items():
                finial_tags_value[(tag, v)] += 1
    df = pd.DataFrame(finial_tags_value.items(), columns=['tag_value', 'cnt'])
    df['tag'] = df.tag_value.apply(lambda x: x[0])
    df['tag_value'] = df.tag_value.apply(lambda x: '{}={}'.format(x[0].encode('utf-8'), x[1].encode('utf-8')))

    import random
    tag_cnt = df[df.tag.isin(tags_of_interest)].groupby('tag').agg(sum)['cnt']
    print tag_cnt.shape
    labels = tag_cnt.index.tolist()
    cnts = tag_cnt.values.tolist()
    color = "#%06x" % random.randint(0, 0xFFFFFF)
    colors = [color] * len(labels)
    parents = [''] * len(labels)
    fn_bar = osm_data_dir + 'osm_nearby_merged_tag_distr.html'
    title = 'tag'
    get_bar_plot(parents, colors, labels, cnts, title, fn_bar)

    df_sort = df[df.tag.isin(tags_of_interest)].sort(['tag', 'tag_value'])
    labels = df_sort.tag_value.values
    cnts = df_sort.cnt.values
    parents = df_sort.tag
    unique_parents = pd.unique(parents)
    rand_color = get_random_color(unique_parents)
    colors = [rand_color[p] for p in parents]
    title = 'tag=value'
    fn_bar = osm_data_dir + 'osm_nearby_merged_tag_value_distr.html'
    get_bar_plot(parents, colors, labels, cnts, title, fn_bar)

    return


def get_random_color(parents):
    rand_colors = {}
    import random
    for p in parents:
        rand_colors[p] = "#%06x" % random.randint(0, 0xFFFFFF)
    return rand_colors


def get_bar_plot(parents, colors, labels, cnts, title, fn_bar):
    from plotly.offline import plot as pplot
    import plotly.graph_objs as pgo
    pplot_para = {}
    pplot_para['data'] = [pgo.Bar(x=labels, y=cnts, text=parents, marker=dict(color=colors))]
    pplot_para['layout'] = pgo.Layout(title='distribution of {}'.format(title),
                                      xaxis=dict(title=title), yaxis=dict(title='frequency'))
    pplot(pplot_para, filename=fn_bar)


def load_obj(path):
    with open(path) as f:
        obj = eval(f.readlines()[0])
    return obj


def get_sub_tree(tree_df, node_id, looping=0):
    mask_node = (tree_df.node == node_id)
    mask_children = (tree_df.parent == str(node_id))
    assert looping < 100, 'looping too much nodeid:' + str(node_id)

    node = tree_df[mask_node]
    oid = node.node_oid.values[0]
    otype = node.node_otype.values[0]
    subtree = {((oid, otype),)}

    children_oid = tree_df[mask_children].node_oid.values
    children_otype = tree_df[mask_children].node_otype.values
    children_oid_otype = zip(children_oid, children_otype)
    children_id = tree_df[mask_children].node.values
    subtree.update(children_oid_otype)
    if len(children_oid) == 0:
        return subtree, node.shape

    for cid in children_id:
        c_subtree, c_tree_shape = get_sub_tree(tree_df, cid, looping + 1)
        subtree.update(c_subtree)
    return subtree, node.shape


def dump_obj(path, str_able_obj):
    with open(path, 'w') as f:
        f.write(str(str_able_obj))


def dump_tree(path, tree_df, gpdf, columns):
    temp_df = tree_df.merge(gpdf[['id', 'type']], how='left', left_on='node', right_index=True).merge(
        gpdf[['id', 'type']], how='left', left_on='parent', right_index=True)
    temp_df.columns = columns
    temp_df.parent_oid = temp_df.parent_oid.fillna('')
    temp_df.to_csv(path)
    return temp_df


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    print("start_time:", START_TIME.strftime(TIME_FORMAT))

    # LOGGER = set_Logger()

    main()

    END_TIME = datetime.datetime.now()
    DELTA_TIME = END_TIME - START_TIME
    print ('run time: %s - %s = %s ' % (START_TIME.strftime(TIME_FORMAT), END_TIME.strftime(TIME_FORMAT), DELTA_TIME))
