--极巨团战开团--
<raid|剑盾极巨团战开团|-1--secondary|副设备(副设备启动游戏时校验)|False>
{
    body:
	[pokemon.swsh.common.restart_game]
    [common.return_home]
    [pokemon.swsh.common.set_date_from_home]
    [pokemon.swsh.common.minus_three_days]
    [common.return_home]
    [common.return_home]
    EXEC>has_watts=False;
    {
        [pokemon.swsh.common.goto_raid_offline]
        [common.return_home]
        [pokemon.swsh.common.set_date_from_home]
        [pokemon.swsh.common.add_one_day_initial]
        [common.return_home]
        [common.return_home]
        B:0.05
        0.7
        A:0.05
        7
        EXEC>has_watts=True;
    }*3
    [pokemon.swsh.common.online]
    [pokemon.swsh.common.goto_raid_wait_online]
    [pokemon.swsh.common.set_raid_password]
    [pokemon.swsh.common.wait_raid]
    [pokemon.swsh.common.raid]
}