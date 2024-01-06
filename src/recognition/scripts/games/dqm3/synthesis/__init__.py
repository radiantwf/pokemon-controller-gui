import multiprocessing
import time

import numpy as np
from recognition.scripts.parameter_struct import ScriptParameter
from recognition.scripts.base.base_script import BaseScript, WorkflowEnum
import cv2
import pytesseract

class DQM3Synthesis(BaseScript):
    def __init__(self, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue, paras: dict() = None):
        super().__init__(DQM3Synthesis.script_name(), stop_event,
                         frame_queue, controller_input_action_queue, DQM3Synthesis.script_paras())
        self._prepare_step_index = -1
        self._circle_step_index = -1
        self._jump_next_frame = False
        self.set_paras(paras)
        self._durations = self.get_para("durations")
        self._secondary = self.get_para("secondary")
        self._shiny_star_template = cv2.imread("resources/img/recognition/dqm3/synthesis/shiny_star.png")
        self._shiny_star_template = cv2.cvtColor(self._shiny_star_template, cv2.COLOR_BGR2GRAY)

        self._shiny = False


    @staticmethod
    def script_name() -> str:
        return "勇者斗恶龙怪兽篇3配种"

    @staticmethod
    def script_paras() -> dict:
        paras = dict()
        paras["durations"] = ScriptParameter(
            "durations", float, -1, "运行时长（分钟）")
        paras["secondary"] = ScriptParameter(
            "secondary", bool, False, "副设备")
        paras["m1_page"] = ScriptParameter(
            "m1_page", int, 1, "怪兽1所在页面")
        paras["m1_row"] = ScriptParameter(
            "m1_row", int, 1, "怪兽1所在行")
        paras["m1_col"] = ScriptParameter(
            "m1_col", int, 1, "怪兽1所在列")
        paras["m2_page"] = ScriptParameter(
            "m2_page", int, 1, "怪兽2所在页面")
        paras["m2_row"] = ScriptParameter(
            "m2_row", int, 1, "怪兽2所在行")
        paras["m2_col"] = ScriptParameter(
            "m2_col", int, 2, "怪兽2所在列")
        paras["m3_target"] = ScriptParameter(
            "m3_target", int, 1, "配种怪兽3位置")
        paras["m3_talents"] = ScriptParameter(
            "m3_talents", str, "1,2,3", "配种怪兽3天赋")
        paras["monster_size"] = ScriptParameter(
            "monster_size", str, "普通体型", "配种怪物体型(个别怪兽超大体型个体需要修改为超大体型)",["普通体型","超大体型"])
        paras["experience_book_index"] = ScriptParameter(
            "experience_book_index", int, 0, "经验之书位置(<=0时跳过能力值检测)")
        paras["check_ability_tag"] = ScriptParameter("check_ability_tag", str, "HP", "属性成长值检测",["HP","MP","攻击","防御","速度","智力"])
        paras["check_ability_value"] = ScriptParameter("check_ability_value", int, 100, "检测阈值(大于等于设定值)")

        paras["def_limit_tag"] = ScriptParameter("def_limit_tag", str, "不检测", "体型检测(防御成长值限制)",["不检测","大于等于","小于等于"])
        paras["def_limit_value"] = ScriptParameter("def_limit_value", int, 0, "防御成长值阈值")

        paras["speed_limit_tag"] = ScriptParameter("speed_limit_tag", str, "不检测", "体型检测(速度成长值限制)",["不检测","大于等于","小于等于"])
        paras["speed_limit_value"] = ScriptParameter("speed_limit_value", int, 0, "速度成长值阈值")
        
        return paras
    
    def check_durations(self):
        if self._durations <= 0:
            return False
        if self.run_time_span >= self._durations * 60:
            self.send_log("运行时间已到达设定值，脚本停止")
            self.finished_process()
            return True
        return False
        
    def process_frame(self):
        if self.check_durations():
            return
        if self.running_status == WorkflowEnum.Preparation:
            if self._prepare_step_index >= 0:
                if self._prepare_step_index >= len(self.prepare_step_list):
                    self.set_circle_begin()
                    self._circle_step_index = 0
                    return
                self.prepare_step_list[self._prepare_step_index]()
            return
        if self.running_status == WorkflowEnum.Circle:
            if self.current_frame_count == 1:
                self.circle_init()
            if self._jump_next_frame:
                self._jump_next_frame = False
                return
            if self._circle_step_index >= 0 and self._circle_step_index < len(self.cycle_step_list):
                self.cycle_step_list[self._circle_step_index]()
            else:
                self.macro_stop()
                self.set_circle_continue()
                self._circle_step_index = 0
            return
        if self.running_status == WorkflowEnum.AfterCircle:
            self.stop_work()
            return

    def on_start(self):
        self._prepare_step_index = 0
        self.send_log(f"开始运行{DQM3Synthesis.script_name()}脚本")

    def on_circle(self):
        pass
        # run_time_span = self.run_time_span
        # self.send_log("脚本运行中，已经运行{}次，耗时{}小时{}分{}秒".format(self.circle_times, int(
        #     run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))

    def on_stop(self):
        run_time_span = self.run_time_span
        self.send_log("[{}] 脚本停止，实际运行{}次，耗时{}小时{}分{}秒".format(DQM3Synthesis.script_name(), self.circle_times, int(
            run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))

    def on_error(self):
        pass

    @property
    def prepare_step_list(self):
        return [
            self.prepare_step_0,
            self.restart_game,
        ]

    def prepare_step_0(self):
        self.macro_text_run("B:0.1\n0.1", loop=1, block=True)
        time.sleep(3)
        self._prepare_step_index += 1

    def restart_game(self):
        self.macro_run("recognition.dqm3.common.restart_game",
                        1, {"secondary": str(self._secondary)}, True, None)
        self._prepare_step_index += 1

    @property
    def cycle_step_list(self):
        return [
            self.prepare_cycle,
            self.synthesis_1,
            self.shiny_check_1,
            self.synthesis_2,
            self.use_experience_book,
            self.shiny_check_2,
            self.reload_game,
        ]
    
    def circle_init(self):
        pass

    def prepare_cycle(self):
        self._shiny = False
        self._check_shiny_frame_count = 0
        self._circle_step_index += 1


    def synthesis_1(self):
        macro_paras = dict()
        for p in self.paras.values():
            macro_paras[p.name] = p.value

        self.macro_run("recognition.dqm3.synthesis.synthesis_1",
                        1, macro_paras, True, None)
        self._jump_next_frame = True
        self._circle_step_index += 1

    def shiny_check_1(self):
        image = self.current_frame

        monster_size = self.paras['monster_size'].value
        if monster_size == "普通体型":
            crop_x, crop_y, crop_w, crop_h = 300, 300, 360, 240
        else:
            crop_x, crop_y, crop_w, crop_h = 350, 240, 260, 300

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        match = cv2.matchTemplate(crop_gray, self._shiny_star_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(match)
        self._check_shiny_frame_count += 1
        # self.send_log("闪光怪兽检测中，当前帧最大匹配值：{}".format(max_val))
        if max_val >= 0.7:
            self._shiny = True
            self._circle_step_index += 1
            self.send_log("已成功配种闪光怪兽")
            return
        if self._check_shiny_frame_count >= 6:
            self._circle_step_index += 1

    def synthesis_2(self):
        self.macro_run("recognition.dqm3.synthesis.synthesis_2",
                        1, {}, True, None)
        self._circle_step_index += 1

    def use_experience_book(self):
        if not self._shiny:
            self._circle_step_index += 1
            return
        if self.paras["experience_book_index"].value <= 0:
            self.finished_process()
            return
        macro_paras = dict()
        for p in self.paras.values():
            macro_paras[p.name] = p.value
        self.macro_run("recognition.dqm3.synthesis.use_experience_book",
                        1, macro_paras, True, None)
        self._jump_next_frame = True
        self._circle_step_index += 1
        
    def shiny_check_2(self):
        if not self._shiny:
            self._circle_step_index += 1
            return
        check_ability_tag = self.paras['check_ability_tag'].value
        check_ability_value = self.paras['check_ability_value'].value
        def_limit_tag = self.paras['def_limit_tag'].value
        def_limit_value = self.paras['def_limit_value'].value
        speed_limit_tag = self.paras['speed_limit_tag'].value
        speed_limit_value = self.paras['speed_limit_value'].value

        self.send_log(f"检测项目：{check_ability_tag}，阈值：{check_ability_value}")

        if check_ability_tag == "HP":
            crop_x, crop_y, crop_w, crop_h = 585, 203, 35, 20
        elif check_ability_tag == "MP":
            crop_x, crop_y, crop_w, crop_h = 585, 228, 35, 20
        elif check_ability_tag == "攻击":
            crop_x, crop_y, crop_w, crop_h = 585, 253, 35, 20
        elif check_ability_tag == "防御":
            crop_x, crop_y, crop_w, crop_h = 585, 278, 35, 20
        elif check_ability_tag == "速度":
            crop_x, crop_y, crop_w, crop_h = 585, 306, 35, 20
        elif check_ability_tag == "智力":
            crop_x, crop_y, crop_w, crop_h = 585, 331, 35, 20
        else:
            self.send_log("检测项目错误")
            self.finished_process()
            return
        
        # self.save_temp_image()

        # 转为灰度图片
        image = self.current_frame
        # 转为灰度图片
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        crop_gray = cv2.resize(crop_gray, (crop_w*5, crop_h*5))
        # 对图片进行二值化处理
        _, thresh1 = cv2.threshold(crop_gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(thresh1, cv2.MORPH_OPEN, kernel)
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)


        # 使用Tesseract进行文字识别
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
        num_text = pytesseract.image_to_string(closing, config=custom_config)
        num_text = "".join(num_text.split())
        num = int(num_text) if num_text.isdigit() else 0

        # 防御成长值：
        crop_x, crop_y, crop_w, crop_h = 585, 278, 35, 20
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        crop_gray = cv2.resize(crop_gray, (crop_w*5, crop_h*5))
        # 对图片进行二值化处理
        _, thresh1 = cv2.threshold(crop_gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(thresh1, cv2.MORPH_OPEN, kernel)
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)
        num_text = pytesseract.image_to_string(closing, config=custom_config)
        num_text = "".join(num_text.split())
        def_num = int(num_text) if num_text.isdigit() else 0
        if def_num <= 0:
            def_limit_tag = "不检测"
        
        # 速度成长值：
        crop_x, crop_y, crop_w, crop_h = 585, 306, 35, 20
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        crop_gray = cv2.resize(crop_gray, (crop_w*5, crop_h*5))
        # 对图片进行二值化处理
        _, thresh1 = cv2.threshold(crop_gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(thresh1, cv2.MORPH_OPEN, kernel)
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)
        num_text = pytesseract.image_to_string(closing, config=custom_config)
        num_text = "".join(num_text.split())
        speed_num = int(num_text) if num_text.isdigit() else 0
        if speed_num <= 0:
            speed_limit_tag = "不检测"

        check_ability = False
        self.send_log(f"闪光属性检测，判断{check_ability_tag}成长值大于是否大于等于{check_ability_value}")
        if num >= check_ability_value:
            check_ability = True
        self.send_log(f"{check_ability_tag}属性成长实际值：{num}")
        if check_ability:
            self.send_log(f"闪光属性检测成长值检测通过")
        else:
            self.send_log(f"闪光属性检测成长值检测未通过")

        check_def = False
        if def_limit_tag == "大于等于" or def_limit_tag == "小于等于":
            if def_limit_tag == "大于等于":
                self.send_log(f"体型检测，判断防御成长值是否大于等于{def_limit_value}")
                if def_num >= def_limit_value:
                    check_def = True
            elif def_limit_tag == "小于等于":
                self.send_log(f"体型检测，判断防御成长值是否小于等于{def_limit_value}")
                if def_num <= def_limit_value:
                    check_def = True
            self.send_log(f"防御成长值：{def_num}")
            if check_def:
                self.send_log(f"体型检测，防御成长值检测通过")
            else:
                self.send_log(f"体型检测，防御成长值检测未通过")
        else:
            check_def = True

        check_speed = False
        if speed_limit_tag == "大于等于" or speed_limit_tag == "小于等于":
            if speed_limit_tag == "大于等于":
                self.send_log(f"体型检测，判断速度成长值是否大于等于{speed_limit_value}")
                if speed_num >= speed_limit_value:
                    check_speed = True
            elif speed_limit_tag == "小于等于":
                self.send_log(f"体型检测，判断速度成长值是否小于等于{speed_limit_value}")
                if speed_num <= speed_limit_value:
                    check_speed = True
            self.send_log(f"速度成长值：{speed_num}")
            if check_speed:
                self.send_log(f"体型检测，速度成长值检测通过")
            else:
                self.send_log(f"体型检测，速度成长值检测未通过")
        else:
            check_speed = True

        if check_ability and check_def and check_speed:
            self.send_log(f"恭喜，全部检测通过")
            self.finished_process()
            return
        else:
            self.send_log(f"检测未通过，重新配种")

        self.macro_text_run("A:0.1\n0.1", loop=1, block=True)
        self.macro_text_run("B:0.1\n0.1", loop=8, block=True)
        time.sleep(3)
        self._circle_step_index += 1

    def reload_game(self):
        self.macro_run("recognition.dqm3.common.reload_game",
                        1, {}, True, None)
        self._circle_step_index += 1

    def finished_process(self):
        run_time_span = self.run_time_span
        self.macro_stop(block=True)
        self.macro_run("common.switch_sleep",
                       loop=1, paras={}, block=True, timeout=10)
        self.send_log("[{}] 脚本完成，已运行{}次，耗时{}小时{}分{}秒".format(DQM3Synthesis.script_name(), self.circle_times, int(
            run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))
        self.stop_work()
