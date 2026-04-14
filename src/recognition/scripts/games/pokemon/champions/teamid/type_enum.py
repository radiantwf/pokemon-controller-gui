
from enum import Enum


class PokemonTypeType(Enum):
    NoneType = "none"
    Dark = "dark"
    Dragon = "dragon"
    Electric = "electric"
    Fairy = "fairy"
    Fighting = "fighting"
    Fire = "fire"
    Flying = "flying"
    Ghost = "ghost"
    Grass = "grass"
    Ground = "ground"
    Ice = "ice"
    Normal = "normal"
    Poison = "poison"
    Psychic = "psychic"
    Rock = "rock"
    Steel = "steel"
    Water = "water"

    @staticmethod
    def get_template_path(name: "PokemonTypeType"):
        return f"resources/img/recognition/pokemon/champions/type/{name.value}.png"
   
