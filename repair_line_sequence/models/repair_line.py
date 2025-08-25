# Copyright Cetmix OU 2025
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class RepairLine(models.Model):
    """Extend repair lines to support manual ordering with a sequence.
    
    The tree view uses the "handle" widget to drag & drop rows. This field
    ensures a stable deterministic order and is increased automatically
    for newly created lines within the same repair order.
    """
    _inherit = "repair.line"

    sequence = fields.Integer(string="Sequence", default=10)
    _order = "sequence, id"

    @api.model
    def create(self, vals):
        """Assign a next sequence inside the same repair if not provided."""
        if not vals.get("sequence") and vals.get("repair_id"):
            last = (
                self.search(
                    [("repair_id", "=", vals["repair_id"])],
                    order="sequence desc",
                    limit=1,
                )
            )
            vals["sequence"] = (last.sequence or 0) + 10
        return super().create(vals)