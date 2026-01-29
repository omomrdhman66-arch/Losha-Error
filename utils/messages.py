import requests
from config.settings import CHANNEL_ICON, TOOL_BY

# ================= USER NAME =================
def get_user_name(user):
    if user.username:
        return f"{user.username} [V I P $]"
    elif user.first_name:
        return user.first_name
    else:
        return str(user.id)


# ================= BIN DATA =================
def dato(zh):
    try:
        api_url = requests.get(
            f"https://bins.antipublic.cc/bins/{zh}",
            timeout=10
        ).json()

        return {
            "brand": api_url.get("brand", "N/A"),
            "type": api_url.get("type", "N/A"),
            "level": api_url.get("level", "N/A"),
            "bank": api_url.get("bank", "N/A"),
            "country": api_url.get("country_name", "N/A"),
            "flag": api_url.get("country_flag", "")
        }

    except Exception as e:
        print(e)
        return {
            "brand": "N/A",
            "type": "N/A",
            "level": "N/A",
            "bank": "N/A",
            "country": "N/A",
            "flag": ""
        }


# ================= APPROVED =================
def approved_message(cc, last, gate_name, execution_time, dato_func):
    info = dato_func(cc[:6])

    return f"""<b>#{gate_name} [{CHANNEL_ICON}] 🌩
- - - - - - - - - - - - - - - - - - - - - -
[{CHANNEL_ICON}] 𝐂𝐚𝐫𝐝: <code>{cc}</code>
[{CHANNEL_ICON}] 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: {last}
[{CHANNEL_ICON}] 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: {gate_name}
[{CHANNEL_ICON}] 𝐓𝐢𝐦𝐞: {execution_time:.2f}s
- - - - - - - - - - - - - - - - - - - - - -
[{CHANNEL_ICON}] 𝐈𝐧𝐟𝐨: {info['brand']} - {info['type']} - {info['level']}
[{CHANNEL_ICON}] 𝐁𝐚𝐧𝐤: {info['bank']}
[{CHANNEL_ICON}] 𝐂𝐨𝐮𝐧𝐭𝐫𝐲: {info['country']} {info['flag']}
- - - - - - - - - - - - - - - - - - - - - -
[⌤] 𝐓𝐨𝐨𝐥 𝐁𝐲: {TOOL_BY}
</b>"""


# ================= CHARGED =================
def charged_message(cc, last, gate_name, execution_time, dato_func):
    info = dato_func(cc[:6])

    return f"""<b>#{gate_name} [{CHANNEL_ICON}] 🌩
- - - - - - - - - - - - - - - - - - - - - -
[{CHANNEL_ICON}] 𝐂𝐚𝐫𝐝: <code>{cc}</code>
[{CHANNEL_ICON}] 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: {last}
[{CHANNEL_ICON}] 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: {gate_name}
[{CHANNEL_ICON}] 𝐓𝐢𝐦𝐞: {execution_time:.2f}s
- - - - - - - - - - - - - - - - - - - - - -
[{CHANNEL_ICON}] 𝐈𝐧𝐟𝐨: {info['brand']} - {info['type']} - {info['level']}
[{CHANNEL_ICON}] 𝐁𝐚𝐧𝐤: {info['bank']}
[{CHANNEL_ICON}] 𝐂𝐨𝐮𝐧𝐭𝐫𝐲: {info['country']} {info['flag']}
- - - - - - - - - - - - - - - - - - - - - -
[⌤] 𝐓𝐨𝐨𝐥 𝐁𝐲: {TOOL_BY}
</b>"""


# ================= FUNDS =================
def insufficient_funds_message(cc, last, gate_name, execution_time, dato_func):
    info = dato_func(cc[:6])

    return f"""<b>#{gate_name} [{CHANNEL_ICON}] 🌩
- - - - - - - - - - - - - - - - - - - - - -
[{CHANNEL_ICON}] 𝐂𝐚𝐫𝐝: <code>{cc}</code>
[{CHANNEL_ICON}] 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: {last}
[{CHANNEL_ICON}] 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: {gate_name}
[{CHANNEL_ICON}] 𝐓𝐢𝐦𝐞: {execution_time:.2f}s
- - - - - - - - - - - - - - - - - - - - - -
[{CHANNEL_ICON}] 𝐈𝐧𝐟𝐨: {info['brand']} - {info['type']} - {info['level']}
[{CHANNEL_ICON}] 𝐁𝐚𝐧𝐤: {info['bank']}
[{CHANNEL_ICON}] 𝐂𝐨𝐮𝐧𝐭𝐫𝐲: {info['country']} {info['flag']}
- - - - - - - - - - - - - - - - - - - - - -
[⌤] 𝐓𝐨𝐨𝐥 𝐁𝐲: {TOOL_BY}
</b>"""


# ================= DECLINED =================
def declined_message(cc, last, gate_name, execution_time, dato_func):
    info = dato_func(cc[:6])

    return f"""<b>#{gate_name} [{CHANNEL_ICON}] 🌩
- - - - - - - - - - - - - - - - - - - - - -
[{CHANNEL_ICON}] 𝐂𝐚𝐫𝐝: <code>{cc}</code>
[{CHANNEL_ICON}] 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: {last}
[{CHANNEL_ICON}] 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: {gate_name}
[{CHANNEL_ICON}] 𝐓𝐢𝐦𝐞: {execution_time:.2f}s
- - - - - - - - - - - - - - - - - - - - - -
[{CHANNEL_ICON}] 𝐈𝐧𝐟𝐨: {info['brand']} - {info['type']} - {info['level']}
[{CHANNEL_ICON}] 𝐁𝐚𝐧𝐤: {info['bank']}
[{CHANNEL_ICON}] 𝐂𝐨𝐮𝐧𝐭𝐫𝐲: {info['country']} {info['flag']}
- - - - - - - - - - - - - - - - - - - - - -
[⌤] 𝐓𝐨𝐨𝐥 𝐁𝐲: {TOOL_BY}
</b>"""


# ================= HIT DETECTED =================
def hit_detected_message(hit_number, name, status_type, execution_time, gateway):
    status_map = {
        "approved": "Approved ✅",
        "charged": "Charged ⚡",
        "funds": "Funds 💸"
    }

    status_text = status_map.get(status_type.lower(), status_type)

    return f"""<b>
[{CHANNEL_ICON}] 𝗛𝗶𝘁 𝗗𝗲𝘁𝗲𝗰𝘁𝗲𝗱 #{hit_number} 🔥
- - - - - - - - - - - - - - - - - - - -
[{CHANNEL_ICON}] 𝐍𝐚𝐦𝐞: {name}
[{CHANNEL_ICON}] 𝐒𝐭𝐚𝐭𝐮𝐬: {status_text}
[{CHANNEL_ICON}] 𝐓𝐢𝐦𝐞: {execution_time:.2f}s
[{CHANNEL_ICON}] 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: {gateway}
- - - - - - - - - - - - - - - - - - - -
[{CHANNEL_ICON}] 𝐓𝐨𝐨𝐥 𝐁𝐲: {TOOL_BY}
</b>"""