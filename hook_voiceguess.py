# 「猜语音/猜ub/cygames」金币钩子（由 coinboard 注入，游戏本体不含任何金币代码）
# 规则沿用原 ADDON：randint(15, 50)；挂点为语音游戏包内 Dao.record_winning
import random

from hoshino.modules.coinboard._coin_core import hook_method
from hoshino.modules.voiceguess import Dao

hook_method(Dao, 'record_winning', lambda: random.randint(15, 50))
