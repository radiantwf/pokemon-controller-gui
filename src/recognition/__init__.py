import multiprocessing
from recognition.scripts.swsh_battle_shiny import SwshBattleShiny

def list_recognition_script():
    scripts = [
        SwshBattleShiny.script_name,
    ]
    return scripts

def run(script_name, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue):
    script = None
    if script_name == SwshBattleShiny.script_name:
        script = SwshBattleShiny(stop_event, frame_queue, controller_input_action_queue)
    else:
        pass
    if script:
        script.run()