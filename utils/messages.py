# utils/messages.py
import requests


def dato(zh):
    try:
        api_url = requests.get(
            f"https://bins.antipublic.cc/bins/{zh}",
            timeout=10
        ).json()

        brand = api_url.get("brand", "N/A")
        card_type = api_url.get("type", "N/A")
        level = api_url.get("level", "N/A")
        bank = api_url.get("bank", "N/A")
        country_name = api_url.get("country_name", "N/A")
        country_flag = api_url.get("country_flag", "")

        return (
            f"ϟ𝗜𝗻𝗳𝗼 ⇾ {brand} - {card_type} - {level}\n"
            f"ϟ 𝐈𝐬𝐬𝐮𝐞𝐫 ⇾ {bank} - {country_flag}\n"
            f"ϟ 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⇾ {country_name} [ {country_flag} ]"
        )

    except Exception as e:
        print(e)
        return "No info"


def approved_message(cc, last, gate_name, execution_time, dato):
    return f"""<b>
𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱 ✅

[❖] 𝗖𝗖 ⇾ <code>{cc}</code>
[❖] 𝗥𝗘𝗦𝗣𝗢𝗡𝗦𝗘 → {last}
[❖] 𝗚𝗔𝗧𝗘𝗦 ⇾ {gate_name}
━━━━━━━━━━━━━━━━
{dato(cc[:6]).strip()}
━━━━━━━━━━━━━━━━
[❖] 𝗣𝗿𝗼𝘅𝘆 ⇾ 𝗟𝗶𝘃𝗲 [1XX.XX.XX 🟢]
━━━━━━━━━━━━━━━━
[❖] 𝗧𝗶𝗺𝗲 𝗧𝗮𝗸𝗲𝗻 ⇾ {"{:.1f}".format(execution_time)} Seconds
━━━━━━━━━━━━━━━━
[❖] 𝗕𝗼𝘁 𝗕𝘆 ⇾ 『@I_EOR』
</b>"""


def charged_message(cc, last, gate_name, execution_time, dato):
    return f"""<b>
𝗖𝗵𝗮𝗿𝗴𝗲𝗱 1$ ⚡

[❖] 𝗖𝗖 ⇾ <code>{cc}</code>
[❖] 𝗥𝗘𝗦𝗣𝗢𝗡𝗦𝗘 → {last}
[❖] 𝗚𝗔𝗧𝗘𝗦 ⇾ {gate_name}
━━━━━━━━━━━━━━━━
{dato(cc[:6]).strip()}
━━━━━━━━━━━━━━━━
[❖] 𝗣𝗿𝗼𝘅𝘆 ⇾ 𝗟𝗶𝘃𝗲 [1XX.XX.XX 🟢]
━━━━━━━━━━━━━━━━
[❖] 𝗧𝗶𝗺𝗲 𝗧𝗮𝗸𝗲𝗻 ⇾ {"{:.1f}".format(execution_time)} Seconds
━━━━━━━━━━━━━━━━
[❖] 𝗕𝗼𝘁 𝗕𝘆 ⇾ 『@I_EOR』
</b>"""


def insufficient_funds_message(cc, last, gate_name, execution_time, dato):
    return f"""<b>
𝗜𝗻𝘀𝘂𝗳𝗳𝗶𝗰𝗶𝗲𝗻𝘁 𝗙𝘂𝗻𝗱𝘀 💸

[❖] 𝗖𝗖 ⇾ <code>{cc}</code>
[❖] 𝗥𝗘𝗦𝗣𝗢𝗡𝗦𝗘 → {last}
[❖] 𝗚𝗔𝗧𝗘𝗦 ⇾ {gate_name}
━━━━━━━━━━━━━━━━
{dato(cc[:6]).strip()}
━━━━━━━━━━━━━━━━
[❖] 𝗣𝗿𝗼𝘅𝘆 ⇾ 𝗟𝗶𝘃𝗲 [1XX.XX.XX 🟢]
━━━━━━━━━━━━━━━━
[❖] 𝗧𝗶𝗺𝗲 𝗧𝗮𝗸𝗲𝗻 ⇾ {"{:.1f}".format(execution_time)} Seconds
━━━━━━━━━━━━━━━━
[❖] 𝗕𝗼𝘁 𝗕𝘆 ⇾ 『@I_EOR』
</b>"""


def declined_message(cc, last, gate_name, execution_time, dato):
    return f"""<b>
𝗗𝗲𝗰𝗹𝗶𝗻𝗲𝗱 ❌

[❖] 𝗖𝗖 ⇾ <code>{cc}</code>
[❖] 𝗥𝗘𝗦𝗣𝗢𝗡𝗦𝗘 → {last}
[❖] 𝗚𝗔𝗧𝗘𝗦 ⇾ {gate_name}
━━━━━━━━━━━━━━━━
{dato(cc[:6]).strip()}
━━━━━━━━━━━━━━━━
[❖] 𝗣𝗿𝗼𝘅𝘆 ⇾ 𝗟𝗶𝘃𝗲 [1XX.XX.XX 🟢]
━━━━━━━━━━━━━━━━
[❖] 𝗧𝗶𝗺𝗲 𝗧𝗮𝗸𝗲𝗻 ⇾ {"{:.1f}".format(execution_time)} Seconds
━━━━━━━━━━━━━━━━
[❖] 𝗕𝗼𝘁 𝗕𝘆 ⇾ 『@I_EOR』
</b>"""