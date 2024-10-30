# Copyright (C) 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestRepairTransfer(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a product with lot/serial tracking
        cls.product_with_lot = cls.env["product.product"].create(
            {
                "name": "Product with lot tracking",
                "type": "product",
                "tracking": "lot",
                "list_price": 10.0,
                "categ_id": cls.env.ref("product.product_category_all").id,
            }
        )
        cls.lot_id = cls.env["stock.lot"].create(
            {
                "name": "LOT0001",
                "product_id": cls.product_with_lot.id,
                "company_id": cls.env.company.id,
            }
        )

        # Create unique repair orders
        cls.repair_r1 = cls.env["repair.order"].create(
            {
                "product_id": cls.product_with_lot.id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "lot_id": cls.lot_id.id,
                "product_qty": 5.0,
            }
        )
        cls.repair_r2 = cls.env["repair.order"].create(
            {
                "product_id": cls.product_with_lot.id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "lot_id": cls.lot_id.id,
                "product_qty": 1.0,
            }
        )

        # Create a destination location
        cls.stock_location_destination = cls.env["stock.location"].create(
            {"name": "Destination Locations", "usage": "internal"}
        )

        # Add stock for repair orders
        cls.env["stock.quant"].create(
            {
                "product_id": cls.product_with_lot.id,
                "lot_id": cls.lot_id.id,
                "location_id": cls.repair_r1.location_id.id,
                "quantity": 5.0,
            }
        )

    def setUpRepairOrder(self, repair_order):
        # Validate and set the state of the repair order
        repair_order.action_validate()
        self.assertEqual(repair_order.state, "confirmed")
        repair_order.action_repair_start()
        self.assertEqual(repair_order.state, "under_repair")
        repair_order.action_repair_end()
        self.assertEqual(repair_order.state, "done")

    def createTransfer(self, repair_order, quantity):
        # Create and execute a transfer wizard
        transfer_repair_wizard = self.env["repair.move.transfer"].create(
            {
                "repair_order_id": repair_order.id,
                "quantity": quantity,
                "location_dest_id": self.stock_location_destination.id,
                "remaining_quantity": repair_order.remaining_quantity,
            }
        )
        transfer_repair_wizard.action_create_transfer()

    def test_repair_transfer_1(self):
        self.setUpRepairOrder(self.repair_r1)
        self.createTransfer(self.repair_r1, 1.0)
        self.assertEqual(len(self.repair_r1.picking_ids), 1)

    def test_repair_transfer_2(self):
        self.setUpRepairOrder(self.repair_r2)
        self.createTransfer(self.repair_r2, 1.0)
        self.assertEqual(len(self.repair_r2.picking_ids), 1)

        move_line = self.repair_r2.picking_ids.mapped("move_ids").mapped(
            "move_line_ids"
        )[0]
        self.assertEqual(move_line.lot_id.name, "LOT0001")

    def test_multiple_transfers(self):
        self.setUpRepairOrder(self.repair_r1)

        # Attempt to create a transfer for 0 items.
        with self.assertRaises(
            UserError, msg="Quantity to transfer must be greater than 0."
        ):
            self.createTransfer(self.repair_r1, 0.0)

        # Create the first transfer for 1 item
        self.createTransfer(self.repair_r1, 1.0)

        # Update remaining quantity after first transfer
        self.repair_r1._compute_remaining_quantity()

        # Create the second transfer for 2 items
        self.createTransfer(self.repair_r1, 2.0)

        # Update remaining quantity after second transfer
        self.repair_r1._compute_remaining_quantity()

        # Attempt to create a third transfer for 3 items,
        # which exceeds the remaining quantity (which is now 2)
        with self.assertRaises(
            UserError,
            msg="Quantity to transfer cannot exceed the remaining "
            "quantity in the repair order.",
        ):
            self.createTransfer(self.repair_r1, 3.0)

        # Check the number of pickings created
        self.assertEqual(len(self.repair_r1.picking_ids), 2)

        # Check the total quantity transferred
        total_transferred = sum(
            qty
            for picking in self.repair_r1.picking_ids
            for qty in picking.move_ids.mapped("product_uom_qty")
        )
        self.assertEqual(
            total_transferred, 3.0, "Total transferred quantity should equal to 3.0"
        )
