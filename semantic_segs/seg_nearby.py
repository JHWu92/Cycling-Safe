def crs_prepossess(gpdf, init_crs, bfr_crs):
    gpdf_crs = gpdf.copy()
    if gpdf_crs.crs == None:
        gpdf_crs.crs = {'init': u'epsg:{}'.format(init_crs)}
    return gpdf_crs.to_crs(epsg=bfr_crs)


def bfr_20m(seg):
    return seg.geometry.buffer(20)


def get_objs_nearby(segments_gpdf, objs_gpdf, bfr_func, init_crs, bfr_crs):
    import geopandas as gp
    seg_crs = crs_prepossess(segments_gpdf, init_crs, bfr_crs)
    obj_crs = crs_prepossess(objs_gpdf, init_crs, bfr_crs)
    seg_crs.geometry = seg_crs.apply(bfr_20m, axis=1)

    sjoin = gp.tools.sjoin(seg_crs, obj_crs, how='left', op='intersects')
    obj_ids_nearby = set(sjoin[~sjoin.index_right.isnull()].index_right)
    objs_nearby = objs_gpdf[objs_gpdf.index.isin(obj_ids_nearby)]
    return objs_nearby


def get_objs_near_dc_seg(segments_gpdf, objs_gpdf, bfr_func):
    return get_objs_nearby(segments_gpdf, objs_gpdf, bfr_func, 4326, 3559)


def get_osm_ids_near_dc_seg(segments, objs, bfr_func):
    objs_gpdf_near = get_objs_near_dc_seg(segments, objs, bfr_func)
    ids_near = {}
    for osmtype, grp in objs_gpdf_near.groupby('type'):
        ids = grp['id']
        unique_ids = set(ids)
        print 'seg nearby.py: get_osm_ids_near_dc_seg, len duplicated ids =', len(ids), 'len unique ids=', len(unique_ids)
        ids_near[osmtype] = unique_ids
    return ids_near
