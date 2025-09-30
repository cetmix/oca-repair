# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestRepairCalendar(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.RepairOrder = cls.env["repair.order"]
        cls.IrConfig = cls.env["ir.config_parameter"].sudo()

    def test_default_planned_duration(self):
        order = self.RepairOrder.create({"name": "Test Repair"})
        self.assertEqual(order.planned_duration, 1.0)

    def test_changed_default_duration(self):
        self.IrConfig.set_param(
            "repair_scheduled_date_calendar_view.planned_duration_default", 2.5
        )
        order = self.RepairOrder.create({"name": "Repair 2"})
        self.assertEqual(order.planned_duration, 2.5)

    def test_manual_override(self):
        order = self.RepairOrder.create({"name": "Repair 3", "planned_duration": 4.0})
        self.assertEqual(order.planned_duration, 4.0)
