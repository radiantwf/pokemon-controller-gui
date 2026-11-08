from recognition.scripts.games.pokemon.champions.teamid.pokemon import Pokemon
import cv2
import os

REGION_WIDTH = 750
REGION_HEIGHT = 217

class Team:
    def __init__(self, offsets_y: int, output_dir: str = "./img_champions", save_images: bool = True, should_stop=None):
        self._offsets_y = offsets_y
        self._pokemons = [None, None, None, None, None, None]
        self._output_dir = output_dir
        self._save_images = save_images
        self._ocr_errors = []
        self._should_stop = should_stop
        self._number_ocr_engine = None
        if self._save_images:
            os.makedirs(self._output_dir, exist_ok=True)

    def split_pokemon(self, image):
        pokes = [(184, 247+self._offsets_y), (985, 247+self._offsets_y), (184, 464+self._offsets_y), (985, 464+self._offsets_y), (184, 682+self._offsets_y), (985, 682+self._offsets_y)
                 ]
        poke_images = []
        for poke in pokes:
            poke_images.append(image[poke[1]:poke[1]+REGION_HEIGHT, poke[0]:poke[0]+REGION_WIDTH])
        return poke_images

    def process_moves_image(self, image):
        if self._save_images:
            cv2.imwrite(f"{self._output_dir}/team_basic.png", image)
        pokes = self.split_pokemon(image)
        for i in range(len(pokes)):
            if self._should_stop and self._should_stop():
                raise InterruptedError
            if self._save_images:
                cv2.imwrite(f"{self._output_dir}/poke{i}.png", pokes[i])

            self._pokemons[i] = Pokemon(number_ocr_engine=self._number_ocr_engine)
            self._number_ocr_engine = self._pokemons[i].ocr_engine_number
            self._pokemons[i].process_moves_image(
                pokes[i],
                i,
                output_dir=self._output_dir,
                save_images=self._save_images,
            )
            if self._pokemons[i].name == None or self._pokemons[i].name.strip() == '':
                self._ocr_errors.extend(self._pokemons[i].ocr_errors)
                self._pokemons[i] = None

    def process_states_image(self, image):
        if self._save_images:
            cv2.imwrite(f"{self._output_dir}/team_states.png", image)
        pokes = self.split_pokemon(image)
        for i in range(len(pokes)):
            if self._should_stop and self._should_stop():
                raise InterruptedError
            if self._save_images:
                cv2.imwrite(f"{self._output_dir}/poke{i}_stats.png", pokes[i])
            if self._pokemons[i] is None:
                continue
            self._pokemons[i].process_states_image(
                pokes[i],
                i,
                output_dir=self._output_dir,
                save_images=self._save_images,
            )

    @property
    def pokemons(self):
        return self._pokemons

    @property
    def ocr_errors(self):
        errors = list(self._ocr_errors)
        for poke in self._pokemons:
            if poke is not None:
                errors.extend(poke.ocr_errors)
        return errors

    @property
    def conversion_errors(self):
        errors = []
        for poke in self._pokemons:
            if poke is not None:
                errors.extend(poke.conversion_errors)
        return errors

    @property
    def ev_errors(self):
        errors = []
        for poke in self._pokemons:
            if poke is not None:
                errors.extend(poke.ev_errors)
        return errors

    def __str__(self) -> str:
        return "\n".join([str(poke) for poke in self._pokemons if poke is not None and poke.name is not None and poke.name.strip() != ""])
