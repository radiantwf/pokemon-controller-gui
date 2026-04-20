from enum import Enum
class DetailTagEnum(Enum):
    Move = 0
    Item = 1
    Teammate = 2
    Nature = 3
    EVs = 4
    Ability = 5


class Pokemon:
    def __init__(self, index: int,name:str):
        self._index = index
        self._name = name
        self._moves = []
        self._items = []
        self._teammates = []
        self._natures = []
        self._evs = []
        self._abilities = []
    
    def __str__(self):
        str = f"{self._index},{self._name}\n"
        str += f"Moves:\n{self._moves}\n"
        str += f"Items:\n{self._items}\n"
        str += f"Teammates:\n{self._teammates}\n"
        str += f"Natures:\n{self._natures}\n"
        str += f"EVs:\n{self._evs}\n"
        str += f"Abilities:\n{self._abilities}\n"
        return str

    def to_dict(self):
        return {
            "index": self._index,
            "name": self._name,
            "moves": self._moves,
            "items": self._items,
            "teammates": self._teammates,
            "natures": self._natures,
            "evs": self._evs,
            "abilities": self._abilities,
        }

    def append_row(self, tag: DetailTagEnum, value):
        if tag == DetailTagEnum.Move:
            self._moves.append(value)
        elif tag == DetailTagEnum.Item:
            self._items.append(value)
        elif tag == DetailTagEnum.Teammate:
            self._teammates.append(value)
        elif tag == DetailTagEnum.Nature:
            self._natures.append(value)
        elif tag == DetailTagEnum.EVs:
            self._evs.append(value)
        elif tag == DetailTagEnum.Ability:
            self._abilities.append(value)

    @property
    def name(self):
        return self._name

    @property
    def moves(self):
        return self._moves

    @property
    def items(self):
        return self._items

    @property
    def teammates(self):
        return self._teammates
        
    @property
    def natures(self):
        return self._natures
        
    @property
    def evs(self):
        return self._evs
        
    @property
    def abilities(self):
        return self._abilities
