from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus
from recognition.scripts.games.pokemon.sv.common.image_match.box_match import BoxMatch
from recognition.scripts.games.pokemon.sv.eggs_hatch.box_opt.move_eggs_to_current_party import SVBoxMoveEggs, reset_global_page_turns_count
from recognition.scripts.games.pokemon.sv.eggs_hatch.box_opt.move_shiny_pokemon_to_box import SVBoxMoveShinyPokemon
from recognition.scripts.games.pokemon.sv.eggs_hatch.box_opt.release import SVBoxReleasePokemon


class SVBoxOptPokemon(BaseSubStep):
    def __init__(self, script: BaseScript, timeout: float = 0) -> None:
        super().__init__(script, timeout)
        self._process_step_index = 0
        self._status = None
        self._sv_box_release = SVBoxReleasePokemon(self.script)
        self._sv_box_move_shiny = SVBoxMoveShinyPokemon(self.script)
        self._sv_box_move_eggs = SVBoxMoveEggs(self.script)

    @staticmethod
    def initial():
        reset_global_page_turns_count()

    def _process(self) -> SubStepRunningStatus:
        self._status = self.running_status
        if self._process_step_index >= 0:
            if self._process_step_index >= len(self._process_steps):
                return SubStepRunningStatus.OK
            elif self._status == SubStepRunningStatus.Running:
                self._process_steps[self._process_step_index]()
                return self._status
            else:
                return self._status
        else:
            self._process_step_index = 0
            return self._process()

    @property
    def _process_steps(self):
        return [
            self.release,
            self.move_shiny,
            self.move_eggs_to_current_party,
        ]

    def release(self):
        status = self._sv_box_release.run()
        if status == SubStepRunningStatus.Running:
            return
        elif status == SubStepRunningStatus.Finished:
            self._status = SubStepRunningStatus.Finished
            return
        elif status == SubStepRunningStatus.OK:
            self._process_step_index += 1
            return
        else:
            self.script.send_log("{}函数返回状态为{}".format("release", status.name))
            if status == SubStepRunningStatus.Timeout:
                self._status = SubStepRunningStatus.Failed
            else:
                self._status = status
            return

    def move_shiny(self):
        status = self._sv_box_move_shiny.run()
        if status == SubStepRunningStatus.Running:
            return
        elif status == SubStepRunningStatus.Finished:
            self._status = SubStepRunningStatus.Finished
            return
        elif status == SubStepRunningStatus.OK:
            self._process_step_index += 1
            return
        else:
            self.script.send_log(
                "{}函数返回状态为{}".format("move_shiny", status.name))
            if status == SubStepRunningStatus.Timeout:
                self._status = SubStepRunningStatus.Failed
            else:
                self._status = status
            return

    def move_eggs_to_current_party(self):
        status = self._sv_box_move_eggs.run()
        if status == SubStepRunningStatus.Running:
            return
        elif status == SubStepRunningStatus.Finished:
            self._status = SubStepRunningStatus.Finished
            return
        elif status == SubStepRunningStatus.OK:
            self._process_step_index += 1
            return
        else:
            self.script.send_log("{}函数返回状态为{}".format(
                "move_eggs_to_current_party", status.name))
            if status == SubStepRunningStatus.Timeout:
                self._status = SubStepRunningStatus.Failed
            else:
                self._status = status
            return
