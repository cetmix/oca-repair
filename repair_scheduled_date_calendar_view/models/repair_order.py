# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    planned_duration = fields.Float(
        default=lambda self: float(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "repair_scheduled_date_calendar_view.planned_duration_default", 1.0
            )
        ),
        help="Planned duration of the repair order in hours.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("schedule_date"):
                vals["schedule_date"] = fields.Datetime.now()

            if not vals.get("planned_duration"):
                vals["planned_duration"] = float(
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param(
                        "repair_scheduled_date_calendar_view.planned_duration_default",
                        1.0,
                    )
                )
        return super().create(vals_list)
