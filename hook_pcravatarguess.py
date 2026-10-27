# 「猜头像」金币钩子（由 coinboard 注入，游戏本体不含任何金币代码）
# 规则沿用原 ADDON：randint(20, 40)
import random

from hoshino.modules.coinboard._coin_core import hook_method
from hoshino.modules.pcravatarguess.pcravatarguess import WinningCounter

hook_method(WinningCounter, '_record_winning', lambda: random.randint(20, 40))
