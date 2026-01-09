def classify_result(text: str):
    t = text.lower()

    if "charged" in t or "thank you for your donation" in t:
        return "CHARGED"

    if "approved" in t or "approved (cvv)" in t or "1000: approved" in t:
        return "APPROVED"

    if "insufficient_funds" in t or "insufficient funds" in t or "funds" in t:
        return "FUNDS"

    return "DECLINED"