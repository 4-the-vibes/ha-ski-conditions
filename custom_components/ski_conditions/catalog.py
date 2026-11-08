"""Built-in resort catalog: Canada + western United States.

Each row: (id, name, region, country, lat, lon, base_m, summit_m, onthesnow_path, snowforecast_slug)

* OnTheSnow paths were taken from onthesnow.com's provincial/state listings (Nov 2026),
  except Arizona and Alaska, which are best guesses.
* Snow-Forecast slugs for Alberta, BC and Colorado were taken from snow-forecast.com
  listings; others follow the site's usual naming and may need correcting. The "Add
  resort" flow test-loads both pages so a bad slug shows up immediately.
* Coordinates / elevations are approximate (they position the Open-Meteo forecast
  points). An empty source string means that site has no page for the resort.
"""

from __future__ import annotations

from .const import Resort

_ROWS: tuple[tuple, ...] = (
    # ---------------------------------------------------------------- Alberta
    ("sunshine_village", "Sunshine Village", "AB", "CA", 51.0785, -115.7731, 1660, 2730, "alberta/banff-sunshine", "Sunshine"),
    ("lake_louise", "Lake Louise", "AB", "CA", 51.4419, -116.1622, 1646, 2637, "alberta/lake-louise", "Lake-Louise"),
    ("norquay", "Norquay", "AB", "CA", 51.2036, -115.6060, 1630, 2133, "alberta/ski-banff-norquay", "Banff-Norquay"),
    ("nakiska", "Nakiska", "AB", "CA", 50.9425, -115.1510, 1525, 2260, "alberta/nakiska-ski-area", "Nakiska"),
    ("castle_mountain", "Castle Mountain", "AB", "CA", 49.3180, -114.4120, 1425, 2273, "alberta/castle-mountain", "Castle-Mountain-Resort"),
    ("marmot_basin", "Marmot Basin", "AB", "CA", 52.8000, -118.0830, 1698, 2612, "alberta/marmot-basin", "Marmot-Basin"),
    ("winsport", "WinSport (Canada Olympic Park)", "AB", "CA", 51.0830, -114.2150, 1130, 1250, "alberta/winsport", "Calgary-Canada-Olympic-Park"),
    ("fortress_mountain", "Fortress Mountain", "AB", "CA", 50.8270, -115.2140, 2000, 2370, "", "Fortress-Mountain"),
    ("pass_powderkeg", "Pass Powderkeg", "AB", "CA", 49.6330, -114.5100, 1340, 1550, "", "Pass-Powderkeg"),
    ("canyon_ski_area", "Canyon Ski Area", "AB", "CA", 52.2700, -113.6600, 870, 950, "", "Canyon-Ski-Area"),
    ("snow_valley_edmonton", "Snow Valley (Edmonton)", "AB", "CA", 53.4900, -113.5500, 640, 690, "", "SnowValleySkiClub"),
    # ------------------------------------------------------- British Columbia
    ("panorama", "Panorama", "BC", "CA", 50.4600, -116.2380, 1150, 2380, "british-columbia/panorama-mountain", "Panorama"),
    ("kicking_horse", "Kicking Horse", "BC", "CA", 51.2975, -117.0480, 1190, 2450, "british-columbia/kicking-horse", "Kicking-Horse"),
    ("fernie", "Fernie", "BC", "CA", 49.4627, -115.0873, 1052, 2134, "british-columbia/fernie-alpine", "Fernie"),
    ("revelstoke", "Revelstoke", "BC", "CA", 50.9580, -118.1630, 512, 2225, "british-columbia/revelstoke-mountain", "Revelstoke"),
    ("kimberley", "Kimberley", "BC", "CA", 49.6880, -116.0060, 1230, 1982, "british-columbia/kimberley", "Kimberley"),
    ("whistler_blackcomb", "Whistler Blackcomb", "BC", "CA", 50.1150, -122.9486, 675, 2284, "british-columbia/whistler-blackcomb", "Whistler-Blackcomb"),
    ("big_white", "Big White", "BC", "CA", 49.7258, -118.9342, 1508, 2319, "british-columbia/big-white", "Big-White"),
    ("sun_peaks", "Sun Peaks", "BC", "CA", 50.8833, -119.8833, 1255, 2152, "british-columbia/sun-peaks", "Sun-Peaks"),
    ("silver_star", "SilverStar", "BC", "CA", 50.3600, -119.0620, 1155, 1915, "british-columbia/silver-star", "Silver-Star"),
    ("red_mountain", "RED Mountain", "BC", "CA", 49.1050, -117.8460, 1185, 2075, "british-columbia/red-resort", "Red-Mountain"),
    ("whitewater", "Whitewater", "BC", "CA", 49.4430, -117.1460, 1640, 2044, "british-columbia/whitewater", "Whitewater"),
    ("apex", "Apex Mountain", "BC", "CA", 49.3906, -119.9036, 1575, 2180, "british-columbia/apex-mountain", "Apex"),
    ("baldy_mountain", "Baldy Mountain", "BC", "CA", 49.1528, -119.2406, 1720, 2304, "british-columbia/mount-baldy-ski-corporation", "Mt-Baldy-Ski-Area"),
    ("mt_washington", "Mount Washington", "BC", "CA", 49.7420, -125.2950, 1110, 1588, "british-columbia/mt-washington-alpine-resort", "Mount-Washington"),
    ("cypress_mountain", "Cypress Mountain", "BC", "CA", 49.3961, -123.2047, 910, 1440, "british-columbia/cypress-mountain", "Cypress-Mountain"),
    ("grouse_mountain", "Grouse Mountain", "BC", "CA", 49.3800, -123.0810, 1100, 1231, "british-columbia/grouse-mountain", "Grouse-Mountain"),
    ("mt_seymour", "Mt Seymour", "BC", "CA", 49.3667, -122.9500, 1000, 1265, "british-columbia/mount-seymour", "Mount-Seymour"),
    ("manning_park", "Manning Park", "BC", "CA", 49.0660, -120.8900, 1340, 1770, "british-columbia/manning-park-resort", "Manning-Park-Resort"),
    ("sasquatch", "Sasquatch Mountain", "BC", "CA", 49.3780, -121.9400, 1000, 1370, "british-columbia/hemlock-valley-resort", "Sasquatch-Mountain"),
    ("hudson_bay_mountain", "Hudson Bay Mountain", "BC", "CA", 54.7900, -127.2900, 1100, 1720, "british-columbia/hudson-bay-mountain", "Ski-Smithers"),
    ("powder_king", "Powder King", "BC", "CA", 55.3600, -122.6100, 880, 1520, "british-columbia/powder-king", "Powder-King"),
    ("mount_timothy", "Mount Timothy", "BC", "CA", 51.9400, -120.9600, 1170, 1470, "british-columbia/mount-timothy-recreation-resort", "Mount-Timothy-Ski-Area"),
    ("mount_cain", "Mount Cain", "BC", "CA", 50.2300, -126.3500, 930, 1260, "", "MountCain"),
    ("murray_ridge", "Murray Ridge", "BC", "CA", 54.5600, -124.3800, 1050, 1560, "", "Murray-Ridge"),
    ("shames_mountain", "Shames Mountain", "BC", "CA", 54.4800, -128.9500, 670, 1200, "", "Shames-Mountain"),
    # ----------------------------------------------------- Prairies / North
    ("table_mountain_sk", "Table Mountain", "SK", "CA", 52.8900, -108.4400, 640, 720, "", "Table-Mountain"),
    ("asessippi", "Asessippi", "MB", "CA", 50.9450, -101.3500, 400, 525, "", "Asessippi"),
    ("mount_sima", "Mount Sima", "YT", "CA", 60.6000, -135.0300, 750, 1060, "", "Mount-Sima"),
    # ---------------------------------------------------------------- Ontario
    ("blue_mountain", "Blue Mountain", "ON", "CA", 44.5017, -80.3097, 230, 450, "ontario/blue-mountain", "Blue-Mountain-Ontario"),
    ("horseshoe", "Horseshoe Resort", "ON", "CA", 44.5500, -79.6700, 300, 395, "ontario/horseshoe-resort", "Horseshoe"),
    ("mt_st_louis_moonstone", "Mt St Louis Moonstone", "ON", "CA", 44.6500, -79.6300, 230, 400, "ontario/mt-st-louis-moonstone", "Mount-St-Louis-Moonstone"),
    ("calabogie_peaks", "Calabogie Peaks", "ON", "CA", 45.3000, -76.7500, 230, 465, "ontario/calabogie-peaks", "Calabogie-Peaks"),
    ("glen_eden", "Glen Eden", "ON", "CA", 43.4970, -79.9400, 230, 300, "ontario/glen-eden", ""),
    ("hidden_valley_on", "Hidden Valley", "ON", "CA", 45.4000, -79.1700, 300, 400, "ontario/hidden-valley", ""),
    ("loch_lomond", "Loch Lomond", "ON", "CA", 48.3000, -89.3300, 330, 560, "ontario/loch-lomond", "Loch-Lomond"),
    ("mt_pakenham", "Mount Pakenham", "ON", "CA", 45.3000, -76.3000, 140, 220, "ontario/mt-pakenham", ""),
    ("searchmont", "Searchmont", "ON", "CA", 46.7900, -84.0700, 380, 600, "ontario/searchmont-resort", "Searchmont"),
    ("antoine_mountain", "Antoine Mountain", "ON", "CA", 46.3300, -78.7100, 210, 380, "ontario/antoine-mountain", ""),
    # ----------------------------------------------------------------- Quebec
    ("tremblant", "Tremblant", "QC", "CA", 46.2100, -74.5800, 265, 875, "quebec/tremblant", "Mont-Tremblant"),
    ("mont_sainte_anne", "Mont-Sainte-Anne", "QC", "CA", 47.0750, -70.9050, 175, 800, "quebec/mont-sainte-anne", "Mont-Sainte-Anne"),
    ("le_massif", "Le Massif de Charlevoix", "QC", "CA", 47.2800, -70.5700, 36, 806, "quebec/le-massif", "Le-Massif"),
    ("stoneham", "Stoneham", "QC", "CA", 47.0200, -71.3700, 210, 630, "quebec/stoneham", "Stoneham"),
    ("mont_sutton", "Mont Sutton", "QC", "CA", 45.1000, -72.5600, 410, 968, "quebec/mont-sutton", "Mont-Sutton"),
    ("owls_head", "Owl's Head", "QC", "CA", 45.0600, -72.3000, 260, 750, "quebec/owls-head", "Owls-Head"),
    ("bromont", "Bromont", "QC", "CA", 45.2900, -72.6500, 185, 570, "quebec/ski-bromont", "Bromont"),
    ("mont_orford", "Mont Orford", "QC", "CA", 45.3200, -72.2400, 320, 853, "quebec/mont-orford", "Mont-Orford"),
    ("massif_du_sud", "Massif du Sud", "QC", "CA", 46.6000, -70.4700, 520, 915, "quebec/massif-du-sud", "Massif-du-Sud"),
    ("mont_saint_sauveur", "Mont Saint-Sauveur", "QC", "CA", 45.8900, -74.1600, 230, 440, "quebec/mont-saint-sauveur", "Mont-Saint-Sauveur"),
    ("mont_blanc_qc", "Mont Blanc", "QC", "CA", 46.0700, -74.4700, 360, 660, "quebec/mont-blanc", ""),
    ("mont_ste_marie", "Mont Ste-Marie", "QC", "CA", 45.9500, -75.9300, 220, 600, "quebec/mont-ste-marie", ""),
    ("camp_fortune", "Camp Fortune", "QC", "CA", 45.5100, -75.8600, 200, 380, "quebec/camp-fortune", ""),
    ("mont_cascades", "Mont Cascades", "QC", "CA", 45.6000, -75.8200, 160, 320, "quebec/mont-cascades", ""),
    ("vorlage", "Vorlage", "QC", "CA", 45.6400, -75.9300, 140, 300, "quebec/vorlage", ""),
    # --------------------------------------------------------------- Atlantic
    ("crabbe_mountain", "Crabbe Mountain", "NB", "CA", 46.1100, -67.3200, 230, 500, "", "Crabbe-Mountain"),
    ("wentworth", "Ski Wentworth", "NS", "CA", 45.6200, -63.5500, 90, 300, "", "Wentworth"),
    ("martock", "Ski Martock", "NS", "CA", 44.9200, -64.1700, 90, 260, "", "Martock"),
    ("marble_mountain", "Marble Mountain", "NL", "CA", 48.9400, -57.8300, 90, 600, "", "Marble-Mountain"),
    # ------------------------------------------------------------- Washington
    ("crystal_mountain_wa", "Crystal Mountain", "WA", "US", 46.9350, -121.4747, 1340, 2135, "washington/crystal-mountain-wa", "Crystal-Mountain-WA"),
    ("stevens_pass", "Stevens Pass", "WA", "US", 47.7450, -121.0900, 1240, 1780, "washington/stevens-pass-resort", "Stevens-Pass"),
    ("mt_baker", "Mt. Baker", "WA", "US", 48.8570, -121.6700, 1070, 1540, "washington/mt-baker", "Mount-Baker"),
    ("summit_snoqualmie", "The Summit at Snoqualmie", "WA", "US", 47.4200, -121.4100, 915, 1615, "washington/the-summit-at-snoqualmie", "Snoqualmie"),
    ("alpental", "Alpental", "WA", "US", 47.4447, -121.4253, 960, 1655, "washington/alpental", "Alpental"),
    ("white_pass", "White Pass", "WA", "US", 46.6400, -121.3900, 1370, 1830, "washington/white-pass", "White-Pass"),
    ("mission_ridge", "Mission Ridge", "WA", "US", 47.2900, -120.4000, 1390, 2070, "washington/mission-ridge", "Mission-Ridge"),
    ("49_degrees_north", "49 Degrees North", "WA", "US", 48.3000, -117.5600, 1190, 1756, "washington/49-degrees-north", "49-Degrees-North"),
    ("mt_spokane", "Mt. Spokane", "WA", "US", 47.9200, -117.1000, 1160, 1793, "washington/mt-spokane-ski-and-snowboard-park", "Mount-Spokane"),
    ("bluewood", "Bluewood", "WA", "US", 46.0800, -117.8500, 1390, 1720, "washington/bluewood", "Bluewood"),
    # ----------------------------------------------------------------- Oregon
    ("mt_bachelor", "Mt. Bachelor", "OR", "US", 43.9790, -121.6880, 1740, 2765, "oregon/mt-bachelor", "Mount-Bachelor"),
    ("mt_hood_meadows", "Mt. Hood Meadows", "OR", "US", 45.3300, -121.6650, 1380, 2225, "oregon/mt-hood-meadows", "Mount-Hood-Meadows"),
    ("timberline", "Timberline Lodge", "OR", "US", 45.3300, -121.7100, 1500, 2600, "oregon/timberline-lodge", "Timberline-Lodge"),
    ("mt_hood_skibowl", "Mt. Hood Skibowl", "OR", "US", 45.3000, -121.7700, 1100, 1550, "oregon/mt-hood-ski-bowl", "Mount-Hood-Skibowl"),
    ("mt_ashland", "Mt. Ashland", "OR", "US", 42.0800, -122.7100, 1935, 2295, "oregon/mount-ashland", "Mount-Ashland"),
    ("hoodoo", "Hoodoo", "OR", "US", 44.4100, -121.8700, 1440, 1740, "oregon/hoodoo-ski-area", "Hoodoo"),
    ("willamette_pass", "Willamette Pass", "OR", "US", 43.6000, -122.0300, 1560, 2030, "oregon/willamette-pass", "Willamette-Pass"),
    ("anthony_lakes", "Anthony Lakes", "OR", "US", 44.9600, -118.2300, 2160, 2440, "oregon/anthony-lakes-mountain-resort", "Anthony-Lakes"),
    ("cooper_spur", "Cooper Spur", "OR", "US", 45.4100, -121.6200, 1080, 1310, "oregon/cooper-spur", ""),
    # ------------------------------------------------------------- California
    ("palisades_tahoe", "Palisades Tahoe", "CA", "US", 39.1970, -120.2350, 1890, 2750, "california/palisades-tahoe", "Palisades-Tahoe"),
    ("mammoth", "Mammoth Mountain", "CA", "US", 37.6300, -119.0300, 2425, 3370, "california/mammoth-mountain-ski-area", "Mammoth-Mountain"),
    ("heavenly", "Heavenly", "CA", "US", 38.9350, -119.9400, 1995, 3060, "california/heavenly-mountain-resort", "Heavenly-Mountain-Resort"),
    ("northstar", "Northstar", "CA", "US", 39.2700, -120.1200, 1930, 2625, "california/northstar-california", "Northstar-at-Tahoe"),
    ("kirkwood", "Kirkwood", "CA", "US", 38.6850, -120.0650, 2375, 2985, "california/kirkwood", "Kirkwood"),
    ("sugar_bowl", "Sugar Bowl", "CA", "US", 39.3000, -120.3350, 2100, 2550, "california/sugar-bowl-resort", "Sugar-Bowl"),
    ("sierra_at_tahoe", "Sierra-at-Tahoe", "CA", "US", 38.8000, -120.0800, 1985, 2700, "california/sierra-at-tahoe", "Sierra-at-Tahoe"),
    ("homewood", "Homewood", "CA", "US", 39.0800, -120.1600, 1900, 2390, "california/homewood-mountain-resort", "Homewood"),
    ("boreal", "Boreal", "CA", "US", 39.3350, -120.3500, 2195, 2300, "california/boreal", "Boreal"),
    ("donner_ski_ranch", "Donner Ski Ranch", "CA", "US", 39.3200, -120.3300, 2140, 2390, "california/donner-ski-ranch", "Donner-Ski-Ranch"),
    ("soda_springs", "Soda Springs", "CA", "US", 39.3200, -120.3800, 2030, 2210, "california/soda-springs", ""),
    ("tahoe_donner", "Tahoe Donner", "CA", "US", 39.3500, -120.2700, 2050, 2240, "california/tahoe-donner", ""),
    ("bear_valley", "Bear Valley", "CA", "US", 38.4900, -120.0000, 2010, 2600, "california/bear-valley", "Bear-Valley"),
    ("dodge_ridge", "Dodge Ridge", "CA", "US", 38.1900, -119.9500, 2010, 2500, "california/dodge-ridge", "Dodge-Ridge"),
    ("june_mountain", "June Mountain", "CA", "US", 37.7700, -119.0900, 2290, 3090, "california/june-mountain", "June-Mountain"),
    ("china_peak", "China Peak", "CA", "US", 37.2350, -119.1550, 2160, 2600, "california/ski-china-peak", "China-Peak"),
    ("badger_pass", "Yosemite Ski & Snowboard Area", "CA", "US", 37.6600, -119.6600, 2190, 2440, "california/badger-pass", "Badger-Pass"),
    ("mt_shasta", "Mt. Shasta Ski Park", "CA", "US", 41.3200, -122.2000, 1660, 2050, "california/mount-shasta-board-ski-park", "Mount-Shasta-Ski-Park"),
    ("bear_mountain_ca", "Bear Mountain", "CA", "US", 34.2270, -116.8600, 2135, 2685, "california/bear-mountain", "Bear-Mountain"),
    ("snow_summit", "Snow Summit", "CA", "US", 34.2300, -116.8900, 2140, 2500, "california/snow-summit", "Snow-Summit"),
    ("snow_valley_ca", "Snow Valley", "CA", "US", 34.2250, -117.0300, 2040, 2390, "california/snow-valley", "Snow-Valley"),
    ("mountain_high", "Mountain High", "CA", "US", 34.3750, -117.6900, 2050, 2510, "california/mountain-high", "Mountain-High"),
    ("mt_baldy_ca", "Mt. Baldy", "CA", "US", 34.2700, -117.6300, 1980, 2620, "california/mt-baldy", ""),
    # ----------------------------------------------------------------- Nevada
    ("mt_rose", "Mt. Rose", "NV", "US", 39.3150, -119.8850, 2520, 2955, "nevada/mt-rose-ski-tahoe", "Mount-Rose"),
    ("diamond_peak", "Diamond Peak", "NV", "US", 39.2500, -119.9200, 2040, 2600, "nevada/diamond-peak", "Diamond-Peak"),
    ("lee_canyon", "Lee Canyon", "NV", "US", 36.3000, -115.6800, 2590, 3290, "nevada/lee-canyon", "Lee-Canyon"),
    ("elko_snobowl", "Elko SnoBowl", "NV", "US", 40.8500, -115.7000, 1950, 2200, "nevada/elko-snobowl", ""),
    # ------------------------------------------------------------------- Utah
    ("alta", "Alta", "UT", "US", 40.5880, -111.6380, 2600, 3215, "utah/alta-ski-area", "Alta"),
    ("snowbird", "Snowbird", "UT", "US", 40.5810, -111.6560, 2365, 3350, "utah/snowbird", "Snowbird"),
    ("brighton", "Brighton", "UT", "US", 40.5980, -111.5830, 2670, 3200, "utah/brighton-resort", "Brighton"),
    ("solitude", "Solitude", "UT", "US", 40.6200, -111.5900, 2400, 3115, "utah/solitude-mountain-resort", "Solitude"),
    ("park_city", "Park City", "UT", "US", 40.6500, -111.5100, 2080, 3050, "utah/park-city-mountain-resort", "Park-City"),
    ("deer_valley", "Deer Valley", "UT", "US", 40.6200, -111.4800, 2000, 2920, "utah/deer-valley-resort", "Deer-Valley"),
    ("snowbasin", "Snowbasin", "UT", "US", 41.2160, -111.8570, 1950, 2850, "utah/snowbasin", "Snowbasin"),
    ("powder_mountain", "Powder Mountain", "UT", "US", 41.3800, -111.7800, 2100, 2830, "utah/powder-mountain", "Powder-Mountain"),
    ("sundance", "Sundance", "UT", "US", 40.3900, -111.5800, 1860, 2515, "utah/sundance", "Sundance"),
    ("brian_head", "Brian Head", "UT", "US", 37.7000, -112.8500, 2925, 3445, "utah/brian-head-resort", "Brian-Head"),
    ("beaver_mountain", "Beaver Mountain", "UT", "US", 41.9700, -111.5400, 2190, 2700, "utah/beaver-mountain", "Beaver-Mountain"),
    ("eagle_point", "Eagle Point", "UT", "US", 38.3200, -112.3800, 2800, 3200, "utah/eagle-point", "Eagle-Point"),
    ("nordic_valley", "Nordic Valley", "UT", "US", 41.3100, -111.8600, 1650, 2010, "utah/wolf-creek", "Nordic-Valley"),
    # --------------------------------------------------------------- Colorado
    ("vail", "Vail", "CO", "US", 39.6060, -106.3550, 2475, 3525, "colorado/vail", "Vail"),
    ("breckenridge", "Breckenridge", "CO", "US", 39.4800, -106.0700, 2925, 3915, "colorado/breckenridge", "Breckenridge"),
    ("aspen_snowmass", "Aspen Snowmass", "CO", "US", 39.2090, -106.9500, 2470, 3810, "colorado/aspen-snowmass", "Snowmass"),
    ("beaver_creek", "Beaver Creek", "CO", "US", 39.6000, -106.5200, 2470, 3490, "colorado/beaver-creek", "Beaver-Creek"),
    ("keystone", "Keystone", "CO", "US", 39.6000, -105.9500, 2830, 3650, "colorado/keystone", "Keystone-Resort"),
    ("copper_mountain", "Copper Mountain", "CO", "US", 39.5000, -106.1500, 2925, 3750, "colorado/copper-mountain-resort", "Copper-Mountain"),
    ("arapahoe_basin", "Arapahoe Basin", "CO", "US", 39.6420, -105.8720, 3290, 3980, "colorado/arapahoe-basin-ski-area", "Arapahoe-Basin"),
    ("loveland", "Loveland", "CO", "US", 39.6800, -105.9000, 3230, 3990, "colorado/loveland", "Loveland"),
    ("winter_park", "Winter Park", "CO", "US", 39.8870, -105.7600, 2745, 3675, "colorado/winter-park-resort", "Winter-Park"),
    ("steamboat", "Steamboat", "CO", "US", 40.4570, -106.8000, 2100, 3220, "colorado/steamboat", "Steamboat"),
    ("telluride", "Telluride", "CO", "US", 37.9360, -107.8460, 2660, 3830, "colorado/telluride", "Telluride"),
    ("crested_butte", "Crested Butte", "CO", "US", 38.9000, -106.9650, 2775, 3710, "colorado/crested-butte-mountain-resort", "Crested-Butte-Mountain"),
    ("wolf_creek_co", "Wolf Creek", "CO", "US", 37.4700, -106.7900, 3150, 3630, "colorado/wolf-creek-ski-area", "Wolf-Creek-Ski-Area"),
    ("purgatory", "Purgatory", "CO", "US", 37.6300, -107.8100, 2680, 3290, "colorado/durango-mountain-resort", "Durango-Mountain-Resort"),
    ("monarch", "Monarch Mountain", "CO", "US", 38.5100, -106.3300, 3290, 3640, "colorado/monarch-mountain", "Monarch-Ski-Area"),
    ("eldora", "Eldora", "CO", "US", 39.9400, -105.5800, 2800, 3230, "colorado/eldora-mountain-resort", "Eldora-Mountain-Resort"),
    ("ski_cooper", "Ski Cooper", "CO", "US", 39.3600, -106.3000, 3200, 3565, "colorado/ski-cooper", "Ski-Cooper"),
    ("powderhorn", "Powderhorn", "CO", "US", 39.0700, -108.1500, 2490, 2990, "colorado/powderhorn", "Powderhorn"),
    ("sunlight", "Sunlight Mountain", "CO", "US", 39.4000, -107.3400, 2400, 2990, "colorado/sunlight-mountain-resort", "Sunlight-Mountain-Resort"),
    ("silverton", "Silverton Mountain", "CO", "US", 37.8800, -107.6650, 3170, 4130, "colorado/silverton-mountain", "Silverton-Mountain"),
    ("echo_mountain", "Echo Mountain", "CO", "US", 39.6800, -105.5200, 3200, 3290, "colorado/echo-mountain", "EchoMountain"),
    ("granby_ranch", "Granby Ranch", "CO", "US", 40.0400, -105.9000, 2490, 2800, "colorado/ski-granby-ranch", ""),
    ("howelsen_hill", "Howelsen Hill", "CO", "US", 40.4800, -106.8400, 2050, 2240, "colorado/howelsen-hill", "HowelsenHill"),
    # ----------------------------------------------------------------- Idaho
    ("sun_valley", "Sun Valley", "ID", "US", 43.6800, -114.3600, 1750, 2790, "idaho/sun-valley", "Sun-Valley"),
    ("schweitzer", "Schweitzer", "ID", "US", 48.3680, -116.6200, 1210, 1950, "idaho/schweitzer", "Schweitzer"),
    ("tamarack", "Tamarack", "ID", "US", 44.6700, -116.1200, 1490, 2350, "idaho/tamarack-resort", "Tamarack"),
    ("bogus_basin", "Bogus Basin", "ID", "US", 43.7650, -116.1000, 1760, 2310, "idaho/bogus-basin", "Bogus-Basin"),
    ("brundage", "Brundage", "ID", "US", 45.0050, -116.1550, 1760, 2320, "idaho/brundage-mountain-resort", "Brundage"),
    ("silver_mountain", "Silver Mountain", "ID", "US", 47.5000, -116.1100, 1250, 1890, "idaho/silver-mountain", "Silver-Mountain"),
    ("lookout_pass", "Lookout Pass", "ID", "US", 47.4550, -115.7000, 1370, 1720, "idaho/lookout-pass-ski-area", "Lookout-Pass"),
    ("pebble_creek", "Pebble Creek", "ID", "US", 42.7700, -112.1000, 1920, 2620, "idaho/pebble-creek-ski-area", "Pebble-Creek"),
    ("pomerelle", "Pomerelle", "ID", "US", 42.3200, -113.6000, 2440, 2750, "idaho/pomerelle-mountain-resort", "Pomerelle"),
    ("soldier_mountain", "Soldier Mountain", "ID", "US", 43.4800, -114.8300, 1770, 2200, "idaho/soldier-mountain-ski-area", "Soldier-Mountain"),
    ("magic_mountain_id", "Magic Mountain", "ID", "US", 42.1800, -114.2900, 1980, 2300, "idaho/magic-mountain-ski-area", ""),
    # --------------------------------------------------------------- Montana
    ("big_sky", "Big Sky", "MT", "US", 45.2850, -111.4000, 2070, 3400, "montana/big-sky-resort", "Big-Sky"),
    ("whitefish", "Whitefish Mountain", "MT", "US", 48.4800, -114.3500, 1360, 2090, "montana/whitefish-mountain-resort", "Whitefish"),
    ("bridger_bowl", "Bridger Bowl", "MT", "US", 45.8170, -110.8970, 1860, 2610, "montana/bridger-bowl", "Bridger-Bowl"),
    ("red_lodge", "Red Lodge Mountain", "MT", "US", 45.1900, -109.3400, 2150, 2840, "montana/red-lodge-mountain", "Red-Lodge"),
    ("montana_snowbowl", "Montana Snowbowl", "MT", "US", 47.0100, -114.0000, 1520, 2320, "montana/montana-snowbowl", "Montana-Snowbowl"),
    ("discovery", "Discovery", "MT", "US", 46.2500, -113.2400, 1980, 2480, "montana/discovery-ski-area", "Discovery"),
    ("lost_trail", "Lost Trail", "MT", "US", 45.6900, -113.9500, 1980, 2560, "montana/lost-trail-powder-mtn", "Lost-Trail"),
    ("showdown", "Showdown", "MT", "US", 46.8400, -110.7000, 2070, 2490, "montana/showdown-ski-area", "Showdown"),
    ("great_divide", "Great Divide", "MT", "US", 46.7500, -112.3200, 1750, 2200, "montana/great-divide", "Great-Divide"),
    ("blacktail", "Blacktail Mountain", "MT", "US", 48.0100, -114.3700, 1720, 2060, "montana/blacktail-mountain-ski-area", "Blacktail-Mountain"),
    ("maverick", "Maverick Mountain", "MT", "US", 45.4300, -113.1300, 2160, 2650, "montana/maverick-mountain", ""),
    ("teton_pass_mt", "Teton Pass", "MT", "US", 47.9200, -112.8000, 1740, 2190, "montana/teton-pass-ski-area", ""),
    # --------------------------------------------------------------- Wyoming
    ("jackson_hole", "Jackson Hole", "WY", "US", 43.5875, -110.8279, 1925, 3185, "wyoming/jackson-hole", "Jackson-Hole"),
    ("grand_targhee", "Grand Targhee", "WY", "US", 43.7900, -110.9580, 2370, 3045, "wyoming/grand-targhee-resort", "Grand-Targhee"),
    ("snow_king", "Snow King", "WY", "US", 43.4700, -110.7600, 1890, 2390, "wyoming/snow-king-resort", "Snow-King"),
    ("white_pine", "White Pine", "WY", "US", 42.9700, -109.7900, 2520, 2740, "wyoming/white-pine-ski-area", ""),
    ("snowy_range", "Snowy Range", "WY", "US", 41.3500, -106.1800, 2620, 2900, "wyoming/snowy-range-ski-recreation-area", ""),
    ("sleeping_giant", "Sleeping Giant", "WY", "US", 44.4900, -109.6200, 2040, 2330, "wyoming/sleeping-giant-ski-resort", ""),
    ("hogadon", "Hogadon Basin", "WY", "US", 42.7400, -106.3300, 2470, 2550, "wyoming/hogadon", ""),
    ("meadowlark", "Meadowlark", "WY", "US", 44.1700, -107.2100, 2600, 2900, "wyoming/meadowlark-ski-lodge", ""),
    # ------------------------------------------------------------ New Mexico
    ("taos", "Taos Ski Valley", "NM", "US", 36.5960, -105.4500, 2805, 3800, "new-mexico/taos-ski-valley", "Taos"),
    ("ski_santa_fe", "Ski Santa Fe", "NM", "US", 35.8000, -105.8000, 3150, 3680, "new-mexico/ski-santa-fe", "Santa-Fe"),
    ("angel_fire", "Angel Fire", "NM", "US", 36.3900, -105.2900, 2600, 3260, "new-mexico/angel-fire-resort", "Angel-Fire"),
    ("red_river", "Red River", "NM", "US", 36.7100, -105.4100, 2650, 3150, "new-mexico/red-river", "Red-River"),
    ("ski_apache", "Ski Apache", "NM", "US", 33.4000, -105.7900, 2940, 3500, "new-mexico/ski-apache", "Ski-Apache"),
    ("sipapu", "Sipapu", "NM", "US", 36.1500, -105.5500, 2500, 2800, "new-mexico/sipapu-ski-and-summer-resort", ""),
    ("pajarito", "Pajarito Mountain", "NM", "US", 35.8900, -106.3900, 2800, 3200, "new-mexico/pajarito-mountain-ski-area", ""),
    ("sandia_peak", "Sandia Peak", "NM", "US", 35.2100, -106.4100, 2645, 3163, "new-mexico/sandia-peak", ""),
    # ------------------------------------------------------ Arizona / Alaska
    ("arizona_snowbowl", "Arizona Snowbowl", "AZ", "US", 35.3300, -111.7100, 2805, 3505, "arizona/arizona-snowbowl", "Arizona-Snowbowl"),
    ("sunrise_park", "Sunrise Park", "AZ", "US", 33.9000, -109.5600, 2830, 3350, "arizona/sunrise-park-resort", "Sunrise-Park"),
    ("alyeska", "Alyeska", "AK", "US", 60.9700, -149.1000, 75, 840, "alaska/alyeska-resort", "Alyeska"),
)

REGION_NAMES = {
    "AB": "Alberta", "BC": "British Columbia", "SK": "Saskatchewan", "MB": "Manitoba",
    "ON": "Ontario", "QC": "Quebec", "NB": "New Brunswick", "NS": "Nova Scotia",
    "NL": "Newfoundland", "YT": "Yukon", "WA": "Washington", "OR": "Oregon",
    "CA": "California", "NV": "Nevada", "UT": "Utah", "CO": "Colorado", "ID": "Idaho",
    "MT": "Montana", "WY": "Wyoming", "NM": "New Mexico", "AZ": "Arizona", "AK": "Alaska",
}

CATALOG: dict[str, Resort] = {
    row[0]: Resort(
        id=row[0], name=row[1], latitude=row[4], longitude=row[5],
        base_elevation=row[6], summit_elevation=row[7],
        onthesnow=row[8], snowforecast=row[9], region=row[2], country=row[3],
    )
    for row in _ROWS
}
COUNTRY_ORDER = {"CA": 0, "US": 1}


def catalog_label(r: Resort) -> str:
    return f"{r.name} — {REGION_NAMES.get(r.region, r.region)}"


def sorted_catalog() -> list[Resort]:
    return sorted(
        CATALOG.values(),
        key=lambda r: (COUNTRY_ORDER.get(r.country, 9), REGION_NAMES.get(r.region, r.region), r.name),
    )
