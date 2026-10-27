# 「宝可梦(pokemanpcr2)」金币钩子（由 coinboard 注入，游戏本体不含任何金币代码）
# 挂点：戳一戳获奖分支末尾的 daily_limiter.increase（全文件唯一调用点，且在
#       获奖消息 send 之后，结算消息自然落在其后）。
# 与三游戏不同，这里 patch 的是实例方法（签名 (key, num=1)，key=(gid, uid)），
# 故不走 hook_method，直接用 schedule_settle。
# 规则：randint(10, 20)，上限 20。
import random

from hoshino.modules.coinboard._coin_core import schedule_settle
from hoshino.modules.pokemanpcr2.poke_man_pcr import daily_limiter

_orig_increase = daily_limiter.increase


def _patched_increase(key, num=1):
    result = _orig_increase(key, num)
    try:
        gid, uid = key
        schedule_settle(gid, uid, random.randint(10, 20))
    except Exception:
        pass  # 结算调度失败不影响宝可梦本体
    return result


daily_limiter.increase = _patched_increase
