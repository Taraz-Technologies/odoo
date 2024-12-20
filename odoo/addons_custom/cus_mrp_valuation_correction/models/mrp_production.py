from PIL.ImageChops import difference

from odoo import fields, models, api, _


class MrpValuationCorrection(models.Model):
    _inherit = 'mrp.production'

    def error_in_stock_consumption(self):
        for rec in self:
            for line in rec.bom_id.bom_line_ids:
                move_ids = rec.move_raw_ids.filtered(lambda l: l.product_id.id == line.product_id.id)
                if sum(move_ids.mapped('quantity_done')) != line.product_qty:
                    return True
        return False

    def correct_error_in_stock_consumption(self):
        for rec in self:
            if not rec.error_in_stock_consumption():
                return
            rec.is_locked = False
            corrected_lines = 0
            for line in rec.bom_id.bom_line_ids:
                move_line_ids = rec.move_raw_ids.move_line_ids.filtered(lambda l: l.product_id.id == line.product_id.id and l.state == 'done')
                diff = line.product_qty - sum(move_line_ids.mapped('qty_done'))
                if diff != 0:
                    corrected_lines += 1
                    for move_line in move_line_ids:
                        if move_line.qty_done + diff >= 0:
                            move_line.write({'qty_done': move_line.qty_done + diff})
                            break
                        else:
                            diff += move_line.qty_done
                            move_line.write({'qty_done': 0})
                if corrected_lines == 2:
                    break
            rec.is_locked = True

    def error_in_stock_production(self):
        for rec in self:
            return True if sum(rec.move_finished_ids.mapped('quantity_done')) != rec.product_qty else False

    def correct_error_in_stock_production(self):
        for rec in self:
            if not rec.error_in_stock_production():
                return
            rec.is_locked = False
            move_line_ids = rec.move_finished_ids.move_line_ids.filtered(lambda l: l.state == 'done')
            diff = rec.product_qty - sum(move_line_ids.mapped('qty_done'))
            for move_line in move_line_ids:
                if move_line.qty_done + diff >= 0:
                    move_line.write({'qty_done': move_line.qty_done + diff})
                    break
                else:
                    diff += move_line.qty_done
                    move_line.write({'qty_done': 0})
            rec.is_locked = True

    def error_in_valuation(self):
        for rec in self:
            return True if sum((rec.move_raw_ids + rec.move_finished_ids + rec.scrap_ids.move_id).stock_valuation_layer_ids.mapped('value')) != 0 else False

    def correct_error_in_valuation(self):
        for rec in self:
            if not rec.error_in_valuation():
                return

            # Correct MO Product Stock Valuation Layer (SVL)
            mo_svl = rec.move_finished_ids[0].stock_valuation_layer_ids[0]
            error_in_value = sum((rec.move_raw_ids + rec.move_finished_ids + rec.scrap_ids.move_id).stock_valuation_layer_ids.mapped('value'))

            # value correction
            vl_correction = mo_svl.value - error_in_value
            # unit_cost correction
            uc_correction = vl_correction / mo_svl.quantity
            # remaining_value correction
            rv_correction = uc_correction * mo_svl.remaining_qty

            mo_svl.stock_move_id.price_unit = uc_correction

            mo_svl.update({
                'value': vl_correction,
                'unit_cost': uc_correction,
                'remaining_value': rv_correction,
            })
            if mo_svl.account_move_id:
                line_ids = mo_svl.account_move_id.mapped('line_ids')
                for line in line_ids:
                    self.env.cr.execute(
                        "UPDATE account_move_line set debit = '%s', credit = '%s', balance = %s WHERE id=%s" % (
                            vl_correction if line.debit != 0 else 0,
                            vl_correction if line.credit != 0 else 0,
                            vl_correction or 0.0,
                            line.id,
                        )
                    )
            else:
                mo_svl.stock_move_id._account_entry_move(mo_svl.quantity, mo_svl.description, mo_svl.id, mo_svl.value)
                mo_svl.account_move_id.update({'date': mo_svl.create_date.date()})

            # Correct SVL value error where quantity is consumed from this MO
            out_svl_ids = self.env['stock.valuation.layer'].search([
                ('product_id', '=', mo_svl.product_id.id),
                ('company_id', '=', mo_svl.company_id.id),
                ('id', '>', mo_svl.id),
                ('quantity', '<', 0),
            ], order="id")

            qty_consumed = mo_svl.quantity - mo_svl.remaining_qty

            for out_svl_id in out_svl_ids:
                update_account_move = False
                out_svl_qty = - out_svl_id.quantity
                if qty_consumed <= out_svl_qty:
                    out_svl_id.value += error_in_value * qty_consumed / mo_svl.quantity
                    out_svl_id.unit_cost = out_svl_id.value / out_svl_qty
                    qty_consumed = 0
                    update_account_move = True
                elif qty_consumed > out_svl_qty:
                    out_svl_id.value += error_in_value * out_svl_qty / mo_svl.quantity
                    out_svl_id.unit_cost = out_svl_id.value / out_svl_qty
                    qty_consumed -= out_svl_qty
                    update_account_move = True

                if update_account_move:
                    if out_svl_id.account_move_id:
                        line_ids = out_svl_id.account_move_id.mapped('line_ids')
                        for line in line_ids:
                            self.env.cr.execute(
                                "UPDATE account_move_line set debit = '%s', credit = '%s', balance = %s WHERE id=%s" % (
                                    - out_svl_id.value if line.debit != 0 else 0,
                                    - out_svl_id.value if line.credit != 0 else 0,
                                    - out_svl_id.value or 0.0,
                                    line.id,
                                )
                            )
                    else:
                        out_svl_id.stock_move_id._account_entry_move(
                            out_svl_id.quantity, out_svl_id.description, out_svl_id.id, out_svl_id.value
                        )
                        out_svl_id.account_move_id.update({'date': out_svl_id.create_date.date()})
                if qty_consumed == 0:
                    break



