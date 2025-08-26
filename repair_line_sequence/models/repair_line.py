# Copyright Cetmix OU 2025
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from collections import defaultdict

from odoo import api, fields, models


class RepairLine(models.Model):
    _inherit = "repair.line"

    sequence = fields.Integer(
        help="Order of repair lines; lower values appear first.",
        default=10,
        index=True,
    )

    _order = "sequence, id"

    @api.model_create_multi
    def create(self, vals_list):
        """Assign next sequence per repair when missing (batch-friendly)."""
        vals_list = [vals.copy() for vals in vals_list]
        per_repair = defaultdict(list)

        for idx, vals in enumerate(vals_list):
            if "sequence" not in vals and vals.get("repair_id"):
                per_repair[vals["repair_id"]].append(idx)

        if per_repair:
            groups = self.read_group(
                [("repair_id", "in", list(per_repair.keys()))],
                ["sequence:max"],
                ["repair_id"],
            )
            max_by_repair = {
                g["repair_id"][0]: (g.get("sequence_max") or 0) for g in groups
            }

            for repair_id, idxs in per_repair.items():
                next_seq = max_by_repair.get(repair_id, 0) + 10
                for i in idxs:
                    vals_list[i]["sequence"] = next_seq
                    next_seq += 10

        return super().create(vals_list)
