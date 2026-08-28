# ---------- Analysis Storage ----------
def save_analysis(username, analysis_type, data):
    """Save an analysis result to user's memory."""
    mem = load_memory(username)
    if "analyses" not in mem:
        mem["analyses"] = []
    analysis_entry = {
        "id": str(uuid.uuid4()),
        "type": analysis_type,
        "data": data,
        "created_at": datetime.now().isoformat(),
    }
    mem["analyses"].append(analysis_entry)
    save_memory(username, mem)
    return analysis_entry["id"]

def get_analyses(username, analysis_type=None):
    """Get all saved analyses for a user, optionally filtered by type."""
    mem = load_memory(username)
    analyses = mem.get("analyses", [])
    if analysis_type:
        return [a for a in analyses if a["type"] == analysis_type]
    return analyses

def delete_analysis(username, analysis_id):
    """Delete a saved analysis."""
    mem = load_memory(username)
    mem["analyses"] = [a for a in mem.get("analyses", []) if a["id"] != analysis_id]
    save_memory(username, mem)

def update_analysis(username, analysis_id, new_data):
    """Update a saved analysis."""
    mem = load_memory(username)
    for a in mem.get("analyses", []):
        if a["id"] == analysis_id:
            a["data"] = new_data
            a["updated_at"] = datetime.now().isoformat()
            break
    save_memory(username, mem)