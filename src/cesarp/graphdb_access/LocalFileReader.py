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
import pandas
import rdflib
from rdflib.namespace import RDF, RDFS, Namespace
import cesarp.common
from cesarp.graphdb_access import _default_config_file
import cesarp.graphdb_access.sparql_queries as sparql_queries


class LocalFileReader:
    def __init__(self, filename=None, custom_config=None):
        self.cfg = cesarp.common.load_config_for_package(_default_config_file, __package__, custom_config)
        if filename is None:
            filename = self.cfg["LOCAL"]["PATH"]
        self.filename = filename  # used as member attribute for debuggin output only
        self.g = rdflib.Graph()
        self.g.parse(filename, format=self.cfg["LOCAL"]["FORMAT"])
        self.g.bind("ues", Namespace(sparql_queries.ues_prefix))
        self.g.bind("rdfs", RDFS)
        self.g.bind("rdf", RDF)

    def get_constructions_from_graph(self, name):
        results = self.g.query(sparql_queries.get_constructions.replace("$$$", name))
        return self.create_df(results)

    def get_layers_from_graph(self, name):
        results = self.g.query(sparql_queries.get_layers.replace("$$$", name))
        return self.create_df(results)

    def get_opaque_material_from_graph(self, name):
        results = self.g.query(sparql_queries.get_opaque_material_properties.replace("$$$", name))
        return self.create_df(results)

    def get_transparent_material_from_graph(self, name):
        results = self.g.query(sparql_queries.get_transparent_material_properties.replace("$$$", name))
        return self.create_df(results)

    def get_material_type_from_graph(self, name):
        results = self.g.query(sparql_queries.get_material_type.replace("$$$", name))
        return self.create_df(results)

    def get_gas_from_graph(self, name):
        results = self.g.query(sparql_queries.get_gas_properties.replace("$$$", name))
        return self.create_df(results)

    def get_retrofit_name(self, name, regulation, target_requirement=False):
        if target_requirement:
            results = self.g.query(sparql_queries.get_tar_req_retrofit_name.replace("$$$", name).replace("$regulation$", regulation))
        else:
            results = self.g.query(sparql_queries.get_min_req_retrofit_name.replace("$$$", name).replace("$regulation$", regulation))
        return self.create_df(results)

    def get_glazing_ratio_from_graph(self, archetype_uri):
        results = self.g.query(sparql_queries.get_glazing_ratio.replace("$$$", archetype_uri))
        return self.create_df(results)

    def get_infiltration_rate_from_graph(self, archetype_uri):
        results = self.g.query(sparql_queries.get_infiltration_rate.replace("$$$", archetype_uri))
        return self.create_df(results)

    def get_archetype_by_year_from_graph(self, year):
        result = self.g.query(sparql_queries.get_archetype_by_year.replace("$$$", str(year)))
        return self.create_df(result)

    def get_u_value_from_graph(self, construction_uri):
        result = self.g.query(sparql_queries.get_construction_u_value.replace("$$$", construction_uri))
        return self.create_df(result)

    def get_construction_emission_from_graph(self, construction_uri):
        result = self.g.query(sparql_queries.get_construction_emission.replace("$$$", construction_uri))
        return self.create_df(result)

    def get_archetype_year_range_from_graph_for_uri(self, archetype_uri):
        result = self.g.query(sparql_queries.get_archetype_year_range_by_uri.replace("$$$", archetype_uri))
        return self.create_df(result)

    def get_window_shading_constr_from_graph_for_uri(self, archetype_uri):
        result = self.g.query(sparql_queries.get_window_shading_constr_by_uri.replace("$$$", archetype_uri))
        return self.create_df(result)

    def create_df(self, sparql_out):
        cols = sparql_out.vars
        cols = [str(c) for c in cols]
        out = []
        for row in sparql_out:
            item = []
            for c in cols:
                if str(row[c]) == "None":
                    item.append(None)
                else:
                    item.append(str(row[c]))
            out.append(item)
        df = pandas.DataFrame(out, columns=cols)
        return df.mask(df.eq(None)).dropna(how="all")

    def __str__(self) -> str:
        return self.filename
