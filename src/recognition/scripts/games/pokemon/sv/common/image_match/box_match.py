import cv2
from cv2 import typing

from recognition.image_func import find_matches


class BoxMatch:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        self._egg_template = cv2.imread(
            "resources/img/recognition/pokemon/sv/eggs/box/egg.png")
        self._egg_template = cv2.cvtColor(
            self._egg_template, cv2.COLOR_BGR2GRAY)

        self._box_space_template = cv2.imread(
            "resources/img/recognition/pokemon/sv/eggs/box/box-space.png")
        self._box_space_template = cv2.cvtColor(
            self._box_space_template, cv2.COLOR_BGR2GRAY)

        self._box_space_selected_template = cv2.imread(
            "resources/img/recognition/pokemon/sv/eggs/box/box-space-selected.png")
        self._box_space_selected_template = cv2.cvtColor(
            self._box_space_selected_template, cv2.COLOR_BGR2GRAY)

        self._current_party_space_template = cv2.imread(
            "resources/img/recognition/pokemon/sv/eggs/box/current-party-space.png")
        self._current_party_space_template = cv2.cvtColor(
            self._current_party_space_template, cv2.COLOR_BGR2GRAY)

        self._current_party_space_selected_1_template = cv2.imread(
            "resources/img/recognition/pokemon/sv/eggs/box/current-party-space-selected-1.png")
        self._current_party_space_selected_1_template = cv2.cvtColor(
            self._current_party_space_selected_1_template, cv2.COLOR_BGR2GRAY)
        self._current_party_space_selected_2_template = cv2.imread(
            "resources/img/recognition/pokemon/sv/eggs/box/current-party-space-selected-2.png")
        self._current_party_space_selected_2_template = cv2.cvtColor(
            self._current_party_space_selected_2_template, cv2.COLOR_BGR2GRAY)

        self._box_arrow_template = cv2.imread(
            "resources/img/recognition/pokemon/sv/eggs/box/box-arrow.png")
        self._box_arrow_template = cv2.cvtColor(
            self._box_arrow_template, cv2.COLOR_BGR2GRAY)

        self._release_tag_template = cv2.imread(
            "resources/img/recognition/pokemon/sv/eggs/box/release-tag.png")
        self._release_tag_template = cv2.cvtColor(
            self._release_tag_template, cv2.COLOR_BGR2GRAY)

        self._shiny_icon_template = cv2.imread(
            "resources/img/recognition/pokemon/sv/eggs/box/shiny-icon.png")
        self._shiny_icon_template = cv2.cvtColor(
            self._shiny_icon_template, cv2.COLOR_BGR2GRAY)

        self._sv_icon_template = cv2.imread(
            "resources/img/recognition/pokemon/sv/eggs/box/sv-icon.png")
        self._sv_icon_template = cv2.cvtColor(
            self._sv_icon_template, cv2.COLOR_BGR2GRAY)

    CURRENT_PARTY_RECT = (180, 60)
    CURRENT_PARTY_1 = (18, 98)
    CURRENT_PARTY_2 = (18, 161)
    CURRENT_PARTY_3 = (18, 224)
    CURRENT_PARTY_4 = (18, 287)
    CURRENT_PARTY_5 = (18, 350)
    CURRENT_PARTY_6 = (18, 413)
    BOX_SPLIT_X = 200
    UNIT_BOX_RECT = (60, 60)
    BOX_1_1 = (225, 100)
    BOX_1_2 = (225, 163)
    BOX_1_3 = (225, 226)
    BOX_1_4 = (225, 289)
    BOX_1_5 = (225, 352)
    BOX_2_1 = (288, 100)
    BOX_2_2 = (288, 163)
    BOX_2_3 = (288, 226)
    BOX_2_4 = (288, 289)
    BOX_2_5 = (288, 352)
    BOX_3_1 = (351, 100)
    BOX_3_2 = (351, 163)
    BOX_3_3 = (351, 226)
    BOX_3_4 = (351, 289)
    BOX_3_5 = (351, 352)
    BOX_4_1 = (414, 100)
    BOX_4_2 = (414, 163)
    BOX_4_3 = (414, 226)
    BOX_4_4 = (414, 289)
    BOX_4_5 = (414, 352)
    BOX_5_1 = (477, 100)
    BOX_5_2 = (477, 163)
    BOX_5_3 = (477, 226)
    BOX_5_4 = (477, 289)
    BOX_5_5 = (477, 352)
    BOX_6_1 = (540, 100)
    BOX_6_2 = (540, 163)
    BOX_6_3 = (540, 226)
    BOX_6_4 = (540, 289)
    BOX_6_5 = (540, 352)
    BOX_POINT = [[CURRENT_PARTY_1, CURRENT_PARTY_2, CURRENT_PARTY_3, CURRENT_PARTY_4, CURRENT_PARTY_5, CURRENT_PARTY_6],
                 [BOX_1_1, BOX_1_2, BOX_1_3, BOX_1_4, BOX_1_5],
                 [BOX_2_1, BOX_2_2, BOX_2_3, BOX_2_4, BOX_2_5],
                 [BOX_3_1, BOX_3_2, BOX_3_3, BOX_3_4, BOX_3_5],
                 [BOX_4_1, BOX_4_2, BOX_4_3, BOX_4_4, BOX_4_5],
                 [BOX_5_1, BOX_5_2, BOX_5_3, BOX_5_4, BOX_5_5],
                 [BOX_6_1, BOX_6_2, BOX_6_3, BOX_6_4, BOX_6_5]]

    def _init_box_list(self) -> list[list[int]]:
        return [[1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, -1], [1, 1, 1, 1, 1, -1], [1, 1, 1, 1, 1, -1], [1, 1, 1, 1, 1, -1], [1, 1, 1, 1, 1, -1], [1, 1, 1, 1, 1, -1],]

    def _match_eggs(self, gray, box: list[list[int]]) -> list[list[int]]:
        if box is None:
            box = self._init_box_list()
        # threshold值为0.8时，无法识别队伍栏中选中的蛋
        locations = find_matches(gray, self._egg_template, 0.7)
        for loc in locations:
            for i in range(len(self.BOX_POINT)):
                for j in range(len(self.BOX_POINT[i])):
                    if self.BOX_POINT[i][j] is not None:
                        x = self.BOX_POINT[i][j][0]
                        y = self.BOX_POINT[i][j][1]
                        if i == 0:
                            width = self.CURRENT_PARTY_RECT[0]
                            height = self.CURRENT_PARTY_RECT[1]
                        else:
                            width = self.UNIT_BOX_RECT[0]
                            height = self.UNIT_BOX_RECT[1]
                        if loc[0] > x and loc[1] > y and loc[0] < x + width and loc[1] < y + height:
                            box[i][j] = 9
        return box

    def _match_box_space(self, gray, box: list[list[int]]) -> list[list[int]]:
        if box is None:
            box = self._init_box_list()
        cropped_gray = gray[:, self.BOX_SPLIT_X:]
        locations = find_matches(
            cropped_gray, self._box_space_template, threshold=0.8)
        for loc in locations:
            loc_x = loc[0] + self.BOX_SPLIT_X
            for i in range(len(self.BOX_POINT)):
                if i == 0:
                    continue
                for j in range(len(self.BOX_POINT[i])):
                    if self.BOX_POINT[i][j] is not None:
                        x = self.BOX_POINT[i][j][0]
                        y = self.BOX_POINT[i][j][1]
                        if loc_x > x - 5 and loc[1] > y - 5 and loc_x < x + 5 and loc[1] < y + 5:
                            box[i][j] = 0

        locations = find_matches(
            cropped_gray, self._box_space_selected_template, threshold=0.6)
        for loc in locations:
            loc_x = loc[0] + self.BOX_SPLIT_X
            for i in range(len(self.BOX_POINT)):
                if i == 0:
                    continue
                for j in range(len(self.BOX_POINT[i])):
                    if self.BOX_POINT[i][j] is not None:
                        x = self.BOX_POINT[i][j][0]
                        y = self.BOX_POINT[i][j][1]
                        if loc_x > x - 5 and loc[1] > y - 5 and loc_x < x + 5 and loc[1] < y + 5:
                            box[i][j] = 0

        return box

    def _match_current_party_space(self, gray, box: list[list[int]]) -> list[list[int]]:
        if box is None:
            box = self._init_box_list()
        cropped_gray = gray[:, :self.BOX_SPLIT_X]
        locations = find_matches(
            cropped_gray, self._current_party_space_template, 0.8)
        for loc in locations:
            i = 0
            for j in range(len(self.BOX_POINT[i])):
                if self.BOX_POINT[i][j] is not None:
                    x = self.BOX_POINT[i][j][0]
                    y = self.BOX_POINT[i][j][1]
                    if loc[0] > x - 5 and loc[1] > y - 5 and loc[0] < x + 5 and loc[1] < y + 5:
                        box[i][j] = 0

        match = cv2.matchTemplate(
            cropped_gray, self._current_party_space_selected_1_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, p = cv2.minMaxLoc(match)
        if max_val >= 0.7:
            i = 0
            for j in range(len(self.BOX_POINT[i])):
                if self.BOX_POINT[i][j] is not None:
                    x = self.BOX_POINT[i][j][0]
                    y = self.BOX_POINT[i][j][1]
                    if p[0] > x - 10 and p[1] > y - 10 and p[0] < x + 10 and p[1] < y + 10:
                        box[i][j] = 0
                        return box

        match = cv2.matchTemplate(
            cropped_gray, self._current_party_space_selected_2_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, p = cv2.minMaxLoc(match)
        if max_val >= 0.7:
            i = 0
            for j in range(len(self.BOX_POINT[i])):
                if self.BOX_POINT[i][j] is not None:
                    x = self.BOX_POINT[i][j][0]
                    y = self.BOX_POINT[i][j][1]
                    if p[0] > x - 10 and p[1] > y - 10 and p[0] < x + 10 and p[1] < y + 10:
                        box[i][j] = 0
                        return box

        return box

    def _match_arrow(self, gray) -> tuple[int, int]:
        arrow = None
        crop_x, crop_y, crop_w, crop_h = 15, 90, 590, 385
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        match = cv2.matchTemplate(
            crop_gray, self._box_arrow_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, p = cv2.minMaxLoc(match)
        if max_val < 0.4:
            return None

        for i in range(len(self.BOX_POINT)):
            if i == 0:
                width = self.CURRENT_PARTY_RECT[0]
            else:
                width = self.UNIT_BOX_RECT[0]
            for j in range(len(self.BOX_POINT[i])):
                if self.BOX_POINT[i][j] is not None:
                    x = self.BOX_POINT[i][j][0] - crop_x
                    y = self.BOX_POINT[i][j][1] - crop_y
                    if p[0] > x - 10 and p[1] > y - 10 and p[0] < x + width and p[1] < y + 10:
                        arrow = (i, j)
                        break
        if arrow is None:
            arrow = self._match_arrow_2(gray)
        return arrow

    def _match_arrow_2(self, gray) -> tuple[int, int]:
        arrow = None
        crop_x, crop_y, crop_w, crop_h = 15, 90, 590, 325
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        match = cv2.matchTemplate(
            crop_gray, self._box_arrow_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, p = cv2.minMaxLoc(match)
        if max_val < 0.4:
            return None

        for i in range(len(self.BOX_POINT)):
            if i == 0:
                width = self.CURRENT_PARTY_RECT[0]
            else:
                width = self.UNIT_BOX_RECT[0]
            for j in range(len(self.BOX_POINT[i])):
                if self.BOX_POINT[i][j] is not None:
                    x = self.BOX_POINT[i][j][0] - crop_x
                    y = self.BOX_POINT[i][j][1] - crop_y
                    if p[0] > x - 10 and p[1] > y - 10 and p[0] < x + width and p[1] < y + 10:
                        arrow = (i, j)
                        break
        return arrow

    def match(self, image) -> tuple[list[list[int]], tuple[int, int]]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        box = self._match_eggs(gray, None)
        box = self._match_box_space(gray, box)
        box = self._match_current_party_space(gray, box)
        p = self._match_arrow(gray)
        return (box, p)

    def match_arrow(self, image) -> tuple[int, int]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        p = self._match_arrow(gray)
        return p

    def release_tag_check(self, image, threshold=0.95) -> bool:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        match = cv2.matchTemplate(
            gray, self._release_tag_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(match)
        if max_val >= threshold:
            return True
        return False

    def sv_tag_check(self, image, threshold=0.9) -> bool:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        x, y, w, h = 625, 40, 335, 30
        crop_gray = gray[y:y+h, x:x+w]
        match = cv2.matchTemplate(
            crop_gray, self._sv_icon_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(match)
        if max_val >= threshold:
            return True
        return False

    def shiny_tag_check(self, image, threshold=0.9) -> bool:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        x, y, w, h = 625, 40, 335, 30
        crop_gray = gray[y:y+h, x:x+w]
        match = cv2.matchTemplate(
            crop_gray, self._shiny_icon_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(match)
        if max_val >= threshold:
            return True
        return False

    def current_party_eggs(self, image) -> int:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        box = self._match_eggs(gray, None)
        num = 0
        try:
            for i in range(len(box[0])):
                if box[0][i] == 9:
                    num += 1
        except:
            pass
        return num
