from odoo import fields, models, api


class ManualProcDemand(models.Model):
    _name = "manual.proc.demand"
    _description = "Manual Production Demand"
    _rec_name = 'x_user_id'

    x_user_id = fields.Many2one(comodel_name='res.users', string='Demand from', default=lambda self: self.env.user)
    x_product_id = fields.Many2one(comodel_name='product.product', string='Product', required=True)
    x_free_qty = fields.Float(related="x_product_id.free_qty", string='Available', required=False)
    x_uom_id = fields.Many2one(related="x_product_id.uom_id", string='UoM')
    x_date = fields.Date(string='Deadline', required=True, default=fields.datetime.today())
    x_delay_days = fields.Integer(string='Delay (Days)', compute="compute_delay_days", store=True)
    x_product_qty = fields.Float(string='Demand Qty', required=False)
    x_url = fields.Char(string='Demand URL', required=False)
    x_note = fields.Char(string='Demand Note', required=False)
    x_status = fields.Selection(selection=[
        ('draft', 'Draft'), ('in_progress', 'In Progress'), ('in_stock', 'In Stock'),
    ], string='Proc. Status', required=True, default='draft')
    x_company_id = fields.Many2one(
        comodel_name='res.company', string='Company', required=True, default=lambda self: self.env.company
    )

    @api.depends('x_date')
    def compute_delay_days(self):
        for rec in self:
            if rec.x_date < fields.date.today():
                rec.x_delay_days = (fields.date.today() - rec.x_date).days


class ManualProcDemandLines(models.Model):
    _name = "manual.proc.demand.lines"
    _rec_name = 'x_product_id'
    _description = 'Manual Procurement Demand Lines'

    x_procurement_cycle_id = fields.Many2one(comodel_name='procurement.cycle', string='Procurement Cycle', required=False)

    x_manual_proc_demand_id = fields.Many2one(comodel_name='manual.proc.demand', string='Manual Procurement Demand')
    x_user_id = fields.Many2one(related='x_manual_proc_demand_id.x_user_id')
    x_product_id = fields.Many2one(related='x_manual_proc_demand_id.x_product_id', readonly=False, store=True)
    x_product_qty = fields.Float(related='x_manual_proc_demand_id.x_product_qty', readonly=False, store=True)
    x_uom_id = fields.Many2one(related='x_manual_proc_demand_id.x_uom_id', readonly=False, store=True)
    x_date = fields.Date(related='x_manual_proc_demand_id.x_date', readonly=False, store=True)
    x_url = fields.Char(related='x_manual_proc_demand_id.x_url')
    x_note = fields.Char(related='x_manual_proc_demand_id.x_note')
    x_status = fields.Selection(related='x_manual_proc_demand_id.x_status')

    def unlink(self):
        for rec in self:
            rec.x_manual_proc_demand_id.x_status = 'draft'
            demand_detail_id = self.env['component.list.demand.details'].search([('x_internal_demand_id', '=', rec.id)])
            if demand_detail_id:
                if len(demand_detail_id.x_component_id.x_demand_detail_ids) == 1:
                    demand_detail_id.x_component_id.unlink()
                else:
                    demand_detail_id.x_component_id.x_required_qty -= rec.x_product_qty
                    demand_detail_id.x_component_id.x_missing_qty -= rec.x_product_qty
                    demand_detail_id.x_component_id.compute_safety_stock()
                    demand_detail_id.unlink()
        return super(ManualProcDemandLines, self).unlink()











