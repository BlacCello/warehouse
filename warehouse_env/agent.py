import copy
from warehouse_env.helpers import print_position
from warehouse_env.constants import (
    MOVE_UP,
    MOVE_DOWN,
    MOVE_LEFT,
    MOVE_RIGHT,
    INVALID_ACTION,
    GOOD_ACTION,
)
from warehouse_env.bins import StagingIn, StagingOut


class Agent:
    def __init__(
        self,
        agent_pos,
        env_height: int,
        env_width: int,
        bin_size: int,
        blocked_positions,
    ):
        self.agent_pos = agent_pos
        self.env_height = env_height
        self.env_width = env_width
        self.bin_size = bin_size
        self.blocked_positions = blocked_positions
        self.loaded_item = None

    def to_string(self) -> str:
        return (
            "Agent at "
            + print_position(self.agent_pos)
            + " with "
            + (
                "Item " + self.loaded_item.to_string()
                if self.loaded_item
                else "no Item"
            )
        )

    def move(self, action: int) -> float:
        if action == MOVE_UP:
            if (
                self.agent_pos[0] - 1 < 0
                or [self.agent_pos[0] - 1, self.agent_pos[1]] in self.blocked_positions
            ):
                return INVALID_ACTION
            else:
                self.agent_pos[0] -= 1
        elif action == MOVE_DOWN:
            if (
                self.agent_pos[0] + 1 >= self.env_height
                or [self.agent_pos[0] + 1, self.agent_pos[1]] in self.blocked_positions
            ):
                return INVALID_ACTION
            else:
                self.agent_pos[0] += 1
        elif action == MOVE_LEFT:
            if (
                self.agent_pos[1] - 1 < 0
                or [self.agent_pos[0], self.agent_pos[1] - 1] in self.blocked_positions
            ):
                return INVALID_ACTION
            else:
                self.agent_pos[1] -= 1
        elif action == MOVE_RIGHT:
            if (
                self.agent_pos[1] + 1 >= self.env_width
                or [self.agent_pos[0], self.agent_pos[1] + 1] in self.blocked_positions
            ):
                return INVALID_ACTION
            else:
                self.agent_pos[1] += 1
        else:
            # TODO check obstacles!!!!
            raise AssertionError("Invalid action Type.")

        assert self.agent_pos not in self.blocked_positions
        return 0.0

    def load_item(
        self, bins, staging_in: StagingIn, staging_out: StagingOut, slot: int
    ) -> float:
        # check if agent has capacity
        if self.loaded_item is not None:
            return INVALID_ACTION
        # check for bins
        for b in bins:
            if self.agent_pos in b.loading_positions and slot in b.get_slots():
                self.loaded_item = b.remove_item(slot)
                if (
                    staging_out.pick_transaction is not None and
                    self.loaded_item.slot in staging_out.pick_transaction.slot_ids
                    and not self.loaded_item.had_first_remove_from_bin_reward
                ):
                    # loaded item that is in pick_transaction
                    print("Item removed first time from Bin")
                    self.loaded_item.had_first_remove_from_bin_reward = True
                    return 0.0 # GOOD_ACTION - GOOD_ACTION here will result in more instable training
                else:
                    # just loaded item of unrelated bin
                    return 0.0

        if (
            self.agent_pos in staging_in.loading_positions
            and slot in staging_in.get_used_slot_ids()
        ):
            # Item picked up from Staging Area
            self.loaded_item = staging_in.remove_item(slot)
            print("Item from Staging In")
            return GOOD_ACTION

        return INVALID_ACTION

    def unload_item(
        self, bins, staging_in: StagingIn, staging_out: StagingOut, slot: int
    ) -> float:
        # check if agent has item to put
        if self.loaded_item is None:
            return INVALID_ACTION

        # check for bins
        for b in bins:
            if self.agent_pos in b.loading_positions and slot == self.loaded_item.slot:
                b.place_item(self.loaded_item, slot)
                if (
                    staging_in.put_transaction is not None
                    and self.loaded_item in staging_in.put_transaction.items
                    and not self.loaded_item.had_first_place_in_bin_reward
                ):
                    # delivered item that was in put transaction
                    self.loaded_item.had_first_place_in_bin_reward = True
                    print("Item placed first time to Bin")
                    self.loaded_item = None
                    return GOOD_ACTION
                else:
                    # just moved item between bins
                    self.loaded_item = None
                    return 0.0

        if (
            self.agent_pos in staging_out.loading_positions
            and slot in staging_out.incoming
        ):
            # At Staging and item is in transaction
            staging_out.place_item(self.loaded_item, slot)
            self.loaded_item = None
            print("Item to Staging Out")
            return GOOD_ACTION

        return INVALID_ACTION

