from .start import register_start
from .prices import register_prices
from .buy import register_buy
from .combo import register_combo
from .redeem import register_redeem
from .me import register_me
from .single_commands import register_single_commands
from .admin_panel import register_admin_panel   # ← أضف دي

def register_all(bot):
    register_start(bot)
    register_prices(bot)
    register_buy(bot)
    register_combo(bot)
    register_redeem(bot)
    register_me(bot)
    register_single_commands(bot)
    register_admin_panel(bot)   # ← أضف دي