# chat_state = {}

# def set_state(user_id, data):
#     chat_state[user_id] = data

# def get_state(user_id):
#     return chat_state.get(user_id)

# def clear_state(user_id):
#     chat_state.pop(user_id, None)

chat_state = {}

def set_state(user_id, data):
    chat_state[user_id] = data

def get_state(user_id):
    return chat_state.get(user_id)

def clear_state(user_id):
    chat_state.pop(user_id, None)