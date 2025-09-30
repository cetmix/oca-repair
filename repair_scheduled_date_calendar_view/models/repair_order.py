# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RepairOrder(models.Model):
    _inherit = "repair.order"

    def _get_default_planned_duration(self):
        """Get default planned duration from config parameter."""
        return float(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "repair_scheduled_date_calendar_view.planned_duration_default",
                1.0,
            )
        )

    planned_duration = fields.Float(
        default=lambda self: self._get_default_planned_duration(),
        help="Planned duration of the repair order in hours.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("schedule_date"):
                vals["schedule_date"] = fields.Datetime.now()

            # Special case: calendar view always injects 1.0
            if "planned_duration" in vals and vals["planned_duration"] == 1.0:
                vals["planned_duration"] = self._get_default_planned_duration()
        return super().create(vals_list)

    @api.constrains("planned_duration")
    def _check_planned_duration(self):
        for rec in self:
            if rec.planned_duration < 0:
                raise ValidationError(_("Planned duration must be non-negative."))
