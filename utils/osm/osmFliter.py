def filter_objs_by_ids(osm_objs, osm_ids):
    return [obj for obj in osm_objs if obj.id in osm_ids]


def have_tag_value(obj, tag='*', value='*'):
    if not obj.tags:  # have no tag, discard it whatever query is
        return False
    if tag == '*':  # True for having any tag
        return True
    if not tag in obj.tags:
        return False
    if value == '*':
        return True
    return obj.tags[tag] in value


def filter_obj(obj, have_one=(('*', '*'),), donthave=()):
    for tag, value in donthave:
        if have_tag_value(obj, tag, value):
            return False

    for tag, value in have_one:
        if have_tag_value(obj, tag, value):
            return True
    return False


def filter_osm_data(osm_objs, have_one=(('*', '*'),), donthave=(), special_filters=None):
    objs = []
    if special_filters:
        for o in osm_objs:
            pass_filter = True
            for filt in special_filters:
                if not filt(o):
                    pass_filter = False
                    break
            if pass_filter:
                objs.append(o)
    else:
        for o in osm_objs:
            if filter_obj(o, have_one, donthave):
                objs.append(o)
    return objs


def filter_osm_data_to_df(osm_objs, have_one=(('*', '*'),), donthave=(), special_filters=None):
    import pandas as pd
    objs = filter_osm_data(osm_objs, have_one, donthave, special_filters=special_filters)
    attr = [x[0] for x in have_one]
    objs = [[o.id] + [o.tags.get(k, '') for k in attr] for o in objs]
    df_objs = pd.DataFrame(objs, columns=['id'] + attr)
    return df_objs


# specific filter
def filter_is_motorway(obj):
    tag_highway = [('highway','*')]
    tag_bike_walk = [('highway', set(['path','pedestrian','footway','steps','cycleway','crossing']))]
    return filter_obj(obj, tag_highway, tag_bike_walk)
def filter_isnot_motorway(obj):
    return not filter_is_motorway(obj)

def filter_is_bike_walk_way(obj):
    tag_bike_walk = [('highway', set(['path','pedestrian','footway','steps','cycleway','crossing']))]
    return filter_obj(obj, tag_bike_walk)
def filter_isnot_bike_walk_way(obj):
    return not filter_is_bike_walk_way(obj)

def filter_is_admin(obj):
    tag_admin_have = [('boundary','*'),('place','*')]
    tag_admin_donthave = [('leisure','*'), ('amenity','*'), ('boundary',['national_park','protected_area']),
                          ('natural','*'), ('place', ['island', 'islet', 'square', 'farm'])]
    return filter_obj(obj, tag_admin_have, tag_admin_donthave)

def filter_isnot_admin(obj):
    return not filter_is_admin(obj)

def filter_is_restriction(obj):
    tag_restriction = [('restriction','*'),('restriction:conditional','*'), ('restriction:hgv','*')]
    return filter_obj(obj, tag_restriction)

def filter_isnot_restriction(obj):
    return not filter_is_restriction(obj)

def filter_is_landuse(obj):
    tag_landuse = [('landuse','*')]
    return filter_obj(obj, tag_landuse)

def filter_isnot_landuse(obj):
    return not filter_is_landuse(obj)