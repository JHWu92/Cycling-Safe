def remove_equal_shpobj(objs):
    import rtree
    size = len(objs)
    equal_pair = []
    keep = []
    exclude_idx = set()

    tree_idx = rtree.index.Index()
    objs_bounds = [o.bounds for o in objs]
    for i in xrange(size):
        try:
            tree_idx.insert(i, objs_bounds[i])
        except Exception as e:
            print i, objs_bounds[i], objs[i]
            raise e

    for i in xrange(size):
        if i in exclude_idx:
            continue
        keep.append(i)
        js = tree_idx.intersection(objs[i].bounds)
        for j in js:
            if i!=j and objs[i].equals(objs[j]):
                equal_pair.append((i,int(j)))
                exclude_idx.add(j)

    return keep, equal_pair


def merge_within(shp_gpdf):
    import geopandas as gp
    import pandas as pd
    import datetime
    from other_utils import find_tree
    print 'begin merge within', datetime.datetime.now()
    keep, equal_pair= remove_equal_shpobj(shp_gpdf.geometry.values)
    equal_pair_index = [(shp_gpdf.iloc[i].name, shp_gpdf.iloc[j].name) for i, j in equal_pair]
    gpdf_no_equal = shp_gpdf.iloc[keep]
    print 'keep =',len(keep), 'equal pair =',len(equal_pair), gpdf_no_equal.shape, datetime.datetime.now()
    sjoin = gp.tools.sjoin(gpdf_no_equal,gpdf_no_equal,op='within')
    print 'sjoin.shape =',sjoin.shape, datetime.datetime.now()
    tree_all_parent = pd.DataFrame(zip(sjoin.index.values, sjoin.index_right.values), columns=['node','parent'])
    print 'messy tree shape =', tree_all_parent.shape, datetime.datetime.now()
    tree_direct_parent = find_tree(tree_all_parent.copy())
    print 'clean tree shape =', tree_direct_parent.shape, datetime.datetime.now()
    top_level_shp_idx = tree_direct_parent[tree_direct_parent.parent==-1].node.values
    return shp_gpdf[shp_gpdf.index.isin(top_level_shp_idx)], tree_all_parent, tree_direct_parent, equal_pair_index

def merge_within_by_list_shp(list_shp):
    import geopandas as gp
    import pandas as pd
    from other_utils import find_tree
    gpdf = gp.GeoDataFrame(list_shp,columns=['geometry'])
    sjoin = gp.tools.sjoin(gpdf,gpdf,op='within')
    messy_tree_df = pd.DataFrame(zip(sjoin.index.values, sjoin.index_right.values), columns=['node','parent'])
    clean_tree_df = find_tree(messy_tree_df)
    top_level_shp_idx = clean_tree_df[clean_tree_df.parent==-1].node.values
    return gpdf[gpdf.index.isin(top_level_shp_idx)].values

def grid_line(mini, maxi, ngrid=10):
    delta = (maxi-mini)/ngrid
    return [(mini+i*delta, mini+(i+1)*delta) for i in range(ngrid)] 


def grid_area(sw, ne, ngrid=10):
    grid_lat = grid_line(sw[0], ne[0], ngrid)
    grid_lon = grid_line(sw[1], ne[1], ngrid)
    grids = []
    for i in range(ngrid):
        for j in range(ngrid):
            s, n = grid_lat[i]
            w, e = grid_lon[j]
            grids.append(((s,w),(n,e)))
    return grids
    

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    from math import radians, cos, sin, asin, sqrt
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    km = 6367 * c
    m = km *1000
    return m   


def ptfromln(pt, ln):
    """
    crs: espg: 4326, crs that uses lat lon
    get the projection of lonlat point to line
    then get distance on earth between point and line
    """
    n_pt = ln.interpolate(ln.project(pt))
    lon1, lat1 = n_pt.coords[0]
    lon2, lat2 = pt.coords[0]
    return haversine(lon1, lat1, lon2, lat2)


def check_crs(gpdf, epsg_code):
    if not gpdf.crs['init'] == u'epsg:%s' % epsg_code:
        raise ValueError('the crs of GeoDataFrame is not epsg:%s' % epsg_code)


def pts2seg(gp_pts, gp_segs, near_dis_thres=5, buffer_dis=50):
    """
    pts and segs are assumed as geopandas.GeoDataFrame with crs:4326
    1. check crs and change crs to epsg:3559 (NAD83(NSRS2007) / Maryland)
    2. get segid of near seg(s) based on var:near_dis_thres for each point
    3. for those points without any near segs
     - buffer them var:buffer_dis meters to find near segs
     - use func:ptfromln to get on earth distance from point to line
     - get one segid of the nearest seg
    """
    import geopandas as gp
    import pandas as pd

    check_crs(gp_pts,4326)
    check_crs(gp_segs, 4326)
    gp_pts_crs,gp_segs_crs = gp_pts.to_crs(epsg=3559), gp_segs.to_crs(epsg=3559)

    gp_pts_crs_bfr = gp_pts_crs.copy()
    gp_pts_crs_bfr.geometry = gp_pts_crs_bfr.buffer(near_dis_thres*1.1)

    close_jn = gp.tools.sjoin(gp_pts_crs_bfr, gp_segs_crs)[['OBJECTID_left','STREETSEGID_right']]

    processed_pts = set(pd.unique(close_jn.OBJECTID_left))
    mask = (~gp_pts_crs_bfr.OBJECTID.isin(processed_pts))
    far_jns = []
    while gp_pts_crs_bfr[mask].shape[0]!=0:
        gp_pts_crs_bfr.loc[mask, 'geometry'] = gp_pts_crs_bfr[mask].buffer(buffer_dis)
        jn = gp.tools.sjoin(gp_pts_crs_bfr[mask], gp_segs_crs)[['OBJECTID_left','STREETSEGID_right']]
        far_jns.append(jn)
        processed_pts |= set(pd.unique(jn.OBJECTID_left))
        mask = (~gp_pts_crs_bfr.OBJECTID.isin(processed_pts))
        
    far_jns = pd.concat(far_jns)
    mr_far_jns = pd.merge(gp_segs[['geometry','STREETSEGID']],far_jns , left_on='STREETSEGID', right_on='STREETSEGID_right')
    mr_far_jns = pd.merge(gp_pts[['OBJECTID','geometry','STREETSEGID']],mr_far_jns, left_on='OBJECTID', right_on='OBJECTID_left')
    mr_far_jns['dis']=mr_far_jns.apply(lambda x: ptfromln(x.geometry_x, x.geometry_y),axis=1)

    result = close_jn.groupby('OBJECTID_left')['STREETSEGID_right'].apply(list).append(mr_far_jns.groupby('OBJECTID').apply(lambda x: [x.ix[x.dis.idxmin()].STREETSEGID_y]))
    return pd.DataFrame(result, columns=['segid'])
