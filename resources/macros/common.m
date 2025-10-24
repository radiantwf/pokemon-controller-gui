--唤醒手柄--
<wakeup_joystick>
LPress:0.1
1
LPress:0.1
3

--返回主界面--
<return_home--ns1|NS1|True>
Home:0.1
0.7
{0.8}?ns1

--返回游戏界面（非Home页面）--
<return_game--ns1|NS1|True>
[return_home]
A:0.1
0.7
{0.8}?ns1

--关闭游戏--
<close_game--ns1|NS1|True>
[return_home]
X:0.1
0.3
{0.2}?ns1
A:0.1
0.8
{4.2}?ns1

--连续点击A--
<press_button_a|连续点击A>
A:0.1
0.2

--连续点击B--
<press_button_b|连续点击B>
B:0.1
0.2

--进入休眠--
<switch_sleep--ns1|NS1|True>
HOME:4
1
A:0.1
0.5
A:0.1
