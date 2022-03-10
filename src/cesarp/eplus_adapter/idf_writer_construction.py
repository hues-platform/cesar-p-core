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
from typing import Tuple, Any, Protocol, List, TypeVar
import pint
from eppy.modeleditor import IDF
from cesarp.model.Gas import Gas
from cesarp.model.ShadingObjectConstruction import ShadingObjectConstruction
from cesarp.model.WindowConstruction import WindowFrameConstruction, WindowGlassConstruction
from cesarp.model.OpaqueMaterial import OpaqueMaterial, OpaqueMaterialRoughness
from cesarp.model.TransparentMaterial import TransparentMaterial
import cesarp.eplus_adapter.idf_strings as idf_strings
import cesarp.eplus_adapter.idf_writing_helpers as idf_writing_helpers


class NamedMaterialProtocol(Protocol):
    @property
    def name(self):
        ...


class LayerProtocol(Protocol):
    name: str
    material: Any
    thickness: pint.Quantity

    @property
    def thermal_resistance(self) -> pint.Quantity:
        ...


LayerType = TypeVar("LayerType")


class LayeredConstructionProtocol(Protocol[LayerType]):
    name: str
    layers: List[LayerType]


def add_detailed_construction(idf: IDF, construction: LayeredConstructionProtocol, ureg: pint.UnitRegistry, is_window=False) -> str:
    """
    Adds a construction to the idf.

    Note that in cesarp.model each layer of a construction or window construction is modelled with a separate
    Layer object having a thickness and material, whereas in the IDF definition a material object has a specific
    thickness, thus a construction has directly materials assigned without an intermediate layer object.
    """
    idf_obj_name = construction.name
    if not idf_writing_helpers.exists_in_idf(idf, idf_strings.IDFObjects.construction, idf_obj_name):
        # assert construction.external_layer_index == 0, \
        #    "external/outside layer of a construction is expected as layer 0. Either change your initialization " \
        #    "of the construction or add some code handling reverse layer order in idf_writer_construction"
        idf_constr = idf.newidfobject(idf_strings.IDFObjects.construction)
        idf_constr.Name = idf_obj_name
        idf_constr.Outside_Layer = add_layer(idf=idf, layer=construction.layers[0], ureg=ureg, is_window_layer=is_window)
        for idx in range(1, len(construction.layers)):
            mat_idf_name = add_layer(idf=idf, layer=construction.layers[idx], ureg=ureg, is_window_layer=is_window)
            idf_constr[f"Layer_{idx+1}"] = mat_idf_name

    return idf_obj_name


def add_win_glass_construction(idf: IDF, glass_constr: WindowGlassConstruction, ureg: pint.UnitRegistry) -> str:
    return add_detailed_construction(idf, glass_constr, ureg, is_window=True)


def add_layer(idf: IDF, layer: LayerProtocol, ureg: pint.UnitRegistry, is_window_layer=False):
    idf_obj_mat_name = layer.name
    mat = layer.material
    if is_window_layer:
        if isinstance(mat, TransparentMaterial):
            add_window_glazing_material(idf=idf, idf_obj_name=idf_obj_mat_name, mat_def=mat, thickness=layer.thickness, ureg=ureg)
        elif isinstance(mat, Gas):
            add_window_material_gas(idf=idf, idf_obj_name=idf_obj_mat_name, mat_def=mat, thickness=layer.thickness, ureg=ureg)
        else:
            raise Exception(f"Material class {type(mat)} not supported for windows")
    else:
        if isinstance(mat, OpaqueMaterial):
            if mat.is_mass_fully_specified():
                add_opaque_material(idf=idf, idf_obj_name=idf_obj_mat_name, mat_def=mat, thickness=layer.thickness, ureg=ureg)
            else:
                add_material_no_mass(
                    idf=idf,
                    idf_obj_name=idf_obj_mat_name,
                    mat_def=mat,
                    thermal_resistance=layer.thermal_resistance,
                    ureg=ureg,
                )
        elif isinstance(mat, Gas):
            add_airgap(idf=idf, idf_obj_name=idf_obj_mat_name, thermal_resistance=layer.thermal_resistance, ureg=ureg)
        else:
            raise Exception(f"Material class {type(mat)} not supported for opaque constructions")

    return idf_obj_mat_name


def add_opaque_material(idf: IDF, idf_obj_name: str, mat_def: OpaqueMaterial, thickness: pint.Quantity, ureg: pint.UnitRegistry) -> None:
    """
    For materials without mass specified (e.g. vapour barriers) thickness is not
    :param idf:
    :param idf_obj_name:
    :param mat_def:
    :param thickness:
    :param ureg:
    :return:
    """
    if not idf_writing_helpers.exists_in_idf(idf, idf_strings.IDFObjects.material, idf_obj_name):
        assert mat_def.is_mass_fully_specified(), f"trying to add opaque material {mat_def.name}, but no mass properties specified"
        idf_mat = idf.newidfobject(idf_strings.IDFObjects.material)
        idf_mat.Name = idf_obj_name
        idf_mat.Roughness = get_idf_roughness_string_for(mat_def.roughness)
        idf_mat.Thickness = thickness.to(ureg.m).m
        idf_mat.Conductivity = mat_def.conductivity.to(ureg.W / (ureg.m * ureg.K)).m
        # checking for mass properties at begin, thus ignore type warning due to Optional[] declaration
        idf_mat.Density = mat_def.density.to(ureg.kg / ureg.m ** 3).m  # type: ignore
        idf_mat.Specific_Heat = mat_def.specific_heat.to(ureg.J / (ureg.kg * ureg.K)).m  # type: ignore
        idf_mat.Thermal_Absorptance = mat_def.thermal_absorptance.to(ureg.dimensionless).m
        idf_mat.Solar_Absorptance = mat_def.solar_absorptance.to(ureg.dimensionless).m
        idf_mat.Visible_Absorptance = mat_def.visible_absorptance.to(ureg.dimensionless).m


def add_material_no_mass(idf: IDF, idf_obj_name: str, mat_def: OpaqueMaterial, thermal_resistance: pint.Quantity, ureg: pint.UnitRegistry) -> None:
    """
    For materials without mass specified (e.g. vapour barriers)
    :param idf:
    :param idf_obj_name:
    :param mat_def:
    :param thermal_resistance:
    :param ureg:
    :return:
    """
    if not idf_writing_helpers.exists_in_idf(idf, idf_strings.IDFObjects.material_no_mass, idf_obj_name):
        idf_mat = idf.newidfobject(idf_strings.IDFObjects.material_no_mass)
        idf_mat.Name = idf_obj_name
        idf_mat.Roughness = get_idf_roughness_string_for(mat_def.roughness)
        idf_mat.Thermal_Resistance = thermal_resistance.to((ureg.m ** 2 * ureg.K) / ureg.W).m
        idf_mat.Thermal_Absorptance = mat_def.thermal_absorptance.to(ureg.dimensionless).m
        idf_mat.Solar_Absorptance = mat_def.solar_absorptance.to(ureg.dimensionless).m
        idf_mat.Visible_Absorptance = mat_def.visible_absorptance.to(ureg.dimensionless).m


def get_idf_roughness_string_for(opaque_mat_roughness: OpaqueMaterialRoughness) -> str:
    if opaque_mat_roughness == OpaqueMaterialRoughness.VERY_ROUGH:
        name = idf_strings.Roughness.VeryRough.name
    elif opaque_mat_roughness == OpaqueMaterialRoughness.ROUGH:
        name = idf_strings.Roughness.Rough.name
    elif opaque_mat_roughness == OpaqueMaterialRoughness.MEDIUM_ROUGH:
        name = idf_strings.Roughness.MediumRough.name
    elif opaque_mat_roughness == OpaqueMaterialRoughness.MEDIUM_SMOOTH:
        name = idf_strings.Roughness.MediumSmooth.name
    elif opaque_mat_roughness == OpaqueMaterialRoughness.SMOOTH:
        name = idf_strings.Roughness.Smooth.name
    elif opaque_mat_roughness == OpaqueMaterialRoughness.VERY_SMOOTH:
        name = idf_strings.Roughness.VerySmooth.name
    else:
        raise Exception(f"roughness {opaque_mat_roughness} not known by eplus_adapter.idf_writer_construction")

    return name


def add_airgap(idf: IDF, idf_obj_name: str, thermal_resistance: pint.Quantity, ureg: pint.UnitRegistry) -> None:
    if not idf_writing_helpers.exists_in_idf(idf, idf_strings.IDFObjects.material_air_gap, idf_obj_name):
        idf_mat = idf.newidfobject(idf_strings.IDFObjects.material_air_gap)
        idf_mat.Name = idf_obj_name
        idf_mat.Thermal_Resistance = thermal_resistance.to(ureg.m ** 2 * ureg.K / ureg.W).m


def add_window_material_gas(idf: IDF, idf_obj_name: str, thickness: pint.Quantity, mat_def: Gas, ureg: pint.UnitRegistry) -> None:
    if not idf_writing_helpers.exists_in_idf(idf, idf_strings.IDFObjects.win_material_gas, idf_obj_name):
        idf_mat = idf.newidfobject(idf_strings.IDFObjects.win_material_gas)
        idf_mat.Name = idf_obj_name
        idf_mat.Gas_Type = get_gas_type(mat_def.name)
        idf_mat.Thickness = thickness.to(ureg.m).m
        # you can define Gas_Type custom, but you need more than just a general conductivity as parameters...
        # idf_mat.Conductivity_Coefficient_A = mat_def.conductivity.to(ureg.W / (ureg.m * ureg.K)).m


def get_gas_type(gas_name) -> str:
    """
    gas_name can have prefix or suffixes, be in upper or lower case.
    supported by EnergyPlus is Air, Argon, Krypton, Xenon
    """
    for gt in idf_strings.win_gas_types:
        if gt.lower() in gas_name.lower():
            return gt

    raise KeyError(
        f"{gas_name} not supported as gas in a window construction by EnergyPlus, supported are"
        f" {idf_strings.win_gas_types} or custom types, which are not implemented with CESAR-P yet"
    )


def add_window_glazing_material(idf: IDF, idf_obj_name: str, mat_def: TransparentMaterial, thickness: pint.Quantity, ureg: pint.UnitRegistry) -> None:

    idf_obj_type = idf_strings.IDFObjects.win_material_glazing
    if not idf_writing_helpers.exists_in_idf(idf, idf_obj_type, idf_obj_name):
        win_glazing = idf.newidfobject(idf_obj_type)
        win_glazing.Name = idf_obj_name
        win_glazing.Thickness = thickness.to(ureg.m).m
        win_glazing.Optical_Data_Type = idf_strings.WindowMatGlazing.optical_data_type
        win_glazing.Solar_Transmittance_at_Normal_Incidence = mat_def.solar_transmittance.to(ureg.dimensionless).m
        win_glazing.Front_Side_Solar_Reflectance_at_Normal_Incidence = mat_def.front_side_solar_reflectance.to(ureg.dimensionless).m
        win_glazing.Back_Side_Solar_Reflectance_at_Normal_Incidence = mat_def.back_side_solar_reflectance.to(ureg.dimensionless).m
        win_glazing.Visible_Transmittance_at_Normal_Incidence = mat_def.visible_transmittance.to(ureg.dimensionless).m
        win_glazing.Front_Side_Visible_Reflectance_at_Normal_Incidence = mat_def.front_side_visible_reflectance.to(ureg.dimensionless).m
        win_glazing.Back_Side_Visible_Reflectance_at_Normal_Incidence = mat_def.back_side_visible_reflectance.to(ureg.dimensionless).m
        win_glazing.Infrared_Transmittance_at_Normal_Incidence = mat_def.infrared_transmittance.to(ureg.dimensionless).m
        win_glazing.Front_Side_Infrared_Hemispherical_Emissivity = mat_def.front_side_infrared_hemispherical_emissivity.to(ureg.dimensionless).m
        win_glazing.Back_Side_Infrared_Hemispherical_Emissivity = mat_def.back_side_infrared_hemispherical_emissivity.to(ureg.dimensionless).m
        win_glazing.Conductivity = mat_def.conductivity.to(ureg.W / (ureg.m * ureg.K)).m
        win_glazing.Dirt_Correction_Factor_for_Solar_and_Visible_Transmittance = mat_def.dirt_correction_factor.to(ureg.dimensionless).m


def add_win_frame_construction(idf: IDF, frame_constr: WindowFrameConstruction, ureg: pint.UnitRegistry) -> Tuple[str, Any]:
    idf_obj_name = frame_constr.name
    # check if frame construction was alredy added. do throw exception if so, because we don't expect that due to special
    # case of window frame and divider idf object beeing mixed construction/geometry definition
    assert not idf_writing_helpers.exists_in_idf(idf, idf_strings.IDFObjects.window_property_frame_and_divider, idf_obj_name)
    f_and_d_idf_obj = idf.newidfobject(idf_strings.IDFObjects.window_property_frame_and_divider)
    f_and_d_idf_obj.Name = idf_obj_name
    f_and_d_idf_obj.Frame_Conductance = frame_constr.frame_conductance.to(ureg.W / ureg.m ** 2 / ureg.K).m
    f_and_d_idf_obj.Frame_Solar_Absorptance = frame_constr.frame_solar_absorptance.to(ureg.dimensionless).m
    f_and_d_idf_obj.Frame_Visible_Absorptance = frame_constr.frame_visible_absorptance.to(ureg.dimensionless).m
    f_and_d_idf_obj.Outside_Reveal_Solar_Absorptance = frame_constr.outside_reveal_solar_absorptance.to(ureg.dimensionless).m

    # make sure you add width of frame to this idf object!
    return (idf_obj_name, f_and_d_idf_obj)


def add_shading_surface_construction(idf: IDF, shading_constr: ShadingObjectConstruction, glazing_constr_idf_obj_name: str, ureg: pint.UnitRegistry) -> Any:
    """
    Adds a ShadingProperty:Reflectance idf object. The object is not linked to a surface geometry here,
    thus make sure to set property "Shading_Surface_Name" on the EpBunch object to link it to a geometry!

    :param idf: IDF object for which to add shading construction
    :param shading_constr: properties of shading construction
    :param glazing_constr_idf_obj_name: idf object name of the glazing construction; needs to be passed because here we cannot handle appropriately to add the
                                        glazing construction if needed as it might be a ConstructionAsIDF...
    :param ureg: pint unit registry
    :return: eppy EpBunch of added ShadingProperty:Reflectance idf object
    """
    shading_reflectence_idf_obj = idf.newidfobject(idf_strings.IDFObjects.shading_prop_reflectance)
    shading_reflectence_idf_obj.Diffuse_Solar_Reflectance_of_Unglazed_Part_of_Shading_Surface = shading_constr.diffuse_solar_reflectance_unglazed_part.to(ureg.dimensionless).m
    shading_reflectence_idf_obj.Diffuse_Visible_Reflectance_of_Unglazed_Part_of_Shading_Surface = shading_constr.diffuse_visible_reflectance_unglazed_part.to(ureg.dimensionless).m
    shading_reflectence_idf_obj.Fraction_of_Shading_Surface_That_Is_Glazed = shading_constr.glazing_ratio.to(ureg.dimensionless).m
    shading_reflectence_idf_obj.Glazing_Construction_Name = glazing_constr_idf_obj_name
    # make sure to set the name of returned idf obj to match the name of the shading geometry object you want to link it to!
    # e.g. shading_reflectence_idf_obj.Shading_Surface_Name = "xyz"
    return shading_reflectence_idf_obj
