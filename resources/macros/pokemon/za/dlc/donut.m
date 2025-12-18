--甜甜圈--
<donut|宝可梦-ZA-DLC-甜甜圈(材料树果脚本中设置)|1>
EXEC>restore_backup=True
# 树果1位置(向上移动次数)，树果1（数量1-8）
# 树果2位置(树果1位置开始向上移动次数)，树果2（数量1-8）
# 树果3位置(树果2位置开始向上移动次数)，树果3（数量1-8）
EXEC>berry2_position=0;berry2_count=0;
EXEC>berry3_position=0;berry3_count=0;

# 酸
EXEC>berry1_position=3;berry1_count=4;
EXEC>berry2_position=1;berry2_count=4;

# 甜1
# EXEC>berry1_position=5;berry1_count=4;
# EXEC>berry2_position=3;berry2_count=4;

# 甜2
# EXEC>berry1_position=5;berry1_count=8;

body:
[pokemon.za.common.restart_game]
Plus:0.1
0.3
Y:0.1
0.2
{
    BOTTOM:0.05
    0.1
}*3
A:0.1
0.5
A:0.05
A:0.05
4.5
LStick@0,-127:0.1->LStick@0,-127|B:0.1->LStick@0,-127:1
A:0.05
3
LStick@0,-127:0.1->LStick@0,-127|B:0.1->LStick@0,-127:1.3->LStick@-127,-40:0.3
0.5
A:0.05
0.4
A:0.05
0.5
A:0.05
1
# 选择树果
{
    LStick@0,-127:0.05
    0.2
}*berry1_position
{
    A:0.05
    0.1
}*berry1_count
{
    LStick@0,-127:0.05
    0.2
}*berry2_position
{
    A:0.05
    0.1
}*berry2_count
{
    LStick@0,-127:0.05
    0.2
}*berry3_position
{
    A:0.05
    0.1
}*berry3_count
0.1
Plus:0.1
{
    A:0.1
    0.5
}*10
