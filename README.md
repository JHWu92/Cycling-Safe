# Cycling-Safe

## Base Map

### data
1. http://opendata.dc.gov
  1. Street segment (ST)
    - 13522 segments
  2. [Moving Violation][MV_dc] (MV)
    - Most STREETSEGID in MV DATA is corresponding to ST DATA
    - Some points in MV DATA have no STREETSEGID
    - Some points’ STREETSEGID is different from ST DATA
    - The best buffer value for spatial match is still undecided

### Tools
1. [Geopandas][Geopandas] (python package)
  - geopandas.tools.sjoin: it can analyse points in polygon/intersections of polygons.
2. [SNAP][SNAP] (python package): Stanford Network Analysis Project
  - snap.GetBetweennessCentr can calculate betweenness for nodes and edges.

### Function
```
def build_load_idx(seg_idx_path, segs_with_ids, update=False):
    """
    params:
        seg_idx_path: the path of segment index if the index doesn't exist, the index will be built.
        segs_with_ids: dict: key=objid, value=shapely.geometry.LineString, segments that will be indexed
        update: True: rebuild the index no matter whether the index exists
    Output:
        rtree index of given segments.
    """

def pt2seg(pt, segs_with_ids, seg_idx):
    """
    params: 
        pt: shapely.geometry.Point
        segs_with_ids:
        seg_idx: rtree index of segments
    Process:
        1. load segment index and find segments(var:idx_match) whose bounds intersect with point's bounds
           if there isn't any matched segment, the point will be buffered until len of idx_match !=0
        2. find the segments that actually intersect with given point
           if there isn't any intersected segment, nearest segment will be returned
    Output:
       hint: whether the returned segid is "nearest" or "intersected"
       segid: assigned segment id
       cnt: len of candidates 
       candidates: the index of segments that are "equally near"/"intersected" to the point
       distance: the distance between point and segment
    """
```

[MV_dc]:http://opendata.dc.gov/datasets?q=moving+violations&sort_by=relevance
[Geopandas]:http://geopandas.org/
