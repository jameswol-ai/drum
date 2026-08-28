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

# ---------- Default state ----------
DEFAULT_STATE = {
    "buildings": [],
    "logs": []
}

# ---------- Utility functions ----------
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

    # If stored password looks like a hash, verify normally
    if stored_pw.startswith(("pbkdf2:", "scrypt:")):
        if check_password_hash(stored_pw, password):
            return user
        return None

    # Legacy plain‑text password – allow once and upgrade
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

# ---------- Memory (per‑user data) ----------
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
    log_entry = {
        "time": datetime.now().isoformat(),
        "msg": message
    }
    memory.setdefault("logs", []).append(log_entry)
    memory["logs"] = memory["logs"][-100:]
    save_memory(username, memory)

# ---------- Building model ----------
class Building:
    def __init__(self, name="Untitled", score=0, plan=None, id=None):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.score = score
        self.plan = plan or []
        self.created_at = datetime.now().isoformat()

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "score": self.score,
            "plan": self.plan,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data):
        b = cls(name=data.get("name", "Untitled"),
                score=data.get("score", 0),
                plan=data.get("plan", []),
                id=data.get("id"))
        b.created_at = data.get("created_at", b.created_at)
        return b

# ---------- Plan generation (simple random) ----------
def generate_plan(building, num_rooms=5):
    import random
    colors = ["#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6"]
    plan = []
    for i in range(num_rooms):
        w = random.randint(100, 200) * 5
        h = random.randint(100, 200) * 5
        x = random.randint(0, 800 - w)
        y = random.randint(0, 500 - h)
        plan.append({
            "x": x, "y": y, "w": w, "h": h,
            "name": f"Room {i+1}",
            "color": random.choice(colors)
        })
    building.plan = plan

# ---------- Quests (simplified) ----------
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

# ---------- Placeholders for other functions ----------
def simulate_evolution(building):
    building.score += 1
    return building

def generate_rhythm():
    return "♩♪♫"

# ---------- User Management (Roles & Permissions) ----------
def list_users():
    """Return list of all users (dicts with username, role)."""
    users = load_users()
    return [{"username": u, "role": data.get("role", "viewer")} for u, data in users.items()]

def update_user_role(username, new_role):
    """Change user's role."""
    allowed_roles = {"admin", "engineer", "viewer"}
    if new_role not in allowed_roles:
        raise ValueError(f"Role must be one of {allowed_roles}")
    users = load_users()
    if username not in users:
        raise ValueError("User not found")
    users[username]["role"] = new_role
    save_users(users)

def delete_user(username):
    """Delete a user (prevent deleting the last admin)."""
    users = load_users()
    if username not in users:
        return False
    # Ensure at least one admin remains
    if users[username]["role"] == "admin":
        admin_count = sum(1 for u in users.values() if u.get("role") == "admin")
        if admin_count <= 1:
            raise ValueError("Cannot delete the last admin account")
    del users[username]
    save_users(users)
    return True

def is_admin(user_data):
    """Return True if user is admin."""
    return user_data and user_data.get("role") == "admin"

def is_engineer(user_data):
    """Return True if user is engineer or admin."""
    return user_data and user_data.get("role") in ("admin", "engineer")