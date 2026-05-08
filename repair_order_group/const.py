# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

ADD_GROUPED_REPAIR_STATE_PARAMS = {
    "draft": "repair_order_group.grouped_repair_state_draft",
    "confirmed": "repair_order_group.grouped_repair_state_confirmed",
    "under_repair": "repair_order_group.grouped_repair_state_under_repair",
}

SALE_ORDER_BLOCKING_STATES = frozenset({"sale", "cancel"})

ADD_GROUPED_REPAIR_DEFAULT_STATES = frozenset({"draft"})
