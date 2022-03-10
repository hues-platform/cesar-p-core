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
Writes geometric properties of the building model to an IDF.
As each geometric element, such as a wall, roof, ground, window, needs a construction assigend, the methods needing
such a construction reference get a object passed with an interface which must match "ConstrWriterProtocol". The design
assumes that the "ConstructionWriter" knows which construction to used based on the building type or for a shading
object. Different constructions for the same BuildingElement (e.g. different constructions for the walls) are not
supported.

Up to 250 footprint vertices for a building are supported (limited by the IDD respectively eppy, which relies that the field for all vertices are defined in the IDD).
Other objects have been extended in the IDD as well. If you want to know all, compare the IDD included in ressources with an original one or have a look
at the notes at the top of the modified IDD.
"""
from typing import Any, Protocol, Tuple, Mapping, Dict, List

from eppy.modeleditor import IDF
from eppy.bunch_subclass import EpBunch
from cesarp.model.Construction import BuildingElement as bec
from cesarp.model.BldgShape import BldgShapeEnvelope, BldgShapeDetailed

from cesarp.eplus_adapter import idf_strings
from cesarp.eplus_adapter.idf_strings import ViewFactorToGround
from cesarp.model.BuildingElement import BuildingElement


class ConstrWriterProtocol(Protocol):
    def add_construction(self, idf: IDF, bldg_elem: BuildingElement) -> str:
        ...

    def add_window_glass_construction(self, idf: IDF) -> str:
        ...

    def add_win_frame_construction(self, idf: IDF) -> Tuple[str, Any]:
        ...

    def add_shading_surface_construction(self, idf: IDF, bldg_elem: BuildingElement) -> Any:
        ...


def add_basic_geometry_settings(idf):
    geometry_rules_idf_obj = idf.newidfobject(idf_strings.IDFObjects.global_geometry_rules)
    geometry_rules_idf_obj.Starting_Vertex_Position = idf_strings.VertexPosition.lower_left_corner
    geometry_rules_idf_obj.Vertex_Entry_Direction = idf_strings.VertexEntryDirection.counter_clockwise
    geometry_rules_idf_obj.Coordinate_System = idf_strings.CoordinateSystem.relative


def add_basic_shading_settings(idf, shadow_calculation_frequency: int):
    shadow_calc_idf_obj = idf.newidfobject(idf_strings.IDFObjects.shadow_calculation)
    if idf.idd_version[0] == 9 and idf.idd_version[1] >= 3:
        shadow_calc_idf_obj.Shading_Calculation_Update_Frequency = shadow_calculation_frequency
    else:
        shadow_calc_idf_obj.Calculation_Frequency = shadow_calculation_frequency


def add_building(idf, bldg_shape: BldgShapeDetailed, constr_handler: ConstrWriterProtocol) -> Dict[int, Tuple[str, List[EpBunch]]]:
    """
    Constraints: floor_nr in walls, adjacent_walls_bool, windows start at 0 for groundfloor and are ascending

    :param bldg_shape - dict according to cesarp.manager.manager_protocols.BldgShapeDetailed
    """
    zones = {}

    assert len(bldg_shape.walls) == (len(bldg_shape.internal_floors) + 1), "number of floors in 'walls' should be one more than number of internal floors"

    # frame and divider geometry and construction properties are currently defined per building
    constr_groundfloor_idf_obj_name = constr_handler.add_construction(idf, BuildingElement.GROUNDFLOOR)
    constr_internal_ceileing_idf_obj_name = constr_handler.add_construction(idf, BuildingElement.INTERNAL_CEILING)
    constr_internal_floor_idf_obj_name = constr_handler.add_construction(idf, BuildingElement.INTERNAL_FLOOR)
    constr_wall_idf_obj_name = constr_handler.add_construction(idf, BuildingElement.WALL)
    constr_roof_idf_obj_name = constr_handler.add_construction(idf, BuildingElement.ROOF)
    # only one window frame width per building is supported. if more than one frame width shall be used,
    # make sure you set unique names for each frame and divider idf obj (currently idf obj is created and name set in constr_handler method)
    (win_frame_idf_obj_name, idf_obj_win_frame) = constr_handler.add_win_frame_construction(idf)
    add_win_frame_geometry(idf_obj_win_frame, bldg_shape.window_frame)
    constr_win_glass_idf_obj_name = constr_handler.add_window_glass_construction(idf)

    zone_idf_obj_name = None
    for story_nr, walls_on_story in enumerate(bldg_shape.walls):
        zone_block_nr = story_nr
        previouse_zone_obj_name = zone_idf_obj_name
        zone_idf_obj_name = add_zone(idf, zone_block_nr)
        windows_in_zone = []

        if story_nr == 0:
            add_groundfloor(idf, bldg_shape.groundfloor, zone_idf_obj_name, constr_groundfloor_idf_obj_name)
        else:
            add_ceiling_floor_pair(
                idf,
                bldg_shape.internal_floors[story_nr - 1],
                previouse_zone_obj_name,
                zone_idf_obj_name,
                constr_internal_ceileing_idf_obj_name,
                constr_internal_floor_idf_obj_name,
            )

        for wall_nr, wall in enumerate(walls_on_story):
            wall_idf_obj_name = add_wall(
                idf,
                wall,
                wall_nr,
                zone_idf_obj_name,
                constr_wall_idf_obj_name,
                is_adjacent=bldg_shape.adjacent_walls_bool[story_nr][wall_nr],
            )

            win_glass_shape = bldg_shape.windows[story_nr][wall_nr]
            if win_glass_shape is not None:
                win_idf_obj = add_window(
                    idf,
                    win_glass_shape,
                    wall_idf_obj_name,
                    constr_win_glass_idf_obj_name,
                    win_frame_idf_obj_name,
                )
                windows_in_zone.append(win_idf_obj)

        # add roof in zone of last story
        if story_nr == len(bldg_shape.walls) - 1:
            add_roof(idf, bldg_shape.roof, zone_idf_obj_name, constr_roof_idf_obj_name)

        zones[story_nr] = (zone_idf_obj_name, windows_in_zone)

    return zones


def add_neighbours_as_shading_objects(idf: IDF, bldg_shapes_simple: Mapping[int, BldgShapeEnvelope], constr_handler: ConstrWriterProtocol):
    for gis_fid, single_bldg_shape in bldg_shapes_simple.items():
        assert len(single_bldg_shape.walls) == 1, f"only one story expected for shading object with gis id {gis_fid}"
        for wall_nr, wall in enumerate(single_bldg_shape.walls[0]):
            shading_reflectance_constr_wall_obj = constr_handler.add_shading_surface_construction(idf, bec.WALL)
            add_shading_surface_wall(idf, gis_fid, wall_nr, wall, shading_reflectance_constr_wall_obj)
        shading_reflectance_constr_roof_obj = constr_handler.add_shading_surface_construction(idf, bec.ROOF)
        add_shading_surface_roof(idf, gis_fid, single_bldg_shape.roof, shading_reflectance_constr_roof_obj)


def add_wall(idf, coords, wall_nr, zone_obj_name, constr_obj_name, is_adjacent=False):
    wall_idf_obj = idf.newidfobject(idf_strings.IDFObjects.bldg_surface_detailed)
    wall_idf_obj.Name = idf_strings.CustomObjNames.wall_name.format(zone_obj_name, wall_nr)
    wall_idf_obj.Surface_Type = idf_strings.BldgSurfaceType.wall
    wall_idf_obj.Construction_Name = constr_obj_name
    wall_idf_obj.Zone_Name = zone_obj_name
    if is_adjacent:
        wall_idf_obj.Outside_Boundary_Condition = idf_strings.OutsideBoundaryCond.adiabatic
        set_params_not_weather_exposed(wall_idf_obj)
        set_veiw_factor_to_ground(wall_idf_obj, ViewFactorToGround.adjacent)
    else:
        wall_idf_obj.Outside_Boundary_Condition = idf_strings.OutsideBoundaryCond.outdoors
        set_params_weather_exposed(wall_idf_obj)
        set_veiw_factor_to_ground(wall_idf_obj)
    set_coordinates_clockwise(wall_idf_obj, coords)
    return wall_idf_obj.Name


def add_ceiling_floor_pair(idf, coords, zone_ceiling_obj_name, zone_floor_obj_name, ceiling_constr_obj_name, floor_constr_obj_name):
    ceiling_name = idf_strings.CustomObjNames.ceiling_name.format(zone_ceiling_obj_name)
    floor_name = idf_strings.CustomObjNames.floor_name.format(zone_floor_obj_name)

    ceiling_idf_obj = idf.newidfobject(idf_strings.IDFObjects.bldg_surface_detailed)
    ceiling_idf_obj.Name = ceiling_name
    ceiling_idf_obj.Surface_Type = idf_strings.BldgSurfaceType.ceiling
    ceiling_idf_obj.Construction_Name = ceiling_constr_obj_name
    ceiling_idf_obj.Zone_Name = zone_ceiling_obj_name
    set_outside_boundary_condition(ceiling_idf_obj, floor_name)
    set_params_not_weather_exposed(ceiling_idf_obj)
    set_veiw_factor_to_ground(ViewFactorToGround.indoors)
    set_coordinates_counterclockwise(ceiling_idf_obj, coords)

    floor_idf_obj = idf.newidfobject(idf_strings.IDFObjects.bldg_surface_detailed)
    floor_idf_obj.Name = floor_name
    floor_idf_obj.Surface_Type = idf_strings.BldgSurfaceType.floor
    floor_idf_obj.Construction_Name = floor_constr_obj_name
    floor_idf_obj.Zone_Name = zone_floor_obj_name
    set_outside_boundary_condition(floor_idf_obj, ceiling_name)
    set_params_not_weather_exposed(floor_idf_obj)
    set_veiw_factor_to_ground(ViewFactorToGround.indoors)
    set_coordinates_clockwise(floor_idf_obj, coords)


def add_roof(idf, coords, zone_obj_name, constr_obj_name):
    roof_idf_obj = idf.newidfobject(idf_strings.IDFObjects.bldg_surface_detailed)
    roof_idf_obj.Name = idf_strings.CustomObjNames.roof_name.format(zone_obj_name)
    roof_idf_obj.Surface_Type = idf_strings.BldgSurfaceType.roof
    roof_idf_obj.Construction_Name = constr_obj_name
    roof_idf_obj.Zone_Name = zone_obj_name
    roof_idf_obj.Outside_Boundary_Condition = idf_strings.OutsideBoundaryCond.outdoors
    set_params_weather_exposed(roof_idf_obj)
    set_veiw_factor_to_ground(roof_idf_obj, ViewFactorToGround.horizontal_up)
    set_coordinates_counterclockwise(roof_idf_obj, coords)


def add_groundfloor(idf, coords, zone_obj_name, constr_obj_name):
    groundfloor_idf_obj = idf.newidfobject(idf_strings.IDFObjects.bldg_surface_detailed)
    groundfloor_idf_obj.Name = idf_strings.CustomObjNames.groundfloor_name.format(zone_obj_name)
    groundfloor_idf_obj.Surface_Type = idf_strings.BldgSurfaceType.floor
    groundfloor_idf_obj.Construction_Name = constr_obj_name
    groundfloor_idf_obj.Zone_Name = zone_obj_name
    groundfloor_idf_obj.Outside_Boundary_Condition = idf_strings.OutsideBoundaryCond.ground
    set_params_not_weather_exposed(groundfloor_idf_obj)
    set_veiw_factor_to_ground(groundfloor_idf_obj, ViewFactorToGround.horizontal_down)
    set_coordinates_clockwise(groundfloor_idf_obj, coords)


def add_window(idf, coords, base_wall_obj_name, win_glass_constr_obj_name, frame_divider_obj_name):
    win_idf_obj = idf.newidfobject(idf_strings.IDFObjects.fenestration_surface_detailed)
    win_idf_obj.Name = idf_strings.CustomObjNames.window_name.format(base_wall_obj_name)
    win_idf_obj.Surface_Type = idf_strings.FenestrationSurfaceType.window
    win_idf_obj.Construction_Name = win_glass_constr_obj_name
    win_idf_obj.Building_Surface_Name = base_wall_obj_name
    set_veiw_factor_to_ground(win_idf_obj, ViewFactorToGround.autocalculate)
    win_idf_obj.Frame_and_Divider_Name = frame_divider_obj_name
    set_coordinates_clockwise(win_idf_obj, coords)
    return win_idf_obj


def add_win_frame_geometry(idf_frame_divder_obj, shape_frame):
    idf_frame_divder_obj.Frame_Width = shape_frame["WIDTH"]


def add_zone(idf, zone_block_nr):
    zone_idf_obj = idf.newidfobject(idf_strings.IDFObjects.zone)
    zone_idf_obj.Name = idf_strings.CustomObjNames.bldg_zone_name.format(zone_block_nr)
    return zone_idf_obj.Name


def add_shading_surface_wall(idf, neigh_nr, bldg_elem_nr, coords, shading_reflectance_idf_obj: Any):
    """
    :param idf:
    :param neigh_nr:
    :param bldg_elem_nr:
    :param coords:
    :param shading_reflectance_idf_obj: eppy EpBunch
    :return:
    """
    shading_idf_obj_name = idf_strings.CustomObjNames.shading_bldg_wall_name.format(neigh_nr, bldg_elem_nr)
    wall_shading_idf_obj = idf.newidfobject(idf_strings.IDFObjects.shading_bldg_detailed)
    wall_shading_idf_obj.Name = shading_idf_obj_name
    set_coordinates_clockwise(wall_shading_idf_obj, coords)
    shading_reflectance_idf_obj.Shading_Surface_Name = shading_idf_obj_name
    return shading_idf_obj_name


def add_shading_surface_roof(idf, neigh_nr, coords, shading_reflectance_constr_roof_obj):
    shading_idf_obj_name = idf_strings.CustomObjNames.shading_bldg_roof_name.format(neigh_nr)
    wall_shading_idf_obj = idf.newidfobject(idf_strings.IDFObjects.shading_bldg_detailed)
    wall_shading_idf_obj.Name = shading_idf_obj_name
    set_coordinates_counterclockwise(wall_shading_idf_obj, coords)
    shading_reflectance_constr_roof_obj.Shading_Surface_Name = shading_idf_obj_name
    return shading_idf_obj_name


def set_outside_boundary_condition(idf_obj, other_surface_idf_name):
    """
    changes idf_obj in place
    :param idf_obj: for which to set the condition
    :param other_surface_idf_name: string name of the adjacent surface as used in the idf
    :return: None
    """
    idf_obj.Outside_Boundary_Condition = idf_strings.OutsideBoundaryCond.surface
    idf_obj.Outside_Boundary_Condition_Object = other_surface_idf_name


def set_params_weather_exposed(bldg_surface_idf_obj):
    bldg_surface_idf_obj.Sun_Exposure = idf_strings.WeahterCond.sun_exposed
    bldg_surface_idf_obj.Wind_Exposure = idf_strings.WeahterCond.wind_exposed


def set_params_not_weather_exposed(bldg_surface_idf_obj):
    bldg_surface_idf_obj.Sun_Exposure = idf_strings.WeahterCond.not_sun_exposed
    bldg_surface_idf_obj.Wind_Exposure = idf_strings.WeahterCond.not_wind_exposed


def set_veiw_factor_to_ground(idf_object, view_factor_prop=ViewFactorToGround.autocalculate):
    idf_object.View_Factor_to_Ground = view_factor_prop.value


def set_coordinates_clockwise(idf_object, wall):
    idf_object.Number_of_Vertices = len(wall)
    id = 1  # create new id for the vertices to be sure they are ascending
    for vertex_id, coord in wall.iterrows():
        setattr(
            idf_object,
            idf_strings.Coords.xcoordinate_pattern.format(id),
            idf_strings.Coords.num_format.format(coord.x),
        )
        setattr(
            idf_object,
            idf_strings.Coords.ycoordinate_pattern.format(id),
            idf_strings.Coords.num_format.format(coord.y),
        )
        setattr(
            idf_object,
            idf_strings.Coords.zcoordinate_pattern.format(id),
            idf_strings.Coords.num_format.format(coord.z),
        )
        id += 1


def set_coordinates_counterclockwise(idf_object, wall):
    idf_object.Number_of_Vertices = len(wall)

    id = 1  # create new id for the vertices to be sure they are ascending
    for wall_index in reversed(wall.index):
        coord = wall.loc[wall_index]
        setattr(idf_object, idf_strings.Coords.xcoordinate_pattern.format(id), idf_strings.Coords.num_format.format(coord.x))
        setattr(idf_object, idf_strings.Coords.ycoordinate_pattern.format(id), idf_strings.Coords.num_format.format(coord.y))
        setattr(idf_object, idf_strings.Coords.zcoordinate_pattern.format(id), idf_strings.Coords.num_format.format(coord.z))
        id += 1
