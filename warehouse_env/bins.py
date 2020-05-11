import random
import copy
import itertools
from warehouse_env.item import Item
from warehouse_env.helpers import print_position
from warehouse_env.transaction import PickTransaction, PutTransaction
from warehouse_env.constants import PICK_T, PUT_T


class Bin:
    def __init__(self, pos, loading_positions):
        self.pos = pos
        self.loading_positions = loading_positions
        self._slots = {}

    def place_item(self, item: Item, slot: int):
        assert item.slot == slot
        self._slots[slot] = item

    def remove_item(self, slot: int) -> Item:
        return self._slots.pop(slot)

    def get_slots(self):
        return self._slots

    def get_used_slot_ids(self):
        return self._slots.keys()

    def to_string(self) -> str:
        return (
            "Bin at "
            + print_position(self.pos)
            + " with Items { "
            + ", ".join(
                [
                    "Slot " + str(slot) + ": " + item.to_string()
                    for slot, item in self._slots.items()
                    if item is not None
                ]
            )
            + " }"
        )


class StagingIn(Bin):
    def __init__(self, pos, loading_positions):
        super().__init__(pos, loading_positions)
        self.put_transaction = None

    def apply_put(self, put_transaction: PutTransaction):
        assert put_transaction.get_type() == PUT_T
        assert len(self.get_slots()) == 0
        for item in put_transaction.items:
            self.get_slots()[item.slot] = item
        self.put_transaction = put_transaction

    def is_current_transaction_done(self, bins):
        used_slots = [
            x for x in itertools.chain.from_iterable(b.get_used_slot_ids() for b in bins)
        ]
        for item in self.put_transaction.items:
            if item.slot not in used_slots:
                return False
        return True

    def place_item(self, item: Item, slot: int):
        raise NotImplementedError("Forbidden action UNLOAD_ITEM for StagingIn")

    def to_string(self) -> str:
        return (
            "StagingIn: "
            + super().to_string()
            + " » Transaction: "
            + (
                self.put_transaction.to_string()
                if self.put_transaction is not None
                else "None"
            )
        )


class StagingOut(Bin):
    def __init__(self, pos, loading_positions):
        super().__init__(pos, loading_positions)
        self.pick_transaction = None
        self.incoming = []

    def get_slots(self):
        raise NotImplementedError("This Method is not allowed for StagingOut")

    def apply_pick(self, pick_transaction: PickTransaction):
        assert pick_transaction.get_type() == PICK_T
        for slot in pick_transaction.slot_ids:
            self.incoming.append(slot)
        self.pick_transaction = pick_transaction

    def is_current_transaction_done(self):
        return len(self.incoming) == 0

    def remove_item(self, slot: int) -> Item:
        raise NotImplementedError("Forbidden action LOAD_ITEM for StagingOut")

    def place_item(self, item: Item, slot: int):
        self.incoming.remove(slot)
        # Do not really place as it's out of the warehouse

    def to_string(self) -> str:
        return (
            "StagingOut: "
            + "Bin at "
            + print_position(self.pos)
            + " with Items { "
            + ", ".join(str(slot) for slot in self.incoming)
            + " }"
            + " » Transaction: "
            + (
                self.pick_transaction.to_string()
                if self.pick_transaction is not None
                else "None"
            )
        )

