<picnic_3|野餐制作三明治|1>
A:0.1
0.1
9
# 往前走一步，开始做料理
LStick@0,-127:0.2
0.8
A:0.1
0.5
A:0.1
5
# 选择超级花生酱三明治（配方：香蕉，花生酱，黄油 各1）
{
	LStick@0,127:0.05
	0.3
}*8
A:0.1
0.7
A:0.1
7
{
	LStick@0,-127:0.5
	0.1
	A:0.1->LStick@0,127|A:0.48->A:0.5
	0.1
}*3
0.6
A:0.1
2
A:0.1
3.5
A:0.1
12
A:0.1
9
A:0.1
0.5
15
A:0.1
2

<hatching_run|孵蛋跑圈|-1>
L:0.1
0.8
LStick@-127,0|RStick@-127,0:0.5->~
LStick@-127,0|RStick@-127,0|LPRESS:0.1->~
body:
LStick@-127,0|RStick@-127,0|LPRESS:0.1->~
LStick@-127,0|RStick@-127,0:1->~