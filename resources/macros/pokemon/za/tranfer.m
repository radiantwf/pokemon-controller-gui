--原地传送--
<tranfer|ZA-稳定-原地传送|-1--area|地区传送(2，5，17区)，0为异次元洞内|0>
EXEC>area_str=str(area)
EXEC>x_offset=20|space|if|space|area_str=="5"|space|else|space|(80|space|if|space|area_str=="17"|space|else|space|(-40|space|if|space|area_str=="2"|space|else|space|0))
EXEC>y_offset=-80|space|if|space|area_str=="5"|space|else|space|(-80|space|if|space|area_str=="17"|space|else|space|(-80|space|if|space|area_str=="2"|space|else|space|0))
EXEC>delay1=0.06|space|if|space|area_str=="5"|space|else|space|(0.06|space|if|space|area_str=="17"|space|else|space|(0.06|space|if|space|area_str=="2"|space|else|space|0))
EXEC>delay2=3|space|if|space|area_str=="5"|space|else|space|(3.5|space|if|space|area_str=="17"|space|else|space|(3|space|if|space|area_str=="2"|space|else|space|(3|space|if|space|area_str=="0"|space|else|space|0)))
body:
Plus:0.1
0.3
{
    LStick@-*x_offset*-,-*y_offset*-:-*delay1*-
    0.1
}?area_str!="0"
A:0.1
0.5
A:0.1
A:0.1
-*delay2*-

--19区刷老翁龙（清晨、传送至19区后启动）--
<tranfer_Area19|ZA-稳定-19区刷老翁龙（清晨、传送至19区后启动）|-1>
EXEC>times=0
EXEC>limit=80
body:
LStick@-127,-100:0.1->LStick@-127,-100|B:0.1->LStick@-127,-100:1.3
0.3
Plus:0.1
0.3
EXEC>times+=1
{
    LStick@-64,64:0.1
    0.1
    [do_transfer]
    0.3
}?times<limit
{
    EXEC>times=0
    LStick@127,127:0.2
    0.1
    [do_transfer]
    0.4
    LStick@-127,-100:0.1->LStick@-127,-100|B:0.1->LStick@-127,-100:0.2
    {
        A:0.05->0.05->~
    }*10*3
    14
    {
        {
            LStick@0,127|A:0.05->LStick@0,127:0.05->~
        }*10*4
        15
    }
    Plus:0.1
    LStick@-127,-80:0.32
    0.1
    [do_transfer]
    0.5
}?times>=limit

--19区刷老翁龙2（阿勃梭罗旁椅子，休息至清晨后启动）--
<tranfer_Area19_2|ZA-稳定-19区刷老翁龙2（阿勃梭罗旁椅子，休息至清晨后启动）|-1>
EXEC>times=0
EXEC>limit=23
LStick@0,-127:0.1->LStick@0,-127|B:0.1->LStick@0,-127:3.2
0.5
LStick@0,127:0.1->LStick@0,127|B:0.1~
body:
{
    EXEC>times+=1
    LStick@0,127:2.4->LStick@-127,0:1.1->LStick@0,127:0.9->~
    LStick@0,-127:1->LStick@127,0:1->LStick@0,-127:2.8->LStick@0,127:0.8->~
}?times<limit
{
    LStick@0,127:3
    {
        A:0.05->0.05->~
    }*10*3
    14
    {
        {
            LStick@0,127|A:0.05->LStick@0,127:0.05->~
        }*10*4
        15
    }
    EXEC>times=0
    LStick@0,-127:0.1->LStick@0,-127|B:0.1->LStick@0,-127:3.2
    0.5
    LStick@0,127:0.1->LStick@0,127|B:0.1~
}?times>=limit


--18区刷暴飞龙（走到门口）--
<tranfer_Area18|ZA-稳定-18区刷暴飞龙（走到门口）|-1>
LStick@0,-127:0.03->LStick@0,-127|B:0.02->LStick@0,-127:1
0.3
Plus:0.1
0.3
LStick@-64,64:0.1
0.1
A:0.1
0.5
A:0.1
A:0.1
3

--20区 左侧大范围覆盖--
<tranfer_area20_left|ZA-测试中-20区左侧大范围覆盖|-1>
EXEC>enter_pokemonCenter_x_offset=-60;enter_pokemonCenter_y_offset=-127;enter_pokemonCenter_delay=0.25
EXEC>leave_pokemonCenter_x_offset=-30;leave_pokemonCenter_y_offset=127;leave_pokemonCenter_delay=0.2
EXEC>wholeDay_flag=False
EXEC>cycles=33
body:
EXEC>index=0
[pokecenter_bench]
{
    EXEC>index=index+1
    LStick@0,-127:0.03->LStick@0,-127|B:0.02->LStick@0,-127:1
    0.3
    A:0.1
    2.5
    LStick@-75,-127:0.03->LStick@-75,-127|B:0.02->LStick@-75,-127:5->~
    LStick@75,127:5.5->A:0.1
    3
    EXEC>flag=index<cycles
    {
        Plus:0.1
        Plus:0.1
        0.3
        LStick@-127,-20:0.1
        0.1
        [do_transfer]
    }?flag
}*cycles

--传送--
<do_transfer>
A:0.1
0.5
A:0.1
A:0.1
3

--宝可梦中心 长椅休息--
<pokecenter_bench>
Plus:0.1
0.3
LStick@-*enter_pokemonCenter_x_offset*-,-*enter_pokemonCenter_y_offset*-:-*enter_pokemonCenter_delay*-
0.1
[do_transfer]
LStick@127,-50:0.03->LStick@127,-50|B:0.02->LStick@127,-50:1.6->~
LStick@30,-127:1.6
{
    A:0.05->0.05->~
}*10*3
15
{
    {
        LStick@0,127|A:0.05->LStick@0,127:0.05->~
    }*10*3
    15
}?wholeDay_flag
Plus:0.1
0.3
LStick@-*leave_pokemonCenter_x_offset*-,-*leave_pokemonCenter_y_offset*-:-*leave_pokemonCenter_delay*-
0.1
[do_transfer]
2

--研究所 巨金怪、黑鲁加、雷电兽--
<metagross|ZA-废弃(有更高效方法)-研究所 巨金怪、黑鲁加、雷电兽|-1>
LStick@-50,-127:0.1->LStick@-50,-127|B:0.1->LStick@-50,-127:1.55->~
LStick@-127,-40:2.2->LStick@-50,-127:0.6->~
LStick@-127,0:1.3->LStick@-60,127:1->LStick@-127,0:0.7->LStick@-127,0:0.2->LStick@-127,-127:1->~
LStick@0,-127:5
1
LStick@0,-127:1.5
0.1
Plus:0.1
0.3
LStick@100,127:0.5
0.1
[do_transfer]

--研究所 巨金怪--
<metagross2|ZA-稳定-研究所 巨金怪(纯跑路)|-1>
LStick@-50,-127:0.1->LStick@-50,-127|B:0.1->LStick@-50,-127:1.55->~
LStick@-127,-40:2.2->LStick@-50,-127:0.6->~
LStick@-127,0:1.3->LStick@-60,127:1->LStick@-127,0:0.7->LStick@-127,0:0.2->LStick@-127,-127:1.2->~
LStick@0,-127:1.65
1
LStick@-127,-127:0.1->LStick@-127,-127|B:0.3->~
body:
LStick@127,-127:0.2->~
LStick@0,-127:3.2->~
LStick@127,-127:1.55->LStick@30,-127:3.2->~
LStick@-30,127:3.1->LStick@-127,127:1.9->~
LStick@0,127:3.2->LStick@-127,127:0.5->LStick@127,-127:0.6->~

--研究所 鬼剑--
<aegislash|ZA-稳定-研究所 鬼剑|-1>
LStick@90,-127:0.1->LStick@90,-127|B:0.1->LStick@90,-127:1
body:
A:0.1
2.6
Y:0.1
0.9
LStick@0,127:0.1->LStick@0,127|B:0.1->LStick@0,127:0.6
A:0.1
2.6

--往返跑 下水道 烛光灵--
<ShuttleRun|ZA-测试中-往返跑 下水道 烛光灵|-1>
LStick@0,127:0.1->LStick@0,127|B:0.1->LStick@0,127:2.9->~
body:
LStick@0,-127:1->LStick@0,-127|A:0.1->LStick@0,-127:2.3->LStick@0,127:3.422->~

