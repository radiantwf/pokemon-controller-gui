import multiprocessing
from recognition.scripts.sv.eggs_hatch import SVEggs
from recognition.scripts.swsh.battle_shiny import SwshBattleShiny


def list_recognition_script():
    scripts = [
        SwshBattleShiny.script_name(),
        SVEggs.script_name(),
    ]
    return scripts


def get_default_parameters(scritp_name: str) -> dict:
    paras = dict()
    if scritp_name == SwshBattleShiny.script_name():
        paras = SwshBattleShiny.script_paras()
    elif scritp_name == SVEggs.script_name():
        paras = SVEggs.script_paras()
    return paras


def run(script_name, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue, paras: dict = None):
    script = None
    if script_name == SwshBattleShiny.script_name():
        script = SwshBattleShiny(
            stop_event, frame_queue, controller_input_action_queue, paras)
    elif script_name == SVEggs.script_name():
        script = SVEggs(stop_event, frame_queue,
                        controller_input_action_queue, paras)
    else:
        pass
    if script:
        script.run()
