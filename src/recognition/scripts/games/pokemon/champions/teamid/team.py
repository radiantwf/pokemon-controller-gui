from recognition.scripts.games.pokemon.champions.teamid.pokemon import Pokemon


class Team:
    def __init__(self, offsets_y: int):
        self._offsets_y = offsets_y
        self._pokemons = [None, None, None, None, None, None]

    def split_pokemon(self, image):
        width, height = 750, 217
        pokes = [(184, 247+self._offsets_y), (985, 247+self._offsets_y), (184, 464+self._offsets_y), (985, 464+self._offsets_y), (184, 682+self._offsets_y), (985, 682+self._offsets_y)
                 ]
        poke_images = []
        for poke in pokes:
            poke_images.append(image[poke[1]:poke[1]+height, poke[0]:poke[0]+width])
        return poke_images

    def process_moves_image(self, image):
        pokes = self.split_pokemon(image)
        for i in range(len(pokes)):
            self._pokemons[i] = Pokemon()
            self._pokemons[i].process_moves_image(pokes[i])
            if self._pokemons[i].name == None or self._pokemons[i].name.strip() == '':
                self._pokemons[i] = None

    def process_states_image(self, image):
        pokes = self.split_pokemon(image)
        for i in range(len(pokes)):
            if self._pokemons[i] is None:
                break
            self._pokemons[i].process_states_image(pokes[i])

    @property
    def pokemons(self):
        return self._pokemons

    def __str__(self) -> str:
        return f"{''.join([str(poke) + '\n' for poke in self._pokemons])}"
