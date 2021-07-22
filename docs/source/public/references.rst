References and Data Sources
============================


Following the listing of references and data sources:

CESAR-P uses EnergyPlus as simulation engine (cesarp.eplus_adapter): NREL (2016). EnergyPlus. url: https://energyplus.net.

Constructions (cesarp.graphdb_access.ressources construction_and_material_data.ttl and legacy version under cesarp.idf_constructions_db_access.ressources)

- BFE. (22. 03 2016). Bauteilkatalog. Von http://www.bauteilkatalog.ch abgerufen
- Institut für Bauforschung e.V. (2010). U-Werte alter Bauteile. Hannover: Fraunhover IRB Verlage.
- Jakob, M. (2008). Grundlagen zur Wirkungsabschätzung der Energiepolitik der Kantone im Gebäudebereich. Zürich: Infras AG.
- SIA. (2009). Thermische Energie im Hochbau (SIA 380/1). Zürich: SIA.
- Hegi, P. (2014). Vollzug der energetischen Massnahmen 2012. Zürich: Baudirektion Kanton Zürich.
- UG u-wert.net. (25. 02 2016). die Seite für energieeffizientes Bauen. Von www.u-value.net abgerufen
- Hegi, Pino (2014). Vollzug der energetischen Massnahmen 2012. Published by Baudirektion Kanton Zürich
- Berkley Lab. (02. 04 2016). Window LBNL Software. Von https://windows.lbl.gov/software/window/window.html abgerufen
- Gloor, R. (13. 03 2016). Energetische Aspekte von Fenstern. Von http://www.energie.ch/fenster abgerufen


Operational data 

- SIA. (2006). Standard-Nutzungsbedingungen für Energie- und Gebäudetechnik (SIA 2024). Zürich: SIA.

Infiltration rates per building age (cesarp.graphdb_access.ressources construction_and_material_data.ttl and legacy version under cesarp.idf_constructions_db_access.ressources)

- Fennel, H. C. (2015). Setting Airtightness Standards. ASHRAE Journal. Von https://en.wikipedia.org/wiki/Infiltration_(HVAC) abgerufen
- Hubbard, D. (2014). Ventilation, Infiltration and Air Permeability of Traditional UK Dewllings. UK. In: Journal of Architectural Conservation.
- MINERGIE. (20. 06 2016). Baustandards. Von http://www.minergie.ch/baustandards.html abgerufen


Retrofit of building envelope 

- Retrofit Rates and strategy (cesarp.energy_strategy.ressources.XX.retrofit and cesarp.retrofit.energy_perspective_2050)

  - Prognos AG. (2012). Die Energieperspektiven für die Schweiz bis 2050. Basel: Bundesamt für Energie
  - N. Heeren, M. G. (2009). Gebäudeparkmodell, SIA Effizienzpfad Energie, Diensleitungs- und Wohngebäude. Bern: BFE.
  - Tomislav Cutic, S. H. (2015). SPEQUA - Rheinfelden case - Report on future heating demands. EMPA, Zürich.
  - Retrofit selection: SIA. (2011). SIA-Effizienzpfad Energie (SIA 2040). Zürich. BFE.

- Retrofit constructions (cesarp.graphdb_access.ressources construction_and_material_data.ttl):

  - SIA. (2009). Thermische Energie im Hochbau (SIA 380/1). Zürich: SIA.
  - Berkley Lab. (02. 04 2016). Window LBNL Software. Von https://windows.lbl.gov/software/window/window.html abgerufen

- Retrofit emissions (cesarp.graphdb_access.ressources construction_and_material_data.ttl, cesarp.construction.default_config.yml): KBOB, eco-bau, IPB. (2014). Ökobilanzdaten im Baubereich. Zürich: KBOB. See also https://www.kbob.admin.ch/kbob/de/home/themen-leistungen/nachhaltiges-bauen/oekobilanzdaten_baubereich.html for newest dataset.
- Retrofit costs (cesarp.retrofit.embodied.ressources): **GEAK. (2014). Kosten Gebäudehüllensanierung. Zürich: GEAK.**


System operational cost and emissions (cesarp.energy_strategy.XX.ressources)

- Wood Mix evolution: BFE. (2014). Schweizerische Holzenergiestatistik, Erhebung für das Jahr 2014. zürich: Bundesamt für Energie.
- Gas Mix evolution: Prognos AG. (2012). Die Energieperspektiven für die Schweiz bis 2050. Basel: Bundesamt für Energie BFE.
- System efficiencies: N. Heeren, M. G. (2009). Gebäudeparkmodell, SIA Effizienzpfad Energie, Diensleitungs- und Wohngebäude. Bern: BFE.
- PEN & CO2 emissions for electricity: F. Wyss, R. F. (2013). Life Cycle Assessment of Electricity Mixes according to the Energy Strategy 2050. Zürich: Stadt Zürich.
- Heating Value Factors and PEN: R. Frischknecht, M. S. (2012). Primärenergiefaktoren von Energiesystemen. Uster: ESU-Services.
- Fuel cost factors: Prognos AG. (2012). Die Energieperspektiven für die Schweiz bis 2050. Basel: Bundesamt für Energie
- energie.ch ag. (8 2016). energie.ch. Von energie.ch/heizwerte-von-holz abgerufen
- IWO. (6 2016). Institut für Wärme- und Öltechnik. Von https://www.zukunftsheizen.de/heizoel.html abgerufen


Ressources that can be used to generate input data for CESAR-P (but are not part of source code package). Note that GWR data is licensed.

- BFS. (2013). Eidgenössisches Gebäude- und Wohnungsregister (GWR). Zurich: Federal Office of Statistics.
- BFS (2014). Swiss Building Statistics. url: http://www.bfs.admin.ch/bfs/portal/de/index/themen/09/02/blank/key/gebaeude/art_und_groesse.html (visited on 09/08/2016).
- Swisstopo. (17. 07 2016). Schweizerische Eidgenossenschaft. Von swissBUILDINGS3D: http://www.toposhop.admin.ch/de/shop/products/landscape/build3D2_1 abgerufen
- meteonorm (2016). Meteonorm. url: http://www.meteonorm.com/de/.


Further sources referenced in original Matlab Tool documentation but not refered to in the documentation text:

- DIN. (2014). DIN EN ISO 6946 Bauteile – Wärmedurchlasswiderstand und Wärmedurchgangskoeffizient - Berechnungsverfahren. Germany: DIN.
- Meyer, J. (20. 07 2016). Effiziente Wärmepumpe. Von http://www.effizientewaermepumpe.ch/wiki/Dimensionierung_Erdwärmesonden abgerufen
- Sherman, M. H. (1987). Estimation of Infiltration from Leakage and Climate Indicators. Energy and Buildings.
- SIA. (2010). SIA 2032, Graue Energie von Gebäuden. Zürich: SIA.


System Retrofit (not implemented in CESAR-P as of version 1.2, will probably later be implemented)

- ELCO. (2015). Heizungssanierung. url: http://www.elco.ch/de/resources/downloads/150420_elco_sanierungsbroschuere_d_web.pdf
- Meteoschweiz. (20. 7 2016). Meteoschweiz. von http://www.meteoschweiz.admin.ch/home/klima/vergangenheit/solarenergie.html abgerufen
- energie.ch ag. (15. 07 2016). energie.ch. Von http://www.energie.ch/heizungsvergleich abgerufen
- energie.ch (2016). Heizung. url: http://www.energie.ch/heizung.
- EVS. (20. 7 2016). Von Erdgasversorgung Sarganserland: http://www.evsag.ch/Downloads/Kostenvergleich.pdf abgerufen
- Viessmann. (2015). Wärmepumpen bis 2000 kW. Zürich: Viessmann.