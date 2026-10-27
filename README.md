# Aya-coinboard

HoshinoBot 金币中枢插件：**统一金币排行榜 + 以钩子注入方式为娱乐插件发放金币**。

设计目标：不装 coinboard 时娱乐插件是默认行为、装上 coinboard 后，由它主动"注入"发币逻辑，金币数值、结算文案、延迟下发全部收拢在一个插件里管理。

## 功能

| 指令               | 说明               |
| ---------------- | ---------------- |
| `金币排行榜` / `金币排行` | 显示本群金币排行（前 10 名） |

- 若bot上存在 pcr_duel(贵族决斗)插件，本插件数据库无缝衔接。单独安装也能正常初始化。

## 钩子注入架构

每个被接入的游戏对应一个 `hook_<模块名>.py`，在 coinboard 被加载时导入游戏模块，原函数行为与返回值完全不变，额外在函数后延迟下发一条结算消息。结算消息形如 `@用户 获得金币22个(共137个)`，独立于游戏的胜利消息单独发送。

```
modules/coinboard/
├── coinboard.py              金币排行榜
├── _coin_core.py             共享内核：
│                             ScoreCounter2 获取/兜底、延迟结算、hook_method()
├── hook_pcravatarguess.py    猜头像   → patch WinningCounter._record_winning
├── hook_pcrfullcardguess.py  猜立绘   → patch WinningCounter._record_winning
├── hook_voiceguess.py        猜语音   → patch Dao.record_winning
└── hook_pokemanpcr2.py       宝可梦   → patch daily_limiter.increase（实例级，不用 hook_method）
```

 `_coin_core.py` 顶部的 `SETTLE_DELAY`（默认 2.0 秒）控制延迟，**避免毫秒级连发触发 QQ 风控**，可按体感自行调整。

### 接入新游戏

在 `modules/coinboard/` 下新增 `hook_<模块名>.py`（会被自动加载），内容仿照现有钩子：

```python
# 要求：该方法恰好在一次结算/获胜/奖励时被调用一次，签名为 (self, gid, uid)
hook_method(<记胜函数所在类>, '<方法名>', lambda: random.randint(10, 30))
```

## 安装

**⚠️&#x20;**`MODULES_ON` 中 `'coinboard'` 必须写在被hook插件之后  
放在 MODULES_ON 末尾附近即可。

## 兼容性

- HoshinoBot（nonebot1 + aiocqhttp），Python 3.8+

## License

[GPL-3.0](./LICENSE)
