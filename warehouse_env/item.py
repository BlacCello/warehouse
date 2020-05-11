class Item:
    def __init__(self, slot: int):
        self.slot = slot
        self.had_first_place_in_bin_reward = False
        self.had_first_remove_from_bin_reward = False

    def to_string(self) -> str:
        return str(self.slot)
