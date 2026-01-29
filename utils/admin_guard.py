from config.settings import ADMINS

def is_admin(user_id:int)->bool:
    return user_id in ADMINS
