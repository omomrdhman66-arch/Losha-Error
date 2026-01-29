GATE_STATES={'stripe_auth':True,'braintree_auth':True,'shopify_charge':True,'stripe_charge':True,'paypal_donation':True}

def toggle(g):
    GATE_STATES[g]=not GATE_STATES.get(g,True); return GATE_STATES[g]

def status(g): return GATE_STATES.get(g,True)
