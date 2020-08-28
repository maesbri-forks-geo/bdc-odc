#
# This file is part of BDC-ODC.
# Copyright (C) 2020 INPE.
#
# stac2odc is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import uuid

import os
import osgeo
from osgeo import osr
from urllib.parse import urlparse

from datetime import datetime


def href_to_path(href, basepath):
    url = urlparse(href)
    return os.path.normpath(basepath + url.path)


def lon_lat_2_y_x(geo_ref_points):
    def transform(p):
        return {'x': p['lon'], 'y': p['lat']}

    return {key: transform(p) for key, p in geo_ref_points.items()}


def generate_id(feature):
    for link in feature['links']:
        if link['rel'] == 'self':
            return str(uuid.uuid5(uuid.NAMESPACE_URL, link['href']))
    return str(uuid.uuid5(uuid.NAMESPACE_URL, feature['id']))


def generate_product_type(collection):
    return "{}_{}_{}".format(
        collection['properties']['bdc:temporal_composition']['schema'],
        collection['properties']['bdc:temporal_composition']['step'],
        collection['properties']['bdc:temporal_composition']['unit'])


def convert_coords(coords, in_spatial_ref, out_spatial_ref):
    t = osr.CoordinateTransformation(in_spatial_ref, out_spatial_ref)

    if int(osgeo.__version__[0]) >= 3:
        # GDAL 3 changes axis order: https://github.com/OSGeo/gdal/issues/1546
        in_spatial_ref.SetAxisMappingStrategy(
            osgeo.osr.OAMS_TRADITIONAL_GIS_ORDER)
        out_spatial_ref.SetAxisMappingStrategy(
            osgeo.osr.OAMS_TRADITIONAL_GIS_ORDER)

    def transform(p):
        a = t.TransformPoint(p['lon'], p['lat'])
        return {'lon': a[0], 'lat': a[1]}

    return {key: transform(p) for key, p in coords.items()}


def convert_coords_xy(coords, in_spatial_ref, out_spatial_ref):
    t = osr.CoordinateTransformation(in_spatial_ref, out_spatial_ref)

    def transform(p):
        a = t.TransformPoint(p['x'], p['y'])
        return {'x': a[0], 'y': a[1]}

    return {key: transform(p) for key, p in coords.items()}


def stacdate_to_odcdate(datepattern):
    """Function to transform stac date pattern to ODC pattern
    
    Args:
        datepattern (str): A String pattern with date (e. g. CB4_64_16D_STK_v1_020024_2020-07-11_2020-07-26)
    Returns:
        datetime
    """

    start_end = datepattern.split('_')[-2:]
    return (
        datetime.strptime(i, '%Y-%m-%d').strftime("%Y-%m-%d %H:%M:%S.%fZ") for i in start_end
    )


def fix_precollection_crs(crs):
    """Function to fix duplicated datum and ellipsoid in proj string of 
    bdc pre-collection datasets
    """
    import re
    return re.sub('\+datum=(\S)*\s', '', crs)
