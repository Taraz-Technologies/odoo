from odoo import _
from odoo.tests import Form
from odoo.tests.common import TransactionCase
import logging
from odoo.fields import Datetime as Dt
from datetime import datetime, timedelta


_logger = logging.getLogger("*__testing__*")

# Command to run test
# ./odoo-bin -c /etc/odoo13.conf --test-enable --stop-after-init -d developer --init cus_mrp_valuation_correction
class TestManufacturingOrder(TransactionCase):

    # Manufacturing Order Performance Testing
    def test_manufacturing_order(self):
        product_to_build = self.env['product.product'].browse([21959])  # CPE-3PH-SiC-800V-50A
        operation_id = self.env['stock.picking.type'].browse([8]) # Manufacturing
        bom_id = product_to_build.bom_ids[0]
        # Create MO
        mo_form = Form(self.env['mrp.production'])
        mo_form.product_id = product_to_build
        mo_form.product_uom_id = product_to_build.uom_id
        mo_form.product_qty = bom_id.product_qty
        mo_form.x_manufacturing_type = 'mrp'
        mo_form.bom_id = bom_id
        mo_form.date_planned_start = Dt.now()
        mo_form.date_planned_finished = Dt.now() + timedelta(days=1)
        mo_form.company_id = self.env['res.company'].browse([1])
        mo_form.picking_type_id = operation_id
        mo_form.location_src_id = operation_id.default_location_src_id
        mo_form.location_dest_id = operation_id.default_location_dest_id
        mo = mo_form.save()
        self.assertEqual(mo.state, 'draft', "Production order should be in draft state.")
        # # Compute Manufacturing BoM
        # mo.compute_bom_lines()
        # Confirm MO
        mo.action_confirm()
        self.assertEqual(mo.state, 'confirmed', "Production order should be in confirmed state.")

        picking_id = self.env['stock.picking'].search([
            ('group_id', '=', mo.procurement_group_id.id), ('group_id', '!=', False),
        ])

        vals = {
            'name': 'Initial inventory',
            'line_ids': []
        }
        for line in picking_id.mapped('move_lines'):
            vals['line_ids'].append((0, 0, {
                'product_id': line.product_id.id,
                'product_uom_id': line.product_uom.id,
                'product_qty': line.product_uom_qty,
                'location_id': operation_id.default_location_dest_id.id
            }))
        inventory = self.env['stock.inventory'].create(vals)
        inventory.action_start()
        inventory.action_validate()

        picking_id.action_assign()
        self.assertEqual(picking_id.state, 'assigned', "Picking order should be in assigned state.")
        for move in picking_id.mapped('move_lines').filtered(lambda m: m.state not in ['done', 'cancel']):
            for move_line in move.move_line_ids:
                move_line.qty_done = move_line.product_uom_qty
        picking_id.action_done()
        self.assertEqual(picking_id.state, 'done', "Picking order should be in done state.")

        # Plan MO
        mo.button_plan()
        self.assertEqual(mo.state, 'planned', "Production order should be in planned state.")
        # Validate WOs
        for workorder_id in mo.workorder_ids:
            workorder_id.button_start()
            workorder_id.record_production()
        self.assertEqual(mo.state, 'to_close', "Production order should be in to_close state.")
        # Validate MO
        mo.button_mark_done()
        self.assertEqual(mo.state, 'done', "Production order should be in done state.")

        # Check MO for Errors
        self._check_mo_for_errors(mo)

        # Unlock MO
        mo.action_toggle_is_locked()

        # Create Error in MO

        # 1A. More Stock is consumed as compared to BoM
        mo.move_raw_ids[0].move_line_ids.update({'qty_done': sum(mo.move_raw_ids[0].move_line_ids.mapped('qty_done')) * 2})
        error_in_stock_consumption = mo.error_in_stock_consumption()
        if error_in_stock_consumption:
            mo.correct_error_in_stock_consumption()

        # 1B. Less Stock is consumed as compared to BoM
        mo.move_raw_ids[0].move_line_ids.update({'qty_done': 0})
        error_in_stock_consumption = mo.error_in_stock_consumption()
        if error_in_stock_consumption:
            mo.correct_error_in_stock_consumption()

        # 2. Qty produced is not equal to MO qty
        mo.move_finished_ids[0].move_line_ids.update({'qty_done': mo.product_qty * 2})
        error_in_stock_production = mo.error_in_stock_production()
        if error_in_stock_production:
            mo.correct_error_in_stock_production()

        # 3. Net Valuation not equal to 0
        mo.move_raw_ids[0].move_line_ids.update({'qty_done': 0})
        error_in_valuation = mo.error_in_valuation()
        if error_in_valuation:
            mo.correct_error_in_valuation()

        # Lock MO
        mo.action_toggle_is_locked()

        # Check MO for Errors
        self._check_mo_for_errors(mo)

    def _check_mo_for_errors(self, order):
        # 1. More or Less Stock is consumed as compared to BoM
        for line in order.bom_id.bom_line_ids:
            move_ids = order.move_raw_ids.filtered(lambda l: l.product_id.id == line.product_id.id)
            self.assertEqual(
                sum(move_ids.mapped('quantity_done')),
                line.product_qty,
                "1. More or Less Stock is consumed of %s as compared to BoM" % line.product_id.name,
            )
        # 2. Qty produced is not equal to MO qty
        self.assertEqual(
            sum(order.move_finished_ids.mapped('quantity_done')),
            order.product_qty,
            "2. Qty produced is not equal to MO qty",
        )
        # 3. Net Valuation not equal to 0
        self.assertEqual(
            -sum(order.move_raw_ids.stock_valuation_layer_ids.mapped('value')),
            sum(order.move_finished_ids.stock_valuation_layer_ids.mapped('value')),
            "3. Net Valuation not equal to 0",
        )
        _logger.info(sum(order.move_raw_ids.stock_valuation_layer_ids.mapped('value')))
        _logger.info(sum(order.move_finished_ids.stock_valuation_layer_ids.mapped('value')))