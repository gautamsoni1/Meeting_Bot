participants_store = {}

def init_meeting(meeting_id):
    participants_store[meeting_id] = {}

def mark_join(meeting_id, user_name):
    if meeting_id not in participants_store:
        participants_store[meeting_id] = {}

    participants_store[meeting_id][user_name] = {
        "name": user_name,
        "join_time": None,
        "leave_time": None
    }

def mark_join_time(meeting_id, user_name, time):
    participants_store[meeting_id][user_name]["join_time"] = time

def mark_leave_time(meeting_id, user_name, time):
    participants_store[meeting_id][user_name]["leave_time"] = time

def get_participants(meeting_id):
    return list(participants_store.get(meeting_id, {}).values())