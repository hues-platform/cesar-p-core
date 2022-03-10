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
from enum import Enum


class SIA2024_2016_RoomType(Enum):
    """Mapping between RoomType key and SIA 2024-2016 Room name"""

    MFH = "Wohnen MFH"
    SFH = "Wohnen EFH"
    Hotel_room = "Hotelzimmer"
    Reception = "Empfang, Lobby"
    Single_office = "Einzel -, Gruppenbüro"
    Office = "Grossraumbüro"
    Meeting_room = "Sitzungszimmer"
    Lobby = "Schalterhalle, Empfang"
    Classroom = "Schulzimmer"
    School_Staff_room = "Lehrerzimmer"
    Library = "Bibliothek"
    Lecture_Hall = "Hörsaal"
    School_physics_chemistry_room = "Schulfachraum(Spezialraum)"
    Food_store = "Lebensmittelverkauf"
    Shopping_mall = "Fachgeschäft"
    Furniture_store = "Verkauf Möbel, Bau, Garten"
    Restaurant = "Restaurant"
    Selfservice_restaurant = "Selbstbedienungsrestaurant"
    Restaurant_kitchen = "Küche zu Restaurant"
    Self_service_restaurant_kitchen = "Küche zu Selbstbedienungsrest."
    Cinema_Theater_Concert_hall = "Vorstellungsraum"
    Multipurpose_hall = "Mehrzweckhalle"
    Exhibition_hall = "Ausstellungshalle"
    Hospital_ward = "Bettenzimmer"
    Hospital_unit_room = "Stationszimmer"
    Medical_treatment_room = "Behandlungsraum"
    Heavy_industry = "Produktion(grobe Arbeit)"
    Light_industry = "Produktion(feine Arbeit)"
    Laboratory = "Laborraum"
    Warehouse = "Lagerhalle"
    Sports_centre_School_gym = "Turnhalle"
    Gym = "Fitnessraum"
    Indoor_swimming_pool = "Schwimmhalle"
    Corridor = "Verkehrsfläche"
    Corridor_24h = "Verkehrsfläche 24h"
    Staircase = "Treppenhaus"
    Storage_space = "Nebenraum"
    Kitchen = "Küche, Teeküche"
    Bathroom_with_shower = "WC, Bad, Dusche"
    WC = "WC"
    Locker_room_shower = "Garderobe, Dusche"
    Car_park = "Parkhaus"
    Washing_drying_room = "Wasch - und Trockenraum"
    Cold_store = "Kühlraum"
    Server_room = "Serverraum"
