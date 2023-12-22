--打开勇者斗恶龙怪兽篇3--
<open_game--secondary|副设备(副设备启动游戏时校验)|False>
A:0.1
1.5
A:0.1
{5}?secondary
44

--返回主界面并读档--
<enter_game>
A:0.1
0.5
A:0.1
1
A:0.1
17


--重启勇者斗恶龙怪兽篇3--
<restart_game--secondary|副设备(副设备启动游戏时校验)|False>
[common.close_game]
[open_game]
[enter_game]

--返回主界面--
<return_main>
X:0.1
1.5
R:0.1
0.6
TOP:0.1
0.3
A:0.1
0.8
LEFT:0.1
0.2
A:0.1
20

--返回主界面并读档--
<reload_game>
[return_main]
[enter_game]
1