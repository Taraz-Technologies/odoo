import datetime

from odoo import _
from odoo.tests import Form
from odoo.tests.common import TransactionCase
from odoo.addons.mrp.tests.common import TestMrpCommon
import logging
from odoo.fields import Datetime as Dt
from datetime import datetime, timedelta

_logger = logging.getLogger("*__testing__*")


class TestManufacturingOrder(TestMrpCommon):

    # Manufacturing Order Performance Testing
    def test_manufacturing_order(self):
        product_to_build = self.env['product.product'].browse([21959])  # CPE-3PH-SiC-800V-50A
        picking_id = self.env['stock.picking.type'].browse([8]) # Manufacturing
        stock_location_id = self.env['stock.location'].browse([7]) # PK
        bom_1 = product_to_build.bom_ids[0]
        # Create MO
        mo_form = Form(self.env['mrp.production'])
        mo_form.product_id = product_to_build
        mo_form.product_uom_id = product_to_build.uom_id
        mo_form.product_qty = bom_1.product_qty
        mo_form.x_manufacturing_type = 'mrp'
        mo_form.bom_id = bom_1
        mo_form.date_planned_start = Dt.now()
        mo_form.date_planned_finished = Dt.now() + timedelta(days=1)
        mo_form.company_id = self.env['res.company'].browse([1])
        mo_form.picking_type_id = picking_id
        mo_form.location_src_id = self.env['stock.location'].browse([17])
        mo_form.location_dest_id = stock_location_id
        mo = mo_form.save()
        self.assertEqual(mo.state, 'draft', "Production order should be in draft state.")
        # # Compute Manufacturing BoM
        # mo.compute_bom_lines()
        # Confirm MO
        mo.action_confirm()
        self.assertEqual(mo.state, 'confirmed', "Production order should be in confirmed state.")

        picking_ids = self.env['stock.picking'].search([
            ('group_id', '=', mo.procurement_group_id.id), ('group_id', '!=', False),
        ])

        vals = {
            'name': 'Initial inventory',
            'line_ids': []
        }
        for line in picking_ids.mapped('move_lines'):
            vals['line_ids'].append((0, 0, {
                'product_id': line.product_id.id,
                'product_uom_id': line.product_uom.id,
                'product_qty': line.product_uom_qty,
                'location_id': stock_location_id.id
            }))
        inventory = self.env['stock.inventory'].create(vals)
        inventory.action_start()
        inventory.action_validate()

        picking_ids.action_assign()
        self.assertEqual(picking_ids.state, 'assigned', "Picking order should be in assigned state.")
        for move in picking_ids.mapped('move_lines').filtered(lambda m: m.state not in ['done', 'cancel']):
            for move_line in move.move_line_ids:
                move_line.qty_done = move_line.product_uom_qty
        picking_ids.action_done()
        self.assertEqual(picking_ids.state, 'done', "Picking order should be in done state.")
        # Plan MO
        mo.button_plan()
        self.assertEqual(mo.state, 'planned', "Production order should be in planned state.")
        # Validate WOs
        for workorder_id in mo.workorder_ids:
            workorder_id.button_start()
            workorder_id.record_production()
        self.assertEqual(mo.state, 'to_close', "Production order should be in to_close state.")
        # Merged Validate MO
        mo.button_mark_done()
        self.assertEqual(mo.state, 'done', "Production order should be in done state.")
