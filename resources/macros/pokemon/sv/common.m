--打开宝可梦朱紫--
<open_game--secondary|副设备(副设备启动游戏时校验)|False>
A:0.1
1.5
A:0.1
19
{5}?secondary
A:0.1
1
A:0.1
1
A:0.1
21

--重启宝可梦朱紫--
<restart_game--secondary|副设备(副设备启动游戏时校验)|False>
[common.close_game]
[open_game]

--进入时间设置界面--
<set_time_from_home>
# 进入设置界面
LStick@0,127:0.05
0.08
LStick@127,0:0.05
0.08
LStick@127,0:0.05
0.08
LStick@127,0:0.05
0.08
LStick@127,0:0.05
0.08
LStick@127,0:0.05
0.08
A:0.05
1
# 进入时间设置界面
{
	LStick@0,127:0.05
	0.08
}*15
0.05
A:0.05
1
{
	LStick@0,127:0.05
	0.08
}*3
LStick@0,127:0.3
0.8
{
	LStick@0,127:0.05
	0.08
}*2
0.05
A:0.05
1
{
	LStick@0,127:0.05
	0.08
}*2


<set_time>
# 进入设置界面
A:0.05
0.5
A:0.05
0.05
A:0.05
0.05
A:0.05
0.05
A:0.05
0.05
# LStick@0,127:0.05
# 0.05
A:0.05
0.05
A:0.05
0.12