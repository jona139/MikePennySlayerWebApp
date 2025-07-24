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
    
    if not name:
        return jsonify({'success': False, 'message': 'Monster name required'}), 400
    
    if not task_ids:
        return jsonify({'success': False, 'message': 'At least one task must be selected'}), 400
    
    success, message = db.add_monster(name, kill_limit, task_ids)
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
    # Add common monsters first
    common_monsters = [
        ('Crawling Hand', 64), ('Cave Crawler', 128), ('Banshee', 512), ('Rock Slug', 512),
        ('Cockatrice', 512), ('Pyrefiend', 128), ('Basilisk', 512), ('Infernal Mage', 512),
        ('Bloodveld', 128), ('Mutated Bloodveld', 128), ('Jelly', 128), ('Turoth', 512),
        ('Cave Horror', 512), ('Aberrant Spectre', 512), ('Dust Devil', 32768), ('Kurask', 1026),
        ('Skeletal Wyvern', 512), ('Gargoyle', 512), ('Nechryael', 116), ('Greater Nechryael', 128),
        ('Abyssal Demon', 32000), ('Cave Kraken', 200), ('Smoke Devil', 32768), ('Blue Dragon', 364),
        ('Baby Blue Dragon', -1), ('Red Dragon', 2731), ('Baby Red Dragon', -1), ('Black Dragon', 128),
        ('Baby Black Dragon', -1), ('Green Dragon', 364.1), ('Bronze Dragon', 2048), ('Iron Dragon', 1024),
        ('Steel Dragon', 512), ('Hellhound', 32768), ('Greater Demon', 128), ('Black Demon', 237.7),
        ('Fire Giant', 287), ('Moss Giant', 150), ('Ice Giant', 16786), ('Ice Troll', 303.4),
        ('Mountain Troll', 7060), ('Kalphite Worker', 780.2), ('Kalphite Soldier', 5461), ('Kalphite Guardian', 237.4),
        ('Dagannoth', 839.1), ('Ankou', 33.3), ('Suqah', 5.16), ('Lizardman', 250), ('Lizardman Shaman', 3000),
        ('Deviant spectre', 512), ('Abyssal Sire', 1066), ('Adamant dragon', 1000), ('Araxytes', 4000), ('Aviansie', 364.1),
        ('Bandit', 148.8), ('Twisted Banshee', 256), ('Basilisk Knight', 5000), ('Bat', -1), ('Bear', -1), ('Bird', -1),
        ('Demonic gorilla', 1500), ('King Black Dragon', 1000), ('Brutal black dragon', 512), ('Black Knight', 1820),
        ('Brutal blue dragon', 128), ('Vorkath', 5000), ('Brine rat', 512), ('Catablepon', 33.67), ('Cave bug', 287.7),
        ('Cave slime', 128), ('Kraken', 512), ('Chaos druid', 128), ('Cow', -1), ('Ammonite Crab', 128),
        ('Frost Crab', 90), ('King Sand Crab', 15104), ('Rock Crab', 128), ('Sand Crab', 128), ('Swamp Crab', 128),
        ('Crocodile', 853.3), ('Dagannoth Prime', 128), ('Dagannoth Rex', 128), ('Dagannoth Supreme', 128),
        ('Dark beast', 512), ('Dark warrior', 1820), ('Dog', -1), ('Drake', 10000), ('Dwarf', -1),
        ('Earth warrior', 7452), ('Elf', 1400), ('Ent', -1), ('Fever spider', 36), ('Flesh Crawler', 33.33),
        ('Fossil Island Wyvern', 2000), ('Ghost', -1), ('Ghoul', -1), ('Goblin', 2731), ('Brutal green dragon', 364.1),
        ('Harpie bug swarm', 128), ('Cerberus', 520), ('Hill Giant', 128), ('Hobgoblin', 896),
        ('Hydra', 10001), ('Icefiend', 128), ('Ice warrior', 7452), ('Iron dragon', 1024), ('Warped Jelly', 64),
        ('Jungle horror', 1101), ('Kalphite Queen', 400), ('Killerwatt', 512), ('Lava dragon', 1092),
        ('Lesser demon', 5461), ('Lesser Nagua', 1500), ('Lizard', 1024), ('Magic axe', 500), ('Mammoth', 682.7),
        ('Mithril dragon', 32768), ('Minotaur', 33.3), ('Mogre', 64), ('Molanisk', 128), ('Monkey', -1),
        ('Ogre', 7060), ('Otherworldly being', 546.1), ('Pirate', 128), ('Rat', -1), ('Revenant', 44000),
        ('Rogue', 237.4), ('Rune dragon', 800), ('Scabarite', 7552), ('Scorpion', -1), ('Sea snake', 9582),
        ('Shade', 4), ('Shadow warrior', 303.4), ('Skeleton', 1650000), ('Sourhog', 12809), ('Spider', -1),
        ('Spiritual creature', 1800), ('Terror dog', 364.1), ('TzHaar', -1),
        ('Vampyre', -1), ('Wall beast', 512), ('Warped creature', 640), ('Waterfiend', 3000),
        ('Werewolf', 7282), ('Wolf', -1), ('Wyrm', 10000), ('Zombie', 1650000), ('Zygomite', 7500)
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
        'Deviant spectre': ['Aberrant spectres'], 'Abyssal Sire': ['Abyssal demons'], 'Adamant dragon': ['Adamant dragons'],
        'Araxytes': ['Araxytes'], 'Aviansie': ['Aviansie'], 'Bandit': ['Bandits'], 'Twisted Banshee': ['Banshees'],
        'Basilisk Knight': ['Basilisks'], 'Bat': ['Bats'], 'Bear': ['Bears'], 'Bird': ['Birds'],
        'Demonic gorilla': ['Black demons'], 'King Black Dragon': ['Black dragons'], 'Brutal black dragon': ['Black dragons'],
        'Black Knight': ['Black Knights'], 'Brutal blue dragon': ['Blue dragons'], 'Vorkath': ['Blue dragons'],
        'Brine rat': ['Brine rats'], 'Catablepon': ['Catablepon'], 'Cave bug': ['Cave bugs'],
        'Cave slime': ['Cave slimes'], 'Kraken': ['Cave kraken'], 'Chaos druid': ['Chaos druids'],
        'Cow': ['Cows'], 'Ammonite Crab': ['Crabs'], 'Frost Crab': ['Crabs'], 'King Sand Crab': ['Crabs'],
        'Rock Crab': ['Crabs'], 'Sand Crab': ['Crabs'], 'Swamp Crab': ['Crabs'], 'Crocodile': ['Crocodiles'],
        'Dagannoth Prime': ['Dagannoths'], 'Dagannoth Rex': ['Dagannoths'], 'Dagannoth Supreme': ['Dagannoths'],
        'Dark beast': ['Dark beasts'], 'Dark warrior': ['Dark warriors'], 'Dog': ['Dogs'], 'Drake': ['Drakes'],
        'Dwarf': ['Dwarves'], 'Earth warrior': ['Earth warriors'], 'Elf': ['Elves'], 'Ent': ['Ents'],
        'Fever spider': ['Fever spiders'], 'Flesh Crawler': ['Flesh Crawlers'], 'Fossil Island Wyvern': ['Fossil Island wyverns'],
        'Ghost': ['Ghosts'], 'Ghoul': ['Ghouls'], 'Goblin': ['Goblins'], 'Brutal green dragon': ['Green dragons'],
        'Elvarg': ['Green dragons'], 'Harpie bug swarm': ['Harpie bug swarms'], 'Cerberus': ['Hellhounds'],
        'Hill Giant': ['Hill Giants'], 'Hobgoblin': ['Hobgoblins'], 'Hydra': ['Hydras'],
        'Icefiend': ['Icefiends'], 'Ice warrior': ['Ice warriors'], 'Iron dragon': ['Iron dragons'],
        'Warped Jelly': ['Jellies'], 'Jungle horror': ['Jungle horrors'], 'Kalphite Queen': ['Kalphite'],
        'Killerwatt': ['Killerwatts'], 'Lava dragon': ['Lava dragons'], 'Lesser demon': ['Lesser demons'],
        'Lesser Nagua': ['Lesser Nagua'], 'Lizard': ['Lizards'], 'Magic axe': ['Magic axes'],
        'Mammoth': ['Mammoth'], 'Mithril dragon': ['Mithril dragons'], 'Minotaur': ['Minotaurs'],
        'Mogre': ['Mogres'], 'Molanisk': ['Molanisks'], 'Monkey': ['Monkeys'], 'Ogre': ['Ogres'],
        'Otherworldly being': ['Otherworldly beings'], 'Pirate': ['Pirates'], 'Rat': ['Rats'],
        'Revenant': ['Revenants'], 'Rogue': ['Rogues'], 'Rune dragon': ['Rune dragons'],
        'Scabarite': ['Scabarites'], 'Scorpion': ['Scorpions'], 'Sea snake': ['Sea snakes'],
        'Shade': ['Shades'], 'Shadow warrior': ['Shadow warriors'], 'Skeleton': ['Skeletons'],
        'Sourhog': ['Sourhogs'], 'Spider': ['Spiders'], 'Spiritual creature': ['Spiritual creatures'],
        'Steel dragon': ['Steel dragons'], 'Terror dog': ['Terror dogs'], 'TzHaar': ['TzHaar'],
        'Vampyre': ['Vampyres'], 'Wall beast': ['Wall beasts'], 'Warped creature': ['Warped creatures'],
        'Waterfiend': ['Waterfiends'], 'Werewolf': ['Werewolves'], 'Wolf': ['Wolves'], 'Wyrm': ['Wyrms'],
        'Zombie': ['Zombies'], 'Zygomite': ['Mutated Zygomites']
    }
    
    # Master task assignments
    master_assignments = [
        ("Turael", "Banshees", 8, 15, 30, 15, ["Priest in Peril"], None),
        ("Turael", "Bats", 7, 15, 30, 1, [], None),
        ("Turael", "Bears", 7, 10, 20, 1, [], None),
        ("Turael", "Birds", 6, 15, 30, 1, [], None),
        ("Turael", "Cave bugs", 8, 10, 30, 7, [], None),
        ("Turael", "Cave crawlers", 8, 15, 30, 10, [], None),
        ("Turael", "Cave slimes", 8, 10, 20, 17, [], None),
        ("Turael", "Cows", 8, 15, 30, 1, [], None),
        ("Turael", "Crawling Hands", 8, 15, 30, 5, ["Priest in Peril"], None),
        ("Turael", "Dogs", 7, 15, 30, 1, [], None),
        ("Turael", "Dwarves", 7, 10, 25, 1, [], None),
        ("Turael", "Ghosts", 7, 15, 30, 1, [], None),
        ("Turael", "Goblins", 7, 15, 30, 1, [], None),
        ("Turael", "Icefiends", 8, 15, 20, 1, [], None),
        ("Turael", "Kalphite", 6, 15, 30, 1, [], None),
        ("Turael", "Lizards", 8, 15, 30, 22, [], None),
        ("Turael", "Minotaurs", 7, 10, 20, 1, [], None),
        ("Turael", "Monkeys", 6, 15, 30, 1, [], None),
        ("Turael", "Rats", 7, 15, 30, 1, [], None),
        ("Turael", "Scorpions", 7, 15, 30, 1, [], None),
        ("Turael", "Skeletons", 7, 15, 30, 1, [], None),
        ("Turael", "Spiders", 6, 15, 30, 1, [], None),
        ("Turael", "Wolves", 7, 15, 30, 1, [], None),
        ("Turael", "Zombies", 7, 15, 30, 1, [], None),
        ("Spria", "Banshees", 8, 15, 30, 15, ["Priest in Peril"], None),
        ("Spria", "Bats", 7, 15, 30, 1, [], None),
        ("Spria", "Bears", 7, 10, 20, 1, [], None),
        ("Spria", "Birds", 6, 15, 30, 1, [], None),
        ("Spria", "Cave bugs", 8, 10, 30, 7, [], None),
        ("Spria", "Cave crawlers", 8, 15, 30, 10, [], None),
        ("Spria", "Cave slimes", 8, 10, 20, 17, [], None),
        ("Spria", "Cows", 8, 15, 30, 1, [], None),
        ("Spria", "Crawling Hands", 8, 15, 30, 5, ["Priest in Peril"], None),
        ("Spria", "Dogs", 7, 15, 30, 1, [], None),
        ("Spria", "Dwarves", 7, 10, 25, 1, [], None),
        ("Spria", "Ghosts", 7, 15, 30, 1, [], None),
        ("Spria", "Goblins", 7, 15, 30, 1, [], None),
        ("Spria", "Icefiends", 8, 15, 20, 1, [], None),
        ("Spria", "Kalphite", 6, 15, 30, 1, [], None),
        ("Spria", "Lizards", 8, 15, 30, 22, [], None),
        ("Spria", "Minotaurs", 7, 10, 20, 1, [], None),
        ("Spria", "Monkeys", 6, 15, 30, 1, [], None),
        ("Spria", "Rats", 7, 15, 30, 1, [], None),
        ("Spria", "Scorpions", 7, 15, 30, 1, [], None),
        ("Spria", "Skeletons", 7, 15, 30, 1, [], None),
        ("Spria", "Sourhogs", 6, 15, 25, 1, ["A Porcine of Interest"], None),
        ("Spria", "Spiders", 6, 15, 30, 1, [], None),
        ("Spria", "Wolves", 7, 15, 30, 1, [], None),
        ("Spria", "Zombies", 7, 15, 30, 1, [], None),
        ("Mazchna", "Banshees", 8, 30, 50, 15, ["Priest in Peril"], None),
        ("Mazchna", "Bats", 7, 30, 50, 1, [], None),
        ("Mazchna", "Bears", 6, 30, 50, 1, [], None),
        ("Mazchna", "Catablepon", 8, 20, 30, 1, [], None),
        ("Mazchna", "Cave bugs", 8, 10, 20, 7, [], None),
        ("Mazchna", "Cave crawlers", 8, 30, 50, 10, [], None),
        ("Mazchna", "Cave slimes", 8, 10, 20, 17, [], None),
        ("Mazchna", "Cockatrice", 8, 30, 50, 25, [], None),
        ("Mazchna", "Crabs", 8, 30, 50, 1, [], None),
        ("Mazchna", "Crawling Hands", 8, 30, 50, 5, ["Priest in Peril"], None),
        ("Mazchna", "Dogs", 7, 30, 50, 1, [], None),
        ("Mazchna", "Flesh Crawlers", 7, 15, 25, 1, [], None),
        ("Mazchna", "Ghosts", 7, 30, 50, 1, [], None),
        ("Mazchna", "Ghouls", 7, 10, 20, 1, ["Priest in Peril"], None),
        ("Mazchna", "Hill Giants", 7, 30, 50, 1, [], None),
        ("Mazchna", "Hobgoblins", 7, 30, 50, 1, [], None),
        ("Mazchna", "Ice warriors", 7, 40, 50, 1, [], None),
        ("Mazchna", "Kalphite", 6, 30, 50, 1, [], None),
        ("Mazchna", "Lizards", 8, 30, 50, 22, [], None),
        ("Mazchna", "Mogres", 8, 30, 50, 32, ["Skippy and the Mogres"], None),
        ("Mazchna", "Molanisks", 7, 40, 50, 39, ["Death to the Dorgeshuun"], None),
        ("Mazchna", "Pyrefiends", 8, 30, 50, 30, [], None),
        ("Mazchna", "Rockslugs", 8, 30, 50, 20, [], None),
        ("Mazchna", "Scorpions", 7, 30, 50, 1, [], None),
        ("Mazchna", "Shades", 8, 30, 70, 1, [], None),
        ("Mazchna", "Skeletons", 7, 30, 50, 1, [], None),
        ("Mazchna", "Vampyres", 6, 10, 20, 1, ["Priest in Peril"], None),
        ("Mazchna", "Wall beasts", 7, 10, 20, 35, [], None),
        ("Mazchna", "Wolves", 7, 30, 50, 1, [], None),
        ("Mazchna", "Zombies", 7, 30, 50, 1, [], None),
        ("Vannaka", "Aberrant spectres", 8, 40, 90, 60, ["Priest in Peril"], None),
        ("Vannaka", "Abyssal demons", 5, 40, 90, 85, ["Priest in Peril", "Fairytale II - Cure a Queen"], None),
        ("Vannaka", "Ankou", 7, 25, 35, 1, [], None),
        ("Vannaka", "Basilisks", 8, 40, 90, 40, [], None),
        ("Vannaka", "Bloodvelds", 8, 40, 90, 50, ["Priest in Peril"], None),
        ("Vannaka", "Blue dragons", 7, 40, 90, 1, ["Dragon Slayer I"], None),
        ("Vannaka", "Brine rats", 7, 40, 90, 47, ["Olaf's Quest"], None),
        ("Vannaka", "Cockatrice", 8, 40, 90, 25, [], None),
        ("Vannaka", "Crabs", 8, 40, 90, 1, [], None),
        ("Vannaka", "Crocodiles", 6, 40, 90, 1, [], None),
        ("Vannaka", "Dagannoths", 7, 40, 90, 1, ["Horror from the Deep"], None),
        ("Vannaka", "Dust devils", 8, 40, 90, 65, ["Desert Treasure I"], None),
        ("Vannaka", "Elves", 7, 30, 70, 1, ["Regicide"], None),
        ("Vannaka", "Fever spiders", 7, 30, 90, 42, ["Rum Deal"], None),
        ("Vannaka", "Fire giants", 7, 40, 90, 1, [], None),
        ("Vannaka", "Ghouls", 7, 10, 40, 1, ["Priest in Peril"], None),
        ("Vannaka", "Hill Giants", 7, 40, 90, 1, [], None),
        ("Vannaka", "Hobgoblins", 7, 40, 90, 1, [], None),
        ("Vannaka", "Ice giants", 7, 30, 80, 1, [], None),
        ("Vannaka", "Ice warriors", 7, 40, 90, 1, [], None),
        ("Vannaka", "Jellies", 8, 40, 90, 52, [], None),
        ("Vannaka", "Jungle horrors", 8, 40, 90, 1, ["Cabin Fever"], None),
        ("Vannaka", "Kalphite", 7, 40, 90, 1, [], None),
        ("Vannaka", "Lesser demons", 7, 40, 90, 1, [], None),
        ("Vannaka", "Moss giants", 7, 40, 90, 1, [], None),
        ("Vannaka", "Ogres", 7, 40, 90, 1, [], None),
        ("Vannaka", "Otherworldly beings", 8, 40, 90, 1, ["Lost City"], None),
        ("Vannaka", "Scorpions", 7, 30, 50, 1, [], None),
        ("Vannaka", "Shades", 8, 30, 70, 1, [], None),
        ("Vannaka", "Shadow warriors", 8, 30, 80, 1, ["Legends' Quest"], None),
        ("Vannaka", "Skeletons", 7, 30, 50, 1, [], None),
        ("Vannaka", "Spiritual creatures", 8, 40, 90, 63, ["Death Plateau"], None),
        ("Vannaka", "Terror dogs", 6, 20, 45, 40, ["Haunted Mine"], None),
        ("Vannaka", "Trolls", 7, 40, 90, 1, [], None),
        ("Vannaka", "Vampyres", 7, 10, 20, 1, ["Priest in Peril"], None),
        ("Vannaka", "Werewolves", 7, 30, 60, 1, ["Priest in Peril"], None),
        ("Vannaka", "Wolves", 7, 30, 50, 1, [], None),
        ("Vannaka", "Zombies", 7, 30, 50, 1, [], None),
        ("Chaeldar", "Aberrant spectres", 8, 70, 130, 60, ["Priest in Peril"], None),
        ("Chaeldar", "Abyssal demons", 12, 70, 130, 85, ["Priest in Peril", "Fairytale II - Cure a Queen"], None),
        ("Chaeldar", "Aviansie", 9, 70, 130, 1, [], "Watch the birdie"),
        ("Chaeldar", "Basilisks", 7, 70, 130, 40, [], None),
        ("Chaeldar", "Black demons", 10, 70, 130, 1, [], None),
        ("Chaeldar", "Bloodvelds", 8, 70, 130, 50, ["Priest in Peril"], None),
        ("Chaeldar", "Blue dragons", 8, 70, 130, 1, ["Dragon Slayer I"], None),
        ("Chaeldar", "Brine rats", 7, 70, 130, 47, ["Olaf's Quest"], None),
        ("Chaeldar", "Cave horrors", 10, 70, 130, 58, ["Cabin Fever"], None),
        ("Chaeldar", "Cave kraken", 12, 30, 50, 87, [], None),
        ("Chaeldar", "Crabs", 8, 70, 130, 1, [], None),
        ("Chaeldar", "Dagannoths", 11, 70, 130, 1, ["Horror from the Deep"], None),
        ("Chaeldar", "Dust devils", 9, 70, 130, 65, ["Desert Treasure I"], None),
        ("Chaeldar", "Elves", 8, 70, 130, 1, ["Regicide"], None),
        ("Chaeldar", "Fever spiders", 7, 70, 130, 42, ["Rum Deal"], None),
        ("Chaeldar", "Fire giants", 12, 70, 130, 1, [], None),
        ("Chaeldar", "Fossil Island wyverns", 7, 10, 20, 66, ["Bone Voyage", "Elemental Workshop I"], None),
        ("Chaeldar", "Gargoyles", 11, 70, 130, 75, ["Priest in Peril"], None),
        ("Chaeldar", "Greater demons", 9, 70, 130, 1, [], None),
        ("Chaeldar", "Hellhounds", 9, 70, 130, 1, [], None),
        ("Chaeldar", "Jellies", 10, 70, 130, 52, [], None),
        ("Chaeldar", "Jungle horrors", 10, 70, 130, 1, ["Cabin Fever"], None),
        ("Chaeldar", "Kalphite", 11, 70, 130, 1, [], None),
        ("Chaeldar", "Kurask", 12, 70, 130, 70, [], None),
        ("Chaeldar", "Lesser demons", 9, 70, 130, 1, [], None),
        ("Chaeldar", "Lesser Nagua", 4, 50, 100, 48, ["Perilous Moons"], None),
        ("Chaeldar", "Lizardmen", 8, 50, 90, 1, [], "Reptile got ripped"),
        ("Chaeldar", "Mutated Zygomites", 7, 8, 15, 57, ["Lost City"], None),
        ("Chaeldar", "Nechryael", 12, 70, 130, 80, [], None),
        ("Chaeldar", "Shadow warriors", 8, 70, 130, 1, ["Legends' Quest"], None),
        ("Chaeldar", "Skeletal Wyverns", 7, 10, 20, 72, ["Elemental Workshop I"], None),
        ("Chaeldar", "Spiritual creatures", 12, 70, 130, 63, ["Death Plateau"], None),
        ("Chaeldar", "Trolls", 11, 70, 130, 1, [], None),
        ("Chaeldar", "Turoth", 10, 70, 130, 55, [], None),
        ("Chaeldar", "TzHaar", 8, 90, 150, 1, [], "Hot stuff"),
        ("Chaeldar", "Vampyres", 6, 80, 100, 1, [], "Actual Vampyre Slayer"),
        ("Chaeldar", "Warped creatures", 6, 70, 130, 1, [], "Warped Reality"),
        ("Chaeldar", "Wyrms", 6, 60, 100, 62, [], None),
        ("Nieve", "Aberrant spectres", 6, 120, 185, 60, ["Priest in Peril"], None),
        ("Nieve", "Abyssal demons", 9, 120, 185, 85, ["Priest in Peril", "Fairytale II - Cure a Queen"], None),
        ("Nieve", "Adamant dragons", 2, 3, 7, 1, ["Dragon Slayer II"], None),
        ("Nieve", "Ankou", 5, 50, 90, 1, [], None),
        ("Nieve", "Araxytes", 8, 40, 60, 92, ["Priest in Peril"], None),
        ("Nieve", "Aviansie", 6, 120, 185, 1, [], "Watch the birdie"),
        ("Nieve", "Basilisks", 6, 120, 185, 40, [], "Basilocked"),
        ("Nieve", "Black demons", 9, 120, 185, 1, [], None),
        ("Nieve", "Black dragons", 6, 10, 20, 1, ["Dragon Slayer I"], None),
        ("Nieve", "Bloodvelds", 9, 120, 185, 50, ["Priest in Peril"], None),
        ("Nieve", "Blue dragons", 4, 110, 170, 1, ["Dragon Slayer I"], None),
        ("Nieve", "Boss", 8, 3, 35, 1, [], "Like a boss"),
        ("Nieve", "Brine rats", 3, 120, 185, 47, ["Olaf's Quest"], None),
        ("Nieve", "Cave horrors", 5, 120, 180, 58, ["Cabin Fever"], None),
        ("Nieve", "Cave kraken", 6, 100, 120, 87, [], None),
        ("Nieve", "Dagannoths", 8, 120, 185, 1, ["Horror from the Deep"], None),
        ("Nieve", "Dark beasts", 11, 10, 20, 90, ["Mourning's End Part II"], None),
        ("Nieve", "Drakes", 7, 30, 95, 84, [], None),
        ("Nieve", "Dust devils", 6, 120, 185, 65, ["Desert Treasure I"], None),
        ("Nieve", "Elves", 4, 60, 90, 1, ["Regicide"], None),
        ("Nieve", "Fire giants", 9, 120, 185, 1, [], None),
        ("Nieve", "Fossil Island wyverns", 5, 5, 25, 66, ["Bone Voyage", "Elemental Workshop I"], None),
        ("Nieve", "Gargoyles", 8, 120, 185, 75, ["Priest in Peril"], None),
        ("Nieve", "Greater demons", 7, 120, 185, 1, [], None),
        ("Nieve", "Hellhounds", 8, 120, 185, 1, [], None),
        ("Nieve", "Iron dragons", 5, 30, 60, 1, ["Dragon Slayer I"], None),
        ("Nieve", "Kalphite", 9, 120, 185, 1, [], None),
        ("Nieve", "Kurask", 3, 120, 185, 70, [], None),
        ("Nieve", "Lizardmen", 10, 130, 210, 1, [], "Reptile got ripped"),
        ("Nieve", "Minions of Scabaras", 4, 30, 60, 1, ["Contact!"], None),
        ("Nieve", "Mithril dragons", 5, 4, 8, 1, ["Barbarian Training"], "I hope you mith me"),
        ("Nieve", "Mutated Zygomites", 2, 10, 25, 57, ["Lost City"], None),
        ("Nieve", "Nechryael", 9, 110, 170, 80, [], None),
        ("Nieve", "Red dragons", 8, 30, 65, 1, ["Dragon Slayer I"], "Seeing red"),
        ("Nieve", "Rune dragons", 2, 3, 8, 1, ["Dragon Slayer II"], None),
        ("Nieve", "Skeletal Wyverns", 7, 20, 40, 72, ["Elemental Workshop I"], None),
        ("Nieve", "Smoke devils", 7, 120, 185, 93, [], None),
        ("Nieve", "Spiritual creatures", 6, 120, 185, 63, ["Death Plateau"], None),
        ("Nieve", "Steel dragons", 7, 10, 20, 1, ["Dragon Slayer I"], None),
        ("Nieve", "Suqah", 8, 60, 90, 1, ["Lunar Diplomacy"], None),
        ("Nieve", "Trolls", 6, 120, 185, 1, [], None),
        ("Nieve", "Turoth", 3, 120, 185, 55, [], None),
        ("Nieve", "TzHaar", 10, 110, 180, 1, [], "Hot stuff"),
        ("Nieve", "Vampyres", 8, 110, 170, 1, [], "Actual Vampyre Slayer"),
        ("Nieve", "Warped creatures", 8, 120, 185, 1, [], "Warped Reality"),
        ("Nieve", "Waterfiends", 2, 130, 200, 1, ["Barbarian Training"], None),
        ("Nieve", "Wyrms", 7, 80, 145, 62, [], None),
        ("Duradel", "Aberrant spectres", 6, 130, 200, 60, ["Priest in Peril"], None),
        ("Duradel", "Abyssal demons", 12, 130, 200, 85, ["Priest in Peril", "Fairytale II - Cure a Queen"], None),
        ("Duradel", "Adamant dragons", 2, 4, 9, 1, ["Dragon Slayer II"], None),
        ("Duradel", "Ankou", 5, 50, 80, 1, [], None),
        ("Duradel", "Araxytes", 10, 60, 80, 92, ["Priest in Peril"], None),
        ("Duradel", "Aviansie", 8, 120, 200, 1, [], "Watch the birdie"),
        ("Duradel", "Basilisks", 7, 130, 200, 40, [], "Basilocked"),
        ("Duradel", "Black demons", 8, 130, 200, 1, [], None),
        ("Duradel", "Black dragons", 9, 10, 20, 1, ["Dragon Slayer I"], None),
        ("Duradel", "Bloodvelds", 8, 130, 200, 50, ["Priest in Peril"], None),
        ("Duradel", "Blue dragons", 4, 110, 170, 1, ["Dragon Slayer I"], None),
        ("Duradel", "Boss", 12, 3, 35, 1, [], "Like a boss"),
        ("Duradel", "Cave horrors", 4, 130, 200, 58, ["Cabin Fever"], None),
        ("Duradel", "Cave kraken", 9, 100, 120, 87, [], None),
        ("Duradel", "Dagannoths", 9, 130, 200, 1, ["Horror from the Deep"], None),
        ("Duradel", "Dark beasts", 11, 10, 20, 90, ["Mourning's End Part II"], None),
        ("Duradel", "Drakes", 8, 50, 110, 84, [], None),
        ("Duradel", "Dust devils", 5, 130, 200, 65, ["Desert Treasure I"], None),
        ("Duradel", "Elves", 4, 110, 170, 1, ["Regicide"], None),
        ("Duradel", "Fire giants", 7, 130, 200, 1, [], None),
        ("Duradel", "Fossil Island wyverns", 7, 20, 50, 66, ["Bone Voyage", "Elemental Workshop I"], None),
        ("Duradel", "Gargoyles", 8, 130, 200, 75, ["Priest in Peril"], None),
        ("Duradel", "Greater demons", 9, 130, 200, 1, [], None),
        ("Duradel", "Hellhounds", 10, 130, 200, 1, [], None),
        ("Duradel", "Iron dragons", 6, 40, 60, 1, ["Dragon Slayer I"], None),
        ("Duradel", "Kalphite", 9, 130, 200, 1, [], None),
        ("Duradel", "Kurask", 4, 130, 200, 70, [], None),
        ("Duradel", "Lizardmen", 10, 130, 210, 1, [], "Reptile got ripped"),
        ("Duradel", "Minions of Scabaras", 4, 30, 60, 1, ["Contact!"], None),
        ("Duradel", "Mithril dragons", 9, 5, 10, 1, ["Barbarian Training"], "I hope you mith me"),
        ("Duradel", "Mutated Zygomites", 2, 20, 30, 57, ["Lost City"], None),
        ("Duradel", "Nechryael", 11, 130, 200, 80, [], None),
        ("Duradel", "Red dragons", 8, 30, 65, 1, ["Dragon Slayer I"], "Seeing red"),
        ("Duradel", "Rune dragons", 2, 3, 8, 1, ["Dragon Slayer II"], None),
        ("Duradel", "Skeletal Wyverns", 7, 20, 40, 72, ["Elemental Workshop I"], None),
        ("Duradel", "Smoke devils", 9, 130, 200, 93, [], None),
        ("Duradel", "Spiritual creatures", 7, 130, 200, 63, ["Death Plateau"], None),
        ("Duradel", "Steel dragons", 7, 10, 20, 1, ["Dragon Slayer I"], None),
        ("Duradel", "Suqah", 8, 60, 90, 1, ["Lunar Diplomacy"], None),
        ("Duradel", "Trolls", 6, 130, 200, 1, [], None),
        ("Duradel", "TzHaar", 10, 130, 199, 1, [], "Hot stuff"),
        ("Duradel", "Vampyres", 8, 100, 210, 1, [], "Actual Vampyre Slayer"),
        ("Duradel", "Warped creatures", 8, 130, 200, 1, [], "Warped Reality"),
        ("Duradel", "Waterfiends", 2, 130, 200, 1, ["Barbarian Training"], None),
        ("Duradel", "Wyrms", 8, 100, 160, 62, [], None),
        ("Krystilia", "Abyssal demons", 5, 75, 125, 85, ["Priest in Peril"], "Slayer task assignments of abyssal demons, dust devils, jellies, and nechryaels from Krystilia can be enabled or disabled for free."),
        ("Krystilia", "Ankou", 6, 75, 125, 1, [], None),
        ("Krystilia", "Aviansie", 7, 75, 125, 1, [], "Watch the birdie"),
        ("Krystilia", "Bandits", 4, 75, 125, 1, [], None),
        ("Krystilia", "Bears", 6, 65, 100, 1, [], None),
        ("Krystilia", "Black demons", 7, 100, 150, 1, [], None),
        ("Krystilia", "Black dragons", 4, 8, 16, 1, [], None),
        ("Krystilia", "Black Knights", 3, 75, 125, 1, [], None),
        ("Krystilia", "Bloodvelds", 4, 70, 110, 50, ["Priest in Peril"], None),
        ("Krystilia", "Chaos druids", 5, 50, 90, 1, [], None),
        ("Krystilia", "Dark warriors", 4, 75, 125, 1, [], None),
        ("Krystilia", "Dust devils", 5, 75, 125, 65, ["Desert Treasure I"], "Slayer task assignments of abyssal demons, dust devils, jellies, and nechryaels from Krystilia can be enabled or disabled for free."),
        ("Krystilia", "Earth warriors", 6, 75, 125, 1, [], None),
        ("Krystilia", "Ents", 5, 35, 60, 1, [], None),
        ("Krystilia", "Fire giants", 7, 75, 125, 1, [], None),
        ("Krystilia", "Greater demons", 8, 100, 150, 1, [], None),
        ("Krystilia", "Green dragons", 4, 65, 100, 1, [], None),
        ("Krystilia", "Hellhounds", 7, 75, 125, 1, [], None),
        ("Krystilia", "Hill Giants", 3, 75, 125, 1, [], None),
        ("Krystilia", "Ice giants", 6, 100, 150, 1, [], None),
        ("Krystilia", "Ice warriors", 7, 100, 150, 1, [], None),
        ("Krystilia", "Jellies", 5, 100, 150, 52, [], "Slayer task assignments of abyssal demons, dust devils, jellies, and nechryaels from Krystilia can be enabled or disabled for free."),
        ("Krystilia", "Lava dragons", 3, 35, 60, 1, [], None),
        ("Krystilia", "Lesser demons", 6, 80, 120, 1, [], None),
        ("Krystilia", "Magic axes", 7, 75, 125, 1, [], None),
        ("Krystilia", "Mammoths", 6, 75, 125, 1, [], None),
        ("Krystilia", "Moss giants", 4, 100, 150, 1, [], None),
        ("Krystilia", "Nechryael", 5, 75, 125, 80, [], "Slayer task assignments of abyssal demons, dust devils, jellies, and nechryaels from Krystilia can be enabled or disabled for free."),
        ("Krystilia", "Pirates", 3, 62, 75, 1, [], None),
        ("Krystilia", "Revenants", 5, 40, 100, 1, [], None),
        ("Krystilia", "Rogues", 5, 75, 125, 1, [], None),
        ("Krystilia", "Scorpions", 6, 65, 100, 1, [], None),
        ("Krystilia", "Skeletons", 5, 65, 100, 1, [], None),
        ("Krystilia", "Spiders", 6, 65, 100, 1, [], None),
        ("Krystilia", "Spiritual creatures", 6, 100, 150, 63, ["Death Plateau"], None),
        ("Krystilia", "Zombies", 3, 75, 125, 1, [], None),
        ("Krystilia", "Wilderness bosses", 8, 3, 35, 1, [], "Like a boss")
    ]
    
    # Create tasks from master assignments if they don't exist
    all_tasks_in_assignments = {assignment[1]: assignment[5] for assignment in master_assignments}
    for task_name, slayer_req in all_tasks_in_assignments.items():
        db.add_task(task_name, slayer_req)

    # Now get all tasks from DB to get their IDs
    tasks = db.get_all_tasks()
    task_ids = {task['name']: task['id'] for task in tasks}

    # Add monsters with their task assignments
    for name, limit in common_monsters:
        
        # Apply the ln(2) calculation for monsters with a drop rate
        if limit != -1:
            kill_limit = math.ceil(limit * math.log(2))
        else:
            kill_limit = -1
            
        if name in monster_task_mapping:
            task_names = monster_task_mapping[name]
            assigned_task_ids = [task_ids[task_name] for task_name in task_names if task_name in task_ids]
            if assigned_task_ids:
                db.add_monster(name, kill_limit, assigned_task_ids)
    
    # Get slayer master IDs
    masters = db.get_slayer_masters()
    master_ids = {master['name']: master['id'] for master in masters}
    
    # Assign tasks to masters
    for master_name, task_name, weight, min_amt, max_amt, slayer_level, quest_unlocks, slayer_unlock in master_assignments:
        if master_name in master_ids and task_name in task_ids:
            db.add_master_task_assignment(
                master_ids[master_name],
                task_ids[task_name],
                weight,
                min_amt,
                max_amt,
                quest_unlocks,
                slayer_unlock
            )
    
    return jsonify({'success': True, 'message': 'Common tasks initialized!'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)