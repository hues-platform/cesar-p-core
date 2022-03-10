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

prefixes = """
        PREFIX ues: <https://ja98.github.io/ues/release/0.0.1/index-en.html#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        """

ues_prefix = "https://ja98.github.io/ues/release/0.0.1/index-en.html#"

# distinct is needed as when querying on remote graph db, the internal ceiling is returned for ues:hasSurface and ues:hasInternalCeiling,
# as the latter is a subproperty of the first. That definition is within the Ontology and I guess those relations are not loaded when reading from the local file.
# the filter is needed because all building construction elements (ground, roof, ...) are a subtype of ues:BuildingSurface
# and if removing the filter, all elements are returned twice, once with ues:BuildingSurface as type
get_constructions = (
    prefixes
    + """
        select distinct ?surface ?type ?CO2Emission ?nonRenewablePrimaryEnergy

        where {
            <$$$> ues:hasSurface | ues:hasInternalCeiling ?surface.
            ?surface rdf:type ?type.
            OPTIONAL
            {?surface ues:co2Emission ?CO2Emission;}
            OPTIONAL
            {?surface ues:nonRenewablePrimaryEnergy ?nonRenewablePrimaryEnergy;}
            filter(?type!=ues:BuildingSurface)

        }
        order by ?surface
        """
)

get_layers = (
    prefixes
    + """
        select distinct ?layer ?thickness ?material ?layerOrder

        where {
            <$$$> ues:hasLayer ?layer.
            ?layer ues:layerThickness ?thickness;
                    ues:hasMaterial ?material;
                    ues:layerOrder ?layerOrder
        }
        order by ?layerOrder
        """
)

get_opaque_material_properties = (
    prefixes
    + """
        select ?density ?roughness ?specificHeat ?solarAbsorptance ?thermalAbsorptance ?Conductivity
        ?visibleAbsorptance ?CO2Emission ?nonRenewablePrimaryEnergy

        where {
            OPTIONAL
            {<$$$> ues:thermalConductivity ?Conductivity;}
            OPTIONAL
            {<$$$> ues:roughness ?roughness;}
            OPTIONAL
            {<$$$> ues:solarAbsorptance ?solarAbsorptance;}
            OPTIONAL
            {<$$$> ues:thermalAbsorptance ?thermalAbsorptance;}
            OPTIONAL
            {<$$$> ues:visibleAbsorptance ?visibleAbsorptance.}
            OPTIONAL
            {<$$$> ues:specificHeat ?specificHeat;}
            OPTIONAL
            {<$$$> ues:density ?density;}
            OPTIONAL
            {<$$$> ues:co2Emission ?CO2Emission;}
            OPTIONAL
            {<$$$> ues:nonRenewablePrimaryEnergy ?nonRenewablePrimaryEnergy;}
        }

        """
)

get_transparent_material_properties = (
    prefixes
    + """
    select ?BackSideInfraredHemisphericalEmissivity ?BackSideSolarReflectance ?BackSideVisibleReflectance ?Conductivity ?DirtCorrectionFactor
    ?FrontSideInfraredHemisphericalEmissivity
    ?FrontSideSolarReflectance ?FrontSideVisibleReflectance ?InfraredTransmittance ?SolarTransmittance ?VisibleTransmittance

    where {
        OPTIONAL
        {<$$$>  ues:backSideInfraredHemisphericalEmissivity ?BackSideInfraredHemisphericalEmissivity;}
        OPTIONAL
        {<$$$>  ues:backSideSolarReflectance ?BackSideSolarReflectance;}
        OPTIONAL
        {<$$$>  ues:backSideVisibleReflectance ?BackSideVisibleReflectance;}
        OPTIONAL
        {<$$$>  ues:thermalConductivity ?Conductivity;}
        OPTIONAL
        {<$$$>  ues:dirtCorrectionFactor ?DirtCorrectionFactor;}
        OPTIONAL
        {<$$$>  ues:frontSideInfraredHemisphericalEmissivity ?FrontSideInfraredHemisphericalEmissivity;}
        OPTIONAL
        {<$$$>  ues:frontSideSolarReflectance ?FrontSideSolarReflectance;}
        OPTIONAL
        {<$$$>  ues:frontSideVisibleReflectance ?FrontSideVisibleReflectance;}
        OPTIONAL
        {<$$$>  ues:infraredTransmittance ?InfraredTransmittance;}
        OPTIONAL
        {<$$$>  ues:solarTransmittance ?SolarTransmittance;}
        OPTIONAL
        {<$$$>  ues:visibleTransmittance ?VisibleTransmittance.}
    }
    """
)

get_material_type = (
    prefixes
    + """
    select ?type

    where {
        <$$$>  rdf:type ?type.
        filter (?type != ues:Material)
        filter (?type != ues:Solid)
        }
    """
)

get_gas_properties = (
    prefixes
    + """
    select ?Conductivity

    where {
        <$$$>  ues:thermalConductivity ?Conductivity.
    }
    """
)

get_min_req_retrofit_name = (
    prefixes
    + """
    select ?Name

    where {
        ?Name ues:retrofitOf <$$$>.
        ?Name ues:minRequirement <http://uesl_data/sources/regulations/$regulation$>
    }
    """
)

get_tar_req_retrofit_name = (
    prefixes
    + """
    select ?Name

    where {
        ?Name ues:retrofitOf <$$$>.
        ?Name ues:targetRequirement <http://uesl_data/sources/regulations/$regulation$>
    }
    """
)

get_glazing_ratio = (
    prefixes
    + """
    select ?GlazingRatioMin ?GlazingRatioMax

    where {
        <$$$> ues:hasGlazingRatioRange ?GlazingRatioRange.
        ?GlazingRatioRange ues:hasMinValue ?GlazingRatioMin;
                           ues:hasMaxValue ?GlazingRatioMax.
    }
    """
)

get_infiltration_rate = (
    prefixes
    + """
    select ?InfiltrationRate

    where {
        <$$$> ues:hasInfiltrationRate ?InfiltrationRate.
    }
    """
)

get_archetype_by_year = (
    prefixes
    + """
    select ?Archetype
    where {
    ?Archetype ues:constructionYearRange ?YearRange.
    ?YearRange ues:hasMinValue ?minValue;
               ues:hasMaxValue ?maxValue.
    filter (?minValue <= $$$)
    filter (?maxValue >= $$$)
    }
    """
)

get_construction_u_value = (
    prefixes
    + """
    select ?UValue
    where {
    <$$$> ues:constructionUValue ?UValue.
    }
    """
)

get_construction_emission = (
    prefixes
    + """
    select ?co2Emission ?nonRenewablePrimaryEnergy
    where {
    <$$$> ues:co2Emission  ?co2Emission;
          ues:nonRenewablePrimaryEnergy ?nonRenewablePrimaryEnergy
    }
    """
)

get_archetype_year_range_by_uri = (
    prefixes
    + """
    select ?minValue ?maxValue
    where {
    <$$$> ues:constructionYearRange ?YearRange.
    OPTIONAL { ?YearRange ues:hasMinValue ?minValue. }
    OPTIONAL { ?YearRange ues:hasMaxValue ?maxValue. }
}"""
)

get_window_shading_constr_by_uri = (
    prefixes
    + """
    select ?name ?isShadingAvailable ?solarTransmittance ?solarReflectance ?visibleTransmittance ?visibleReflectance
           ?infraredHemisphericalEmissivity ?infraredTransmittance ?conductivity ?thickness  ?shadeToGlassDistance
           ?topOpeningMultiplier  ?bottomOpeningMultiplier ?leftsideOpeningMultiplier ?rightsideOpeningMultiplier
           ?airflowPermeability
    where {
    <$$$> ues:hasWindowShadingMaterial  ?ShadingMaterial.
    ?ShadingMaterial rdfs:label ?name.
    ?ShadingMaterial ues:isShadingAvailable ?isShadingAvailable.
    ?ShadingMaterial ues:solarTransmittance ?solarTransmittance.
    ?ShadingMaterial ues:solarReflectance ?solarReflectance.
    ?ShadingMaterial ues:visibleTransmittance ?visibleTransmittance.
    ?ShadingMaterial ues:visibleReflectance ?visibleReflectance.
    ?ShadingMaterial ues:infraredHemisphericalEmissivity ?infraredHemisphericalEmissivity.
    ?ShadingMaterial ues:infraredTransmittance ?infraredTransmittance.
    ?ShadingMaterial ues:conductivity ?conductivity.
    ?ShadingMaterial ues:thickness ?thickness.
    ?ShadingMaterial ues:shadeToGlassDistance ?shadeToGlassDistance.
    ?ShadingMaterial ues:topOpeningMultiplier ?topOpeningMultiplier.
    ?ShadingMaterial ues:bottomOpeningMultiplier ?bottomOpeningMultiplier.
    ?ShadingMaterial ues:leftsideOpeningMultiplier ?leftsideOpeningMultiplier.
    ?ShadingMaterial ues:rightsideOpeningMultiplier ?rightsideOpeningMultiplier.
    ?ShadingMaterial ues:airflowPermeability ?airflowPermeability.

}"""
)
