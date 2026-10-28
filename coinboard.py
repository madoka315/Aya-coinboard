# 金币数据与猜头像/猜立绘/猜语音/贵族决斗/大透彩/宝可梦共用
# 优先用 pcr_duel 的 ScoreCounter2；没有该插件时用下面的内置等价实现
# （同一库文件同一表结构，数据互通，本模块单独安装也能正常初始化）

from hoshino import Service
from hoshino.typing import CQEvent

try:
    from hoshino.modules.pcr_duel import ScoreCounter2
except ImportError:
    try:
        # 兼容旧版：pcr_duel 尚作为 priconne 子包安装时的路径
        from hoshino.modules.priconne.pcr_duel import ScoreCounter2
    except ImportError:
        import os
        import sqlite3

        _DB_PATH = os.path.expanduser('~/.hoshino/pcr_running_counter.db')

        class ScoreCounter2:
            """与 pcr_duel.ScoreCounter2 同库同表的最小等价实现"""

            def __init__(self):
                os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
                self._create_table()

            def _connect(self):
                return sqlite3.connect(_DB_PATH)

            def _create_table(self):
                self._connect().execute('''CREATE TABLE IF NOT EXISTS SCORECOUNTER
                              (GID             INT    NOT NULL,
                               UID             INT    NOT NULL,
                               SCORE           INT    NOT NULL,
                               PRIMARY KEY(GID, UID));''')

            def _get_score(self, gid, uid):
                r = self._connect().execute("SELECT SCORE FROM SCORECOUNTER WHERE GID=? AND UID=?", (gid, uid)).fetchone()
                return 0 if r is None else r[0]

            def _add_score(self, gid, uid, score):
                current_score = self._get_score(gid, uid)
                conn = self._connect()
                conn.execute("INSERT OR REPLACE INTO SCORECOUNTER (GID,UID,SCORE) \
                                    VALUES (?,?,?)", (gid, uid, current_score + score))
                conn.commit()

            def _reduce_score(self, gid, uid, score):
                current_score = self._get_score(gid, uid)
                conn = self._connect()
                conn.execute("INSERT OR REPLACE INTO SCORECOUNTER (GID,UID,SCORE) \
                                    VALUES (?,?,?)", (gid, uid, max(0, current_score - score)))
                conn.commit()


sv = Service('金币排行', visible=False, bundle='pcr娱乐', help_='''
金币排行榜 | 查看本群金币排行(猜游戏/贵族决斗等获得的金币都在这里)
'''.strip())


async def get_user_card_dict(bot, group_id):
    mlist = await bot.get_group_member_list(group_id=group_id)
    d = {}
    for m in mlist:
        d[m['user_id']] = m['card'] if m['card'] != '' else m['nickname']
    return d


@sv.on_fullmatch(('金币排行榜', '金币排行'))
async def coin_ranking(bot, ev: CQEvent):
    try:
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        score_counter = ScoreCounter2()
        gid = ev.group_id
        score_dict = {}
        for uid in user_card_dict.keys():
            if uid != ev.self_id:
                score_dict[user_card_dict[uid]] = score_counter._get_score(gid, uid)
        group_ranking = sorted(score_dict.items(), key=lambda x: x[1], reverse=True)
        msg = '此群金币排行为:\n'
        for i in range(min(len(group_ranking), 10)):
            if group_ranking[i][1] != 0:
                msg += f'第{i+1}名: {group_ranking[i][0]}, 金币: {group_ranking[i][1]}\n'
        await bot.send(ev, msg.strip())
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))
