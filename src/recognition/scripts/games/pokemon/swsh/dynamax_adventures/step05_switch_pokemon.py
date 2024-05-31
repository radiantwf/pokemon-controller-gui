from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus
import cv2
import numpy as np
import pytesseract


class SWSHDASwitchPokemon(BaseSubStep):
    _except_moves = ["打嗝","打邑","打啊"]

    def __init__(self, script: BaseScript, battle_index: int = 0, switch: bool = True, timeout: float = -1) -> None:
        super().__init__(script, timeout)
        self._process_step_index = 0
        self._battle_index = battle_index
        self._switch_pokemon = switch
        self._switch_pokemon_template = cv2.imread(
            "resources/img/recognition/pokemon/swsh/dynamax_adventures/switch_pokemon/switch_pokemon.png")
        self._switch_pokemon_template = cv2.cvtColor(
            self._switch_pokemon_template, cv2.COLOR_BGR2GRAY)

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
            self._process_steps_0,
        ]

    def _process_steps_0(self):
        if self._battle_index >= 3:
            self._process_step_index += 1
            return

        current_frame = self.script.current_frame
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        if self._match_switch_pokemon(gray_frame):
            if self._ocr_moves_defective(gray_frame):
                self._switch_pokemon = False
            if self._switch_pokemon:
                self.script.macro_text_run("A:0.1", block=True)
            else:
                self.script.macro_text_run(
                    "BOTTOM:0.1->0.4->A:0.1", block=True)
            self.time_sleep(3)
            self._process_step_index += 1
        else:
            self.time_sleep(0.5)

    def _match_switch_pokemon(self, gray) -> bool:
        crop_x, crop_y, crop_w, crop_h = 336, 172, 76, 195
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        res = cv2.matchTemplate(
            crop_gray, self._switch_pokemon_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val > 0.9:
            return True

    def _ocr_moves_defective(self, gray, zoom=10) -> bool:
        for i in range(4):
            crop_x, crop_y, crop_w, crop_h = 680, 253+i*32, 110, 25
            crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
            crop_gray = cv2.resize(crop_gray, (crop_w*zoom, crop_h*zoom))
            # 对图片进行二值化处理
            _, thresh1 = cv2.threshold(
                crop_gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)

            kernel = np.ones((3, 3), np.uint8)
            opening = cv2.morphologyEx(thresh1, cv2.MORPH_OPEN, kernel)
            closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)
            closing = cv2.resize(closing, (crop_w, crop_h))
            custom_config = r'--oem 3 --psm 7'
            text = pytesseract.image_to_string(
                closing, lang='chi_sim', config=custom_config)
            text = "".join(text.split())
            # print(text)
            if text in self._except_moves:
                return True
        return False
