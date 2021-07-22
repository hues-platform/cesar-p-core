# coding=utf-8
#
# Copyright (c) 2021, Empa, Leonie Fierz, Aaron Bojarski, Ricardo Parreira da Silva, Sven Eggimann.
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
from typing import Dict, Any, Optional
import pint

import cesarp.common
from cesarp.model.WindowConstruction import WindowFrameConstruction
from cesarp.model.Construction import Construction
from cesarp.model.BuildingConstruction import InstallationsCharacteristics, LightingCharacteristics
from cesarp.construction import _default_config_file
from cesarp.model.BuildingElement import BuildingElement
from cesarp.model.OpaqueMaterial import OpaqueMaterial, OpaqueMaterialRoughness
from cesarp.model.Layer import Layer
from cesarp.model.EnergySource import EnergySource
from cesarp.model.WindowConstruction import WindowShadingMaterial


class ConstructionBasics:
    def __init__(self, ureg: pint.UnitRegistry, custom_config: Dict[str, Any] = {}):
        self._cfg = cesarp.common.config_loader.load_config_for_package(_default_config_file, __package__, custom_config)
        self.ureg = ureg

    def get_fixed_window_frame_construction(self):
        win_frame_props = self._cfg["FIXED_WINDOW_FRAME_CONSTRUCTION_PARAMETERS"]
        return WindowFrameConstruction(
            name=win_frame_props["name"],
            short_name=win_frame_props["name"],
            frame_conductance=self.ureg(win_frame_props["frame_conductance"]),
            frame_solar_absorptance=self.ureg(win_frame_props["frame_solar_absorptance"]),
            frame_visible_absorptance=self.ureg(win_frame_props["frame_visible_absorptance"]),
            outside_reveal_solar_absorptance=self.ureg(win_frame_props["outside_reveal_solar_absorptance"]),
            emb_co2_emission_per_m2=self.ureg(win_frame_props["embodied_co2_emission_per_m2"]),
            emb_non_ren_primary_energy_per_m2=self.ureg(win_frame_props["embodied_non_renewable_primary_energy_per_m2"]),
        )

    def get_inst_characteristics(self, e_carrier_dhw: Optional[EnergySource] = None, e_carrier_heating: Optional[EnergySource] = None):
        """get fixed installation characteristics and default CH EnergySource mix for DHW and HEATING"""
        props = self._cfg["FIXED_INSTALLATION_CHARACTERISTICS"]
        return InstallationsCharacteristics(
            fraction_radiant_from_activity=self.ureg(str(props["FRACTION_RADIANT_FROM_ACTIVITY"])),
            lighting_characteristics=LightingCharacteristics(
                self.ureg(str(props["LIGHTING_RETURN_AIR_FRACTION"])),
                self.ureg(str(props["LIGHTING_FRACTION_RADIANT"])),
                self.ureg(str(props["LIGHTING_FRACTION_VISIBLE"])),
            ),
            dhw_fraction_lost=self.ureg(str(props["DHW_FRACTION_LOST"])),
            electric_appliances_fraction_radiant=self.ureg(str(props["ELECTRIC_APPLIANCES_FRACTION_RADIANT"])),
            e_carrier_dhw=e_carrier_dhw,
            e_carrier_heating=e_carrier_heating,
        )

    def get_internal_ceiling_construction(self):
        constr_props = self._cfg["FIXED_INTERNAL_CEILING_CONSTRUCTION_PARAMETERS"]
        return self._get_internal_construction(constr_props, BuildingElement.INTERNAL_CEILING)

    def _get_internal_construction(self, constr_props: Dict, bldg_element: BuildingElement):
        layers = []
        for layer in constr_props["layers"]:
            material = self._get_internal_material(str(constr_props["layers"][layer]["material"]))
            layers.append(Layer(name=layer, thickness=self.ureg(str(constr_props["layers"][layer]["thickness"])), material=material))
        return Construction(name=constr_props["name"], layers=layers, bldg_element=bldg_element)

    def _get_internal_material(self, material_name):
        material_props = self._cfg["MATERIALS"][material_name]
        return OpaqueMaterial(
            name=material_name,
            density=self.ureg(str(material_props["density"])),
            roughness=OpaqueMaterialRoughness(str(material_props["roughness"])),
            solar_absorptance=self.ureg(str(material_props["solar_absorptance"])),
            specific_heat=self.ureg(str(material_props["specific_heat"])),
            thermal_absorptance=self.ureg(str(material_props["thermal_absorptance"])),
            conductivity=self.ureg(str(material_props["conductivity"])),
            visible_absorptance=self.ureg(str(material_props["visible_absorptance"])),
            co2_emission_per_kg=None,
            non_renewable_primary_energy_per_kg=None,
        )

    def get_window_shading_constr(self, bldg_age: int) -> WindowShadingMaterial:
        if bldg_age < 2010:
            return WindowShadingMaterial(
                True,
                "Shade0101",
                self.ureg("0.31 solar_transmittance"),
                self.ureg("0.5 solar_reflectance"),
                self.ureg("0.31 visible_transmittance"),
                self.ureg("0.5 visible_reflectance"),
                self.ureg("0.9 infrared_hemispherical_emissivity"),
                self.ureg("0.0 infrared_transmittance"),
                self.ureg("0.9 W/(m*K)"),
                self.ureg("0.001 m"),
                self.ureg("0.1 m"),
                0,
                0,
                0,
                0,
                0,
            )
        elif bldg_age > 2010 and bldg_age < 2014:
            return WindowShadingMaterial(
                True,
                "Shade0801",
                self.ureg("0.28 solar_transmittance"),
                self.ureg("0.6 solar_reflectance"),
                self.ureg("0.28 visible_transmittance"),
                self.ureg("0.6 visible_reflectance"),
                self.ureg("0.9 infrared_hemispherical_emissivity"),
                self.ureg("0.0 infrared_transmittance"),
                self.ureg("0.9 W/(m*K)"),
                self.ureg("0.001 m"),
                self.ureg("0.1 m"),
                0,
                0,
                0,
                0,
                0,
            )
        else:
            return WindowShadingMaterial(
                True,
                "Shade0901",
                self.ureg("0.2 solar_transmittance"),
                self.ureg("0.7 solar_reflectance"),
                self.ureg("0.2 visible_transmittance"),
                self.ureg("0.7 visible_reflectance"),
                self.ureg("0.9 infrared_hemispherical_emissivity"),
                self.ureg("0.0 infrared_transmittance"),
                self.ureg("0.9 W/(m*K)"),
                self.ureg("0.001 m"),
                self.ureg("0.1 m"),
                0,
                0,
                0,
                0,
                0,
            )
