# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestRepairOrderGroup(TransactionCase):
    """Test cases for Repair Order Group functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()

        cls.company = cls.env.company
        cls.partner = cls.env["res.partner"].create({"name": "Test Customer"})
        cls.another_partner = cls.env["res.partner"].create(
            {"name": "Another Customer"}
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "list_price": 100.0,
            }
        )

        cls.picking_type = cls.env["stock.picking.type"].search(
            [("code", "=", "repair_operation"), ("company_id", "=", cls.company.id)],
            limit=1,
        )
        if not cls.picking_type:
            warehouse = cls.env["stock.warehouse"].search([], limit=1)
            cls.picking_type = cls.env["stock.picking.type"].create(
                {
                    "name": "Test Repair Operation",
                    "code": "repair_operation",
                    "sequence_code": "REP",
                    "warehouse_id": warehouse.id,
                }
            )

    def test_01_create_repair_order_group(self):
        """Test creating repair order group."""
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
            }
        )

        repair.action_add_another_repair()
        group = repair.group_id

        self.assertTrue(group.name)
        self.assertEqual(group.partner_id, self.partner)
        self.assertEqual(group.repair_count, 2)

    def test_02_add_another_repair_action(self):
        """Test adding another repair to group."""
        repair1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
            }
        )
        self.assertFalse(repair1.group_id)

        action = repair1.action_add_another_repair()
        repair2 = self.env["repair.order"].browse(action["res_id"])

        self.assertTrue(repair1.group_id)
        self.assertEqual(repair1.group_id, repair2.group_id)
        self.assertEqual(repair1.partner_id, repair2.partner_id)
        self.assertIn(repair2, repair1.grouped_repair_ids)
        self.assertEqual(repair1.group_id.repair_count, 2)

    def test_03_partner_synchronization(self):
        """Test partner synchronization across group."""
        group = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )

        repair1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )
        repair2 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )

        # Test changing partner
        repair1.write({"partner_id": self.another_partner.id})

        self.assertEqual(repair1.partner_id, self.another_partner)
        self.assertEqual(repair2.partner_id, self.another_partner)
        self.assertEqual(group.partner_id, self.another_partner)

        # Test clearing partner
        repair1.write({"partner_id": False})
        self.assertFalse(repair1.partner_id)
        self.assertFalse(repair2.partner_id)
        self.assertFalse(group.partner_id)

    def test_04_cascade_confirmation(self):
        """Test cascade confirmation of group repairs."""
        group = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        repair1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )
        repair2 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )

        repair1.action_validate()
        repair2.action_validate()
        repair1._action_repair_confirm()

        self.assertEqual(repair1.state, "confirmed")
        self.assertEqual(repair2.state, "confirmed")

    def test_05_cascade_cancellation(self):
        """Test cascade cancellation of group repairs."""
        group = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        repair1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )
        repair2 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )

        repair1.action_validate()
        repair1._action_repair_confirm()
        repair2.action_validate()
        repair2._action_repair_confirm()

        repair1.action_repair_cancel()

        self.assertEqual(repair1.state, "cancel")
        self.assertEqual(repair2.state, "cancel")

    def test_06_group_sale_order_creation(self):
        """Test creating sale order for entire group."""
        group = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )

        repair1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
                "group_id": group.id,
            }
        )
        repair2 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
                "group_id": group.id,
            }
        )

        action = repair1.action_create_sale_order()
        sale_order = self.env["sale.order"].browse(action["res_id"])

        self.assertEqual(repair1.sale_order_id, sale_order)
        self.assertEqual(repair2.sale_order_id, sale_order)

        # Main assertion: SO was created and repairs are linked
        # Order lines depend on additional materials, not main products
        self.assertTrue(sale_order)

    def test_07_warranty_pricing(self):
        """Test warranty pricing in sale order lines."""
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
                "under_warranty": True,
            }
        )
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        repair.write({"sale_order_id": sale_order.id})

        move = self.env["stock.move"].create(
            {
                "name": "Warranty add",
                "company_id": self.company.id,
                "repair_id": repair.id,
                "repair_line_type": "add",
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": 1.0,
            }
        )
        move._create_repair_sale_order_line()
        self.assertTrue(sale_order.order_line)

        order_line = sale_order.order_line[0]
        self.assertEqual(order_line.price_unit, 0.0)

    def test_08_prevent_multiple_sale_orders(self):
        """Test that repairs with existing SO raise error when selected."""
        group = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        repair1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
                "group_id": group.id,
            }
        )
        repair2 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
                "group_id": group.id,
            }
        )

        repair1.action_create_sale_order()

        self.assertTrue(repair1.sale_order_id)
        self.assertTrue(repair2.sale_order_id)
        self.assertEqual(repair1.sale_order_id, repair2.sale_order_id)

        with self.assertRaises(UserError):
            repair1.action_create_sale_order()

        repair3 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
                "group_id": group.id,
            }
        )
        with self.assertRaises(UserError):
            (repair1 + repair3).action_create_sale_order()

    def test_09_no_partner_error(self):
        """Test error when creating sale order without partner."""
        repair = self.env["repair.order"].create(
            {
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
            }
        )
        with self.assertRaises(UserError):
            repair.action_create_sale_order()

    def test_10_skip_context_flags(self):
        """Test context flags to prevent recursion."""
        group = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )

        # Test skip_group_sync
        repair1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )
        repair2 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )

        repair1.with_context(skip_group_sync=True).write(
            {"partner_id": self.another_partner.id}
        )
        self.assertEqual(repair2.partner_id, self.partner)

        group2 = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        repair3 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group2.id,
            }
        )
        repair4 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group2.id,
            }
        )

        repair3.with_context(skip_group_confirm=True)._action_repair_confirm()
        self.assertEqual(repair4.state, "draft")

        group3 = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        repair5 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group3.id,
            }
        )
        repair6 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group3.id,
            }
        )

        repair5.action_validate()
        repair5._action_repair_confirm()
        repair6.action_validate()
        repair6._action_repair_confirm()

        repair5.with_context(skip_group_cancel=True).action_repair_cancel()
        self.assertEqual(repair6.state, "confirmed")

    def test_11_repair_count_computation(self):
        """Test repair count computation in groups."""
        group = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        self.assertEqual(group.repair_count, 0)

        for _ in range(3):
            self.env["repair.order"].create(
                {
                    "partner_id": self.partner.id,
                    "picking_type_id": self.picking_type.id,
                    "group_id": group.id,
                }
            )
        self.assertEqual(group.repair_count, 3)

    def test_12_group_sale_order_creation_with_multiple_warehouses(self):
        """RO from the same group with different warehouses create separate SOs."""
        group = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )

        # Create second warehouse and picking type
        warehouse_2 = self.env["stock.warehouse"].create(
            {
                "name": "Second Warehouse",
                "code": "WH_TEST_2",
            }
        )
        picking_type_2 = self.env["stock.picking.type"].create(
            {
                "name": "Test Repair Operation 2",
                "code": "repair_operation",
                "sequence_code": "REP2",
                "warehouse_id": warehouse_2.id,
            }
        )

        # Two repairs with first warehouse
        repair1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,  # Warehouse 1
                "product_id": self.product.id,
                "group_id": group.id,
            }
        )
        repair2 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,  # Warehouse 1
                "product_id": self.product.id,
                "group_id": group.id,
            }
        )

        # One repair with second warehouse
        repair3 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": picking_type_2.id,  # Warehouse 2
                "product_id": self.product.id,
                "group_id": group.id,
            }
        )

        # Trigger grouped SO creation
        repair1.action_create_sale_order()

        # Each repair must be linked to a sale order
        self.assertTrue(repair1.sale_order_id)
        self.assertTrue(repair2.sale_order_id)
        self.assertTrue(repair3.sale_order_id)

        # Repairs with the same warehouse share the same SO
        self.assertEqual(repair1.sale_order_id, repair2.sale_order_id)

        # Repair with different warehouse has a different SO
        self.assertNotEqual(repair1.sale_order_id, repair3.sale_order_id)

        # Sanity check: group has exactly two distinct sale orders
        sale_orders = group.repair_ids.mapped("sale_order_id")
        self.assertEqual(len(sale_orders), 2)

    def test_13_empty_group_so_creation(self):
        """Test SO creation for group with no valid repairs."""
        group = self.env["repair.order.group"].create({"partner_id": self.partner.id})

        # Create cancelled repair (not valid for SO)
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
                "state": "cancel",
            }
        )

        # Should not create SO and not raise error
        repair.action_create_sale_order()
        self.assertFalse(repair.sale_order_id)

    def test_14_mixed_repair_states_in_group(self):
        """Test cascade actions with mixed repair states."""
        group = self.env["repair.order.group"].create({"partner_id": self.partner.id})

        repair1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
                "state": "draft",
            }
        )
        repair2 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
                "state": "confirmed",  # Already confirmed
            }
        )

        # Should only confirm draft repairs
        repair1._action_repair_confirm()
        self.assertEqual(repair1.state, "confirmed")
        self.assertEqual(repair2.state, "confirmed")  # Should remain confirmed

    def test_15_warehouse_none_handling(self):
        """Test SO creation with repairs where warehouse is None."""
        group = self.env["repair.order.group"].create({"partner_id": self.partner.id})

        # Use existing picking type but simulate None warehouse
        # by mocking the warehouse_id to be None/False
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
                "group_id": group.id,
            }
        )

        # Temporarily set warehouse to None to test the logic
        original_warehouse = self.picking_type.warehouse_id
        self.picking_type.warehouse_id = False

        try:
            repair.action_create_sale_order()
            self.assertTrue(repair.sale_order_id)
            self.assertFalse(repair.sale_order_id.warehouse_id)
        finally:
            # Restore original warehouse
            self.picking_type.warehouse_id = original_warehouse

    def test_16_partner_sync_complex_scenarios(self):
        """Test partner synchronization in complex scenarios."""
        group = self.env["repair.order.group"].create({"partner_id": self.partner.id})

        repairs = self.env["repair.order"].create(
            [
                {
                    "partner_id": self.partner.id,
                    "picking_type_id": self.picking_type.id,
                    "group_id": group.id,
                }
                for _ in range(5)
            ]
        )

        # Test bulk partner change
        repairs[0].write({"partner_id": self.another_partner.id})

        # All should have new partner
        for repair in repairs:
            self.assertEqual(repair.partner_id, self.another_partner)

    def test_17_empty_recordset_handling(self):
        """Test methods with empty recordsets."""
        # Test empty recordset in _action_repair_confirm
        empty_repairs = self.env["repair.order"]
        result = empty_repairs._action_repair_confirm()
        self.assertTrue(result)  # Should return True for empty recordset

        # Test empty recordset in action_repair_cancel
        result = empty_repairs.action_repair_cancel()
        self.assertTrue(result)  # Should return True for empty recordset

    def test_18_no_partner_error_multiple_repairs(self):
        """Test no partner error with multiple repairs."""
        repairs = self.env["repair.order"].create(
            [
                {
                    "picking_type_id": self.picking_type.id,
                    "product_id": self.product.id,
                    # No partner_id - should raise error
                }
                for _ in range(3)
            ]
        )

        with self.assertRaises(UserError) as context:
            repairs.action_create_sale_order()

        self.assertIn("define a customer", str(context.exception))

    def test_19_valid_ungrouped_repairs(self):
        """Test SO creation for valid ungrouped repairs."""
        # Create ungrouped repairs (no group_id)
        repair1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
                # No group_id - should use standard logic
            }
        )
        repair2 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
                # No group_id - should use standard logic
            }
        )

        # Test each repair individually to avoid multiple SOs in action
        repair1.action_create_sale_order()
        repair2.action_create_sale_order()

        # Both should have SOs created
        self.assertTrue(repair1.sale_order_id)
        self.assertTrue(repair2.sale_order_id)
        # They should have different SOs since they're ungrouped
        self.assertNotEqual(repair1.sale_order_id, repair2.sale_order_id)

    def test_20_empty_repairs_to_process(self):
        """Test partner sync when no repairs to process."""
        group = self.env["repair.order.group"].create({"partner_id": self.partner.id})

        # Single repair in group - no other repairs to sync with
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )

        # Should not crash when no grouped_repair_ids
        repair.write({"partner_id": self.another_partner.id})
        self.assertEqual(repair.partner_id, self.another_partner)

    def test_21_cascade_empty_group_repairs(self):
        """Test cascade actions when group has no other repairs."""
        group = self.env["repair.order.group"].create({"partner_id": self.partner.id})

        # Only one repair in group
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )

        # Should work fine even with no other repairs in group
        repair.action_validate()
        repair._action_repair_confirm()
        self.assertEqual(repair.state, "confirmed")

        repair.action_repair_cancel()
        self.assertEqual(repair.state, "cancel")

    # ------------------------------------------------------------------ #
    #  Tests for task 5417: configurable "Add Grouped Repair" visibility  #
    # ------------------------------------------------------------------ #

    def _set_allowed_states(self, **state_flags):
        """Helper: set config_parameter for each state via ir.config_parameter.

        Pass state=True/False keyword arguments, e.g.:
            self._set_allowed_states(draft=True, confirmed=False)
        Unspecified states default to False.
        """
        from ..const import ADD_GROUPED_REPAIR_STATE_PARAMS

        ICP = self.env["ir.config_parameter"].sudo()
        for state, param in ADD_GROUPED_REPAIR_STATE_PARAMS.items():
            ICP.set_param(param, str(state_flags.get(state, False)))

    def test_22_button_visible_in_allowed_state_no_so(self):
        """Button is visible when state is allowed and no SO exists."""
        self._set_allowed_states(draft=True)
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
            }
        )
        self.assertEqual(repair.state, "draft")
        self.assertTrue(repair.show_add_grouped_repair)
        self.assertTrue(repair._can_add_grouped_repair())

    def test_23_button_hidden_in_disallowed_state(self):
        """Button is hidden when current state is not in allowed list."""
        self._set_allowed_states(draft=True)
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
            }
        )
        repair._action_repair_confirm()
        # state is now 'confirmed', not in allowed list
        self.assertFalse(repair.show_add_grouped_repair)
        self.assertFalse(repair._can_add_grouped_repair())

    def test_24_button_hidden_when_so_confirmed(self):
        """Button is hidden regardless of state when SO is confirmed."""
        self._set_allowed_states(draft=True, confirmed=True, under_repair=True)
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
            }
        )
        sale_order = self.env["sale.order"].create({"partner_id": self.partner.id})
        sale_order.action_confirm()  # state -> 'sale'
        repair.write({"sale_order_id": sale_order.id})
        self.assertFalse(repair.show_add_grouped_repair)
        self.assertFalse(repair._can_add_grouped_repair())

    def test_25_button_hidden_when_so_cancelled(self):
        """Button is hidden when the related SO is cancelled."""
        self._set_allowed_states(draft=True, confirmed=True, under_repair=True)
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
            }
        )
        sale_order = self.env["sale.order"].create({"partner_id": self.partner.id})
        sale_order.action_cancel()  # state -> 'cancel'
        repair.write({"sale_order_id": sale_order.id})
        self.assertFalse(repair.show_add_grouped_repair)
        self.assertFalse(repair._can_add_grouped_repair())

    def test_26_button_hidden_when_setting_empty(self):
        """When no states are configured button is hidden everywhere."""
        self._set_allowed_states()  # all False -> deny all
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
            }
        )
        self.assertFalse(repair.show_add_grouped_repair)
        self.assertFalse(repair._can_add_grouped_repair())

    def test_27_button_visible_multiple_allowed_states(self):
        """Button is visible when current state is one of several allowed."""
        self._set_allowed_states(draft=True, confirmed=True)
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
            }
        )
        repair._action_repair_confirm()
        self.assertEqual(repair.state, "confirmed")
        self.assertTrue(repair.show_add_grouped_repair)
        self.assertTrue(repair._can_add_grouped_repair())

    def test_28_action_raises_when_not_allowed(self):
        """action_add_another_repair raises UserError when state is not allowed."""
        self._set_allowed_states()  # deny all
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
            }
        )
        with self.assertRaises(UserError):
            repair.action_add_another_repair()

    def test_29_default_state_draft_enabled(self):
        """After installation, draft state is enabled by default via field default."""
        from ..const import ADD_GROUPED_REPAIR_STATE_PARAMS

        ICP = self.env["ir.config_parameter"].sudo()
        draft_param = ADD_GROUPED_REPAIR_STATE_PARAMS["draft"]
        val = ICP.get_param(draft_param, False)
        self.assertTrue(val)
