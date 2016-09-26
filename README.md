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

[MV_dc]:http://opendata.dc.gov/datasets?q=moving+violations&sort_by=relevance
[Geopandas]:http://geopandas.org/
