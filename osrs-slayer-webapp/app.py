from flask import Flask, render_template, request, jsonify
from database import SlayerDatabase
import json
import math

app = Flask(__name__)
db = SlayerDatabase()

@app.route('/')
def index():
    return render_template('index.html')

# API Routes
@app.route('/api/monsters', methods=['GET'])
def get_monsters():
    monsters = db.get_all_monsters()
    return jsonify(monsters)

@app.route('/api/monsters', methods=['POST'])
def add_monster():
    data = request.json
    name = data.get('name')
    kill_limit = data.get('kill_limit', -1)
    task_ids = data.get('task_ids', [])
    locations = data.get('locations', [])
    
    if not name:
        return jsonify({'success': False, 'message': 'Monster name required'}), 400
    
    if not task_ids:
        return jsonify({'success': False, 'message': 'At least one task must be selected'}), 400
    
    success, message = db.add_monster(name, kill_limit, task_ids, locations)
    return jsonify({'success': success, 'message': message})

@app.route('/api/monsters/<int:monster_id>/drop-rate', methods=['PUT'])
def update_monster_drop_rate(monster_id):
    data = request.json
    new_kill_limit = data.get('kill_limit')
    
    if new_kill_limit is None:
        return jsonify({'success': False, 'message': 'Kill limit required'}), 400
    
    success, message = db.update_monster_drop_rate(monster_id, new_kill_limit)
    return jsonify({'success': success, 'message': message})

@app.route('/api/monsters/<int:monster_id>/kills', methods=['POST'])
def record_kills(monster_id):
    data = request.json
    kills = data.get('kills', 0)
    
    if kills <= 0:
        return jsonify({'success': False, 'message': 'Invalid kill count'}), 400
    
    db.record_kills(monster_id, kills)
    return jsonify({'success': True, 'message': f'Recorded {kills} kills'})

@app.route('/api/slayer-masters', methods=['GET'])
def get_slayer_masters():
    player_info = db.get_all_player_data()
    player_info['combat_level'] = int(player_info.get('combat_level', 3))
    player_info['slayer_level'] = int(player_info.get('slayer_level', 1))

    masters = db.get_slayer_masters()
    
    # Add efficiency data for each master
    for master in masters:
        master['efficiency'] = db.calculate_master_efficiency(master['id'], player_info)
    
    return jsonify(masters)

@app.route('/api/slayer-masters/<int:master_id>/tasks', methods=['GET'])
def get_master_tasks(master_id):
    player_info = db.get_all_player_data()
    player_info['combat_level'] = int(player_info.get('combat_level', 3))
    player_info['slayer_level'] = int(player_info.get('slayer_level', 1))
    tasks = db.get_tasks_for_master(master_id, player_info)
    return jsonify(tasks)

@app.route('/api/all-tasks', methods=['GET'])
def get_all_tasks():
    tasks = db.get_all_tasks()
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
def add_task():
    data = request.json
    name = data.get('name')
    slayer_requirement = data.get('slayer_requirement', 1)
    
    if not name:
        return jsonify({'success': False, 'message': 'Task name required'}), 400
    
    success, message = db.add_task(name, slayer_requirement)
    return jsonify({'success': success, 'message': message})

@app.route('/api/block-task', methods=['POST'])
def block_task():
    data = request.json
    master_id = data.get('master_id')
    task_id = data.get('task_id')
    
    if not master_id or not task_id:
        return jsonify({'success': False, 'message': 'Invalid data'}), 400
    
    success = db.block_task(master_id, task_id)
    return jsonify({'success': success})

@app.route('/api/unblock-task', methods=['POST'])
def unblock_task():
    data = request.json
    master_id = data.get('master_id')
    task_id = data.get('task_id')
    
    if not master_id or not task_id:
        return jsonify({'success': False, 'message': 'Invalid data'}), 400
    
    success = db.unblock_task(master_id, task_id)
    return jsonify({'success': success})

@app.route('/api/player-data', methods=['GET'])
def get_player_data_all():
    data = db.get_all_player_data()
    return jsonify(data)


@app.route('/api/player-data', methods=['POST'])
def set_player_data_all():
    data = request.json
    for key, value in data.items():
        db.set_player_data(key, value)
    return jsonify({'success': True})

@app.route('/api/unlocks', methods=['GET'])
def get_unlocks():
    unlocks = db.get_all_unlocks()
    return jsonify(unlocks)

# Add some common tasks when first running
@app.route('/api/init-common-tasks', methods=['POST'])
def init_common_tasks():
    # Add common monsters first with their locations
    common_monsters = [
        ('Crawling Hand', 64, ['Slayer Tower', 'Catacombs of Kourend']),
        ('Cave Crawler', 128, ['Fremennik Slayer Dungeon', 'Lumbridge Swamp Caves']),
        ('Banshee', 512, ['Slayer Tower', 'Catacombs of Kourend']),
        ('Rock Slug', 512, ['Fremennik Slayer Dungeon', 'Lumbridge Swamp Caves']),
        ('Cockatrice', 512, ['Fremennik Slayer Dungeon']),
        ('Pyrefiend', 128, ['Fremennik Slayer Dungeon']),
        ('Basilisk', 512, ['Fremennik Slayer Dungeon', "Jormungand's Prison"]),
        ('Infernal Mage', 512, ['Slayer Tower']),
        ('Bloodveld', 128, ['Slayer Tower', 'Catacombs of Kourend', 'God Wars Dungeon', 'Stronghold Slayer Cave', 'Iorwerth Dungeon', 'Meiyerditch Laboratories']),
        ('Mutated Bloodveld', 128, ['Catacombs of Kourend', 'Iorwerth Dungeon', 'Meiyerditch Laboratories']),
        ('Jelly', 128, ['Fremennik Slayer Dungeon', 'Catacombs of Kourend', 'Ruins of Tapoyauik']),
        ('Turoth', 512, ['Fremennik Slayer Dungeon']),
        ('Cave Horror', 512, ['Mos Le\'Harmless Cave']),
        ('Aberrant Spectre', 512, ['Slayer Tower', 'Catacombs of Kourend', 'Stronghold Slayer Cave']),
        ('Dust Devil', 32768, ['Smoke Dungeon', 'Catacombs of Kourend']),
        ('Kurask', 1026, ['Fremennik Slayer Dungeon', 'Iorwerth Dungeon']),
        ('Skeletal Wyvern', 512, ['Asgarnian Ice Dungeon']),
        ('Gargoyle', 512, ['Slayer Tower']),
        ('Nechryael', 116, ['Slayer Tower', 'Catacombs of Kourend', 'Iorwerth Dungeon']),
        ('Greater Nechryael', 128, ['Catacombs of Kourend', 'Iorwerth Dungeon']),
        ('Abyssal Demon', 32000, ['Slayer Tower', 'Catacombs of Kourend', 'Abyssal Area']),
        ('Cave Kraken', 200, ['Kraken Cove']),
        ('Smoke Devil', 32768, ['Smoke Devil Dungeon']),
        ('Blue Dragon', 364, ['Taverley Dungeon', 'Ogre Enclave', 'Catacombs of Kourend', "Myths' Guild Dungeon", 'Isle of Souls Dungeon', 'Ruins of Tapoyauik']),
        ('Baby Blue Dragon', -1, ['Taverley Dungeon', "Myths' Guild Dungeon", 'Isle of Souls Dungeon', 'Ruins of Tapoyauik']),
        ('Red Dragon', 2731, ['Brimhaven Dungeon', 'Catacombs of Kourend', 'Forthos Dungeon', "Myths' Guild Dungeon"]),
        ('Baby Red Dragon', -1, ['Brimhaven Dungeon', 'Forthos Dungeon', "Myths' Guild Dungeon"]),
        ('Black Dragon', 128, ['Taverley Dungeon', "Evil Chicken's Lair", 'Catacombs of Kourend', "Myths' Guild Dungeon"]),
        ('Baby Black Dragon', -1, ['Taverley Dungeon', "Evil Chicken's Lair", "Myths' Guild Dungeon"]),
        ('Green Dragon', 364.1, ['Wilderness']),
        ('Bronze Dragon', 2048, ['Brimhaven Dungeon', 'Catacombs of Kourend']),
        ('Iron Dragon', 1024, ['Brimhaven Dungeon', 'Catacombs of Kourend', 'Isle of Souls Dungeon']),
        ('Steel Dragon', 512, ['Brimhaven Dungeon', 'Catacombs of Kourend']),
        ('Hellhound', 32768, ['Taverley Dungeon', 'Witchaven Dungeon', 'Catacombs of Kourend', 'Stronghold Slayer Cave', 'Karuulm Slayer Dungeon', 'Wilderness']),
        ('Greater Demon', 128, ['Brimhaven Dungeon', 'Catacombs of Kourend', 'Chasm of Fire', 'Isle of Souls Dungeon', 'Karuulm Slayer Dungeon', 'Wilderness']),
        ('Black Demon', 237.7, ['Taverley Dungeon', 'Brimhaven Dungeon', 'Catacombs of Kourend', 'Chasm of Fire', 'Wilderness']),
        ('Fire Giant', 287, ['Waterfall Dungeon', 'Brimhaven Dungeon', 'Catacombs of Kourend', 'Stronghold Slayer Cave', 'Isle of Souls Dungeon', "Giants' Den", 'Karuulm Slayer Dungeon']),
        ('Moss Giant', 150, ['Varrock Sewers', 'Wilderness', 'Brimhaven Dungeon', 'West Ardougne', 'Catacombs of Kourend']),
        ('Ice Giant', 16786, ['Wilderness', 'Asgarnian Ice Dungeon']),
        ('Ice Troll', 303.4, ['Trollheim']),
        ('Mountain Troll', 7060, ['Trollheim', 'Death Plateau', 'Troll Stronghold']),
        ('Kalphite Worker', 780.2, ['Kalphite Lair', 'Kalphite Cave']),
        ('Kalphite Soldier', 5461, ['Kalphite Lair', 'Kalphite Cave']),
        ('Kalphite Guardian', 237.4, ['Kalphite Lair', 'Kalphite Cave']),
        ('Dagannoth', 839.1, ['Lighthouse', 'Waterbirth Island', 'Catacombs of Kourend', "Jormungand's Prison"]),
        ('Ankou', 33.3, ['Stronghold of Security', 'Stronghold Slayer Cave', 'Catacombs of Kourend', 'Wilderness']),
        ('Suqah', 5.16, ['Lunar Isle']),
        ('Lizardman', 250, ['Lizardman Canyon', 'Lizardman Settlement', 'Battlefront', 'Kebos Swamp', 'Molch']),
        ('Lizardman Shaman', 3000, ['Lizardman Canyon', 'Lizardman Settlement', 'Molch']),
        ('Demonic gorilla', 1500, ['Crash Site Cavern']),
        ('King Black Dragon', 1000, ['Wilderness']),
        ('Brutal black dragon', 512, ['Catacombs of Kourend']),
        ('Brutal blue dragon', 128, ['Catacombs of Kourend', 'Ruins of Tapoyauik']),
        ('Vorkath', 5000, ['Ungael']),
        ('Brine rat', 512, ['Brine Rat Cavern']),
        ('Drake', 10000, ['Karuulm Slayer Dungeon']),
        ('Fossil Island Wyvern', 2000, ['Wyvern Cave']),
        ('Cerberus', 520, ['Taverley Dungeon']),
        ('Hydra', 10001, ['Karuulm Slayer Dungeon']),
        ('Kraken', 512, ['Kraken Cove']),
        ('Dark beast', 512, ['Mourner Tunnels', 'Iorwerth Dungeon']),
        ('Warped Jelly', 64, ['Catacombs of Kourend']),
        ('Kalphite Queen', 400, ['Kalphite Lair']),
        ('Lava dragon', 1092, ['Wilderness']),
        ('Lesser demon', 5461, ['Wilderness', 'Karamja Dungeon', 'Catacombs of Kourend']),
        ('Mithril dragon', 32768, ['Ancient Cavern']),
        ('Adamant dragon', 1000, ['Lithkren Vault']),
        ('Rune dragon', 800, ['Lithkren Vault']),
        ('Abyssal Sire', 1066, ['Abyssal Nexus']),
        ('Alchemical Hydra', 1500, ['Karuulm Slayer Dungeon']),
        ('Scorpion', -1, ['Wilderness', 'Al Kharid mine']),
        ('Spider', -1, ['Wilderness', 'Lumbridge']),
        ('Bear', -1, ['Wilderness', 'East Ardougne']),
        ('Skeleton', 1650000, ['Wilderness', 'Edgeville Dungeon', 'Taverley Dungeon']),
        ('Hill Giant', 128, ['Wilderness', 'Edgeville Dungeon']),
        ('Ice warrior', 7452, ['Wilderness', 'Asgarnian Ice Dungeon']),
        ('Chaos druid', 128, ['Wilderness', 'Taverley Dungeon', 'Edgeville Dungeon']),
        ('Dark warrior', 1820, ['Wilderness']),
        ('Bandit', 148.8, ['Wilderness']),
        ('Rogue', 237.4, ['Wilderness']),
        ('Mammoth', 682.7, ['Wilderness']),
        ('Ent', -1, ['Wilderness']),
        ('Earth warrior', 7452, ['Wilderness', 'Edgeville Dungeon']),
        ('Magic axe', 500, ['Wilderness']),
        ('Black Knight', 1820, ['Wilderness']),
        ('Lesser Nagua', 1500, ['Neypotzli', 'Ruins of Tapoyauik']),
        ('Basilisk Knight', 5000, ["Jormungand's Prison"]),
        ('Deviant spectre', 512, ['Catacombs of Kourend']),
        ('Wyrm', 10000, ['Karuulm Slayer Dungeon', 'Neypotzli']),
        ('Waterfiend', 3000, ['Ancient Cavern', 'Iorwerth Dungeon', 'Kraken Cove']),
        ('Zombies', 1650000, ['Wilderness', 'Edgeville Dungeon', 'Draynor Sewers']),
        ('Troll', 7060, ['Troll Stronghold', 'Keldagrim', 'Death Plateau', 'South of Mount Quidamortem'])
    ]
    
    # Monster to task mapping
    monster_task_mapping = {
        'Crawling Hand': ['Crawling Hands'], 'Cave Crawler': ['Cave crawlers'], 'Banshee': ['Banshees'],
        'Rock Slug': ['Rockslugs'], 'Cockatrice': ['Cockatrice'], 'Pyrefiend': ['Pyrefiends'],
        'Basilisk': ['Basilisks'], 'Infernal Mage': ['Infernal Mages'], 'Bloodveld': ['Bloodvelds'],
        'Mutated Bloodveld': ['Bloodvelds'], 'Jelly': ['Jellies'], 'Turoth': ['Turoth'],
        'Cave Horror': ['Cave horrors'], 'Aberrant Spectre': ['Aberrant spectres'], 'Dust Devil': ['Dust devils'],
        'Kurask': ['Kurask'], 'Skeletal Wyvern': ['Skeletal Wyverns'], 'Gargoyle': ['Gargoyles'],
        'Nechryael': ['Nechryael'], 'Greater Nechryael': ['Nechryael'], 'Abyssal Demon': ['Abyssal demons'],
        'Cave Kraken': ['Cave kraken'], 'Smoke Devil': ['Smoke devils'], 'Blue Dragon': ['Blue dragons'],
        'Baby Blue Dragon': ['Blue dragons'], 'Red Dragon': ['Red dragons'], 'Baby Red Dragon': ['Red dragons'],
        'Black Dragon': ['Black dragons'], 'Baby Black Dragon': ['Black dragons'], 'Green Dragon': ['Green dragons'],
        'Bronze Dragon': ['Bronze dragons'], 'Iron Dragon': ['Iron dragons'], 'Steel Dragon': ['Steel dragons'],
        'Hellhound': ['Hellhounds'], 'Greater Demon': ['Greater demons'], 'Black Demon': ['Black demons'],
        'Fire Giant': ['Fire giants'], 'Moss Giant': ['Moss giants'], 'Ice Giant': ['Ice giants'],
        'Troll': ['Trolls'], 'Ice Troll': ['Trolls'], 'Mountain Troll': ['Trolls'],
        'Kalphite Worker': ['Kalphite'], 'Kalphite Soldier': ['Kalphite'], 'Kalphite Guardian': ['Kalphite'],
        'Dagannoth': ['Dagannoths'], 'Ankou': ['Ankou'], 'Suqah': ['Suqah'],
        'Lizardman': ['Lizardmen'], 'Lizardman Shaman': ['Lizardmen'],
        'Demonic gorilla': ['Black demons'], 'King Black Dragon': ['Black dragons'], 'Brutal black dragon': ['Black dragons'],
        'Brutal blue dragon': ['Blue dragons'], 'Vorkath': ['Blue dragons'],
        'Brine rat': ['Brine rats'], 'Drake': ['Drakes'], 'Fossil Island Wyvern': ['Fossil Island wyverns'],
        'Cerberus': ['Hellhounds'], 'Hydra': ['Hydras'], 'Kraken': ['Cave kraken'],
        'Dark beast': ['Dark beasts'], 'Warped Jelly': ['Jellies'], 'Kalphite Queen': ['Kalphite'],
        'Lava dragon': ['Lava dragons'], 'Lesser demon': ['Lesser demons'], 'Mithril dragon': ['Mithril dragons'],
        'Adamant dragon': ['Adamant dragons'], 'Rune dragon': ['Rune dragons'],
        'Abyssal Sire': ['Abyssal demons'], 'Alchemical Hydra': ['Hydras'],
        'Scorpion': ['Scorpions'], 'Spider': ['Spiders'], 'Bear': ['Bears'],
        'Skeleton': ['Skeletons'], 'Hill Giant': ['Hill Giants'], 'Ice warrior': ['Ice warriors'],
        'Chaos druid': ['Chaos druids'], 'Dark warrior': ['Dark warriors'], 'Bandit': ['Bandits'],
        'Rogue': ['Rogues'], 'Mammoth': ['Mammoths'], 'Ent': ['Ents'],
        'Earth warrior': ['Earth warriors'], 'Magic axe': ['Magic axes'], 'Black Knight': ['Black Knights'],
        'Lesser Nagua': ['Lesser Nagua'], 'Basilisk Knight': ['Basilisks'], 'Deviant spectre': ['Aberrant spectres'],
        'Wyrm': ['Wyrms'], 'Waterfiend': ['Waterfiends'], 'Zombies': ['Zombies']
    }
    
    # Master task assignments including Konar's location-based assignments
    master_assignments = [
        ("Turael", "Banshees", 8, 15, 30, 15, ["Priest in Peril"], None, None),
        ("Turael", "Bats", 7, 15, 30, 1, [], None, None),
        ("Turael", "Bears", 7, 10, 20, 1, [], None, None),
        ("Turael", "Birds", 6, 15, 30, 1, [], None, None),
        ("Turael", "Cave bugs", 8, 10, 30, 7, [], None, None),
        ("Turael", "Cave crawlers", 8, 15, 30, 10, [], None, None),
        ("Turael", "Cave slimes", 8, 10, 20, 17, [], None, None),
        ("Turael", "Cows", 8, 15, 30, 1, [], None, None),
        ("Turael", "Crawling Hands", 8, 15, 30, 5, ["Priest in Peril"], None, None),
        ("Turael", "Dogs", 7, 15, 30, 1, [], None, None),
        ("Turael", "Dwarves", 7, 10, 25, 1, [], None, None),
        ("Turael", "Ghosts", 7, 15, 30, 1, [], None, None),
        ("Turael", "Goblins", 7, 15, 30, 1, [], None, None),
        ("Turael", "Icefiends", 8, 15, 20, 1, [], None, None),
        ("Turael", "Kalphite", 6, 15, 30, 1, [], None, None),
        ("Turael", "Lizards", 8, 15, 30, 22, [], None, None),
        ("Turael", "Minotaurs", 7, 10, 20, 1, [], None, None),
        ("Turael", "Monkeys", 6, 15, 30, 1, [], None, None),
        ("Turael", "Rats", 7, 15, 30, 1, [], None, None),
        ("Turael", "Scorpions", 7, 15, 30, 1, [], None, None),
        ("Turael", "Skeletons", 7, 15, 30, 1, [], None, None),
        ("Turael", "Spiders", 6, 15, 30, 1, [], None, None),
        ("Turael", "Wolves", 7, 15, 30, 1, [], None, None),
        ("Turael", "Zombies", 7, 15, 30, 1, [], None, None),
        ("Spria", "Banshees", 8, 15, 30, 15, ["Priest in Peril"], None, None),
        ("Spria", "Bats", 7, 15, 30, 1, [], None, None),
        ("Spria", "Bears", 7, 10, 20, 1, [], None, None),
        ("Spria", "Birds", 6, 15, 30, 1, [], None, None),
        ("Spria", "Cave bugs", 8, 10, 30, 7, [], None, None),
        ("Spria", "Cave crawlers", 8, 15, 30, 10, [], None, None),
        ("Spria", "Cave slimes", 8, 10, 20, 17, [], None, None),
        ("Spria", "Cows", 8, 15, 30, 1, [], None, None),
        ("Spria", "Crawling Hands", 8, 15, 30, 5, ["Priest in Peril"], None, None),
        ("Spria", "Dogs", 7, 15, 30, 1, [], None, None),
        ("Spria", "Dwarves", 7, 10, 25, 1, [], None, None),
        ("Spria", "Ghosts", 7, 15, 30, 1, [], None, None),
        ("Spria", "Goblins", 7, 15, 30, 1, [], None, None),
        ("Spria", "Icefiends", 8, 15, 20, 1, [], None, None),
        ("Spria", "Kalphite", 6, 15, 30, 1, [], None, None),
        ("Spria", "Lizards", 8, 15, 30, 22, [], None, None),
        ("Spria", "Minotaurs", 7, 10, 20, 1, [], None, None),
        ("Spria", "Monkeys", 6, 15, 30, 1, [], None, None),
        ("Spria", "Rats", 7, 15, 30, 1, [], None, None),
        ("Spria", "Scorpions", 7, 15, 30, 1, [], None, None),
        ("Spria", "Skeletons", 7, 15, 30, 1, [], None, None),
        ("Spria", "Sourhogs", 6, 15, 25, 1, ["A Porcine of Interest"], None, None),
        ("Spria", "Spiders", 6, 15, 30, 1, [], None, None),
        ("Spria", "Wolves", 7, 15, 30, 1, [], None, None),
        ("Spria", "Zombies", 7, 15, 30, 1, [], None, None),
        ("Mazchna", "Banshees", 8, 30, 50, 15, ["Priest in Peril"], None, None),
        ("Mazchna", "Bats", 7, 30, 50, 1, [], None, None),
        ("Mazchna", "Bears", 6, 30, 50, 1, [], None, None),
        ("Mazchna", "Catablepon", 8, 20, 30, 1, [], None, None),
        ("Mazchna", "Cave bugs", 8, 10, 20, 7, [], None, None),
        ("Mazchna", "Cave crawlers", 8, 30, 50, 10, [], None, None),
        ("Mazchna", "Cave slimes", 8, 10, 20, 17, [], None, None),
        ("Mazchna", "Cockatrice", 8, 30, 50, 25, [], None, None),
        ("Mazchna", "Crabs", 8, 30, 50, 1, [], None, None),
        ("Mazchna", "Crawling Hands", 8, 30, 50, 5, ["Priest in Peril"], None, None),
        ("Mazchna", "Dogs", 7, 30, 50, 1, [], None, None),
        ("Mazchna", "Flesh Crawlers", 7, 15, 25, 1, [], None, None),
        ("Mazchna", "Ghosts", 7, 30, 50, 1, [], None, None),
        ("Mazchna", "Ghouls", 7, 10, 20, 1, ["Priest in Peril"], None, None),
        ("Mazchna", "Hill Giants", 7, 30, 50, 1, [], None, None),
        ("Mazchna", "Hobgoblins", 7, 30, 50, 1, [], None, None),
        ("Mazchna", "Ice warriors", 7, 40, 50, 1, [], None, None),
        ("Mazchna", "Kalphite", 6, 30, 50, 1, [], None, None),
        ("Mazchna", "Lizards", 8, 30, 50, 22, [], None, None),
        ("Mazchna", "Mogres", 8, 30, 50, 32, ["Skippy and the Mogres"], None, None),
        ("Mazchna", "Molanisks", 7, 40, 50, 39, ["Death to the Dorgeshuun"], None, None),
        ("Mazchna", "Pyrefiends", 8, 30, 50, 30, [], None, None),
        ("Mazchna", "Rockslugs", 8, 30, 50, 20, [], None, None),
        ("Mazchna", "Scorpions", 7, 30, 50, 1, [], None, None),
        ("Mazchna", "Shades", 8, 30, 70, 1, [], None, None),
        ("Mazchna", "Skeletons", 7, 30, 50, 1, [], None, None),
        ("Mazchna", "Vampyres", 6, 10, 20, 1, ["Priest in Peril"], None, None),
        ("Mazchna", "Wall beasts", 7, 10, 20, 35, [], None, None),
        ("Mazchna", "Wolves", 7, 30, 50, 1, [], None, None),
        ("Mazchna", "Zombies", 7, 30, 50, 1, [], None, None),
        ("Vannaka", "Aberrant spectres", 8, 40, 90, 60, ["Priest in Peril"], None, None),
        ("Vannaka", "Abyssal demons", 5, 40, 90, 85, ["Priest in Peril", "Fairytale II - Cure a Queen"], None, None),
        ("Vannaka", "Ankou", 7, 25, 35, 1, [], None, None),
        ("Vannaka", "Basilisks", 8, 40, 90, 40, [], None, None),
        ("Vannaka", "Bloodvelds", 8, 40, 90, 50, ["Priest in Peril"], None, None),
        ("Vannaka", "Blue dragons", 7, 40, 90, 1, ["Dragon Slayer I"], None, None),
        ("Vannaka", "Brine rats", 7, 40, 90, 47, ["Olaf's Quest"], None, None),
        ("Vannaka", "Cockatrice", 8, 40, 90, 25, [], None, None),
        ("Vannaka", "Crabs", 8, 40, 90, 1, [], None, None),
        ("Vannaka", "Crocodiles", 6, 40, 90, 1, [], None, None),
        ("Vannaka", "Dagannoths", 7, 40, 90, 1, ["Horror from the Deep"], None, None),
        ("Vannaka", "Dust devils", 8, 40, 90, 65, ["Desert Treasure I"], None, None),
        ("Vannaka", "Elves", 7, 30, 70, 1, ["Regicide"], None, None),
        ("Vannaka", "Fever spiders", 7, 30, 90, 42, ["Rum Deal"], None, None),
        ("Vannaka", "Fire giants", 7, 40, 90, 1, [], None, None),
        ("Vannaka", "Ghouls", 7, 10, 40, 1, ["Priest in Peril"], None, None),
        ("Vannaka", "Hill Giants", 7, 40, 90, 1, [], None, None),
        ("Vannaka", "Hobgoblins", 7, 40, 90, 1, [], None, None),
        ("Vannaka", "Ice giants", 7, 30, 80, 1, [], None, None),
        ("Vannaka", "Ice warriors", 7, 40, 90, 1, [], None, None),
        ("Vannaka", "Jellies", 8, 40, 90, 52, [], None, None),
        ("Vannaka", "Jungle horrors", 8, 40, 90, 1, ["Cabin Fever"], None, None),
        ("Vannaka", "Kalphite", 7, 40, 90, 1, [], None, None),
        ("Vannaka", "Lesser demons", 7, 40, 90, 1, [], None, None),
        ("Vannaka", "Moss giants", 7, 40, 90, 1, [], None, None),
        ("Vannaka", "Ogres", 7, 40, 90, 1, [], None, None),
        ("Vannaka", "Otherworldly beings", 8, 40, 90, 1, ["Lost City"], None, None),
        ("Vannaka", "Scorpions", 7, 30, 50, 1, [], None, None),
        ("Vannaka", "Shades", 8, 30, 70, 1, [], None, None),
        ("Vannaka", "Shadow warriors", 8, 30, 80, 1, ["Legends' Quest"], None, None),
        ("Vannaka", "Skeletons", 7, 30, 50, 1, [], None, None),
        ("Vannaka", "Spiritual creatures", 8, 40, 90, 63, ["Death Plateau"], None, None),
        ("Vannaka", "Terror dogs", 6, 20, 45, 40, ["Haunted Mine"], None, None),
        ("Vannaka", "Trolls", 7, 40, 90, 1, [], None, None),
        ("Vannaka", "Vampyres", 7, 10, 20, 1, ["Priest in Peril"], None, None),
        ("Vannaka", "Werewolves", 7, 30, 60, 1, ["Priest in Peril"], None, None),
        ("Vannaka", "Wolves", 7, 30, 50, 1, [], None, None),
        ("Vannaka", "Zombies", 7, 30, 50, 1, [], None, None),
        ("Chaeldar", "Aberrant spectres", 8, 70, 130, 60, ["Priest in Peril"], None, None),
        ("Chaeldar", "Abyssal demons", 12, 70, 130, 85, ["Priest in Peril", "Fairytale II - Cure a Queen"], None, None),
        ("Chaeldar", "Aviansie", 9, 70, 130, 1, [], "Watch the birdie", None),
        ("Chaeldar", "Basilisks", 7, 70, 130, 40, [], None, None),
        ("Chaeldar", "Black demons", 10, 70, 130, 1, [], None, None),
        ("Chaeldar", "Bloodvelds", 8, 70, 130, 50, ["Priest in Peril"], None, None),
        ("Chaeldar", "Blue dragons", 8, 70, 130, 1, ["Dragon Slayer I"], None, None),
        ("Chaeldar", "Brine rats", 7, 70, 130, 47, ["Olaf's Quest"], None, None),
        ("Chaeldar", "Cave horrors", 10, 70, 130, 58, ["Cabin Fever"], None, None),
        ("Chaeldar", "Cave kraken", 12, 30, 50, 87, [], None, None),
        ("Chaeldar", "Crabs", 8, 70, 130, 1, [], None, None),
        ("Chaeldar", "Dagannoths", 11, 70, 130, 1, ["Horror from the Deep"], None, None),
        ("Chaeldar", "Dust devils", 9, 70, 130, 65, ["Desert Treasure I"], None, None),
        ("Chaeldar", "Elves", 8, 70, 130, 1, ["Regicide"], None, None),
        ("Chaeldar", "Fever spiders", 7, 70, 130, 42, ["Rum Deal"], None, None),
        ("Chaeldar", "Fire giants", 12, 70, 130, 1, [], None, None),
        ("Chaeldar", "Fossil Island wyverns", 7, 10, 20, 66, ["Bone Voyage", "Elemental Workshop I"], None, None),
        ("Chaeldar", "Gargoyles", 11, 70, 130, 75, ["Priest in Peril"], None, None),
        ("Chaeldar", "Greater demons", 9, 70, 130, 1, [], None, None),
        ("Chaeldar", "Hellhounds", 9, 70, 130, 1, [], None, None),
        ("Chaeldar", "Jellies", 10, 70, 130, 52, [], None, None),
        ("Chaeldar", "Jungle horrors", 10, 70, 130, 1, ["Cabin Fever"], None, None),
        ("Chaeldar", "Kalphite", 11, 70, 130, 1, [], None, None),
        ("Chaeldar", "Kurask", 12, 70, 130, 70, [], None, None),
        ("Chaeldar", "Lesser demons", 9, 70, 130, 1, [], None, None),
        ("Chaeldar", "Lesser Nagua", 4, 50, 100, 48, ["Perilous Moons"], None, None),
        ("Chaeldar", "Lizardmen", 8, 50, 90, 1, [], "Reptile got ripped", None),
        ("Chaeldar", "Mutated Zygomites", 7, 8, 15, 57, ["Lost City"], None, None),
        ("Chaeldar", "Nechryael", 12, 70, 130, 80, [], None, None),
        ("Chaeldar", "Shadow warriors", 8, 70, 130, 1, ["Legends' Quest"], None, None),
        ("Chaeldar", "Skeletal Wyverns", 7, 10, 20, 72, ["Elemental Workshop I"], None, None),
        ("Chaeldar", "Spiritual creatures", 12, 70, 130, 63, ["Death Plateau"], None, None),
        ("Chaeldar", "Trolls", 11, 70, 130, 1, [], None, None),
        ("Chaeldar", "Turoth", 10, 70, 130, 55, [], None, None),
        ("Chaeldar", "TzHaar", 8, 90, 150, 1, [], "Hot stuff", None),
        ("Chaeldar", "Vampyres", 6, 80, 100, 1, [], "Actual Vampyre Slayer", None),
        ("Chaeldar", "Warped creatures", 6, 70, 130, 1, [], "Warped Reality", None),
        ("Chaeldar", "Wyrms", 6, 60, 100, 62, [], None, None),
        ("Nieve", "Aberrant spectres", 6, 120, 185, 60, ["Priest in Peril"], None, None),
        ("Nieve", "Abyssal demons", 9, 120, 185, 85, ["Priest in Peril", "Fairytale II - Cure a Queen"], None, None),
        ("Nieve", "Adamant dragons", 2, 3, 7, 1, ["Dragon Slayer II"], None, None),
        ("Nieve", "Ankou", 5, 50, 90, 1, [], None, None),
        ("Nieve", "Araxytes", 8, 40, 60, 92, ["Priest in Peril"], None, None),
        ("Nieve", "Aviansie", 6, 120, 185, 1, [], "Watch the birdie", None),
        ("Nieve", "Basilisks", 6, 120, 185, 40, [], "Basilocked", None),
        ("Nieve", "Black demons", 9, 120, 185, 1, [], None, None),
        ("Nieve", "Black dragons", 6, 10, 20, 1, ["Dragon Slayer I"], None, None),
        ("Nieve", "Bloodvelds", 9, 120, 185, 50, ["Priest in Peril"], None, None),
        ("Nieve", "Blue dragons", 4, 110, 170, 1, ["Dragon Slayer I"], None, None),
        ("Nieve", "Boss", 8, 3, 35, 1, [], "Like a boss", None),
        ("Nieve", "Brine rats", 3, 120, 185, 47, ["Olaf's Quest"], None, None),
        ("Nieve", "Cave horrors", 5, 120, 180, 58, ["Cabin Fever"], None, None),
        ("Nieve", "Cave kraken", 6, 100, 120, 87, [], None, None),
        ("Nieve", "Dagannoths", 8, 120, 185, 1, ["Horror from the Deep"], None, None),
        ("Nieve", "Dark beasts", 11, 10, 20, 90, ["Mourning's End Part II"], None, None),
        ("Nieve", "Drakes", 7, 30, 95, 84, [], None, None),
        ("Nieve", "Dust devils", 6, 120, 185, 65, ["Desert Treasure I"], None, None),
        ("Nieve", "Elves", 4, 60, 90, 1, ["Regicide"], None, None),
        ("Nieve", "Fire giants", 9, 120, 185, 1, [], None, None),
        ("Nieve", "Fossil Island wyverns", 5, 5, 25, 66, ["Bone Voyage", "Elemental Workshop I"], None, None),
        ("Nieve", "Gargoyles", 8, 120, 185, 75, ["Priest in Peril"], None, None),
        ("Nieve", "Greater demons", 7, 120, 185, 1, [], None, None),
        ("Nieve", "Hellhounds", 8, 120, 185, 1, [], None, None),
        ("Nieve", "Iron dragons", 5, 30, 60, 1, ["Dragon Slayer I"], None, None),
        ("Nieve", "Kalphite", 9, 120, 185, 1, [], None, None),
        ("Nieve", "Kurask", 3, 120, 185, 70, [], None, None),
        ("Nieve", "Lizardmen", 10, 130, 210, 1, [], "Reptile got ripped", None),
        ("Nieve", "Minions of Scabaras", 4, 30, 60, 1, ["Contact!"], None, None),
        ("Nieve", "Mithril dragons", 5, 4, 8, 1, ["Barbarian Training"], "I hope you mith me", None),
        ("Nieve", "Mutated Zygomites", 2, 10, 25, 57, ["Lost City"], None, None),
        ("Nieve", "Nechryael", 9, 110, 170, 80, [], None, None),
        ("Nieve", "Red dragons", 8, 30, 65, 1, ["Dragon Slayer I"], "Seeing red", None),
        ("Nieve", "Rune dragons", 2, 3, 8, 1, ["Dragon Slayer II"], None, None),
        ("Nieve", "Skeletal Wyverns", 7, 20, 40, 72, ["Elemental Workshop I"], None, None),
        ("Nieve", "Smoke devils", 7, 120, 185, 93, [], None, None),
        ("Nieve", "Spiritual creatures", 6, 120, 185, 63, ["Death Plateau"], None, None),
        ("Nieve", "Steel dragons", 7, 10, 20, 1, ["Dragon Slayer I"], None, None),
        ("Nieve", "Suqah", 8, 60, 90, 1, ["Lunar Diplomacy"], None, None),
        ("Nieve", "Trolls", 6, 120, 185, 1, [], None, None),
        ("Nieve", "Turoth", 3, 120, 185, 55, [], None, None),
        ("Nieve", "TzHaar", 10, 110, 180, 1, [], "Hot stuff", None),
        ("Nieve", "Vampyres", 8, 110, 170, 1, [], "Actual Vampyre Slayer", None),
        ("Nieve", "Warped creatures", 8, 120, 185, 1, [], "Warped Reality", None),
        ("Nieve", "Waterfiends", 2, 130, 200, 1, ["Barbarian Training"], None, None),
        ("Nieve", "Wyrms", 7, 80, 145, 62, [], None, None),
        ("Duradel", "Aberrant spectres", 6, 130, 200, 60, ["Priest in Peril"], None, None),
        ("Duradel", "Abyssal demons", 12, 130, 200, 85, ["Priest in Peril", "Fairytale II - Cure a Queen"], None, None),
        ("Duradel", "Adamant dragons", 2, 4, 9, 1, ["Dragon Slayer II"], None, None),
        ("Duradel", "Ankou", 5, 50, 80, 1, [], None, None),
        ("Duradel", "Araxytes", 10, 60, 80, 92, ["Priest in Peril"], None, None),
        ("Duradel", "Aviansie", 8, 120, 200, 1, [], "Watch the birdie", None),
        ("Duradel", "Basilisks", 7, 130, 200, 40, [], "Basilocked", None),
        ("Duradel", "Black demons", 8, 130, 200, 1, [], None, None),
        ("Duradel", "Black dragons", 9, 10, 20, 1, ["Dragon Slayer I"], None, None),
        ("Duradel", "Bloodvelds", 8, 130, 200, 50, ["Priest in Peril"], None, None),
        ("Duradel", "Blue dragons", 4, 110, 170, 1, ["Dragon Slayer I"], None, None),
        ("Duradel", "Boss", 12, 3, 35, 1, [], "Like a boss", None),
        ("Duradel", "Cave horrors", 4, 130, 200, 58, ["Cabin Fever"], None, None),
        ("Duradel", "Cave kraken", 9, 100, 120, 87, [], None, None),
        ("Duradel", "Dagannoths", 9, 130, 200, 1, ["Horror from the Deep"], None, None),
        ("Duradel", "Dark beasts", 11, 10, 20, 90, ["Mourning's End Part II"], None, None),
        ("Duradel", "Drakes", 8, 50, 110, 84, [], None, None),
        ("Duradel", "Dust devils", 5, 130, 200, 65, ["Desert Treasure I"], None, None),
        ("Duradel", "Elves", 4, 110, 170, 1, ["Regicide"], None, None),
        ("Duradel", "Fire giants", 7, 130, 200, 1, [], None, None),
        ("Duradel", "Fossil Island wyverns", 7, 20, 50, 66, ["Bone Voyage", "Elemental Workshop I"], None, None),
        ("Duradel", "Gargoyles", 8, 130, 200, 75, ["Priest in Peril"], None, None),
        ("Duradel", "Greater demons", 9, 130, 200, 1, [], None, None),
        ("Duradel", "Hellhounds", 10, 130, 200, 1, [], None, None),
        ("Duradel", "Iron dragons", 6, 40, 60, 1, ["Dragon Slayer I"], None, None),
        ("Duradel", "Kalphite", 9, 130, 200, 1, [], None, None),
        ("Duradel", "Kurask", 4, 130, 200, 70, [], None, None),
        ("Duradel", "Lizardmen", 10, 130, 210, 1, [], "Reptile got ripped", None),
        ("Duradel", "Minions of Scabaras", 4, 30, 60, 1, ["Contact!"], None, None),
        ("Duradel", "Mithril dragons", 9, 5, 10, 1, ["Barbarian Training"], "I hope you mith me", None),
        ("Duradel", "Mutated Zygomites", 2, 20, 30, 57, ["Lost City"], None, None),
        ("Duradel", "Nechryael", 11, 130, 200, 80, [], None, None),
        ("Duradel", "Red dragons", 8, 30, 65, 1, ["Dragon Slayer I"], "Seeing red", None),
        ("Duradel", "Rune dragons", 2, 3, 8, 1, ["Dragon Slayer II"], None, None),
        ("Duradel", "Skeletal Wyverns", 7, 20, 40, 72, ["Elemental Workshop I"], None, None),
        ("Duradel", "Smoke devils", 9, 130, 200, 93, [], None, None),
        ("Duradel", "Spiritual creatures", 7, 130, 200, 63, ["Death Plateau"], None, None),
        ("Duradel", "Steel dragons", 7, 10, 20, 1, ["Dragon Slayer I"], None, None),
        ("Duradel", "Suqah", 8, 60, 90, 1, ["Lunar Diplomacy"], None, None),
        ("Duradel", "Trolls", 6, 130, 200, 1, [], None, None),
        ("Duradel", "TzHaar", 10, 130, 199, 1, [], "Hot stuff", None),
        ("Duradel", "Vampyres", 8, 100, 210, 1, [], "Actual Vampyre Slayer", None),
        ("Duradel", "Warped creatures", 8, 130, 200, 1, [], "Warped Reality", None),
        ("Duradel", "Waterfiends", 2, 130, 200, 1, ["Barbarian Training"], None, None),
        ("Duradel", "Wyrms", 8, 100, 160, 62, [], None, None),
        # Krystilia - All tasks have Wilderness location restriction
        ("Krystilia", "Abyssal demons", 5, 75, 125, 85, ["Priest in Peril"], "Slayer task assignments of abyssal demons, dust devils, jellies, and nechryaels from Krystilia can be enabled or disabled for free.", None),
        ("Krystilia", "Ankou", 6, 75, 125, 1, [], None, None),
        ("Krystilia", "Aviansie", 7, 75, 125, 1, [], "Watch the birdie", None),
        ("Krystilia", "Bandits", 4, 75, 125, 1, [], None, None),
        ("Krystilia", "Bears", 6, 65, 100, 1, [], None, None),
        ("Krystilia", "Black demons", 7, 100, 150, 1, [], None, None),
        ("Krystilia", "Black dragons", 4, 8, 16, 1, [], None, None),
        ("Krystilia", "Black Knights", 3, 75, 125, 1, [], None, None),
        ("Krystilia", "Bloodvelds", 4, 70, 110, 50, ["Priest in Peril"], None, None),
        ("Krystilia", "Chaos druids", 5, 50, 90, 1, [], None, None),
        ("Krystilia", "Dark warriors", 4, 75, 125, 1, [], None, None),
        ("Krystilia", "Dust devils", 5, 75, 125, 65, ["Desert Treasure I"], "Slayer task assignments of abyssal demons, dust devils, jellies, and nechryaels from Krystilia can be enabled or disabled for free.", None),
        ("Krystilia", "Earth warriors", 6, 75, 125, 1, [], None, None),
        ("Krystilia", "Ents", 5, 35, 60, 1, [], None, None),
        ("Krystilia", "Fire giants", 7, 75, 125, 1, [], None, None),
        ("Krystilia", "Greater demons", 8, 100, 150, 1, [], None, None),
        ("Krystilia", "Green dragons", 4, 65, 100, 1, [], None, None),
        ("Krystilia", "Hellhounds", 7, 75, 125, 1, [], None, None),
        ("Krystilia", "Hill Giants", 3, 75, 125, 1, [], None, None),
        ("Krystilia", "Ice giants", 6, 100, 150, 1, [], None, None),
        ("Krystilia", "Ice warriors", 7, 100, 150, 1, [], None, None),
        ("Krystilia", "Jellies", 5, 100, 150, 52, [], "Slayer task assignments of abyssal demons, dust devils, jellies, and nechryaels from Krystilia can be enabled or disabled for free.", None),
        ("Krystilia", "Lava dragons", 3, 35, 60, 1, [], None, None),
        ("Krystilia", "Lesser demons", 6, 80, 120, 1, [], None, None),
        ("Krystilia", "Magic axes", 7, 75, 125, 1, [], None, None),
        ("Krystilia", "Mammoths", 6, 75, 125, 1, [], None, None),
        ("Krystilia", "Moss giants", 4, 100, 150, 1, [], None, None),
        ("Krystilia", "Nechryael", 5, 75, 125, 80, [], "Slayer task assignments of abyssal demons, dust devils, jellies, and nechryaels from Krystilia can be enabled or disabled for free.", None),
        ("Krystilia", "Pirates", 3, 62, 75, 1, [], None, None),
        ("Krystilia", "Revenants", 5, 40, 100, 1, [], None, None),
        ("Krystilia", "Rogues", 5, 75, 125, 1, [], None, None),
        ("Krystilia", "Scorpions", 6, 65, 100, 1, [], None, None),
        ("Krystilia", "Skeletons", 5, 65, 100, 1, [], None, None),
        ("Krystilia", "Spiders", 6, 65, 100, 1, [], None, None),
        ("Krystilia", "Spiritual creatures", 6, 100, 150, 63, ["Death Plateau"], None, None),
        ("Krystilia", "Zombies", 3, 75, 125, 1, [], None, None),
        ("Krystilia", "Wilderness bosses", 8, 3, 35, 1, [], "Like a boss", None),
        # Konar tasks with specific locations
        ("Konar", "Aberrant spectres", 6, 120, 170, 60, ["Priest in Peril"], None, "Catacombs of Kourend"),
        ("Konar", "Aberrant spectres", 6, 120, 170, 60, ["Priest in Peril"], None, "Slayer Tower"),
        ("Konar", "Aberrant spectres", 6, 120, 170, 60, ["Priest in Peril"], None, "Stronghold Slayer Cave"),
        ("Konar", "Abyssal demons", 9, 120, 170, 85, ["Priest in Peril", "Fairytale II - Cure a Queen"], None, "Catacombs of Kourend"),
        ("Konar", "Abyssal demons", 9, 120, 170, 85, ["Priest in Peril", "Fairytale II - Cure a Queen"], None, "Abyssal Area"),
        ("Konar", "Abyssal demons", 9, 120, 170, 85, ["Priest in Peril", "Fairytale II - Cure a Queen"], None, "Slayer Tower"),
        ("Konar", "Adamant dragons", 5, 3, 6, 1, ["Dragon Slayer II"], None, "Lithkren Vault"),
        ("Konar", "Ankou", 5, 50, 50, 40, [], None, "Stronghold of Security"),
        ("Konar", "Ankou", 5, 50, 50, 40, [], None, "Stronghold Slayer Cave"),
        ("Konar", "Ankou", 5, 50, 50, 40, [], None, "Catacombs of Kourend"),
        ("Konar", "Aviansie", 6, 120, 170, 1, [], "Watch the birdie", "God Wars Dungeon"),
        ("Konar", "Basilisks", 5, 110, 170, 40, [], "Basilocked", "Fremennik Slayer Dungeon"),
        ("Konar", "Basilisks", 5, 110, 170, 40, [], "Basilocked", "Jormungand's Prison"),
        ("Konar", "Black demons", 9, 120, 170, 80, [], None, "Catacombs of Kourend"),
        ("Konar", "Black demons", 9, 120, 170, 80, [], None, "Chasm of Fire"),
        ("Konar", "Black demons", 9, 120, 170, 80, [], None, "Taverley Dungeon"),
        ("Konar", "Black demons", 9, 120, 170, 80, [], None, "Brimhaven Dungeon"),
        ("Konar", "Black dragons", 6, 10, 15, 80, ["Dragon Slayer I"], None, "Catacombs of Kourend"),
        ("Konar", "Black dragons", 6, 10, 15, 80, ["Dragon Slayer I"], None, "Myths' Guild Dungeon"),
        ("Konar", "Black dragons", 6, 10, 15, 80, ["Dragon Slayer I"], None, "Evil Chicken's Lair"),
        ("Konar", "Black dragons", 6, 10, 15, 80, ["Dragon Slayer I"], None, "Taverley Dungeon"),
        ("Konar", "Bloodvelds", 9, 120, 170, 50, ["Priest in Peril"], None, "Catacombs of Kourend"),
        ("Konar", "Bloodvelds", 9, 120, 170, 50, ["Priest in Peril"], None, "God Wars Dungeon"),
        ("Konar", "Bloodvelds", 9, 120, 170, 50, ["Priest in Peril"], None, "Iorwerth Dungeon"),
        ("Konar", "Bloodvelds", 9, 120, 170, 50, ["Priest in Peril"], None, "Meiyerditch Laboratories"),
        ("Konar", "Bloodvelds", 9, 120, 170, 50, ["Priest in Peril"], None, "Slayer Tower"),
        ("Konar", "Bloodvelds", 9, 120, 170, 50, ["Priest in Peril"], None, "Stronghold Slayer Cave"),
        ("Konar", "Blue dragons", 4, 120, 170, 65, ["Dragon Slayer I"], None, "Catacombs of Kourend"),
        ("Konar", "Blue dragons", 4, 120, 170, 65, ["Dragon Slayer I"], None, "Isle of Souls Dungeon"),
        ("Konar", "Blue dragons", 4, 120, 170, 65, ["Dragon Slayer I"], None, "Myths' Guild Dungeon"),
        ("Konar", "Blue dragons", 4, 120, 170, 65, ["Dragon Slayer I", "Watchtower"], None, "Ogre Enclave"),
        ("Konar", "Blue dragons", 4, 120, 170, 65, ["Dragon Slayer I"], None, "Ruins of Tapoyauik"),
        ("Konar", "Blue dragons", 4, 120, 170, 65, ["Dragon Slayer I"], None, "Taverley Dungeon"),
        ("Konar", "Boss", 8, 3, 35, 1, [], "Like a boss", None),
        ("Konar", "Brine rats", 2, 120, 170, 47, ["Olaf's Quest"], None, "Brine Rat Cavern"),
        ("Konar", "Bronze dragons", 5, 30, 50, 75, ["Dragon Slayer I"], None, "Catacombs of Kourend"),
        ("Konar", "Bronze dragons", 5, 30, 50, 75, ["Dragon Slayer I"], None, "Brimhaven Dungeon"),
        ("Konar", "Cave kraken", 9, 80, 100, 87, [], None, "Kraken Cove"),
        ("Konar", "Dagannoths", 8, 120, 170, 75, ["Horror from the Deep"], None, "Catacombs of Kourend"),
        ("Konar", "Dagannoths", 8, 120, 170, 75, ["Horror from the Deep"], None, "Lighthouse"),
        ("Konar", "Dagannoths", 8, 120, 170, 75, ["Horror from the Deep"], None, "Waterbirth Island"),
        ("Konar", "Dagannoths", 8, 120, 170, 75, ["Horror from the Deep"], None, "Jormungand's Prison"),
        ("Konar", "Dark beasts", 5, 10, 15, 90, ["Mourning's End Part II"], None, "Mourner Tunnels"),
        ("Konar", "Dark beasts", 5, 10, 15, 90, ["Mourning's End Part II", "Song of the Elves"], None, "Iorwerth Dungeon"),
        ("Konar", "Drakes", 10, 75, 140, 84, [], None, "Karuulm Slayer Dungeon"),
        ("Konar", "Dust devils", 6, 120, 170, 65, ["Desert Treasure I"], None, "Catacombs of Kourend"),
        ("Konar", "Dust devils", 6, 120, 170, 65, ["Desert Treasure I"], None, "Smoke Dungeon"),
        ("Konar", "Fire giants", 9, 120, 170, 65, [], None, "Brimhaven Dungeon"),
        ("Konar", "Fire giants", 9, 120, 170, 65, [], None, "Catacombs of Kourend"),
        ("Konar", "Fire giants", 9, 120, 170, 65, [], None, "Isle of Souls Dungeon"),
        ("Konar", "Fire giants", 9, 120, 170, 65, [], None, "Giants' Den"),
        ("Konar", "Fire giants", 9, 120, 170, 65, [], None, "Karuulm Slayer Dungeon"),
        ("Konar", "Fire giants", 9, 120, 170, 65, [], None, "Stronghold Slayer Cave"),
        ("Konar", "Fire giants", 9, 120, 170, 65, [], None, "Waterfall Dungeon"),
        ("Konar", "Fossil Island wyverns", 5, 15, 30, 66, ["Bone Voyage", "Elemental Workshop I"], None, "Wyvern Cave"),
        ("Konar", "Gargoyles", 6, 120, 170, 75, ["Priest in Peril"], None, "Slayer Tower"),
        ("Konar", "Greater demons", 7, 120, 170, 75, [], None, "Catacombs of Kourend"),
        ("Konar", "Greater demons", 7, 120, 170, 75, [], None, "Chasm of Fire"),
        ("Konar", "Greater demons", 7, 120, 170, 75, [], None, "Isle of Souls Dungeon"),
        ("Konar", "Greater demons", 7, 120, 170, 75, [], None, "Karuulm Slayer Dungeon"),
        ("Konar", "Greater demons", 7, 120, 170, 75, [], None, "Brimhaven Dungeon"),
        ("Konar", "Hellhounds", 8, 120, 170, 75, [], None, "Karuulm Slayer Dungeon"),
        ("Konar", "Hellhounds", 8, 120, 170, 75, [], None, "Catacombs of Kourend"),
        ("Konar", "Hellhounds", 8, 120, 170, 75, [], None, "Stronghold Slayer Cave"),
        ("Konar", "Hellhounds", 8, 120, 170, 75, [], None, "Taverley Dungeon"),
        ("Konar", "Hellhounds", 8, 120, 170, 75, [], None, "Witchaven Dungeon"),
        ("Konar", "Hydras", 10, 125, 190, 95, [], None, "Karuulm Slayer Dungeon"),
        ("Konar", "Iron dragons", 5, 30, 50, 80, ["Dragon Slayer I"], None, "Brimhaven Dungeon"),
        ("Konar", "Iron dragons", 5, 30, 50, 80, ["Dragon Slayer I"], None, "Catacombs of Kourend"),
        ("Konar", "Iron dragons", 5, 30, 50, 80, ["Dragon Slayer I"], None, "Isle of Souls Dungeon"),
        ("Konar", "Jellies", 6, 120, 170, 52, [], None, "Fremennik Slayer Dungeon"),
        ("Konar", "Jellies", 6, 120, 170, 52, [], None, "Catacombs of Kourend"),
        ("Konar", "Jellies", 6, 120, 170, 52, [], None, "Ruins of Tapoyauik"),
        ("Konar", "Kalphite", 9, 120, 170, 15, [], None, "Kalphite Lair"),
        ("Konar", "Kalphite", 9, 120, 170, 15, [], None, "Kalphite Cave"),
        ("Konar", "Kurask", 3, 120, 170, 70, [], None, "Fremennik Slayer Dungeon"),
        ("Konar", "Kurask", 3, 120, 170, 70, ["Song of the Elves"], None, "Iorwerth Dungeon"),
        ("Konar", "Lesser Nagua", 2, 55, 120, 48, ["Perilous Moons"], None, "Neypotzli"),
        ("Konar", "Lesser Nagua", 2, 55, 120, 48, ["Perilous Moons"], None, "Ruins of Tapoyauik"),
        ("Konar", "Lizardmen", 8, 90, 110, 1, [], "Reptile got ripped", "Battlefront"),
        ("Konar", "Lizardmen", 8, 90, 110, 1, [], "Reptile got ripped", "Lizardman Canyon"),
        ("Konar", "Lizardmen", 8, 90, 110, 1, [], "Reptile got ripped", "Lizardman Settlement"),
        ("Konar", "Lizardmen", 8, 90, 110, 1, [], "Reptile got ripped", "Kebos Swamp"),
        ("Konar", "Lizardmen", 8, 90, 110, 1, [], "Reptile got ripped", "Molch"),
        ("Konar", "Mithril dragons", 5, 3, 6, 1, ["Barbarian Training"], "I hope you mith me", "Ancient Cavern"),
        ("Konar", "Mutated Zygomites", 2, 10, 25, 57, ["Lost City"], None, "Fossil Island"),
        ("Konar", "Mutated Zygomites", 2, 10, 25, 57, ["Lost City"], None, "Zanaris"),
        ("Konar", "Nechryael", 7, 110, 110, 80, [], None, "Catacombs of Kourend"),
        ("Konar", "Nechryael", 7, 110, 110, 80, ["Song of the Elves"], None, "Iorwerth Dungeon"),
        ("Konar", "Nechryael", 7, 110, 110, 80, [], None, "Slayer Tower"),
        ("Konar", "Red dragons", 5, 30, 50, 68, ["Dragon Slayer I"], "Seeing red", "Brimhaven Dungeon"),
        ("Konar", "Red dragons", 5, 30, 50, 68, ["Dragon Slayer I"], "Seeing red", "Catacombs of Kourend"),
        ("Konar", "Red dragons", 5, 30, 50, 68, ["Dragon Slayer I"], "Seeing red", "Forthos Dungeon"),
        ("Konar", "Red dragons", 5, 30, 50, 68, ["Dragon Slayer I"], "Seeing red", "Myths' Guild Dungeon"),
        ("Konar", "Rune dragons", 5, 3, 6, 1, ["Dragon Slayer II"], None, "Lithkren Vault"),
        ("Konar", "Skeletal Wyverns", 5, 5, 12, 72, ["Elemental Workshop I"], None, "Asgarnian Ice Dungeon"),
        ("Konar", "Smoke devils", 7, 120, 170, 93, [], None, "Smoke Devil Dungeon"),
        ("Konar", "Steel dragons", 5, 30, 50, 85, ["Dragon Slayer I"], None, "Catacombs of Kourend"),
        ("Konar", "Steel dragons", 5, 30, 50, 85, ["Dragon Slayer I"], None, "Brimhaven Dungeon"),
        ("Konar", "Trolls", 6, 120, 170, 60, [], None, "Troll Stronghold"),
        ("Konar", "Trolls", 6, 120, 170, 60, [], None, "Keldagrim"),
        ("Konar", "Trolls", 6, 120, 170, 60, [], None, "Death Plateau"),
        ("Konar", "Trolls", 6, 120, 170, 60, [], None, "South of Mount Quidamortem"),
        ("Konar", "Turoth", 3, 120, 170, 55, [], None, "Fremennik Slayer Dungeon"),
        ("Konar", "Vampyres", 4, 100, 160, 1, [], "Actual Vampyre Slayer", "Darkmeyer"),
        ("Konar", "Vampyres", 4, 100, 160, 1, [], "Actual Vampyre Slayer", "Meiyerditch"),
        ("Konar", "Vampyres", 4, 100, 160, 1, [], "Actual Vampyre Slayer", "Slepe"),
        ("Konar", "Warped creatures", 4, 110, 170, 1, [], "Warped Reality", "Poison Waste Dungeon"),
        ("Konar", "Waterfiends", 2, 120, 170, 75, ["Barbarian Training"], None, "Ancient Cavern"),
        ("Konar", "Waterfiends", 2, 120, 170, 75, ["Barbarian Training", "Song of the Elves"], None, "Iorwerth Dungeon"),
        ("Konar", "Waterfiends", 2, 120, 170, 75, ["Barbarian Training"], None, "Kraken Cove"),
        ("Konar", "Wyrms", 10, 125, 190, 62, [], None, "Karuulm Slayer Dungeon"),
        ("Konar", "Wyrms", 10, 125, 190, 62, [], None, "Neypotzli")
    ]
    
    # Create tasks from master assignments if they don't exist
    all_tasks_in_assignments = {assignment[1]: assignment[5] for assignment in master_assignments}
    for task_name, slayer_req in all_tasks_in_assignments.items():
        db.add_task(task_name, slayer_req)

    # Now get all tasks from DB to get their IDs
    tasks = db.get_all_tasks()
    task_ids = {task['name']: task['id'] for task in tasks}

    # Add monsters with their task assignments and locations
    for name, limit, locations in common_monsters:
        
        # Apply the ln(2) calculation for monsters with a drop rate
        if limit != -1:
            kill_limit = math.ceil(limit * math.log(2))
        else:
            kill_limit = -1
            
        if name in monster_task_mapping:
            task_names = monster_task_mapping[name]
            assigned_task_ids = [task_ids[task_name] for task_name in task_names if task_name in task_ids]
            if assigned_task_ids:
                db.add_monster(name, kill_limit, assigned_task_ids, locations)
    
    # Get slayer master IDs
    masters = db.get_slayer_masters()
    master_ids = {master['name']: master['id'] for master in masters}
    
    # Assign tasks to masters
    for master_name, task_name, weight, min_amt, max_amt, slayer_level, quest_unlocks, slayer_unlock, location_restriction in master_assignments:
        if master_name in master_ids and task_name in task_ids:
            db.add_master_task_assignment(
                master_ids[master_name],
                task_ids[task_name],
                weight,
                min_amt,
                max_amt,
                quest_unlocks,
                slayer_unlock,
                location_restriction
            )
    
    return jsonify({'success': True, 'message': 'Common tasks initialized!'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)