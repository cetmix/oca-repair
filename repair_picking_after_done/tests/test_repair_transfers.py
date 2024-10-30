# Copyright (C) 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.tests.common import TransactionCase


class TestRepairTransfer(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create unique repair orders
        cls.repair_r1 = cls.env.ref("repair.repair_r1").copy()
        cls.repair_r2 = cls.env.ref("repair.repair_r2").copy()

        # Now we will create a destination location
        cls.stock_location_destination = cls.env["stock.location"].create(
            {"name": "Destination Locations", "usage": "internal"}
        )

        # Let's add some stock for repair_r1
        cls.env["stock.quant"].create(
            {
                "product_id": cls.repair_r1.product_id.id,
                "location_id": cls.repair_r1.location_id.id,
                "quantity": 1.0,
            }
        )

        # Create a product with lot/serial tracking
        product_with_lot = cls.env["product.product"].create(
            {
                "name": "Product with lot tracking",
                "type": "product",
                "tracking": "lot",
                "list_price": 10.0,
                "categ_id": cls.env.ref("product.product_category_all").id,
            }
        )
        lot_id = cls.env["stock.lot"].create(
            {
                "name": "LOT0001",
                "product_id": product_with_lot.id,
                "company_id": cls.env.company.id,
            }
        )

        # Add stock for repair_r2
        cls.env["stock.quant"].create(
            {
                "product_id": product_with_lot.id,
                "lot_id": lot_id.id,
                "location_id": cls.repair_r2.location_id.id,
                "quantity": 1.0,
            }
        )
        cls.repair_r2.write({"lot_id": lot_id.id, "product_id": product_with_lot.id})

    def test_repair_transfer_1(self):
        # Validate the repair order
        self.repair_r1.action_validate()
        self.assertEqual(self.repair_r1.state, "confirmed")

        self.repair_r1.action_repair_start()
        self.assertEqual(self.repair_r1.state, "under_repair")

        self.repair_r1.action_repair_end()
        self.assertEqual(self.repair_r1.state, "done")

        transfer_repair_wizard = self.env["repair.move.transfer"].create(
            {
                "repair_order_id": self.repair_r1.id,
                "quantity": 1.0,
                "location_dest_id": self.stock_location_destination.id,
            }
        )
        transfer_repair_wizard.action_create_transfer()

        self.assertEqual(len(self.repair_r1.picking_ids), 1)

    def test_repair_transfer_2(self):
        # Validate the repair order
        self.repair_r2.action_validate()
        self.assertEqual(self.repair_r2.state, "confirmed")

        self.repair_r2.action_repair_start()
        self.assertEqual(self.repair_r2.state, "under_repair")

        self.repair_r2.action_repair_end()
        self.assertEqual(self.repair_r2.state, "done")

        transfer_repair_wizard = self.env["repair.move.transfer"].create(
            {
                "repair_order_id": self.repair_r2.id,
                "quantity": 1.0,
                "location_dest_id": self.stock_location_destination.id,
            }
        )
        transfer_repair_wizard.action_create_transfer()
        self.assertEqual(len(self.repair_r2.picking_ids), 1)

        move_line = self.repair_r2.picking_ids.mapped("move_ids").mapped(
            "move_line_ids"
        )[0]
        self.assertEqual(move_line.lot_id.name, "LOT0001")
