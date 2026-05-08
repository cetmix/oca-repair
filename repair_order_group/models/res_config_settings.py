# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from ..const import ADD_GROUPED_REPAIR_STATE_PARAMS


class ResConfigSettings(models.TransientModel):
    """Add repair group settings to the Repair configuration page."""

    _inherit = "res.config.settings"

    grouped_repair_state_draft = fields.Boolean(
        string="New",
        config_parameter=ADD_GROUPED_REPAIR_STATE_PARAMS["draft"],
        default=True,
    )
    grouped_repair_state_confirmed = fields.Boolean(
        string="Confirmed",
        config_parameter=ADD_GROUPED_REPAIR_STATE_PARAMS["confirmed"],
    )
    grouped_repair_state_under_repair = fields.Boolean(
        string="Under Repair",
        config_parameter=ADD_GROUPED_REPAIR_STATE_PARAMS["under_repair"],
    )
