"""
CONFIGURACIÓ BANNER NEWS CHANNEL - VERSIÓ DADES REALS
Configuració per al sistema de banner meteorològic amb dades reals de Meteocat
Fitxer generat automàticament: 2026-01-08 18:07:32
Total estacions: 189 (Actives: 35, Comentades: 154)
"""

import os
from datetime import datetime, timedelta

# ============================================================================
# CONFIGURACIÓ DE LES ESTACIONS (189 estacions) - ORDENADES ALFABÈTICAMENT
# Les estacions comentades (COM) tenen un # al davant
# ============================================================================
STATIONS = [
    # {'code': 'WB', 'name': 'ALBESA_WB', 'display_name': 'Albesa'},  # COM
    # {'code': 'XY', 'name': 'ALCARRAS_XY', 'display_name': 'Alcarràs'},  # COM
    # {'code': 'U7', 'name': 'ALDOVER_U7', 'display_name': 'Aldover'},  # COM
    # {'code': 'WK', 'name': 'ALFARRAS_WK', 'display_name': 'Alfarràs'},  # COM
    # {'code': 'WG', 'name': 'ALGERRI_WG', 'display_name': 'Algerri'},  # COM
    # {'code': 'X3', 'name': 'ALGUAIRE_X3', 'display_name': 'Alguaire'},  # COM
    # {'code': 'ZB', 'name': 'ALINS___SALORIA_2451_M_ZB', 'display_name': 'Alins - Salòria (2.451 m)'},  # COM
    {'code': 'YT', 'name': 'ALT_ANEU___BONABE_1693_M_YT', 'display_name': 'Alt Àneu - Bonabé (1.693 m)'},
    {'code': 'Z1', 'name': 'ALT_ANEU___BONAIGUA_2266_M_Z1', 'display_name': 'Alt Àneu - Bonaigua (2.266 m)'},
    # {'code': 'UU', 'name': 'AMPOSTA_UU', 'display_name': 'Amposta'},  # COM
    # {'code': 'XX', 'name': 'ANGLESOLA___TORNABOUS_XX', 'display_name': 'Anglesola - Tornabous'},  # COM
    {'code': 'DN', 'name': 'ANGLES_DN', 'display_name': 'Anglès'},
    # {'code': 'Z6', 'name': 'ARRES___SASSEUVA_2228_M_Z6', 'display_name': 'Arres - Sasseuva (2.228 m)'},  # COM
    # {'code': 'X6', 'name': 'ARTESA_DE_SEGRE___BALDOMAR_X6', 'display_name': 'Artesa de Segre - Baldomar'},  # COM
    # {'code': 'WW', 'name': 'ARTES_WW', 'display_name': 'Artés'},  # COM
    # {'code': 'VA', 'name': 'ASCO_VA', 'display_name': 'Ascó'},  # COM
    # {'code': 'WU', 'name': 'BADALONA___MUSEU_WU', 'display_name': 'Badalona - Museu'},  # COM
    {'code': 'DJ', 'name': 'BANYOLES_DJ', 'display_name': 'Banyoles'},
    {'code': 'X4', 'name': 'BARCELONA___EL_RAVAL_X4', 'display_name': 'Barcelona - el Raval'},
    {'code': 'D5', 'name': 'BARCELONA___OBSERVATORI_FABRA_D5', 'display_name': 'Barcelona - Observatori Fabra'},  # COM
    # {'code': 'X8', 'name': 'BARCELONA___ZONA_UNIVERSITARIA_X8', 'display_name': 'Barcelona - Zona Universitària'},  # COM
    # {'code': 'YX', 'name': 'BATEA_YX', 'display_name': 'Batea'},  # COM
    # {'code': 'UF', 'name': 'BEGUES___PN_DEL_GARRAF___EL_RASCLER_UF', 'display_name': 'Begues - Pn del Garraf - el Rascler'},  # COM
    # {'code': 'VB', 'name': 'BENISSANET_VB', 'display_name': 'Benissanet'},  # COM
    # {'code': 'WM', 'name': 'BERGA___SANTUARI_DE_QUERALT_WM', 'display_name': 'Berga - Santuari de Queralt'},  # COM
    # {'code': 'W8', 'name': 'BLANCAFORT_W8', 'display_name': 'Blancafort'},  # COM
    # {'code': 'YS', 'name': 'CABANES_YS', 'display_name': 'Cabanes'},  # COM
    # {'code': 'UP', 'name': 'CABRILS_UP', 'display_name': 'Cabrils'},  # COM
    # {'code': 'X9', 'name': 'CALDES_DE_MONTBUI_X9', 'display_name': 'Caldes de Montbui'},  # COM
    # {'code': 'WX', 'name': 'CAMARASA_WX', 'display_name': 'Camarasa'},  # COM
    # {'code': 'XU', 'name': 'CANYELLES_XU', 'display_name': 'Canyelles'},  # COM
    # {'code': 'MQ', 'name': 'CARDONA_MQ', 'display_name': 'Cardona'},  # COM
    {'code': 'UN', 'name': 'CASSA_DE_LA_SELVA_UN', 'display_name': 'Cassà de la Selva'},
    # {'code': 'DO', 'name': 'CASTELL_DARO_PLATJA_DARO_I_SAGARO___CASTELL_DARO_D', 'display_name': 'Castell D\'aro, Platja D\'aro i S\'agaró - Castell D\'aro'},  # COM
    {'code': 'MS', 'name': 'CASTELLAR_DE_NHUG___EL_CLOT_DEL_MORO_MS', 'display_name': 'Castellar de N\'hug - el Clot del Moro'},
    # {'code': 'XC', 'name': 'CASTELLBISBAL_XC', 'display_name': 'Castellbisbal'},  # COM
    # {'code': 'U4', 'name': 'CASTELLNOU_DE_BAGES_U4', 'display_name': 'Castellnou de Bages'},  # COM
    # {'code': 'C6', 'name': 'CASTELLNOU_DE_SEANA_C6', 'display_name': 'Castellnou de Seana'},  # COM
    {'code': 'W1', 'name': 'CASTELLO_DEMPURIES_W1', 'display_name': 'Castelló D\'empúries'},
    # {'code': 'C8', 'name': 'CERVERA_C8', 'display_name': 'Cervera'},  # COM
    # {'code': 'VQ', 'name': 'CONSTANTI_VQ', 'display_name': 'Constantí'},  # COM
    # {'code': 'MR', 'name': 'CORNUDELLA_DE_MONTSANT___PANTA_DE_SIURANA_MR', 'display_name': 'Cornudella de Montsant - Pantà de Siurana'},  # COM
    # {'code': 'WZ', 'name': 'CUNIT_WZ', 'display_name': 'Cunit'},  # COM
    {'code': 'DP', 'name': 'DAS___AERODROM_DP', 'display_name': 'Das - Aeròdrom'},
    # {'code': 'UQ', 'name': 'DOSRIUS___PN_MONTNEGRE_CORREDOR_UQ', 'display_name': 'Dosrius - Pn Montnegre Corredor'},  # COM
    # {'code': 'WJ', 'name': 'EL_MASROIG___EL_MASROIG_WJ', 'display_name': 'El Masroig - el Masroig'},  # COM
    # {'code': 'UH', 'name': 'EL_MONTMELL___EL_MONTMELL_UH', 'display_name': 'El Montmell - el Montmell'},  # COM
    # {'code': 'DB', 'name': 'EL_PERELLO___EL_PERELLO_DB', 'display_name': 'El Perelló - el Perelló'},  # COM
    # {'code': 'V8', 'name': 'EL_POAL___EL_POAL_V8', 'display_name': 'El Poal - el Poal'},  # COM
    # {'code': 'CT', 'name': 'EL_PONT_DE_SUERT___EL_PONT_DE_SUERT_CT', 'display_name': 'El Pont de Suert - el Pont de Suert'},  # COM
    {'code': 'XL', 'name': 'EL_PRAT_DE_LLOBREGAT___EL_PRAT_DE_LLOBREGAT_XL', 'display_name': 'El Prat de Llobregat - el Prat de Llobregat'},
    # {'code': 'Y7', 'name': 'EL_PRAT_DE_LLOBREGAT___PORT_DE_BARCELONA___BOCANA_', 'display_name': 'El Prat de Llobregat - Port de Barcelona - Bocana Sud'},  # COM
    # {'code': 'YQ', 'name': 'EL_PRAT_DE_LLOBREGAT___PORT_DE_BARCELONA___ZAL_PRA', 'display_name': 'El Prat de Llobregat - Port de Barcelona - Zal Prat'},  # COM
    # {'code': 'D9', 'name': 'EL_VENDRELL___EL_VENDRELL_D9', 'display_name': 'El Vendrell - el Vendrell'},  # COM
    # {'code': 'XM', 'name': 'ELS_ALAMUS___ELS_ALAMUS_XM', 'display_name': 'Els Alamús - els Alamús'},  # COM
    # {'code': 'CE', 'name': 'ELS_HOSTALETS_DE_PIEROLA___ELS_HOSTALETS_DE_PIEROL', 'display_name': 'Els Hostalets de Pierola - els Hostalets de Pierola'},  # COM
    # {'code': 'VD', 'name': 'ELS_PLANS_DE_SIO___EL_CANOS_VD', 'display_name': 'Els Plans de Sió - el Canós'},  # COM
    {'code': 'VZ', 'name': 'ESPOLLA_VZ', 'display_name': 'Espolla'},  # COM
    {'code': 'Z7', 'name': 'ESPOT_2519_M_Z7', 'display_name': 'Espot (2.519 m)'},
    # {'code': 'X1', 'name': 'FALSET_X1', 'display_name': 'Falset'},  # COM
    # {'code': 'KP', 'name': 'FOGARS_DE_LA_SELVA_KP', 'display_name': 'Fogars de la Selva'},  # COM
    # {'code': 'XK', 'name': 'FOGARS_DE_MONTCLUS___PUIG_SESOLLES_1668_M_XK', 'display_name': 'Fogars de Montclús - Puig Sesolles (1.668 m)'},  # COM
    # {'code': 'DI', 'name': 'FONT_RUBI_DI', 'display_name': 'Font-rubí'},  # COM
    # {'code': 'UO', 'name': 'FORNELLS_DE_LA_SELVA_UO', 'display_name': 'Fornells de la Selva'},
    # {'code': 'Y4', 'name': 'FIGOLS_I_ALINYA___ALINYA_Y4', 'display_name': 'Fígols i Alinyà - Alinyà'},  # COM
    # {'code': 'XP', 'name': 'GANDESA_XP', 'display_name': 'Gandesa'},  # COM
    # {'code': 'VH', 'name': 'GIMENELLS_I_EL_PLA_DE_LA_FONT___GIMENELLS_VH', 'display_name': 'Gimenells i el Pla de la Font - Gimenells'},  # COM
    {'code': 'XJ', 'name': 'GIRONA_XJ', 'display_name': 'Girona'},
    # {'code': 'UI', 'name': 'GISCLARENY_UI', 'display_name': 'Gisclareny'},  # COM
    # {'code': 'WC', 'name': 'GOLMES_WC', 'display_name': 'Golmés'},  # COM
    # {'code': 'YM', 'name': 'GRANOLLERS_YM', 'display_name': 'Granollers'},  # COM
    # {'code': 'WV', 'name': 'GUARDIOLA_DE_BERGUEDA_WV', 'display_name': 'Guardiola de Berguedà'},  # COM
    # {'code': 'MV', 'name': 'GUIXERS___VALLS_MV', 'display_name': 'Guixers - Valls'},  # COM
    # {'code': 'D8', 'name': 'HORTA_DE_SANT_JOAN_D8', 'display_name': 'Horta de Sant Joan'},  # COM
    # {'code': 'CP', 'name': 'ISONA_I_CONCA_DELLA___SANT_ROMA_DABELLA_CP', 'display_name': 'Isona i Conca Dellà - Sant Romà D\'abella'},  # COM
    # {'code': 'U9', 'name': 'LALDEA___LALDEA_U9', 'display_name': 'L\'aldea - L\'aldea'},  # COM
    # {'code': 'UA', 'name': 'LAMETLLA_DE_MAR___LAMETLLA_DE_MAR_UA', 'display_name': 'L\'ametlla de Mar - L\'ametlla de Mar'},  # COM
    # {'code': 'CW', 'name': 'LESPLUGA_DE_FRANCOLI___LESPLUGA_DE_FRANCOLI_CW', 'display_name': 'L\'espluga de Francolí - L\'espluga de Francolí'},  # COM
    {'code': 'YU', 'name': 'LESQUIROL___CANTONIGROS_YU', 'display_name': 'L\'esquirol - Cantonigròs'},
    # {'code': 'DF', 'name': 'LA_BISBAL_DEMPORDA___LA_BISBAL_DEMPORDA_DF', 'display_name': 'La Bisbal D\'empordà - la Bisbal D\'empordà'},  # COM
    # {'code': 'WO', 'name': 'LA_BISBAL_DEL_PENEDES___LA_BISBAL_DEL_PENEDES_WO', 'display_name': 'La Bisbal del Penedès - la Bisbal del Penedès'},  # COM
    # {'code': 'ZE', 'name': 'LA_COMA_I_LA_PEDRA___EL_PORT_DEL_COMTE_2290_M_ZE', 'display_name': 'La Coma i la Pedra - el Port del Comte (2.290 m)'},  # COM
    # {'code': 'UM', 'name': 'LA_GRANADELLA___LA_GRANADELLA_UM', 'display_name': 'La Granadella - la Granadella'},  # COM
    # {'code': 'XB', 'name': 'LA_LLACUNA___LA_LLACUNA_XB', 'display_name': 'La Llacuna - la Llacuna'},  # COM
    # {'code': 'YC', 'name': 'LA_POBLA_DE_SEGUR___LA_POBLA_DE_SEGUR_YC', 'display_name': 'La Pobla de Segur - la Pobla de Segur'},  # COM
    # {'code': 'CR', 'name': 'LA_QUAR___LA_QUAR_CR', 'display_name': 'La Quar - la Quar'},  # COM
    # {'code': 'KX', 'name': 'LA_ROCA_DEL_VALLES___LA_ROCA_DEL_VALLES___ETAP_CAR', 'display_name': 'La Roca del Vallès - la Roca del Vallès - Etap Cardedeu'},  # COM
    # {'code': 'UW', 'name': 'LA_RAPITA___ELS_ALFACS_UW', 'display_name': 'La Ràpita - els Alfacs'},  # COM
    {'code': 'CD', 'name': 'LA_SEU_DURGELL___LA_SEU_DURGELL___BELLESTAR_CD', 'display_name': 'La Seu D\'urgell - la Seu D\'urgell - Bellestar'},
    # {'code': 'UB', 'name': 'LA_TALLADA_DEMPORDA___LA_TALLADA_DEMPORDA_UB', 'display_name': 'La Tallada D\'empordà - la Tallada D\'empordà'},  # COM
    # {'code': 'ZD', 'name': 'LA_TOSA_DALP_2478_M_ZD', 'display_name': 'La Tosa D\'alp (2.478 m)'},  # COM
    # {'code': 'W9', 'name': 'LA_VALL_DEN_BAS___LA_VALL_DEN_BAS_W9', 'display_name': 'La Vall D\'en Bas - la Vall D\'en Bas'},  # COM
    {'code': 'Z2', 'name': 'LA_VALL_DE_BOI___BOI_2535_M_Z2', 'display_name': 'La Vall de Boí - Boí (2.535 m)'},
    # {'code': 'YD', 'name': 'LES_BORGES_BLANQUES___LES_BORGES_BLANQUES_YD', 'display_name': 'Les Borges Blanques - Les Borges Blanques'},  # COM
    # {'code': 'US', 'name': 'LES_CASES_DALCANAR_US', 'display_name': 'Les Cases D\'alcanar'},  # COM
    # {'code': 'Z5', 'name': 'LLADORRE___CERTASCAN_2400_M_Z5', 'display_name': 'Lladorre - Certascan (2.400 m)'},  # COM
    # {'code': 'VO', 'name': 'LLADURS_VO', 'display_name': 'Lladurs'},  # COM
    # {'code': 'YJ', 'name': 'LLEIDA___LA_FEMOSA_YJ', 'display_name': 'Lleida - la Femosa'},  # COM
    {'code': 'VK', 'name': 'LLEIDA___RAIMAT_VK', 'display_name': 'Lleida - Raimat'},
    # {'code': 'WI', 'name': 'MAIALS_WI', 'display_name': 'Maials'},  # COM
    # {'code': 'WT', 'name': 'MALGRAT_DE_MAR_WT', 'display_name': 'Malgrat de Mar'},  # COM
    # {'code': 'D1', 'name': 'MARGALEF_D1', 'display_name': 'Margalef'},  # COM
    # {'code': 'C9', 'name': 'MAS_DE_BARBERANS_C9', 'display_name': 'Mas de Barberans'},  # COM
    # {'code': 'YE', 'name': 'MASSOTERES_YE', 'display_name': 'Massoteres'},  # COM
    # {'code': 'YV', 'name': 'MATARO_YV', 'display_name': 'Mataró'},  # COM
    # {'code': 'WP', 'name': 'MEDIONA___CANALETES_WP', 'display_name': 'Mediona - Canaletes'},  # COM
    {'code': 'Z3', 'name': 'MERANGES___MALNIU_2230_M_Z3', 'display_name': 'Meranges - Malniu (2.230 m)'},
    # {'code': 'XI', 'name': 'MOLLERUSSA_XI', 'display_name': 'Mollerussa'},  # COM
    # {'code': 'CG', 'name': 'MOLLO___FABERT_CG', 'display_name': 'Molló - Fabert'},  # COM
    # {'code': 'WN', 'name': 'MONISTROL_DE_MONTSERRAT___MONTSERRAT___SANT_DIMES_', 'display_name': 'Monistrol de Montserrat - Montserrat - Sant Dimes'},  # COM
    # {'code': 'YF', 'name': 'MONT_ROIG_DEL_CAMP___MIAMI_PLATJA_YF', 'display_name': 'Mont-roig del Camp - Miami Platja'},  # COM
    # {'code': 'Z9', 'name': 'MONTELLA_I_MARTINET___CADI_NORD_2143_M___PRAT_DAGU', 'display_name': 'Montellà i Martinet - Cadí Nord (2.143 m) - Prat D\'aguiló'},  # COM
    # {'code': 'V4', 'name': 'MONTESQUIU_V4', 'display_name': 'Montesquiu'},  # COM
    # {'code': 'XA', 'name': 'MONTMANEU___LA_PANADELLA_XA', 'display_name': 'Montmaneu - la Panadella'},  # COM
    # {'code': 'CY', 'name': 'MUNTANYOLA_CY', 'display_name': 'Muntanyola'},  # COM
    # {'code': 'Y5', 'name': 'NAVATA_Y5', 'display_name': 'Navata'},  # COM
    # {'code': 'MW', 'name': 'NAVES_MW', 'display_name': 'Navès'},  # COM
    # {'code': 'VY', 'name': 'NULLES_VY', 'display_name': 'Nulles'},  # COM
    # {'code': 'W5', 'name': 'OLIANA_W5', 'display_name': 'Oliana'},  # COM
    # {'code': 'WA', 'name': 'OLIOLA_WA', 'display_name': 'Oliola'},  # COM
    {'code': 'YB', 'name': 'OLOT_YB', 'display_name': 'Olot'},
    # {'code': 'CJ', 'name': 'ORGANYA_CJ', 'display_name': 'Organyà'},  # COM
    # {'code': 'CC', 'name': 'ORIS_CC', 'display_name': 'Orís'},  # COM
    # {'code': 'UY', 'name': 'OS_DE_BALAGUER___EL_MONESTIR_DAVELLANES_UY', 'display_name': 'Os de Balaguer - el Monestir D\'avellanes'},  # COM
    {'code': 'YP', 'name': 'PALAFRUGELL_YP', 'display_name': 'Palafrugell'},
    {'code': 'J5', 'name': 'PANTA_DE_DARNIUS___BOADELLA_J5', 'display_name': 'Pantà de Darnius - Boadella'},
    # {'code': 'XG', 'name': 'PARETS_DEL_VALLES_XG', 'display_name': 'Parets del Vallès'},  # COM
    # {'code': 'V5', 'name': 'PERAFITA_V5', 'display_name': 'Perafita'},  # COM
    # {'code': 'VP', 'name': 'PINOS_VP', 'display_name': 'Pinós'},  # COM
    {'code': 'D6', 'name': 'PORTBOU___COLL_DELS_BELITRES_D6', 'display_name': 'Portbou - Coll dels Belitres'},  # COM
    # {'code': 'XR', 'name': 'PRADES_XR', 'display_name': 'Prades'},  # COM
    {'code': 'YA', 'name': 'PUIGCERDA_YA', 'display_name': 'Puigcerdà'},
    # {'code': 'YH', 'name': 'PUJALT_YH', 'display_name': 'Pujalt'},  # COM
    {'code': 'DG', 'name': 'QUERALBS___NURIA_1971_M_DG', 'display_name': 'Queralbs - Núria (1.971 m)'},
    # {'code': 'VU', 'name': 'RELLINARS_VU', 'display_name': 'Rellinars'},  # COM
    # {'code': 'VC', 'name': 'RIBA_ROJA_DEBRE___PANTA_DE_RIBA_ROJA_VC', 'display_name': 'Riba-roja D\'ebre - Pantà de Riba-roja'},  # COM
    # {'code': 'YL', 'name': 'RIUDECANYES_YL', 'display_name': 'Riudecanyes'},  # COM
    # {'code': 'X5', 'name': 'ROQUETES___PN_DELS_PORTS_X5', 'display_name': 'Roquetes - Pn dels Ports'},  # COM
    {'code': 'D4', 'name': 'ROSES_D4', 'display_name': 'Roses'},
    # {'code': 'XF', 'name': 'SABADELL___PARC_AGRARI_XF', 'display_name': 'Sabadell - Parc Agrari'},  # COM
    # {'code': 'XV', 'name': 'SANT_CUGAT_DEL_VALLES___CAR_XV', 'display_name': 'Sant Cugat del Vallès - Car'},  # COM
    # {'code': 'WQ', 'name': 'SANT_ESTEVE_DE_LA_SARGA___MONTSEC_DARES_1572_M_WQ', 'display_name': 'Sant Esteve de la Sarga - Montsec D\'ares (1.572 m)'},  # COM
    # {'code': 'DL', 'name': 'SANT_JAUME_DENVEJA___ILLA_DE_BUDA_DL', 'display_name': 'Sant Jaume D\'enveja - Illa de Buda'},  # COM
    # {'code': 'M6', 'name': 'SANT_JOAN_DE_LES_ABADESSES_M6', 'display_name': 'Sant Joan de Les Abadesses'},  # COM
    # {'code': 'VV', 'name': 'SANT_LLORENC_SAVALL_VV', 'display_name': 'Sant Llorenç Savall'},  # COM
    # {'code': 'WL', 'name': 'SANT_MARTI_DE_RIUCORB_WL', 'display_name': 'Sant Martí de Riucorb'},  # COM
    # {'code': 'U3', 'name': 'SANT_MARTI_SARROCA_U3', 'display_name': 'Sant Martí Sarroca'},  # COM
    {'code': 'CI', 'name': 'SANT_PAU_DE_SEGURIES_CI', 'display_name': 'Sant Pau de Segúries'},
    # {'code': 'UK', 'name': 'SANT_PERE_DE_RIBES___PN_DEL_GARRAF_UK', 'display_name': 'Sant Pere de Ribes - Pn del Garraf'},  # COM
    # {'code': 'U2', 'name': 'SANT_PERE_PESCADOR_U2', 'display_name': 'Sant Pere Pescador'},  # COM
    # {'code': 'YO', 'name': 'SANT_SADURNI_DANOIA_YO', 'display_name': 'Sant Sadurní D\'anoia'},  # COM
    # {'code': 'CL', 'name': 'SANT_SALVADOR_DE_GUARDIOLA_CL', 'display_name': 'Sant Salvador de Guardiola'},  # COM
    {'code': 'XS', 'name': 'SANTA_COLOMA_DE_FARNERS_XS', 'display_name': 'Santa Coloma de Farners'},
    # {'code': 'UJ', 'name': 'SANTA_COLOMA_DE_QUERALT_UJ', 'display_name': 'Santa Coloma de Queralt'},  # COM
    # {'code': 'XN', 'name': 'SEROS_XN', 'display_name': 'Seròs'},  # COM
    {'code': 'ZC', 'name': 'SETCASES___ULLDETER_2413_M_ZC', 'display_name': 'Setcases - Ulldeter (2.413 m)'},
    # {'code': 'XT', 'name': 'SOLSONA_XT', 'display_name': 'Solsona'},  # COM
    {'code': 'XH', 'name': 'SORT_XH', 'display_name': 'Sort'},
    # {'code': 'VX', 'name': 'TAGAMANENT___PN_DEL_MONTSENY_VX', 'display_name': 'Tagamanent - Pn del Montseny'},  # COM
    {'code': 'XE', 'name': 'TARRAGONA___COMPLEX_EDUCATIU_XE', 'display_name': 'Tarragona - Complex Educatiu'},
    # {'code': 'YK', 'name': 'TERRASSA_YK', 'display_name': 'Terrassa'},  # COM
    # {'code': 'Y6', 'name': 'TIVISSA_Y6', 'display_name': 'Tivissa'},  # COM
    # {'code': 'DK', 'name': 'TORREDEMBARRA_DK', 'display_name': 'Torredembarra'},  # COM
    # {'code': 'X7', 'name': 'TORRES_DE_SEGRE_X7', 'display_name': 'Torres de Segre'},  # COM
    # {'code': 'XZ', 'name': 'TORROELLA_DE_FLUVIA_XZ', 'display_name': 'Torroella de Fluvià'},  # COM
    {'code': 'UE', 'name': 'TORROELLA_DE_MONTGRI_UE', 'display_name': 'Torroella de Montgrí'},
    # {'code': 'WR', 'name': 'TORROJA_DEL_PRIORAT_WR', 'display_name': 'Torroja del Priorat'},  # COM
    # {'code': 'XQ', 'name': 'TREMP_XQ', 'display_name': 'Tremp'},  # COM
    # {'code': 'C7', 'name': 'TARREGA_C7', 'display_name': 'Tàrrega'},  # COM
    # {'code': 'YG', 'name': 'TIRVIA_YG', 'display_name': 'Tírvia'},  # COM
    # {'code': 'UX', 'name': 'ULLDECONA___ELS_VALENTINS_UX', 'display_name': 'Ulldecona - els Valentins'},  # COM
    # {'code': 'XD', 'name': 'ULLDEMOLINS_XD', 'display_name': 'Ulldemolins'},  # COM
    # {'code': 'D2', 'name': 'VACARISSES_D2', 'display_name': 'Vacarisses'},  # COM
    # {'code': 'V1', 'name': 'VALLFOGONA_DE_BALAGUER_V1', 'display_name': 'Vallfogona de Balaguer'},  # COM
    # {'code': 'D3', 'name': 'VALLIRANA_D3', 'display_name': 'Vallirana'},  # COM
    {'code': 'XO', 'name': 'VIC_XO', 'display_name': 'Vic'},
    {'code': 'VS', 'name': 'VIELHA_E_MIJARAN___LAC_REDON_2247_M_VS', 'display_name': 'Vielha e Mijaran - Lac Redon (2.247 m)'},
    # {'code': 'YN', 'name': 'VIELHA_E_MIJARAN___VIELHA___ELIPORT_YN', 'display_name': 'Vielha e Mijaran - Vielha - Elipòrt'},  # COM
    # {'code': 'DQ', 'name': 'VILA_RODONA_DQ', 'display_name': 'Vila-rodona'},  # COM
    # {'code': 'UG', 'name': 'VILADECANS_UG', 'display_name': 'Viladecans'},  # COM
    # {'code': 'WS', 'name': 'VILADRAU_WS', 'display_name': 'Viladrau'},  # COM
    # {'code': 'W4', 'name': 'VILAFRANCA_DEL_PENEDES___LA_GRANADA_W4', 'display_name': 'Vilafranca del Penedès - la Granada'},  # COM
    # {'code': 'CQ', 'name': 'VILANOVA_DE_MEIA_CQ', 'display_name': 'Vilanova de Meià'},  # COM
    # {'code': 'KE', 'name': 'VILANOVA_DE_SAU___PANTA_DE_SAU_KE', 'display_name': 'Vilanova de Sau - Pantà de Sau'},  # COM
    # {'code': 'VM', 'name': 'VILANOVA_DE_SEGRIA_VM', 'display_name': 'Vilanova de Segrià'},  # COM
    # {'code': 'YR', 'name': 'VILANOVA_I_LA_GELTRU_YR', 'display_name': 'Vilanova i la Geltrú'},  # COM
    {'code': 'D7', 'name': 'VINEBRE_D7', 'display_name': 'Vinebre'},
    # {'code': 'U6', 'name': 'VINYOLS_I_ELS_ARCS___CAMBRILS_U6', 'display_name': 'Vinyols i els Arcs - Cambrils'},  # COM
    # {'code': 'H1', 'name': 'ODENA_H1', 'display_name': 'Òdena'},  # COM
]

# ============================================================================
# VARIABLES METEOROLÒGIQUES A CAPTURAR
# ============================================================================
VARIABLES = {
    'TX': 'Temperatura màxima (°C)',
    'TN': 'Temperatura mínima (°C)', 
    'PPT': 'Precipitació (mm)'
}

# ============================================================================
# CONFIGURACIÓ DE RUTES
# ============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Fitxers de dades
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

LATEST_DATA_FILE = os.path.join(DATA_DIR, 'latest_weather.json')
HISTORICAL_DIR = os.path.join(DATA_DIR, 'historical')
os.makedirs(HISTORICAL_DIR, exist_ok=True)

# Fitxers HTML
HTML_TEMPLATE = os.path.join(BASE_DIR, 'banner_news_channel.html')
OUTPUT_HTML = os.path.join(BASE_DIR, 'banner_output.html')

# ============================================================================
# CONFIGURACIÓ API METEOCAT
# ============================================================================
METEOcat_CONFIG = {
    'api_base': 'https://api.meteo.cat/v1',
    'timeout': 30,
    'max_retries': 3,
    'backoff_factor': 2
}

API_KEY = None  # Modo web scraping

# ============================================================================
# CONFIGURACIÓ DE TEMPS
# ============================================================================
# Període de dades (avui)
TODAY = datetime.now().date()
YESTERDAY = TODAY - timedelta(days=1)

# Scroll del banner
SCROLL_CONFIG = {
    'transition_duration': 0.8,
    'display_duration': 15,
    'stations_per_view': 2
}

# ============================================================================
# FUNCIONS UTILS
# ============================================================================
def get_current_datetime():
    """Retorna la data i hora actual formatejada"""
    now = datetime.now()
    return {
        'time': now.strftime('%H:%M'),
        'date': now.strftime('%d/%m/%Y'),
        'datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
        'timestamp': int(now.timestamp())
    }

def get_update_text():
    """Retorna el text d'actualització per al peu del banner"""
    current = get_current_datetime()
    return f"Actualitzat: {current['time']} - Data: {current['date']}"

def get_station_file_path(station_code):
    """Retorna la ruta del fitxer històric per una estació"""
    return os.path.join(HISTORICAL_DIR, f"{station_code}.json")

# ============================================================================
# VALORS PER DEFECTE
# ============================================================================
DEFAULT_VALUES = {
    'TX': '--',
    'TN': '--',
    'PPT': '--'
}

# ============================================================================
# INFORMACIÓ DE GENERACIÓ
# ============================================================================
GENERATION_INFO = {
    'generated_at': '2026-01-08 18:07:32',
    'total_stations': 189,
    'active_stations': 33,
    'comented_stations': 156,
    'false_stations': 0,
    'config_banner_version': 'v2.0 - Lògica: Op+CERT+Activa',
    'generator': 'ConfiguradorEstacions v2.1'
}

# ============================================================================
# COMPROVACIÓ INICIAL
# ============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print(f"CONFIG_BANNER.PY - VERSIÓ {GENERATION_INFO['config_banner_version']}")
    print("=" * 70)
    print(f"📊 Total estacions: {len(STATIONS)}")
    print(f"✅ Actives: {GENERATION_INFO['active_stations']}")
    print(f"💬 Comentades: {GENERATION_INFO['comented_stations']}")
    print(f"🗑️ Desmantellades: {GENERATION_INFO['false_stations']}")
    print("=" * 70)
    
    active_count = 0
    commented_count = 0
    
    for i, station_line in enumerate(STATIONS, 1):
        # Determinar si l'estació està comentada
        if isinstance(station_line, str) and station_line.strip().startswith('#'):
            status = "💬"
            commented_count += 1
        else:
            status = "✅"
            active_count += 1
        
        # Mostrar la línia
        print(f"  {status} {i:2}. {station_line}")
    
    print("=" * 70)
    print(f"🚀 Configuració carregada correctament!")
    print(f"✅ Actives reals: {active_count}")
    print(f"💬 Comentades reals: {commented_count}")
    print(f"💾 Dades actualitzades: {GENERATION_INFO['generated_at']}")
    print("=" * 70)
