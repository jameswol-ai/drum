# main.py
import json
import os
import uuid
from datetime import datetime
from copy import deepcopy

from werkzeug.security import generate_password_hash, check_password_hash

# ---------- File paths ----------
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(DATA_DIR, "users.json")
MEMORY_DIR = os.path.join(DATA_DIR, "memory")

DEFAULT_STATE = {
    "projects": [],
    "logs": [],
    "settings": {
        "theme": "dark",
        "default_material_costs": {
            "concrete": 150,
            "steel": 80,
            "glass": 120,
            "labor": 100,
        }
    }
}

def ensure_dirs():
    os.makedirs(MEMORY_DIR, exist_ok=True)

def load_users():
    ensure_dirs()
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_users(users):
    ensure_dirs()
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def get_user(username):
    users = load_users()
    return users.get(username)

def create_user(username, password, role="user"):
    users = load_users()
    if username in users:
        raise ValueError("Username already exists")
    users[username] = {
        "password": generate_password_hash(password),
        "role": role,
        "created_at": datetime.now().isoformat(),
        "xp": 0,
        "level": 1,
        "quests": init_quests(),
    }
    save_users(users)
    return users[username]

def authenticate(username, password):
    users = load_users()
    user = users.get(username)
    if not user:
        return None
    stored_pw = user.get("password", "")
    if stored_pw.startswith(("pbkdf2:", "scrypt:")):
        if check_password_hash(stored_pw, password):
            return user
        return None
    if stored_pw == password:
        user["password"] = generate_password_hash(password)
        users[username] = user
        save_users(users)
        return user
    return None

def update_user_data(username, data):
    users = load_users()
    if username in users:
        users[username].update(data)
        save_users(users)

def xp_for_level(level):
    return level * 100

def add_xp(username, amount):
    user = get_user(username)
    if not user:
        return None
    user["xp"] = user.get("xp", 0) + amount
    while user["xp"] >= xp_for_level(user.get("level", 1)):
        user["xp"] -= xp_for_level(user.get("level", 1))
        user["level"] = user.get("level", 1) + 1
    update_user_data(username, user)
    return user

def memory_file(username):
    return os.path.join(MEMORY_DIR, f"{username}.json")

def load_memory(username):
    ensure_dirs()
    path = memory_file(username)
    if not os.path.exists(path):
        return deepcopy(DEFAULT_STATE)
    try:
        with open(path, "r") as f:
            mem = json.load(f)
            for key, val in DEFAULT_STATE.items():
                if key not in mem:
                    mem[key] = val
            return mem
    except (json.JSONDecodeError, IOError):
        return deepcopy(DEFAULT_STATE)

def save_memory(username, memory):
    ensure_dirs()
    path = memory_file(username)
    with open(path, "w") as f:
        json.dump(memory, f, indent=2)

def log_event(username, memory, message):
    log_entry = {"time": datetime.now().isoformat(), "msg": message}
    memory.setdefault("logs", []).append(log_entry)
    memory["logs"] = memory["logs"][-100:]
    save_memory(username, memory)

# ---------- Project Management ----------
class Project:
    def __init__(self, name="Untitled", description="", project_type="building", level="superstructure", id=None):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.project_type = project_type
        self.level = level
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.members = []
        self.drawings = []

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "project_type": self.project_type,
            "level": self.level,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "members": self.members,
            "drawings": self.drawings,
        }

    @classmethod
    def from_dict(cls, data):
        p = cls(
            name=data.get("name", "Untitled"),
            description=data.get("description", ""),
            project_type=data.get("project_type", "building"),
            level=data.get("level", "superstructure"),
            id=data.get("id")
        )
        p.created_at = data.get("created_at", p.created_at)
        p.updated_at = data.get("updated_at", p.updated_at)
        p.members = data.get("members", [])
        p.drawings = data.get("drawings", [])
        return p

def create_project(username, name, description="", project_type="building", level="superstructure"):
    mem = load_memory(username)
    project = Project(name=name, description=description, project_type=project_type, level=level)
    mem["projects"].append(project.to_dict())
    save_memory(username, mem)
    return project

def get_projects(username):
    mem = load_memory(username)
    return [Project.from_dict(p) for p in mem.get("projects", [])]

def get_project(username, project_id):
    projects = get_projects(username)
    for p in projects:
        if p.id == project_id:
            return p
    return None

def update_project(username, project_id, name=None, description=None, project_type=None, level=None):
    mem = load_memory(username)
    for p in mem.get("projects", []):
        if p["id"] == project_id:
            if name is not None:
                p["name"] = name
            if description is not None:
                p["description"] = description
            if project_type is not None:
                p["project_type"] = project_type
            if level is not None:
                p["level"] = level
            p["updated_at"] = datetime.now().isoformat()
            break
    save_memory(username, mem)

def delete_project(username, project_id):
    mem = load_memory(username)
    mem["projects"] = [p for p in mem.get("projects", []) if p["id"] != project_id]
    save_memory(username, mem)

# ---------- Member Management ----------
def add_member(username, project_id, member_type, name, properties, level="superstructure"):
    mem = load_memory(username)
    member = {
        "id": str(uuid.uuid4()),
        "type": member_type,
        "name": name,
        "properties": properties,
        "level": level,
        "analyses": [],
        "created_at": datetime.now().isoformat(),
    }
    for p in mem.get("projects", []):
        if p["id"] == project_id:
            p["members"].append(member)
            break
    save_memory(username, mem)
    return member

def get_members(username, project_id, level=None):
    project = get_project(username, project_id)
    if project:
        if level:
            return [m for m in project.members if m.get("level") == level]
        return project.members
    return []

def update_member(username, project_id, member_id, name=None, properties=None, level=None):
    mem = load_memory(username)
    for p in mem.get("projects", []):
        if p["id"] == project_id:
            for m in p["members"]:
                if m["id"] == member_id:
                    if name is not None:
                        m["name"] = name
                    if properties is not None:
                        m["properties"] = properties
                    if level is not None:
                        m["level"] = level
                    break
    save_memory(username, mem)

def delete_member(username, project_id, member_id):
    mem = load_memory(username)
    for p in mem.get("projects", []):
        if p["id"] == project_id:
            p["members"] = [m for m in p["members"] if m["id"] != member_id]
            break
    save_memory(username, mem)

def add_member_analysis(username, project_id, member_id, analysis_type, data):
    mem = load_memory(username)
    analysis_entry = {
        "id": str(uuid.uuid4()),
        "type": analysis_type,
        "data": data,
        "created_at": datetime.now().isoformat(),
    }
    for p in mem.get("projects", []):
        if p["id"] == project_id:
            for m in p["members"]:
                if m["id"] == member_id:
                    m["analyses"].append(analysis_entry)
                    break
    save_memory(username, mem)
    return analysis_entry

def delete_member_analysis(username, project_id, member_id, analysis_id):
    mem = load_memory(username)
    for p in mem.get("projects", []):
        if p["id"] == project_id:
            for m in p["members"]:
                if m["id"] == member_id:
                    m["analyses"] = [a for a in m["analyses"] if a["id"] != analysis_id]
                    break
    save_memory(username, mem)

# ---------- Drawing Management ----------
def add_drawing(username, project_id, drawing_name, drawing_type, level, file_data=None):
    mem = load_memory(username)
    drawing = {
        "id": str(uuid.uuid4()),
        "name": drawing_name,
        "type": drawing_type,
        "level": level,
        "file_data": file_data,
        "created_at": datetime.now().isoformat(),
    }
    for p in mem.get("projects", []):
        if p["id"] == project_id:
            p["drawings"].append(drawing)
            break
    save_memory(username, mem)
    return drawing

def get_drawings(username, project_id):
    project = get_project(username, project_id)
    if project:
        return project.drawings
    return []

def delete_drawing(username, project_id, drawing_id):
    mem = load_memory(username)
    for p in mem.get("projects", []):
        if p["id"] == project_id:
            p["drawings"] = [d for d in p["drawings"] if d["id"] != drawing_id]
            break
    save_memory(username, mem)

# ---------- Analysis Storage ----------
def save_analysis(username, analysis_type, data, project_id=None):
    mem = load_memory(username)
    if "analyses" not in mem:
        mem["analyses"] = []
    analysis_entry = {
        "id": str(uuid.uuid4()),
        "type": analysis_type,
        "data": data,
        "created_at": datetime.now().isoformat(),
        "project_id": project_id,
    }
    mem["analyses"].append(analysis_entry)
    save_memory(username, mem)
    return analysis_entry["id"]

def get_analyses(username, analysis_type=None, project_id=None):
    mem = load_memory(username)
    analyses = mem.get("analyses", [])
    if analysis_type:
        analyses = [a for a in analyses if a["type"] == analysis_type]
    if project_id:
        analyses = [a for a in analyses if a.get("project_id") == project_id]
    return analyses

def delete_analysis(username, analysis_id):
    mem = load_memory(username)
    mem["analyses"] = [a for a in mem.get("analyses", []) if a["id"] != analysis_id]
    save_memory(username, mem)

# ---------- User Management ----------
def list_users():
    users = load_users()
    return [{"username": u, "role": data.get("role", "viewer")} for u, data in users.items()]

def update_user_role(username, new_role):
    allowed_roles = {"admin", "engineer", "viewer"}
    if new_role not in allowed_roles:
        raise ValueError(f"Role must be one of {allowed_roles}")
    users = load_users()
    if username not in users:
        raise ValueError("User not found")
    users[username]["role"] = new_role
    save_users(users)

def delete_user(username):
    users = load_users()
    if username not in users:
        return False
    if users[username]["role"] == "admin":
        admin_count = sum(1 for u in users.values() if u.get("role") == "admin")
        if admin_count <= 1:
            raise ValueError("Cannot delete the last admin account")
    del users[username]
    save_users(users)
    return True

def is_admin(user_data):
    return user_data and user_data.get("role") == "admin"

def is_engineer(user_data):
    return user_data and user_data.get("role") in ("admin", "engineer")

# ---------- Settings ----------
def get_material_costs(username):
    mem = load_memory(username)
    return mem.get("settings", {}).get("default_material_costs", {
        "concrete": 150, "steel": 80, "glass": 120, "labor": 100,
    })

def update_material_costs(username, costs):
    mem = load_memory(username)
    if "settings" not in mem:
        mem["settings"] = {}
    mem["settings"]["default_material_costs"] = costs
    save_memory(username, mem)

def get_theme(username):
    mem = load_memory(username)
    return mem.get("settings", {}).get("theme", "dark")

def update_theme(username, theme):
    mem = load_memory(username)
    if "settings" not in mem:
        mem["settings"] = {}
    mem["settings"]["theme"] = theme
    save_memory(username, mem)

# ---------- Quests ----------
def init_quests():
    return {
        "create_project": {"progress": 0, "target": 1, "completed": False},
        "run_analysis": {"progress": 0, "target": 1, "completed": False},
    }

def update_quests(username, quest_id, progress_increment=1):
    user = get_user(username)
    if not user:
        return
    quests = user.get("quests", init_quests())
    if quest_id in quests:
        q = quests[quest_id]
        if not q["completed"]:
            q["progress"] = min(q["target"], q["progress"] + progress_increment)
            if q["progress"] >= q["target"]:
                q["completed"] = True
        user["quests"] = quests
        update_user_data(username, user)

def grant_quest_rewards(username, quest_id):
    user = get_user(username)
    if not user:
        return
    quests = user.get("quests", {})
    q = quests.get(quest_id)
    if q and q["completed"] and not q.get("rewarded", False):
        add_xp(username, 50)
        q["rewarded"] = True
        user["quests"] = quests
        update_user_data(username, user)