import cv2

class MenuCursorMatch:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        self._menu_arrow_template = cv2.imread(
            "resources/img/recognition/pokemon/sv/menu_arrow.jpg")
        self._menu_arrow_template = cv2.cvtColor(
            self._menu_arrow_template, cv2.COLOR_BGR2GRAY)

    # x = 0
    # 宝可梦1 0.9802355170249939 (23, 91)
    # 宝可梦2 0.9705981016159058 (23, 154)
    # 宝可梦3 0.9855178594589233 (23, 217)
    # 宝可梦4 0.9850992560386658 (23, 280)
    # 宝可梦5 0.9853918552398682 (23, 343)
    # 宝可梦6 0.9780521988868713 (23, 406)
    # 坐骑 0.9853339195251465 (23, 491)

    # x = 1
    # 包包 0.9837725162506104 (648, 121)
    # 盒子 0.9873440265655518 (649, 161)
    # 野餐 0.9854351282119751 (648, 201)
    # 宝可入口站 0.9781053066253662 (648, 241)
    # 设置 0.9854401350021362 (648, 281)
    # 记录 0.9784520864486694 (648, 321)
    # 付费新增内容 0.9627913236618042 (649, 419)

    MENU_SPLIT_X = 600

    MENU_ITEM_BAG_Y = 121
    MENU_ITEM_BOX_Y = 161
    MENU_ITEM_PANIC_Y = 201
    MENU_ITEM_ENTER_STATION_Y = 241
    MENU_ITEM_SETTINGS_Y = 281
    MENU_ITEM_SAVE_Y = 321
    MENU_ITEM_DLC_Y = 419

    CURRENT_PARTY_1_Y = 91
    CURRENT_PARTY_2_Y = 154
    CURRENT_PARTY_3_Y = 217
    CURRENT_PARTY_4_Y = 280
    CURRENT_PARTY_5_Y = 343
    CURRENT_PARTY_6_Y = 406
    CURRENT_PARTY_MOUNT_Y = 491

    def match(self, image, max_value_threshold=0.5) -> tuple(int, int, tuple[float, float, cv2.typing.Point, cv2.typing.Point]):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        match = cv2.matchTemplate(
            gray, self._menu_arrow_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, p = cv2.minMaxLoc(match)
        if max_val < max_value_threshold:
            return None
        
        x = -1
        y = -1

        if p[0] < self.MENU_SPLIT_X:
            x = 0
            if p[1] > self.CURRENT_PARTY_1_Y - 10 and p[1] < self.CURRENT_PARTY_1_Y + 10:
                y = 0
            elif p[1] > self.CURRENT_PARTY_2_Y - 10 and p[1] < self.CURRENT_PARTY_2_Y + 10:
                y = 1
            elif p[1] > self.CURRENT_PARTY_3_Y - 10 and p[1] < self.CURRENT_PARTY_3_Y + 10:
                y = 2
            elif p[1] > self.CURRENT_PARTY_4_Y - 10 and p[1] < self.CURRENT_PARTY_4_Y + 10:
                y = 3
            elif p[1] > self.CURRENT_PARTY_5_Y - 10 and p[1] < self.CURRENT_PARTY_5_Y + 10:
                y = 4
            elif p[1] > self.CURRENT_PARTY_6_Y - 10 and p[1] < self.CURRENT_PARTY_6_Y + 10:
                y = 5
            elif p[1] > self.CURRENT_PARTY_MOUNT_Y - 10 and p[1] < self.CURRENT_PARTY_MOUNT_Y + 10:
                y = 6
            else:
                x = -1
        else:
            x = 1
            if p[1] > self.MENU_ITEM_BAG_Y - 10 and p[1] < self.MENU_ITEM_BAG_Y + 10:
                y = 0
            elif p[1] > self.MENU_ITEM_BOX_Y - 10 and p[1] < self.MENU_ITEM_BOX_Y + 10:
                y = 1
            elif p[1] > self.MENU_ITEM_PANIC_Y - 10 and p[1] < self.MENU_ITEM_PANIC_Y + 10:
                y = 2
            elif p[1] > self.MENU_ITEM_ENTER_STATION_Y - 10 and p[1] < self.MENU_ITEM_ENTER_STATION_Y + 10:
                y = 3
            elif p[1] > self.MENU_ITEM_SETTINGS_Y - 10 and p[1] < self.MENU_ITEM_SETTINGS_Y + 10:
                y = 4
            elif p[1] > self.MENU_ITEM_SAVE_Y - 10 and p[1] < self.MENU_ITEM_SAVE_Y + 10:
                y = 5
            elif p[1] > self.MENU_ITEM_DLC_Y - 10 and p[1] < self.MENU_ITEM_DLC_Y + 10:
                y = 6
            else:
                x = -1
        return (x, y, p)
