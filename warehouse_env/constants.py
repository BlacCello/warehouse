"""
Actions:
- MoveUp
- MoveDown
- MoveLeft
- MoveRight
- BinSlotUp
- BinSlotDown
- LoadItem
- UnloadItem
"""


# Actions
MOVE_UP = 0
MOVE_DOWN = 1
MOVE_LEFT = 2
MOVE_RIGHT = 3


# Transactions
PUT_T = 1
PICK_T = 2
TRANSACTION_NAMES = {
    PUT_T: "Put",
    PICK_T: "Pick"
}

# REWARDS
INVALID_ACTION = -0.5
GOOD_ACTION = 5.0