# vip.py
from datetime import datetime, timedelta
from storage.db import get_connection

# مدة VIP بالثواني (مثال: ساعة واحدة)
VIP_DURATION = 60 * 60  # يمكن تغييره حسب الحاجة

def start_vip(user_id: int):
    """
    تسجيل وقت بداية VIP عند التفعيل.
    عند استدعاء هذه الدالة، يبدأ عدّ مدة الـ VIP.
    """
    now = datetime.utcnow()
    conn = get_connection()
    cur = conn.cursor()
    # تأكد أن المستخدم موجود في جدول users
    cur.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
    # سجل وقت بداية الـ VIP
    cur.execute("UPDATE users SET vip_start = ? WHERE id = ?", (now.isoformat(), user_id))
    conn.commit()
    conn.close()

def is_vip_active(user_id: int) -> bool:
    """
    التحقق إذا كان VIP مازال فعال.
    ترجع True إذا لا زالت المدة متبقية، False خلاف ذلك.
    """
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute("SELECT vip_start FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    if not row or not row[0]:
        return False

    try:
        vip_start = datetime.fromisoformat(row[0])
    except ValueError:
        return False  # في حال كان التاريخ غير صحيح

    elapsed = (datetime.utcnow() - vip_start).total_seconds()
    return elapsed < VIP_DURATION

def get_remaining_time(user_id: int) -> int:
    """
    الحصول على الوقت المتبقي بالثواني للـ VIP.
    إذا لم يكن VIP فعال، يرجع 0.
    """
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute("SELECT vip_start FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    if not row or not row[0]:
        return 0

    try:
        vip_start = datetime.fromisoformat(row[0])
    except ValueError:
        return 0

    elapsed = (datetime.utcnow() - vip_start).total_seconds()
    remaining = VIP_DURATION - elapsed
    return max(0, int(remaining))