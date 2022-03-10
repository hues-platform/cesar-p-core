# coding=utf-8
#
# Copyright (c) 2022, Empa, Leonie Fierz, Aaron Bojarski, Ricardo Parreira da Silva, Sven Eggimann.
#
# This file is part of CESAR-P - Combined Energy Simulation And Retrofit written in Python
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Contact: https://www.empa.ch/web/s313
#
"""
Import building shape data from shape file.
!!! NOTE: Please install geopandas library manually, as it could not be automated with poetry (...fiona is not available on PyPI for Windows...).
Download GDAL and fiona wheels from https://www.lfd.uci.edu/~gohlke/pythonlibs, pip install them and then do pip install geopandas.
See also https://github.com/Toblerity/Fiona#windows
I needed to manually copy geos_c.dll, geos.dll to .venv/Library/bin from a geopandas installation with conda....
"""
import pandas as pd

try:
    import geopandas as gpd
except ModuleNotFoundError:
    pass


def read_sitevertices_from_shp(file_path):
    """
    Read building shape information from shp and aggregate to a DataFrame.
    To each building a unique bld_id is assigned.

    Expected entries per row in csv, each representing one vertex of a building
    'gis_fid': fid identifying building in the external gis tool
    'height': height of building in meter
    'x': x coordinate of vertex, meter
    'y': y coordinate of vertex, meter

    :param file_path: full path to shp file
    :return: pandas DataFrame with one row for each building, columns being 'gis_fid', 'height', 'footprint_shape' and 'bld_id' as index.
             'footprint_shape' is a pandas DataFrame[columns=[x,y]] holding all building vertices
    """
    try:
        gdf_shp = gpd.read_file(file_path)
    except NameError:
        raise ModuleNotFoundError(f"to use read_sitevertices_from_shp please install geopandas. See instructions {__file__}")

    required_keys = ["TARGET_FID", "HEIGHT"]

    gdf_columns = gdf_shp.columns.tolist()

    for required_key in required_keys:
        assert required_key in gdf_columns, "Attribute: '{}' is missing in shapefile".format(required_key)

    container_list = []

    for building_index in gdf_shp.index:

        building_geometry = gdf_shp.loc[building_index].geometry

        target_fid = gdf_shp.loc[building_index]["TARGET_FID"]
        height = gdf_shp.loc[building_index]["HEIGHT"]

        # Check if closed polygon
        assert building_geometry.boundary.is_ring, "Polygon with target_fid {} is not closed".format(target_fid)

        # Get boundary coordinates
        clockwise_coordinates = list(building_geometry.boundary.coords)

        # Iterate building vertices anti-clockwise
        for vertex in clockwise_coordinates:
            x_coordinate = vertex[0]
            y_coordinate = vertex[1]

            container_list.append([target_fid, x_coordinate, y_coordinate, height])

    df_geometry = pd.DataFrame(container_list, columns=["gis_fid", "x", "y", "height"], dtype=float)

    return df_geometry
