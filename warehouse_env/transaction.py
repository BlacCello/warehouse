import random
import itertools
from warehouse_env.item import Item
from warehouse_env.constants import PICK_T, PUT_T, TRANSACTION_NAMES


class Transaction:
    def to_string(self) -> str:
        return TRANSACTION_NAMES[self.get_type()] + self.info()

    def info(self) -> str:
        raise NotImplementedError("This Method is abstract.")

    def get_type(self) -> int:
        raise NotImplementedError("This Method is abstract.")


class PickTransaction(Transaction):
    def __init__(self, slot_ids):
        super().__init__()
        self.slot_ids = slot_ids

    def get_type(self) -> int:
        return PICK_T

    def info(self) -> str:
        return " with Items " + ", ".join(str(item_id) for item_id in self.slot_ids)


class PutTransaction(Transaction):
    def __init__(self, items):
        super().__init__()
        self.items = items

    def get_type(self) -> int:
        return PUT_T

    def info(self) -> str:
        return " with Items " + ", ".join(item.to_string() for item in self.items)


def create_new_transaction(
    max_items_in_env: int, bin_slot_size: int, bins
) -> Transaction:
    # ignore agent item as a new transaction should be only generated if agent has no item
    used_slots = [
        x for x in itertools.chain.from_iterable(b.get_used_slot_ids() for b in bins)
    ]
    is_put_possible = max_items_in_env - len(used_slots) > 0
    is_pick_possible = len(used_slots) > 0

    if is_pick_possible and is_put_possible:
        if bool(random.getrandbits(1)):
            return _create_pick_transation(used_slots, bin_slot_size)
        else:
            return _create_put_transaction(
                used_slots, max_items_in_env, bin_slot_size
            )
    elif is_pick_possible:
        return _create_pick_transation(used_slots, bin_slot_size)
    elif is_put_possible:
        return _create_put_transaction(
            used_slots, max_items_in_env, bin_slot_size
        )
    else:
        raise AssertionError("Either pick or put transaction must be creatable")


def _create_pick_transation(used_slots: int, bin_slot_size: int) -> Transaction:
    number_of_picks = random.randint(1, min(bin_slot_size, len(used_slots)))
    pick_up_ids = random.sample(used_slots, number_of_picks)
    return PickTransaction([item_id for item_id in pick_up_ids])


def _create_put_transaction(
    used_slots: int, max_items_in_env: int, bin_slot_size: int
) -> Transaction:
    number_of_picks = random.randint(
        1, min(bin_slot_size, max_items_in_env - len(used_slots))
    )
    # items must not be zero based!
    free_ids = [
        item_id + 1
        for item_id in range(max_items_in_env)
        if (item_id + 1) not in used_slots
    ]
    pick_up_ids = random.sample(free_ids, number_of_picks)
    return PutTransaction([Item(item_id) for item_id in pick_up_ids])
