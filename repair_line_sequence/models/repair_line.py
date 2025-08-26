# Copyright Cetmix OU 2025
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from collections import defaultdict

from odoo import api, fields, models


class RepairLine(models.Model):
    _inherit = "repair.line"

    sequence = fields.Integer(default=10, index=True)
    _order = "sequence, id"

    @api.model_create_multi
    def create(self, vals_list):
        """Assign next sequence per repair when missing (batch-friendly)."""
        vals_list = [vals.copy() for vals in vals_list]
        per_repair = defaultdict(list)

        for idx, vals in enumerate(vals_list):
            if "sequence" not in vals and vals.get("repair_id"):
                per_repair[vals["repair_id"]].append(idx)

        for repair_id, idxs in per_repair.items():
            last = self.search(
                [("repair_id", "=", repair_id)], order="sequence desc", limit=1
            )
            next_seq = (last.sequence or 0) + 10
            for i in idxs:
                vals_list[i]["sequence"] = next_seq
                next_seq += 10

        return super().create(vals_list)
