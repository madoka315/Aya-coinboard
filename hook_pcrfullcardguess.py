# 「猜立绘」金币钩子（由 coinboard 注入，游戏本体不含任何金币代码）
# 规则沿用原 ADDON：choice([30, 40, 50])
import random

from hoshino.modules.coinboard._coin_core import hook_method
from hoshino.modules.pcrfullcardguess.pcrfullcardguess import WinningCounter

hook_method(WinningCounter, '_record_winning', lambda: random.choice([30, 40, 50]))
