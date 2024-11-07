import multiprocessing
from recognition.scripts.games.dqm3.synthesis import DQM3Synthesis
from recognition.scripts.games.pokemon.sv.eggs_hatch import SVEggs
from recognition.scripts.games.pokemon.sv.tera_raid.gimmighoul import SvTeraRaidGimmighoul
from recognition.scripts.games.pokemon.swsh.battle_shiny import SwshBattleShiny
from recognition.scripts.games.pokemon.swsh.dynamax_adventures import SwshDynamaxAdventures


def list_recognition_script():
    scripts = [
        SwshBattleShiny.script_name(),
        SwshDynamaxAdventures.script_name(),
        SVEggs.script_name(),
        SvTeraRaidGimmighoul.script_name(),
        DQM3Synthesis.script_name(),
    ]
    return scripts


def get_default_parameters(scritp_name: str) -> dict:
    paras = dict()
    if scritp_name == SwshBattleShiny.script_name():
        paras = SwshBattleShiny.script_paras()
    elif scritp_name == SwshDynamaxAdventures.script_name():
        paras = SwshDynamaxAdventures.script_paras()
    elif scritp_name == SVEggs.script_name():
        paras = SVEggs.script_paras()
    elif scritp_name == SvTeraRaidGimmighoul.script_name():
        paras = SvTeraRaidGimmighoul.script_paras()
    elif scritp_name == DQM3Synthesis.script_name():
        paras = DQM3Synthesis.script_paras()
    return paras


def run(script_name, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue, paras: dict = None):
    script = None
    if script_name == SwshBattleShiny.script_name():
        script = SwshBattleShiny(
            stop_event, frame_queue, controller_input_action_queue, paras)
    elif script_name == SwshDynamaxAdventures.script_name():
        script = SwshDynamaxAdventures(stop_event, frame_queue,
                                       controller_input_action_queue, paras)
    elif script_name == SVEggs.script_name():
        script = SVEggs(stop_event, frame_queue,
                        controller_input_action_queue, paras)
    elif script_name == SvTeraRaidGimmighoul.script_name():
        script = SvTeraRaidGimmighoul(stop_event, frame_queue,
                        controller_input_action_queue, paras)
    elif script_name == DQM3Synthesis.script_name():
        script = DQM3Synthesis(stop_event, frame_queue,
                               controller_input_action_queue, paras)
    else:
        pass
    if script:
        script.run()
