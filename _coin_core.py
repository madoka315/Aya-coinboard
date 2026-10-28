# coinboard 共享内核（文件名下划线开头 → nonebot load_plugins 跳过，不作插件入口）
# 职责：金币结算与延迟下发；各游戏的钩子 hook_*.py 在导入时调用 hook_method() 注入
# ⚠️ 隐形约束：本模块须在 MODULES_ON 中晚于被钩的游戏加载（当前在其后，调整顺序前先核对）

import asyncio
import os
import sqlite3

import hoshino
from nonebot import MessageSegment

# 钩子触发点早于游戏发出胜利消息（游戏还需查群成员列表、拼图再发送），
# 此延迟从"记胜"时刻起算，使结算消息落在胜利消息之后约 1 秒，避免同毫秒连发触发QQ风控
SETTLE_DELAY = 2.0

try:
    from hoshino.modules.pcr_duel import ScoreCounter2
except ImportError:
    try:
        # 兼容旧版：pcr_duel 尚作为 priconne 子包安装时的路径
        from hoshino.modules.priconne.pcr_duel import ScoreCounter2
    except ImportError:
            # pcr_duel 不存在时的内置等价实现（同库同表，单独安装 coinboard 也可用）
        _DB_PATH = os.path.expanduser('~/.hoshino/pcr_running_counter.db')

        class ScoreCounter2:
            def __init__(self):
                os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
                self._connect().execute('''CREATE TABLE IF NOT EXISTS SCORECOUNTER
                              (GID             INT    NOT NULL,
                               UID             INT    NOT NULL,
                               SCORE           INT    NOT NULL,
                               PRIMARY KEY(GID, UID));''')

            def _connect(self):
                return sqlite3.connect(_DB_PATH)

            def _get_score(self, gid, uid):
                r = self._connect().execute("SELECT SCORE FROM SCORECOUNTER WHERE GID=? AND UID=?", (gid, uid)).fetchone()
                return 0 if r is None else r[0]

            def _add_score(self, gid, uid, score):
                conn = self._connect()
                conn.execute("INSERT OR REPLACE INTO SCORECOUNTER (GID,UID,SCORE) \
                                    VALUES (?,?,?)", (gid, uid, self._get_score(gid, uid) + score))
                conn.commit()

            def _reduce_score(self, gid, uid, score):
                conn = self._connect()
                conn.execute("INSERT OR REPLACE INTO SCORECOUNTER (GID,UID,SCORE) \
                                    VALUES (?,?,?)", (gid, uid, max(0, self._get_score(gid, uid) - score)))
                conn.commit()


async def _settle(gid, uid, score):
    await asyncio.sleep(SETTLE_DELAY)
    try:
        score_counter = ScoreCounter2()
        score_counter._add_score(gid, uid, score)
        total = score_counter._get_score(gid, uid)
        msg = f'{MessageSegment.at(uid)}获得金币{score}个(共{total}个)'
        await hoshino.get_bot().send_group_msg(group_id=gid, message=msg)
    except Exception:
        hoshino.logger.exception(f'coinboard 金币结算失败 gid={gid} uid={uid}')


def schedule_settle(gid, uid, score):
    """调度一次延迟金币结算；供 hook_method 及自定义钩子（如宝可梦的实例级 patch）使用"""
    asyncio.ensure_future(_settle(gid, uid, score))


def hook_method(cls, method_name, score_func):
    """把 cls.<method_name>(self, gid, uid) 包上发币逻辑。

    要求该方法恰好在一次猜对胜利时被调用一次（三游戏现状如此）；
    原方法行为与返回值保持不变，发币失败也不影响游戏本体。
    """
    orig = getattr(cls, method_name)

    def patched(instance, gid, uid):
        result = orig(instance, gid, uid)
        try:
            schedule_settle(gid, uid, score_func())
        except Exception:
            hoshino.logger.exception('coinboard 金币结算调度失败')
        return result

    setattr(cls, method_name, patched)
