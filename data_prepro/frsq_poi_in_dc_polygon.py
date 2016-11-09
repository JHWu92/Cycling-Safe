import numpy as np
import time
import geopandas as gp
import pandas as pd
import shapely.geometry as shpgeo
import sys, os
sys.path.insert(0, os.path.abspath('../'))
print sys.path

from utils.geofunc import grid_line, grid_area
def tu2str(tu):
    return ','.join([str(t) for t in tu])


def swne2poly(sw,ne):
    return shpgeo.box(sw[1], sw[0], ne[1], ne[0])
    
   
    
import foursquare
clients_id_secret = [
    ('B5UXLIK21H3XVVIIKBYVG55XXOAVF50OAEFYT5KNWEZ0AJFS', 'AZGHYGMVF3CPO0VUWQWIFP4DYBEIPUOLCT31SUKVTA3FOQRP'),
    ('VLX3BBUP4VTKT5BP53CBWMTKUWGVGBE34O52S4ULNWAAJURO','2534VD02WWGCJCILTTRJXXEOPLDTXDVREKXAKGX515HJV3H0'),
    ('VJR0HIRSW5AEWJL1U0YVP2CJNNY1DOMEBRBM3XD15MW55LQZ', 'MM55NWKDFC51M1PU2I3GNXDJQ0NNIDKNVBRNZJSW4COLBQIR'),
    ('CWCA2GY2YJKS4GTCBU4V3KI0KH2KMDVZXVJVKFS5C3VPXGCV', 'NLMSW00OFS2FZDYIEA5ZPM4RH35ZAHHFGQSTTC3BYGGX0OIS'),
    ('GOOWLBFKGWVYJA5E4ES5MUQCF5B2NWITHFNCCVUOLIIN3ZF3', 'UUZ32DS3U5CC22XJ5LIO3RVVMRWL4NFYOM2V3SZ0H1ETWKSC'),
    ('FJLWGSADBT2R1ELM0W14CIHSOSDZ0ZVGGKJOV5CUEC3JSUKM','0SA5RHLJ5LKRPPPAKQMLJVBB0HCWTQJ2LJD5OPO4LCO3H00L'),
    ('QUKQ3QQUXVAYNJOEYNOJIKLGGFPUTOQ2PWS4PNYJUTVY2UKB','BLCCAQAZYXFVLELFDYKJT4EOFLI3WGW4YKMDOIQ2XPFE3J3C'),
    ('I5QIF0SFJCRMAVBSBV3KEZSCQ02MLQZPJ2JPKIG2UFREDUXL','GQDNDG03NP4IXXM0QSIJUL3H3KMX0B2OWRNJRVQX3LH3FFOJ'),
    ('NRAQWNRMKH4W1BP3SQXTLJEKCQKXYOH1G0WPEBPFHVKEGZTM', 'BU2ST3EPY3MSUMKU1XLNTVV00XYBFDWCNWIVJNCWQ502OF11'),
]

clients = [foursquare.Foursquare(client_id=client_id, client_secret=client_secret) for client_id, client_secret in clients_id_secret]
print 'prepare foursquare api'
    
    
dc_poly_gpdf = gp.read_file('../data/dc_polygon.geojson')
dc_poly = dc_poly_gpdf.geometry.values[0]
dc_bbox = dc_poly.buffer(0.001).bounds
SW = (dc_bbox[1], dc_bbox[0])
NE = (dc_bbox[3], dc_bbox[2])
grids = grid_area(SW, NE, ngrid=100)
print 'get dc grids'

request_cnt = 0
data_cach = []
while len(grids)>0:
    sw, ne = grids.pop()
    swnepoly = swne2poly(sw,ne)
    if swnepoly.intersects(dc_poly):
#         time.sleep(0.01)
        client = clients[request_cnt%len(clients)]
        search = client.venues.search(params={'intent': 'browse', 'sw':tu2str(sw), 'ne':tu2str(ne), 'limit':50})
        request_cnt += 1
        len_venues = search['venues'].__len__()
        data_cach.append('{}\t{}\t{}'.format((sw,ne),len_venues, search))
        if len_venues>=50:
            new_grids = grid_area(sw,ne)
            grids.extend(new_grids)
        if request_cnt % 2000==0:
            print 'requested', request_cnt, ', writing results'
            with open('../data/output/4square/{}.txt'.format(request_cnt),'w') as f:
                f.write('\n'.join(data_cach))
            data_cach = []
if len(data_cach)>0:
    with open('../data/output/4square/{}.txt'.format(request_cnt),'w') as f:
        f.write('\n'.join(data_cach))
    data_cach = []
    
