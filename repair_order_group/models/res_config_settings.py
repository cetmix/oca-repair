# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

PARAM_KEY = "repair_order_group.add_grouped_repair_states"


class ResConfigSettings(models.TransientModel):
    """Add repair group settings to the Repair configuration page."""

    _inherit = "res.config.settings"

    grouped_repair_state_draft = fields.Boolean(string="New")
    grouped_repair_state_confirmed = fields.Boolean(string="Confirmed")
    grouped_repair_state_under_repair = fields.Boolean(string="Under Repair")

    def _states_to_booleans(self, states):
        return {
            "grouped_repair_state_draft": "draft" in states,
            "grouped_repair_state_confirmed": "confirmed" in states,
            "grouped_repair_state_under_repair": "under_repair" in states,
        }

    def _booleans_to_states(self):
        states = []
        if self.grouped_repair_state_draft:
            states.append("draft")
        if self.grouped_repair_state_confirmed:
            states.append("confirmed")
        if self.grouped_repair_state_under_repair:
            states.append("under_repair")
        return states

    def get_values(self):
        res = super().get_values()
        raw = self.env["ir.config_parameter"].sudo().get_param(PARAM_KEY, "")
        states = {s.strip() for s in raw.split(",") if s.strip()}
        res.update(self._states_to_booleans(states))
        return res

    def set_values(self):
        super().set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            PARAM_KEY, ",".join(self._booleans_to_states())
        )
        return

    @api.model
    def _set_default_add_grouped_repair_stages(self):
        """Set 'draft' as the default allowed state on module installation."""
        self.env["ir.config_parameter"].sudo().set_param(PARAM_KEY, "draft")
