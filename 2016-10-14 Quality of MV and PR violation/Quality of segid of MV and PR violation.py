import datetime
import geopandas as gp
import numpy as np
import pandas as pd

def pts2seg(pts, gp_segs, buffer_dis=50, near_dis_thres=5):
    pts_crs,gp_segs_crs = pts.to_crs(epsg=3559), dc_segs.to_crs(epsg=3559)
    pts_crs_bfr = pts_crs.copy()

    pts_crs_bfr.geometry = pts_crs_bfr.buffer(near_dis_thres*1.1)
    close_jn = gp.tools.sjoin(pts_crs_bfr, gp_segs_crs)[['OBJECTID_left','STREETSEGID_right']]
    handledid = set(pd.unique(close_jn.OBJECTID_left))
    mask = (~pts_crs_bfr.OBJECTID.isin(handledid))

    far_jns = []
    while pts_crs_bfr[mask].shape[0]!=0:
        pts_crs_bfr.loc[mask, 'geometry'] = pts_crs_bfr[mask].buffer(buffer_dis)
        jn = gp.tools.sjoin(pts_crs_bfr[mask], gp_segs_crs)[['OBJECTID_left','STREETSEGID_right']]
        far_jns.append(jn)
        handledid |= set(pd.unique(jn.OBJECTID_left))
        mask = (~pts_crs_bfr.OBJECTID.isin(handledid))
        
    far_jns = pd.concat(far_jns)
    mr = pd.merge(dc_segs[['geometry','STREETSEGID']],far_jns , left_on='STREETSEGID', right_on='STREETSEGID_right')
    mr = pd.merge(pts[['OBJECTID','geometry','STREETSEGID']],mr, left_on='OBJECTID', right_on='OBJECTID_left')
    mr['dis']=mr.apply(lambda x: ptfromln(x.geometry_x, x.geometry_y),axis=1)
    result = close_jn.groupby('OBJECTID_left')['STREETSEGID_right'].apply(list).append(mr.groupby('OBJECTID').apply(lambda x: [x.ix[x.dis.idxmin()].STREETSEGID_y]))
    return pd.DataFrame(result, columns=['segid'])


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
    n_pt = ln.interpolate(ln.project(pt))
    lon1, lat1 = n_pt.coords[0]
    lon2, lat2 = pt.coords[0]
    return haversine(lon1, lat1, lon2, lat2)
    

pts_files = [
    #'dcdata/Moving_Violations_in_December_2011.geojson',
    'dcdata/Moving_Violations_in_January_2016.geojson',
    'dcdata/Moving_Violations_in_February_2016.geojson',
    'dcdata/Moving_Violations_in_March_2016.geojson',
    'dcdata/Moving_Violations_in_April_2016.geojson',
    'dcdata/Moving_Violations_in_May_2016.geojson',
    'dcdata/Parking_Violations_in_January_2016.geojson',
    'dcdata/Parking_Violations_in_February_2016.geojson',
    'dcdata/Parking_Violations_in_March_2016.geojson',
    'dcdata/Parking_Violations_in_April_2016.geojson',
    'dcdata/Parking_Violations_in_May_2016.geojson',
    #'dcdata/Crashes_in_the_District_of_Columbia.geojson',
]
output_data_file = 'Quality of segid of MV and PR violation.txt'
dc_segs = gp.read_file('dcdata\Street_Segments.geojson')
dc_STREETSEGIDS = set(dc_segs.STREETSEGID.tolist())
results = []
bins_dis= [5,10,50,100,150,200]
bins_ratio = [1,2,5,10,100,1000,10000]
def get_bins_tag(bins):
    bins = ['']+bins+['']
    l = len(bins)
    return ['%s~%s' % (bins[i],bins[i+1]) for i in range(l-1)]
bins_dis_tag = get_bins_tag(bins_dis)
bins_ratio_tag = get_bins_tag(bins_ratio)
columns = ['data','total','match','perfect match','match but intrstn','intersection','seg not exist','no seg', 'not match org seg']+bins_ratio_tag+bins_dis_tag+bins_dis_tag
with open(output_data_file,'w') as f:
    f.write(','.join(columns))
    f.write('\n')
    print 'begin analysing'
    for pts_file in pts_files:
        print 'file: %s' %pts_file, datetime.datetime.now()
        pts = gp.read_file(pts_file)
        pts_seg = pts2seg(pts, dc_segs)
        pts_seg_ids = pd.merge(pts_seg, pts[['OBJECTID','STREETSEGID','geometry']], left_index=True, right_on='OBJECTID')
        pts_seg_ids = pd.merge(pts_seg_ids, dc_segs[['OBJECTID','STREETSEGID','geometry']], left_on='STREETSEGID', right_on='STREETSEGID',how='left')
        pts_seg_ids['no_seg'] = pts_seg_ids.STREETSEGID.isnull()
        pts_seg_ids['match'] = pts_seg_ids.apply(lambda x: x.STREETSEGID in x.segid ,axis=1)
        pts_seg_ids['seg_exist'] = pts_seg_ids.STREETSEGID.apply(lambda x: x in dc_STREETSEGIDS)
        cndtn=(~pts_seg_ids.match)&(~pts_seg_ids['no_seg'])&(pts_seg_ids['seg_exist'])
        pts_seg_ids.loc[cndtn, 'dis_org'] = pts_seg_ids[cndtn].apply(
            lambda x: ptfromln(x.geometry_x, x.geometry_y) if not np.isnan(x.STREETSEGID) else None, axis=1)
        def get_dis_avg(x, gp_segs):
            pt = x.geometry_x
            segs = gp_segs[gp_segs.STREETSEGID.isin(x.segid)].geometry.tolist()
            dis = []
            for ln in segs:
                dis.append(ptfromln(pt, ln))
            return np.array(dis).mean()
        pts_seg_ids['dis_avg'] = pts_seg_ids.apply(lambda x: get_dis_avg(x, dc_segs),axis=1)
        pts_seg_ids.loc[~pts_seg_ids.dis_org.isnull(),'ratio'] = pts_seg_ids[~pts_seg_ids.dis_org.isnull()].apply(lambda x: x.dis_org/x.dis_avg, axis=1)
        cnt_match_seg =pts_seg_ids.match.value_counts()[True]
        cnt_match_intrscn = pts_seg_ids[(pts_seg_ids.match)&pts_seg_ids.segid.apply(lambda x: len(x)>1)].shape[0]
        cnt_perfect_match = pts_seg_ids[(pts_seg_ids.match)&pts_seg_ids.segid.apply(lambda x: len(x)==1)].shape[0]
        cnt_intrscn =  pts_seg_ids[pts_seg_ids.segid.apply(lambda x: len(x)>1)].shape[0]
        cnt_not_match_intrscn = pts_seg_ids[(~pts_seg_ids.match)&pts_seg_ids.segid.apply(lambda x: len(x)>1)].shape[0]
        cnt_no_seg = pts_seg_ids.no_seg.value_counts()[True]
        cnt_seg_not_exist = pts_seg_ids.seg_exist.value_counts()[False] - cnt_no_seg
        cnt_has_dis_org = pts_seg_ids[~pts_seg_ids.dis_org.isnull()].shape[0]
        cdtn=(~pts_seg_ids.dis_org.isnull())
        pts_seg_ids.loc[cdtn,'ratio_binned'] = [bins_ratio_tag[int(x)] for x in np.digitize(pts_seg_ids[cdtn].ratio,bins_ratio)]
        pts_seg_ids.loc[cdtn,'dis_org_binned'] = [bins_dis_tag[int(x)] for x in np.digitize(pts_seg_ids.loc[cdtn].dis_org,bins_dis)]
        pts_seg_ids.loc[cdtn,'dis_avg_binned'] = [bins_dis_tag[int(x)] for x in np.digitize(pts_seg_ids.loc[cdtn].dis_avg, bins_dis)]
        total = pts.shape[0]
        result = [total, cnt_match_seg, cnt_perfect_match, cnt_match_intrscn, cnt_intrscn,cnt_seg_not_exist, cnt_no_seg, cnt_has_dis_org]+\
        pts_seg_ids.ratio_binned.value_counts().reindex(bins_ratio_tag).fillna(0).tolist()+\
        pts_seg_ids.dis_org_binned.value_counts().reindex(bins_dis_tag).fillna(0).tolist()+\
        pts_seg_ids.dis_avg_binned.value_counts().reindex(bins_dis_tag).fillna(0).tolist()
        result_prcnt = np.array(result)/total*1.0

        results.append(','.join([str(int(x)) for x in result]))
        results.append(','.join(['%.3f%%' % (x*100) for x in result_prcnt]))
        print 'writing results'
        f.write(pts_file)
        f.write(',')
        f.write(','.join([str(int(x)) for x in result]))
        f.write('\n')
        f.write(pts_file)
        f.write(',')
        f.write(','.join(['%.3f%%' % (x*100) for x in result_prcnt]))
        f.write('\n')
        
print datetime.datetime.now()
print 'finished'

