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
import logging
import os
import pandas
from typing import Dict, Any, Optional
from SPARQLWrapper import SPARQLWrapper, JSON

import cesarp.graphdb_access.sparql_queries as sparql_queries
import cesarp.common
from cesarp.graphdb_access import _default_config_file


class GraphDBReader:
    def __init__(self, sparql_endpoint: str = None, custom_config: Optional[Dict[str, Any]] = None):
        self.cfg = cesarp.common.load_config_for_package(_default_config_file, __package__, custom_config)
        if sparql_endpoint is None:
            sparql_endpoint = self.cfg["REMOTE"]["SPARQL_ENDPOINT"]
        self.sparql_endpoint = sparql_endpoint
        self.sparql = SPARQLWrapper(self.sparql_endpoint)
        self.sparql.setReturnFormat(JSON)
        try:
            self.sparql.user = os.environ["GRAPHDB_USER"]
            self.sparql.passwd = os.environ["GRAPHDB_PASSWORD"]
        except KeyError:
            logging.error("please set username and passwort as environment variables GRAPHDB_USER and GRAPHDB_PASSWORD")

    def get_constructions_from_graph(self, name):
        self.sparql.setQuery(sparql_queries.get_constructions.replace("$$$", name))
        results = self.sparql.query().convert()
        return self.create_df(results)

    def get_layers_from_graph(self, name):
        self.sparql.setQuery(sparql_queries.get_layers.replace("$$$", name))
        results = self.sparql.query().convert()
        return self.create_df(results)

    def get_opaque_material_from_graph(self, name):
        self.sparql.setQuery(sparql_queries.get_opaque_material_properties.replace("$$$", name))
        results = self.sparql.query().convert()
        return self.create_df(results)

    def get_transparent_material_from_graph(self, name):
        self.sparql.setQuery(sparql_queries.get_transparent_material_properties.replace("$$$", name))
        results = self.sparql.query().convert()
        return self.create_df(results)

    def get_material_type_from_graph(self, name):
        self.sparql.setQuery(sparql_queries.get_material_type.replace("$$$", name))
        results = self.sparql.query().convert()
        return self.create_df(results)

    def get_gas_from_graph(self, name):
        self.sparql.setQuery(sparql_queries.get_gas_properties.replace("$$$", name))
        results = self.sparql.query().convert()
        return self.create_df(results)

    def get_retrofit_name(self, name, regulation, target_requirement=False):
        if target_requirement:
            self.sparql.setQuery(sparql_queries.get_tar_req_retrofit_name.replace("$$$", name).replace("$regulation$", regulation))
        else:
            self.sparql.setQuery(sparql_queries.get_min_req_retrofit_name.replace("$$$", name).replace("$regulation$", regulation))
        results = self.sparql.query().convert()
        return self.create_df(results)

    def get_glazing_ratio_from_graph(self, archetype_uri):
        self.sparql.setQuery(sparql_queries.get_glazing_ratio.replace("$$$", archetype_uri))
        results = self.sparql.query().convert()
        return self.create_df(results)

    def get_infiltration_rate_from_graph(self, archetype_uri):
        self.sparql.setQuery(sparql_queries.get_infiltration_rate.replace("$$$", archetype_uri))
        results = self.sparql.query().convert()
        return self.create_df(results)

    def get_archetype_by_year_from_graph(self, year):
        self.sparql.setQuery(sparql_queries.get_archetype_by_year.replace("$$$", str(year)))
        results = self.sparql.query().convert()
        return self.create_df(results)

    def get_u_value_from_graph(self, construction_uri):
        self.sparql.setQuery(sparql_queries.get_construction_u_value.replace("$$$", construction_uri))
        results = self.sparql.query().convert()
        return self.create_df(results)

    def get_construction_emission_from_graph(self, construction_uri):
        self.sparql.setQuery(sparql_queries.get_construction_emission.replace("$$$", construction_uri))
        results = self.sparql.query().convert()
        return self.create_df(results)

    def get_archetype_year_range_from_graph_for_uri(self, archetype_uri):
        self.sparql.setQuery(sparql_queries.get_archetype_year_range_by_uri.replace("$$$", archetype_uri))
        results = self.sparql.query().convert()
        return self.create_df(results)

    def get_window_shading_constr_from_graph_for_uri(self, archetype_uri):
        self.sparql.setQuery(sparql_queries.get_window_shading_constr_by_uri.replace("$$$", archetype_uri))
        results = self.sparql.query().convert()
        return self.create_df(results)

    def create_df(self, sparql_out):
        cols = sparql_out["head"]["vars"]

        out = []

        for row in sparql_out["results"]["bindings"]:
            item = []
            for c in cols:
                item.append(row.get(c, {}).get("value"))
            out.append(item)

        df = pandas.DataFrame(out, columns=cols)
        return df.mask(df.eq(None)).dropna(how="all")

    def __str__(self) -> str:
        return self.sparql_endpoint
