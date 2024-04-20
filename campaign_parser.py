from lxml import etree
import os
import pandas as pd
from tqdm import tqdm
import math


UNITS_PER_LIGHTYEAR = 2000

CONDITION_EFFECTS = {
    'ruins_scattered': { 'tech': 1},
    'ruins_widespread': { 'tech': 2},
    'ruins_extensive': { 'tech': 3},
    'ruins_vast': { 'tech': 4},
    'ore_sparse': { 'ore': 1},
    'ore_moderate': { 'ore': 2},
    'ore_abundant': { 'ore': 3},
    'ore_rich': { 'ore': 4},
    'ore_ultrarich': { 'ore': 5},
    'rare_ore_sparse': { 'rare_ore': 1},
    'rare_ore_moderate': { 'rare_ore': 2},
    'rare_ore_abundant': { 'rare_ore': 3},
    'rare_ore_rich': { 'rare_ore': 4},
    'rare_ore_ultrarich': { 'rare_ore': 5},
    'volatiles_trace': { 'volatiles': 1},
    'volatiles_diffuse': { 'volatiles': 2},
    'volatiles_abundant': { 'volatiles': 3},
    'volatiles_plentiful': { 'volatiles': 4},
    'organics_trace': { 'organics': 1},
    'organics_common': { 'organics': 2},
    'organics_abundant': { 'organics': 3},
    'organics_plentiful': { 'organics': 4},
    'farmland_poor': { 'food': 1},
    'farmland_adequate': { 'food': 2},
    'farmland_rich': { 'food': 3},
    'farmland_bountiful': { 'food': 4},
    'solar_array': { 'food': 2 }, # Also counters Hot and Poor Light
    'habitable': { 'hazard_rating': -0.25, 'growth': 4 },
    'decivilized': { 'hazard_rating': 0.25, 'stability': -2, 'decivilization': 1 }, # TODO: +size growth
    'cold': { 'hazard_rating': 0.25, 'temperature': 1 },
    'very_cold': { 'hazard_rating': 0.50, 'temperature': 0 },
    'hot': { 'hazard_rating': 0.25, 'temperature': 3 },
    'very_hot': { 'hazard_rating': 0.50, 'temperature': 4 },
    'tectonic_activity': { 'hazard_rating': 0.25, 'tectonics': 1 },
    'extreme_tectonic_activity': { 'hazard_rating': 0.50, 'tectonics': 2 },
    'no_atmosphere': { 'hazard_rating': 0.50, 'atmosphere': 0 },
    'thin_atmosphere': { 'hazard_rating': 0.25, 'atmosphere': 1 },
    'toxic_atmosphere': { 'hazard_rating': 0.50, 'atmosphere': 4 },
    'dense_atmosphere': { 'hazard_rating': 0.50, 'atmosphere': 3 },
    'mild_climate': { 'hazard_rating': -0.25}, # Also a growth bonus
    'extreme_weather': { 'hazard_rating': 0.25},
    'low_gravity': { 'hazard_rating': 0.25, 'gravity': 0 },
    'high_gravity': { 'hazard_rating': 0.50, 'gravity': 2 },
    'irradiated': { 'hazard_rating': 0.50},
    'inimical_biosphere': { 'hazard_rating': 0.25},
    'water_surface': { 'hazard_rating': 0.25},
    'poor_light': { 'hazard_rating': 0.25},
    'dark': { 'hazard_rating': 0.50},
    'meteor_impacts': { 'hazard_rating': 0.50},
    'pollution': { 'hazard_rating': 0.25},
}
HAZARD_NAMES = {
    'habitable': 'Habitable',
    'decivilized': 'Decivilized',
    'cold': 'Cold',
    'very_cold': 'Extreme Cold',
    'hot': 'Hot',
    'very_hot': 'Extreme Heat',
    'tectonic_activity': 'Tectonic Activity',
    'extreme_tectonic_activity': 'Extreme Tectonic Activity',
    'no_atmosphere': 'No Atmosphere',
    'thin_atmosphere': 'Thin Atmosphere',
    'toxic_atmosphere': 'Toxic Atmosphere',
    'dense_atmosphere': 'Dense Atmosphere',
    'mild_climate': 'Mild Climate',
    'extreme_weather': 'Extreme Weather',
    'low_gravity': 'Low Gravity',
    'high_gravity': 'High Gravity',
    'irradiated': 'Irradiated',
    'inimical_biosphere': 'Inimical Biosphere',
    'water_surface': 'Water-covered Surface',
    'poor_light': 'Poor Light',
    'dark': 'Darkness',
    'meteor_impacts': 'Meteor Impacts',
    'pollution': 'Pollution',
}

def euclidean_distance(system1, system2):
    return math.sqrt((system1['x'] - system2['x']) ** 2 + (system1['y'] - system2['y']) ** 2)

def find_nearby_systems(sector, distance_threshold=20000):
    cryosleeper_systems = [system for system in sector if system['Cryosleeper']]
    hypershunt_systems = [system for system in sector if system['Hypershunt']]
    
    for system in sector:
        cryo_flag = False
        shunt_flag = False
        for cryosleeper in cryosleeper_systems:
            if euclidean_distance(system, cryosleeper) <= distance_threshold:
                cryo_flag = True
                break
        for hypershunt in hypershunt_systems:
            if euclidean_distance(system, hypershunt) <= distance_threshold:
                shunt_flag = True
                break
        system['cryo_nearby'] = cryo_flag
        system['shunt_nearby'] = shunt_flag
    return sector

# Define a function to recursively extract system data
def extract_system_data(system_element):

    #pprint.pprint(etree.tostring(system_element, encoding='unicode'))
    system = {}

    # Extract system name from the Sstm attribute "bN"
    system["name"] = system_element.get("bN")

    # Initialize a list to store market data
    system["planets"] = []

    tags = [st.text for st in system_element.findall("tags/st")]

    #print(system["name"])
    #print(tags)

    if "has_coronal_tap" in tags:
        system['Hypershunt'] = True
    else:
        system['Hypershunt'] = False
    if "theme_derelict_cryosleeper" in tags:
        system['Cryosleeper'] = True
    else:
        system['Cryosleeper'] = False

    # Find the location element
    l_element = system_element.find(".//l")

    if l_element is not None:
        x, y = map(float, l_element.text.split('|'))
        system["x"] = float(x)
        system["y"] = float(y)

    # Check if planets exist
    planet_elements = system_element.findall("o/saved/Plnt/market/..")  # Find parent of <market>
    for planet_element in planet_elements:
        planet = {}
        planet["type"] = planet_element.find("type").text  # Extract planet type
        planet["name"] = planet_element.find("market/name").text  # Extract planet name
        planet["features"] = [st.text for st in planet_element.findall("market/cond/st")]  # Extract planet features
        system["planets"].append(planet)

    #get comm_relay
    station_elements = [st.text for st in system_element.findall("o/saved/CCEnt/tags/st")]
    for station_element in station_elements:
        if "comm_relay" in station_element:
            if not "makeshift" in station_element:
                system['Relay'] = True
                return system
    system['Relay'] = False
    return system



# Define a function to recursively extract all systems data
def extract_all_systems(root_element):
    sector = []

    #construct coords dict
    #coords = construct_coords_dictionary(root_element)
    #system_elements = root_element.findall(".//con/systems/Sstm or .//s[@cl='Sstm'] or .//where[@cl='Sstm'] or .//cL[@cl='Sstm']")

    # Find all systems in the XML
    system_elements = root_element.findall(".//con/systems/Sstm")#| .//con/systems/")
    #print(len(system_elements))
    system_elements.extend(root_element.findall(".//s[@cl='Sstm']"))
    #print(len(system_elements))
    system_elements.extend(root_element.findall(".//where[@cl='Sstm']"))
    #print(len(system_elements))
    system_elements.extend(root_element.findall(".//cL[@cl='Sstm']"))
    #print(len(system_elements))

    for system_element in system_elements:
        system_data = extract_system_data(system_element)
        # Skip systems without names
        if system_data["name"] is not None:
            #print(system_data["name"])
            sector.append(system_data)

    sector = find_nearby_systems(sector)

    return sector

def get_stats(system):
    for planet in system['planets']:
        planet['stats'] = {'hazard_rating':1}
        if 'solar_array' in planet['features']:
            try:
                planet['features'].remove('hot')
                planet['features'].remove('poor_light')
            except ValueError:
                pass

        for keyword in planet['features']:
            effects = CONDITION_EFFECTS[keyword]
            for cond, value in effects.items():
                if cond in planet['stats']:
                    planet['stats'][cond] += value
                else:
                    planet['stats'][cond] = value

        # apply special items
        if ('habitable' not in planet['features']) and (planet['type'] != 'gas_giant'):
            if 'ore' in planet['stats']:
                planet['stats']['ore'] += 3
            if 'rare_ore' in planet['stats']:
                planet['stats']['rare_ore'] += 3
            if 'organics' in planet['stats']:
                planet['stats']['organics'] += 3

        if (planet['type'] == 'gas_giant') or (planet['type'] == 'ice_giant'):
            if 'volatiles' in planet['stats']:
                planet['stats']['volatiles'] += 3

        if ('rare_ore' not in planet['stats']) and ('volatiles' not in planet['stats']):
            if 'food' in planet['stats']:
                planet['stats']['food'] += 2

        # now score
        #total_production = 0
        #for stat in relevant_stats:
        #    if stat in planet['stats']:
        #        total_production += planet['stats'][stat]
        #
        #    planet['score'] = total_production / planet['stats']['hazard_rating']

    return system

def parse_campaign_file(file_path):
    # Parse the XML file
    tree = etree.parse(file_path)
    root = tree.getroot()

    seed = root.find(".//seedString").text

    # Extract all systems data
    sector = extract_all_systems(root)
    for system in sector:
        if system["name"]:  # Check if the system has a name
            system = get_stats(system)

    return seed, sector
"""
def construct_coords_dictionary(root):
    coords = {}
    # Find all elements with tag name 'l' or 'lIH' that have a 'z' attribute
    l_elements = root.xpath('//l[@z] | //lIH[@z]')
    # Iterate over each selected element
    for coord in l_elements:
        # Get the value of the 'z' attribute
        z_value = coord.get('z')
        # Add an entry to the coords dictionary
        coords[z_value] = coord.text
    return coords
"""


relevant_stats = ['food','ore','rare_ore','volatiles','organics']

# Define the directory containing the campaign.xml files
saves_directory = r"C:\Program Files (x86)\Fractal Softworks\Starsector\saves"
#saves_directory = r"C:\Program Files (x86)\Fractal Softworks\Starsector\saves\save_auto103457044250_1482954649063795460"

# Initialize empty lists to store data
sectors = []
# Flatten the nested dictionary structure
flattened_sectors = []
# Iterate over all directories and files in the "saves" directory
file_counter = 0
for root, dirs, files in tqdm(os.walk(saves_directory), desc="Parsing XML Files"):
    for file in files:
        if file == "campaign.xml":

            file_counter += 1
            # Generate the file path
            file_path = os.path.join(root, file)
            
            # Parse the campaign file to generate a sector
            seed, sector = parse_campaign_file(file_path)
            
            # Add sector to list
            sectors.append(sector)

            for system in sector:
                #if system['name']== 'Alpha Yomi':
                #    print(system)

                if not (system['Relay'] & system['cryo_nearby'] & system['shunt_nearby']):
                    continue

                if not system['planets']:
                        flattened_sectors.append({
                            "Seed": seed,
                            "Save Directory": os.path.basename(os.path.dirname(file_path)),
                            "X": system["x"],
                            "Y": system["y"],
                            "System Name": system["name"],
                            "Cryosleeper": system['Cryosleeper'],
                            "Hypershunt": system['Hypershunt'],
                            "Relay": system['Relay'],
                            "Cryosleeper In Range": system['cryo_nearby'],
                            "Hypershunt In Range": system['shunt_nearby'],
                            "Planet Name": 'None'
                        })
                for planet in system["planets"]:
                        flattened_sectors.append({
                            "Seed": seed,
                            "Save Directory": os.path.basename(os.path.dirname(file_path)),
                            "X": system["x"],
                            "Y": system["y"],
                            "System Name": system["name"],
                            "Cryosleeper": system['Cryosleeper'],
                            "Hypershunt": system['Hypershunt'],
                            "Relay": system['Relay'],
                            "Cryosleeper In Range": system['cryo_nearby'],
                            "Hypershunt In Range": system['shunt_nearby'],
                            "Planet Name": planet["name"],
                            "Planet Type": planet.get("type", ""),
                            "Planet Features": ", ".join(planet.get("features", [])),
                            **planet["stats"],  # Add all planet stats as separate columns
                            #"Score": planet["score"]
                        })

    # Break the loop if 10 files have been processed
    #if file_counter == 100:
    #    break
# Create a DataFrame from the flattened data
df = pd.DataFrame(flattened_sectors)


#print(df.loc[(df['Save Directory']=='save_auto100045156751_3770330867970133603')])#

# Print the DataFrame
print(df.loc[df['Cryosleeper'], ['Save Directory','System Name']].drop_duplicates().value_counts().value_counts())
print(df.loc[df['Hypershunt'], ['Save Directory','System Name']].drop_duplicates().value_counts().value_counts())
print(df.loc[df['Hypershunt'], ['Save Directory','System Name']].drop_duplicates().value_counts().value_counts())

print(df.loc[df['Hypershunt'], ['Save Directory','System Name']].drop_duplicates())
print(df.describe())
df.to_csv("C:\Program Files (x86)\Fractal Softworks\Starsector\saves\parsed_saves.csv")