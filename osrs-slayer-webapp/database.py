import sqlite3
import json
from datetime import datetime

class SlayerDatabase:
    def __init__(self, db_name='slayer_tracker.db'):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monsters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                kill_limit INTEGER NOT NULL,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                monster_id INTEGER,
                kills INTEGER DEFAULT 0,
                FOREIGN KEY (monster_id) REFERENCES monsters (id),
                UNIQUE(monster_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS slayer_masters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                combat_requirement INTEGER DEFAULT 0,
                slayer_requirement INTEGER DEFAULT 0,
                points_per_task INTEGER DEFAULT 0,
                points_per_10th INTEGER DEFAULT 0
            )
        ''')
        
        # Global tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                slayer_requirement INTEGER DEFAULT 1
            )
        ''')
        
        # Which masters can assign which tasks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS master_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slayer_master_id INTEGER,
                task_id INTEGER,
                weight INTEGER DEFAULT 1,
                min_amount INTEGER DEFAULT 10,
                max_amount INTEGER DEFAULT 50,
                quest_unlocks TEXT,
                slayer_unlock TEXT,
                FOREIGN KEY (slayer_master_id) REFERENCES slayer_masters (id),
                FOREIGN KEY (task_id) REFERENCES tasks (id),
                UNIQUE(slayer_master_id, task_id)
            )
        ''')
        
        # Which monsters belong to which tasks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_monsters (
                task_id INTEGER,
                monster_id INTEGER,
                FOREIGN KEY (task_id) REFERENCES tasks (id),
                FOREIGN KEY (monster_id) REFERENCES monsters (id),
                PRIMARY KEY (task_id, monster_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_data (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocked_tasks (
                slayer_master_id INTEGER,
                task_id INTEGER,
                FOREIGN KEY (slayer_master_id) REFERENCES slayer_masters (id),
                FOREIGN KEY (task_id) REFERENCES tasks (id),
                PRIMARY KEY (slayer_master_id, task_id)
            )
        ''')
        
        # Initialize slayer masters if they don't exist
        masters = [
            ('Turael', 0, 1, 0, 0),
            ('Mazchna', 20, 1, 2, 5),
            ('Vannaka', 40, 1, 4, 20),
            ('Chaeldar', 70, 1, 10, 50),
            ('Nieve', 85, 1, 12, 60),
            ('Duradel', 100, 50, 15, 75),
            ('Krystilia', 0, 1, 25, 125),
            ('Spria', 0, 1, 0, 0)
        ]
        
        for master in masters:
            cursor.execute('''
                INSERT OR IGNORE INTO slayer_masters 
                (name, combat_requirement, slayer_requirement, points_per_task, points_per_10th)
                VALUES (?, ?, ?, ?, ?)
            ''', master)
        
        # Initialize player data with defaults
        player_defaults = {
            'slayer_points': '0',
            'task_streak': '0',
            'combat_level': '3',
            'slayer_level': '1',
            'completed_quests': '[]',
            'slayer_unlocks': '[]',
            'block_slots': '0'
        }
        for key, value in player_defaults.items():
            cursor.execute('INSERT OR IGNORE INTO player_data (key, value) VALUES (?, ?)', (key, value))

        
        conn.commit()
        conn.close()
    
    # Monster Management
    def add_monster(self, name, kill_limit, task_ids):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Insert monster
            cursor.execute('INSERT INTO monsters (name, kill_limit) VALUES (?, ?)', 
                          (name, kill_limit))
            monster_id = cursor.lastrowid
            
            # Initialize kill counter
            cursor.execute('INSERT INTO kills (monster_id, kills) VALUES (?, 0)', 
                          (monster_id,))
            
            # Link monster to tasks
            for task_id in task_ids:
                cursor.execute('INSERT INTO task_monsters (task_id, monster_id) VALUES (?, ?)',
                              (task_id, monster_id))
            
            conn.commit()
            return True, "Monster added successfully!"
        except sqlite3.IntegrityError:
            return False, "Monster already exists!"
        except Exception as e:
            conn.rollback()
            return False, f"Error: {str(e)}"
        finally:
            conn.close()
    
    def update_monster_drop_rate(self, monster_id, new_kill_limit):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('UPDATE monsters SET kill_limit = ? WHERE id = ?',
                          (new_kill_limit, monster_id))
            conn.commit()
            return True, "Drop rate updated successfully!"
        except Exception as e:
            return False, f"Error: {str(e)}"
        finally:
            conn.close()
    
    def get_all_monsters(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.id, m.name, m.kill_limit, COALESCE(k.kills, 0) as current_kills
            FROM monsters m
            LEFT JOIN kills k ON m.id = k.monster_id
            ORDER BY m.name
        ''')
        
        monsters = []
        for row in cursor.fetchall():
            # Get tasks for this monster
            cursor.execute('''
                SELECT t.id, t.name
                FROM task_monsters tm
                JOIN tasks t ON tm.task_id = t.id
                WHERE tm.monster_id = ?
                ORDER BY t.name
            ''', (row['id'],))
            
            tasks = [{'id': task['id'], 'name': task['name']} for task in cursor.fetchall()]
            
            monsters.append({
                'id': row['id'],
                'name': row['name'],
                'kill_limit': row['kill_limit'],
                'current_kills': row['current_kills'],
                'remaining': -1 if row['kill_limit'] == -1 else row['kill_limit'] - row['current_kills'],
                'tasks': tasks
            })
        
        conn.close()
        return monsters
    
    def record_kills(self, monster_id, kills):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE kills 
            SET kills = kills + ? 
            WHERE monster_id = ?
        ''', (kills, monster_id))
        
        if cursor.rowcount == 0:
            cursor.execute('INSERT INTO kills (monster_id, kills) VALUES (?, ?)', 
                          (monster_id, kills))
        
        conn.commit()
        conn.close()
        return True
    
    # Task Management
    def add_task(self, name, slayer_requirement):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO tasks (name, slayer_requirement)
                VALUES (?, ?)
            ''', (name, slayer_requirement))
            
            conn.commit()
            return True, "Task added successfully!"
        except sqlite3.IntegrityError:
            return False, "Task already exists!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    
    def add_master_task_assignment(self, slayer_master_id, task_id, weight, min_amount, max_amount, quest_unlocks, slayer_unlock):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO master_tasks 
                (slayer_master_id, task_id, weight, min_amount, max_amount, quest_unlocks, slayer_unlock)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (slayer_master_id, task_id, weight, min_amount, max_amount, json.dumps(quest_unlocks), slayer_unlock))
            
            conn.commit()
            return True
        except Exception as e:
            return False
        finally:
            conn.close()

    def get_tasks_for_master(self, master_id, player_info=None):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT t.id, t.name, t.slayer_requirement,
                   mt.weight, mt.min_amount, mt.max_amount,
                   mt.quest_unlocks, mt.slayer_unlock,
                   sm.combat_requirement
            FROM master_tasks mt
            JOIN tasks t ON mt.task_id = t.id
            JOIN slayer_masters sm ON mt.slayer_master_id = sm.id
            WHERE mt.slayer_master_id = ?
            ORDER BY t.name
        ''', (master_id,))

        tasks = []
        for row in cursor.fetchall():
            task_id = row['id']

            # Basic requirements check
            is_assignable = True
            if player_info:
                # Check combat and slayer levels
                if player_info['combat_level'] < row['combat_requirement']: is_assignable = False
                if player_info['slayer_level'] < row['slayer_requirement']: is_assignable = False

                # Check quest unlocks (must have all)
                quest_unlocks = json.loads(row['quest_unlocks']) if row['quest_unlocks'] else []
                if not all(q in player_info['completed_quests'] for q in quest_unlocks):
                    is_assignable = False

                # Check slayer unlock (must have it if specified)
                if row['slayer_unlock'] and row['slayer_unlock'] not in player_info['slayer_unlocks']:
                    is_assignable = False

            # Get monsters for this task
            cursor.execute('''
                SELECT m.id, m.name, m.kill_limit, COALESCE(k.kills, 0) as current_kills
                FROM task_monsters tm
                JOIN monsters m ON tm.monster_id = m.id
                LEFT JOIN kills k ON m.id = k.monster_id
                WHERE tm.task_id = ?
            ''', (task_id,))

            monsters = []
            can_do_task = False
            avg_task_size = (row['min_amount'] + row['max_amount']) / 2
            
            for monster_row in cursor.fetchall():
                kill_limit = monster_row['kill_limit']
                current_kills = monster_row['current_kills']
                remaining_kills = -1 if kill_limit == -1 else kill_limit - current_kills
                
                can_kill = remaining_kills == -1 or remaining_kills >= avg_task_size
                
                if can_kill:
                    can_do_task = True
                
                monsters.append({
                    'id': monster_row['id'],
                    'name': monster_row['name'],
                    'kill_limit': kill_limit,
                    'current_kills': current_kills,
                    'can_kill': can_kill
                })

            # Check if task is blocked
            cursor.execute('SELECT 1 FROM blocked_tasks WHERE slayer_master_id = ? AND task_id = ?', (master_id, task_id))
            is_blocked = cursor.fetchone() is not None

            tasks.append({
                'id': row['id'],
                'name': row['name'],
                'weight': row['weight'],
                'min_amount': row['min_amount'],
                'max_amount': row['max_amount'],
                'slayer_requirement': row['slayer_requirement'],
                'quest_unlocks': json.loads(row['quest_unlocks']) if row['quest_unlocks'] else [],
                'slayer_unlock': row['slayer_unlock'],
                'monsters': monsters,
                'can_do': can_do_task,
                'is_blocked': is_blocked,
                'is_assignable': is_assignable
            })

        conn.close()
        return tasks
    
    def get_all_tasks(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, slayer_requirement
            FROM tasks
            ORDER BY name
        ''')
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                'id': row['id'],
                'name': row['name'],
                'slayer_requirement': row['slayer_requirement']
            })
        
        conn.close()
        return tasks

    def get_all_unlocks(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get all unique quests
        cursor.execute("SELECT DISTINCT quest_unlocks FROM master_tasks WHERE quest_unlocks IS NOT NULL AND quest_unlocks != '[]'")
        quests = set()
        for row in cursor.fetchall():
            quest_list = json.loads(row['quest_unlocks'])
            for quest in quest_list:
                quests.add(quest)

        # Get all unique slayer unlocks
        cursor.execute("SELECT DISTINCT slayer_unlock FROM master_tasks WHERE slayer_unlock IS NOT NULL")
        slayer_unlocks = {row['slayer_unlock'] for row in cursor.fetchall()}

        conn.close()
        return {
            'quests': sorted(list(quests)),
            'slayer_unlocks': sorted(list(slayer_unlocks))
        }

    
    def get_slayer_masters(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM slayer_masters ORDER BY combat_requirement')
        masters = []
        
        for row in cursor.fetchall():
            masters.append({
                'id': row['id'],
                'name': row['name'],
                'combat_requirement': row['combat_requirement'],
                'slayer_requirement': row['slayer_requirement'],
                'points_per_task': row['points_per_task'],
                'points_per_10th': row['points_per_10th']
            })
        
        conn.close()
        return masters
    
    def block_task(self, master_id, task_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO blocked_tasks (slayer_master_id, task_id)
                VALUES (?, ?)
            ''', (master_id, task_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def unblock_task(self, master_id, task_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM blocked_tasks 
            WHERE slayer_master_id = ? AND task_id = ?
        ''', (master_id, task_id))
        
        conn.commit()
        conn.close()
        return True
    
    def get_player_data(self, key):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM player_data WHERE key = ?', (key,))
        row = cursor.fetchone()
        
        conn.close()
        # Handle JSON fields
        if key in ['completed_quests', 'slayer_unlocks']:
            return json.loads(row['value']) if row else []
        return row['value'] if row else None

    def get_all_player_data(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT key, value FROM player_data')
        data = {}
        for row in cursor.fetchall():
            if row['key'] in ['completed_quests', 'slayer_unlocks']:
                data[row['key']] = json.loads(row['value'])
            else:
                data[row['key']] = row['value']
        conn.close()
        return data

    def set_player_data(self, key, value):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Handle list fields
        val_to_store = json.dumps(value) if isinstance(value, list) else str(value)
        
        cursor.execute('''
            INSERT OR REPLACE INTO player_data (key, value)
            VALUES (?, ?)
        ''', (key, val_to_store))
        
        conn.commit()
        conn.close()
    
    def calculate_master_efficiency(self, master_id, player_info):
        tasks = self.get_tasks_for_master(master_id, player_info)
        
        # Get master info first, which is needed in all cases
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM slayer_masters WHERE id = ?', (master_id,))
        master = cursor.fetchone()
        conn.close()

        # Return a default, zeroed-out structure if master doesn't exist.
        if not master:
            return {
                'total_tasks': 0, 'doable_tasks': 0, 'blocked_tasks': 0, 'skip_rate': 0,
                'avg_points': 0, 'skip_cost': 0, 'net_points': 0
            }

        # Filter for tasks that are assignable
        assignable_tasks = [task for task in tasks if task['is_assignable']]

        # Pre-calculate values
        doable_tasks_count = sum(1 for task in assignable_tasks if task['can_do'] and not task['is_blocked'])
        blocked_tasks_count = sum(1 for task in assignable_tasks if task['is_blocked'])
        avg_points = (9 * master['points_per_task'] + master['points_per_10th']) / 10
        total_weight = sum(task['weight'] for task in assignable_tasks if not task['is_blocked'])
        
        # Handle case with no assignable tasks (all blocked or none exist)
        if total_weight == 0:
            return {
                'total_tasks': len(assignable_tasks),
                'doable_tasks': doable_tasks_count,
                'blocked_tasks': blocked_tasks_count,
                'skip_rate': 100.0 if len(assignable_tasks) > blocked_tasks_count else 0.0,
                'avg_points': avg_points,
                'skip_cost': 30.0 if len(assignable_tasks) > blocked_tasks_count and doable_tasks_count == 0 else 0.0,
                'net_points': avg_points - (30.0 if len(assignable_tasks) > blocked_tasks_count and doable_tasks_count == 0 else 0.0)
            }
        
        # Normal calculation for masters with assignable tasks
        doable_weight = sum(task['weight'] for task in assignable_tasks 
                           if not task['is_blocked'] and task['can_do'])
        
        skip_rate = 1 - (doable_weight / total_weight)
        skip_cost = skip_rate * 30
        
        efficiency = avg_points - skip_cost
        
        return {
            'total_tasks': len(assignable_tasks),
            'doable_tasks': doable_tasks_count,
            'blocked_tasks': blocked_tasks_count,
            'skip_rate': skip_rate * 100,
            'avg_points': avg_points,
            'skip_cost': skip_cost,
            'net_points': efficiency
        }