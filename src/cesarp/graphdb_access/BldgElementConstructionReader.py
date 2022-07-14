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
from typing import Protocol, Sequence, Union, Dict, Any, Tuple, Optional
import pint
import pandas as pd
import logging

import cesarp.common
from cesarp.common.AgeClass import AgeClass
from cesarp.graphdb_access.BuildingElementConstructionsArchetype import BuildingElementConstrcutionsArchetype
from cesarp.model.Construction import Construction, BuildingElement
from cesarp.model.WindowConstruction import WindowGlassConstruction, WindowShadingMaterial
from cesarp.model.Layer import Layer, LayerFunction
from cesarp.model.WindowLayer import WindowLayer
from cesarp.model.OpaqueMaterial import OpaqueMaterial
from cesarp.model.TransparentMaterial import TransparentMaterial
from cesarp.model.Gas import Gas
from cesarp.model.OpaqueMaterial import OpaqueMaterialRoughness
from cesarp.construction.MinMaxValue import MinMaxValue
from cesarp.graphdb_access.GraphDataException import GraphDataException
from cesarp.graphdb_access import _default_config_file


class GraphReaderProtocol(Protocol):
    def get_constructions_from_graph(self, name) -> pd.DataFrame:
        ...

    def get_layers_from_graph(self, name) -> pd.DataFrame:
        ...

    def get_opaque_material_from_graph(self, name) -> pd.DataFrame:
        ...

    def get_transparent_material_from_graph(self, name) -> pd.DataFrame:
        ...

    def get_material_type_from_graph(self, name) -> pd.DataFrame:
        ...

    def get_gas_from_graph(self, name) -> pd.DataFrame:
        ...

    def get_retrofit_name(self, name, regulation, target_requirement: bool) -> pd.DataFrame:
        """
        :param name:
        :param regulation:
        :param target_requirement: if true, retrofit construction fulfilling target requirements are chosen,
                                    otherwise constructions fulfilling minimal requirements of chosen regulation
        :return:
        """
        ...

    def get_glazing_ratio_from_graph(self, archetype_uri) -> pd.DataFrame:
        ...

    def get_infiltration_rate_from_graph(self, archetype_uri) -> pd.DataFrame:
        ...

    def get_archetype_by_year_from_graph(self, year) -> pd.DataFrame:
        ...

    def get_u_value_from_graph(self, construction_uri) -> pd.DataFrame:
        ...

    def get_construction_emission_from_graph(self, construction_uri) -> pd.DataFrame:
        ...

    def get_archetype_year_range_from_graph_for_uri(self, archetype_uri) -> pd.DataFrame:
        ...

    def get_window_shading_constr_from_graph_for_uri(self, archetype_uri):
        ...


class BldgElementConstructionReader:
    def __init__(self, graph_reader: GraphReaderProtocol, ureg: pint.UnitRegistry, custom_config: Optional[Dict[str, Any]] = None):
        self.graph_reader = graph_reader
        self.ureg = ureg
        self._cfg = cesarp.common.config_loader.load_config_for_package(_default_config_file, __package__, custom_config)
        self._logger = logging.getLogger(__name__)
        self._materials_cache: Dict[str, Any] = dict()

    def get_bldg_elem_construction_archetype(self, archetype_uri: str):
        grounds_from_db = []
        roofs_from_db = []
        walls_from_db = []
        windows_from_db = []
        internal_ceiling_from_db = []

        df = self.graph_reader.get_constructions_from_graph(archetype_uri)
        if df.empty:
            raise GraphDataException(f"Could not find {archetype_uri} in GraphDB {str(self.graph_reader)}")
        for index, row in df.iterrows():
            bldg_element = BuildingElement(row["type"])

            if bldg_element == BuildingElement.WINDOW:
                win_uri = row["surface"]
                var_win_construction = self.get_win_glass_constr_for(win_uri)
                windows_from_db.append(var_win_construction)
            else:
                constr_uri = row["surface"]
                co2_emission = None
                non_renewable_primary_energy = None
                if row["CO2Emission"]:
                    co2_emission = self.ureg(row["CO2Emission"])
                    non_renewable_primary_energy = self.ureg(row["nonRenewablePrimaryEnergy"])

                var_construction = Construction(
                    name=constr_uri,
                    layers=self.get_layers(constr_uri),
                    bldg_element=bldg_element,
                    co2_emission_per_m2=co2_emission,
                    non_renewable_primary_energy_per_m2=non_renewable_primary_energy,
                )
                self.set_layer_functions(var_construction)
                if bldg_element == BuildingElement.GROUNDFLOOR:
                    grounds_from_db.append(var_construction)
                elif bldg_element == BuildingElement.ROOF:
                    roofs_from_db.append(var_construction)
                elif bldg_element == BuildingElement.WALL:
                    walls_from_db.append(var_construction)
                elif bldg_element == BuildingElement.INTERNAL_CEILING:
                    internal_ceiling_from_db.append(var_construction)

        return BuildingElementConstrcutionsArchetype(
            name=archetype_uri, grounds=grounds_from_db, roofs=roofs_from_db, walls=walls_from_db, windows=windows_from_db, internal_ceilings=internal_ceiling_from_db
        )

    def get_win_glass_constr_for(self, win_glass_uri, emb_emissions_needed: bool = False) -> WindowGlassConstruction:
        """
        :param win_glass_uri: GraphDB URI for window
        :param emb_emissions_needed: pass True if method should raise exception if embodied co2 and non-renewable pen are not available
        :return: WindowGlassConstruction
        """
        try:
            emb_co2, emb_pen = self.get_construction_emission_values(win_glass_uri)
        except GraphDataException as graph_err:
            if emb_emissions_needed:
                raise graph_err
            self._logger.debug(repr(graph_err) + ". Setting co2 and pen to None.")
            emb_co2 = None
            emb_pen = None

        return WindowGlassConstruction(
            name=win_glass_uri,
            layers=self.get_window_layers(win_glass_uri),
            emb_co2_emission_per_m2=emb_co2,
            emb_non_ren_primary_energy_per_m2=emb_pen,
        )

    def get_layers(self, name):
        df = self.graph_reader.get_layers_from_graph(name)
        layers = []
        for index, row in df.iterrows():
            var_layer = Layer((row["layer"]), self.ureg(row["thickness"]), self.get_material(row["material"]))
            layers.append(var_layer)
        return layers

    def get_window_layers(self, name):
        df = self.graph_reader.get_layers_from_graph(name)
        layers = []
        for index, row in df.iterrows():
            var_layer = WindowLayer((row["layer"]), self.ureg(row["thickness"]), self.get_material(row["material"]))
            layers.append(var_layer)
        return layers

    def get_opaque_material(self, name):
        df = self.graph_reader.get_opaque_material_from_graph(name)
        if not df.empty:
            density = None
            specific_heat = None
            conductivity = self.ureg(df.at[0, "Conductivity"])
            co2_emission = None
            non_renewable_primary_energy = None
            roughness = OpaqueMaterialRoughness(df.at[0, "roughness"])
            solar_absorptance = self.ureg(df.at[0, "solarAbsorptance"])
            thermal_absorptance = self.ureg(df.at[0, "thermalAbsorptance"])
            visible_absorptance = self.ureg(df.at[0, "visibleAbsorptance"])
            if df.at[0, "specificHeat"]:
                density = self.ureg(df.at[0, "density"]).to(self.ureg.kg / self.ureg.m ** 3)
                specific_heat = self.ureg(df.at[0, "specificHeat"])

                # NOTE pint converts "kg CO2eq / kg" to "CO2", because kg/kg = dimensionless
                co2_emission = self.ureg(df.at[0, "CO2Emission"])
                non_renewable_primary_energy = self.ureg(df.at[0, "nonRenewablePrimaryEnergy"])
            return OpaqueMaterial(
                name,
                density,
                roughness,
                solar_absorptance,
                specific_heat,
                thermal_absorptance,
                conductivity,
                visible_absorptance,
                co2_emission,
                non_renewable_primary_energy,
            )
        else:
            raise ValueError(f"{name} has missing properties in Graph")

    def get_material(self, name):
        if name in self._materials_cache.keys():
            return self._materials_cache[name]

        type = self.get_material_type(name)
        material = None
        if "Transparent" in type:
            material = self.get_transparent_material(name)
        if "Gas" in type:
            material = self.get_gas_material(name)
        if "Opaque" in type:
            material = self.get_opaque_material(name)
        self._materials_cache[name] = material
        return material

    def get_transparent_material(self, name):
        df = self.graph_reader.get_transparent_material_from_graph(name)
        if not df.empty:
            back_side_infrared_hemispherical_emissivity = self.ureg(df.at[0, "BackSideInfraredHemisphericalEmissivity"])
            back_side_solar_reflectance = self.ureg(df.at[0, "BackSideSolarReflectance"])
            back_side_visible_reflectance = self.ureg(df.at[0, "BackSideVisibleReflectance"])
            conductivity = self.ureg(df.at[0, "Conductivity"])
            dirt_correction_factor = self.ureg(df.at[0, "DirtCorrectionFactor"])
            front_side_infrared_hemispherical_emissivity = self.ureg(df.at[0, "FrontSideInfraredHemisphericalEmissivity"])
            front_side_solar_reflectance = self.ureg(df.at[0, "FrontSideSolarReflectance"])
            front_side_visible_reflectance = self.ureg(df.at[0, "FrontSideVisibleReflectance"])
            infrared_transmittance = self.ureg(df.at[0, "InfraredTransmittance"])
            solar_transmittance = self.ureg(df.at[0, "SolarTransmittance"])
            visible_transmittance = self.ureg(df.at[0, "VisibleTransmittance"])

            return TransparentMaterial(
                name,
                back_side_infrared_hemispherical_emissivity,
                back_side_solar_reflectance,
                back_side_visible_reflectance,
                conductivity,
                dirt_correction_factor,
                front_side_infrared_hemispherical_emissivity,
                front_side_solar_reflectance,
                front_side_visible_reflectance,
                infrared_transmittance,
                solar_transmittance,
                visible_transmittance,
            )

        else:
            raise ValueError(f"{name} has missing properties in Graph")

    def get_gas_material(self, name):
        df = self.graph_reader.get_gas_from_graph(name)
        if not df.empty:
            conductivity = self.ureg(df.at[0, "Conductivity"])
            return Gas(name, conductivity)
        else:
            raise ValueError(f"{name} has missing properties in Graph")

    def get_material_type(self, name):
        df = self.graph_reader.get_material_type_from_graph(name)
        return df.at[0, "type"]

    def get_retrofitted_window_glass(self, win_glass_constr: WindowGlassConstruction) -> WindowGlassConstruction:
        retrofitted_uri = self._get_uri_of_retrofit_for(win_glass_constr)
        # windows are exchanged completely, thus marking the window as retrofitted and not single layers
        retrofitted_win_construction = self.get_win_glass_constr_for(retrofitted_uri, emb_emissions_needed=True)
        retrofitted_win_construction.retrofitted = True
        return retrofitted_win_construction

    def get_retrofitted_construction(self, construction: Construction) -> Construction:
        retrofitted_uri = self._get_uri_of_retrofit_for(construction)

        retrofitted_construction = Construction(name=retrofitted_uri, layers=self.get_layers(retrofitted_uri), bldg_element=construction.bldg_element)
        additional_layer_counter = 0
        for layer in retrofitted_construction.layers:
            retrofitted = True
            for i in range(len(construction.layers)):
                if layer.material == construction.layers[i].material and layer.thickness == construction.layers[i].thickness:
                    retrofitted = False
            if retrofitted:
                layer.retrofitted = True
                additional_layer_counter += 1
        if len(retrofitted_construction.layers) - len(construction.layers) != additional_layer_counter:
            if retrofitted_construction.layers[1].retrofitted:
                retrofitted_construction.layers[0].retrofitted = True
                additional_layer_counter += 1
            elif retrofitted_construction.layers[len(retrofitted_construction.layers) - 1].retrofitted:
                retrofitted_construction.layers[len(retrofitted_construction.layers)].retrofitted = True
                additional_layer_counter += 1

        # if the above function can't identify the, in the retrofit, added layers, the first n layers are marked
        # as retrofitted (until "retrofitted_construction" has same number of not retrofitted layers as
        # "construction")
        i = 0
        while len(retrofitted_construction.layers) - len(construction.layers) > additional_layer_counter:
            if not retrofitted_construction.layers[i].retrofitted:
                retrofitted_construction.layers[i].retrofitted = True
                additional_layer_counter += 1
            i += 1
        return self.set_layer_functions(retrofitted_construction)

    def _get_uri_of_retrofit_for(self, construction):
        regulation = self._cfg["RETROFIT"]["regulation"]
        target_requirement = self._cfg["RETROFIT"]["target_requirement"]
        df = self.graph_reader.get_retrofit_name(construction.name, regulation, target_requirement)
        if df.empty:
            raise LookupError("No retrofit option found for " + construction.short_name)
        retrofitted_uri = df.at[0, "Name"]
        return retrofitted_uri

    def get_retrofit_target_info(self) -> str:
        regulation = self._cfg["RETROFIT"]["regulation"]
        if self._cfg["RETROFIT"]["target_requirement"]:
            return regulation + " Minimal"
        else:
            return regulation + " Target"

    def get_default_construction(
        self, constructions: Sequence[Union[Construction, WindowGlassConstruction]], archetype_shortname: str = None
    ) -> Union[Construction, WindowGlassConstruction]:
        assert constructions, f"no constructions passed for getting default construction in archetpye {archetype_shortname}"
        if len(constructions) == 1:  # nothing to do if only one construction option
            return constructions[0]
        if archetype_shortname:
            try:
                return self._get_default_construction_from_config(constructions, archetype_shortname)
            except GraphDataException as e:
                logging.warning(f"fallback to default construction by uvalue due to error: {str(e)} \n")

        return self._get_default_construction_by_uvalue(constructions)

    def _get_default_construction_from_config(self, constructions: Sequence[Union[Construction, WindowGlassConstruction]], archetype_shortname: str):
        try:
            bldg_element = constructions[0].bldg_element
            if self._cfg["ARCHETYPES"][archetype_shortname.upper()]["DEFAULT_CONSTRUCTION_SPECIFIC"]["ACTIVE"]:
                default_constr = self._cfg["ARCHETYPES"][archetype_shortname.upper()]["DEFAULT_CONSTRUCTION_SPECIFIC"][bldg_element.name]
                for construction in constructions:
                    if construction.name == default_constr:
                        return construction
        except KeyError:
            raise GraphDataException(f"Default construction lookup in configuration failed for archetype {archetype_shortname} element {bldg_element.name}")

        raise GraphDataException(f"Default construction set in configuration for {archetype_shortname} is not matching one of {[c.name for c in constructions]}")

    def _get_default_construction_by_uvalue(self, constructions: Sequence[Union[Construction, WindowGlassConstruction]]) -> Union[Construction, WindowGlassConstruction]:
        u_values = []
        for construction in constructions:
            u_values.append(self.get_u_value(construction))
        u_value_mean = sum(u_values) / len(u_values)
        default_constr_index = 0
        for index in range(len(u_values)):
            if abs(u_values[index] - u_value_mean) < abs(u_values[default_constr_index] - u_value_mean):
                default_constr_index = index
        return constructions[default_constr_index]

    def get_u_value(self, construction: Union[Construction, WindowGlassConstruction]) -> float:
        """
        Calculation of U-Value according to formula in Master Thesis of Jonas Landolt,
        details (also the thermal resistance coefficients used for heat transfer between solid material and air,
        which are actually according to DIN, 2014) see chapter '8.1.3. Setup of Constructions' in CESAR-Tool_Documentation.pdf
        """

        THERMAL_R_INTERIOR_WALL_TO_INDOOR_AIR = self.ureg.Quantity(0.13, self.ureg("kelvin * meter ** 2 / W"))
        THERMAL_R_OUTDOOR_WALL_TO_OUTDOOR_AIR = self.ureg.Quantity(0.04, self.ureg("kelvin * meter ** 2 / W"))
        if construction.bldg_element == BuildingElement.WINDOW:
            return self.ureg(self.graph_reader.get_u_value_from_graph(construction.name).iat[0, 0])
        if construction.bldg_element == BuildingElement.GROUNDFLOOR:
            total_resistance = 2 * THERMAL_R_INTERIOR_WALL_TO_INDOOR_AIR
        elif construction.bldg_element == BuildingElement.WALL or construction.bldg_element == BuildingElement.ROOF:
            total_resistance = THERMAL_R_INTERIOR_WALL_TO_INDOOR_AIR + THERMAL_R_OUTDOOR_WALL_TO_OUTDOOR_AIR
        else:
            raise NotImplementedError(f"get_u_value() not implemented for Building Element " f"{construction.bldg_element.name}, construction {construction.short_name}")
        for layer in construction.layers:
            conductivity = layer.material.conductivity
            resistance = layer.thickness.to(self.ureg.m) / conductivity.to(self.ureg.W / self.ureg.m / self.ureg.K)
            total_resistance += resistance
        return 1 / total_resistance

    def get_glazing_ratio(self, archetype_uri):
        df = self.graph_reader.get_glazing_ratio_from_graph(archetype_uri)
        gl_ratio_min = float(df.at[0, "GlazingRatioMin"])
        gl_ratio_max = float(df.at[0, "GlazingRatioMax"])
        if gl_ratio_min > 1 or gl_ratio_max > 1:
            gl_ratio_min = gl_ratio_min / 100
            gl_ratio_max = gl_ratio_max / 100
        return MinMaxValue(self.ureg.Quantity(gl_ratio_min), self.ureg.Quantity(gl_ratio_max))

    def get_infiltration_rate(self, archetype_uri):
        df = self.graph_reader.get_infiltration_rate_from_graph(archetype_uri)
        return self.ureg(df.at[0, "InfiltrationRate"])

    def get_construction_emission_values(self, construction_uri) -> Tuple[pint.Quantity, pint.Quantity]:
        df = self.graph_reader.get_construction_emission_from_graph(construction_uri)
        if len(df.index) != 1:
            msg = f"Could not read embodied emissions for {construction_uri}. One entry expected, but there were {len(df.index)}."
            raise GraphDataException(msg)
        co2_emission_per_kg = self.ureg(df.at[0, "co2Emission"])
        non_renewable_primary_energy_per_kg = self.ureg(df.at[0, "nonRenewablePrimaryEnergy"])
        return co2_emission_per_kg, non_renewable_primary_energy_per_kg

    def get_age_class_of_archetype(self, archetype_uri):
        df = self.graph_reader.get_archetype_year_range_from_graph_for_uri(archetype_uri)
        if not df.empty:
            min_raw = df.at[0, "minValue"]
            if min_raw == "-":
                min_value = None
            else:
                min_value = int(min_raw)
            max_raw = df.at[0, "maxValue"]
            if max_raw == "-":
                max_value = None
            else:
                max_value = int(max_raw)
            return AgeClass(min_value, max_value)
        else:
            raise LookupError(f"There is no Archetype with uri {archetype_uri} in the database.")

    def get_window_shading_constr(self, archetype_uri) -> WindowShadingMaterial:
        df = self.graph_reader.get_window_shading_constr_from_graph_for_uri(archetype_uri)
        if not df.empty:
            is_shading_available = bool(df.at[0, "isShadingAvailable"])
            name = str(df.at[0, "name"])
            solar_transmittance = self.ureg(df.at[0, "solarTransmittance"])
            solar_reflectance = self.ureg(df.at[0, "solarReflectance"])
            visible_transmittance = self.ureg(df.at[0, "visibleTransmittance"])
            visible_reflectance = self.ureg(df.at[0, "visibleReflectance"])
            infrared_hemispherical_emissivity = self.ureg(df.at[0, "infraredHemisphericalEmissivity"])
            infrared_transmittance = self.ureg(df.at[0, "infraredTransmittance"])
            conductivity = self.ureg(df.at[0, "conductivity"])
            thickness = self.ureg(df.at[0, "thickness"])
            shade_to_glass_distance = self.ureg(df.at[0, "shadeToGlassDistance"])
            top_opening_multiplier = float(df.at[0, "topOpeningMultiplier"])
            bottom_opening_multiplier = float(df.at[0, "bottomOpeningMultiplier"])
            leftside_opening_multiplier = float(df.at[0, "leftsideOpeningMultiplier"])
            rightside_opening_multiplier = float(df.at[0, "rightsideOpeningMultiplier"])
            airflow_permeability = float(df.at[0, "airflowPermeability"])
            return WindowShadingMaterial(
                is_shading_available,
                name,
                solar_transmittance,
                solar_reflectance,
                visible_transmittance,
                visible_reflectance,
                infrared_hemispherical_emissivity,
                infrared_transmittance,
                conductivity,
                thickness,
                shade_to_glass_distance,
                top_opening_multiplier,
                bottom_opening_multiplier,
                leftside_opening_multiplier,
                rightside_opening_multiplier,
                airflow_permeability,
            )
        else:
            raise LookupError(f"There is no Shading for Archetype with uri {archetype_uri} in the database.")

    def set_layer_functions(self, construction: Construction) -> Construction:
        number_of_layer = len(construction.layers)
        if construction.layers[number_of_layer - 1].material.conductivity.m < 0.1:
            construction.layers[number_of_layer - 1].function = LayerFunction.INSULATION_INSIDE
        if construction.layers[0].material.conductivity.m < 0.1:
            construction.layers[0].function = LayerFunction.INSULATION_OUTSIDE
        outside_index = 1
        inside_index = number_of_layer - 2
        while outside_index <= inside_index:
            if construction.layers[outside_index].material.conductivity.m < 0.1:
                construction.layers[outside_index].function = LayerFunction.INSULATION_OUTSIDE
                outside_index += 1
            else:
                break
        while outside_index <= inside_index:
            if construction.layers[inside_index].material.conductivity.m < 0.1:
                construction.layers[inside_index].function = LayerFunction.INSULATION_INSIDE
                inside_index -= 1
            else:
                break
        i = outside_index + 1
        while i < inside_index:
            if construction.layers[i].material.conductivity.m < 0.1:
                if type(construction.layers[i - 1].material) == Gas or type(construction.layers[i + 1].material) == Gas:
                    construction.layers[i].function = LayerFunction.INSULATION_OUTSIDE_BACK_VENTILATED
                elif construction.layers[i - 1].material.conductivity.m > 0.1 and construction.layers[i + 1].material.conductivity.m > 0.1:
                    construction.layers[i].function = LayerFunction.INSULATION_IN_BETWEEN
                else:
                    construction.layers[i].function = LayerFunction.INSULATION_INSIDE
            i += 1
        return construction
