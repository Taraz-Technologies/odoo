from odoo import api, fields, models


class AssemblyProcess(models.Model):
    _name = "assembly.process"
    _description = "Assembly Process"


class Nd4Feeders(models.Model):
    _name = "nd4.feeders"
    _description = "ND4 Feeders"
    _rec_name = "x_name"
    _order = "x_name"

    x_group = fields.Integer(string='Group', required=False)
    x_name = fields.Char(string='Name', readonly=True)

    x_nozzle = fields.Selection(selection=[
        ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('12', '12'), ('13', '13'), ('14', '14'), ('23', '23'),
        ('24', '24'), ('34', '34'), ('123', '123'), ('124', '124'), ('134', '134'), ('234', '234'), ('1234', '1234'),
    ], string='Nozzle', default='1', compute="compute_nozzles", store=True, readonly=False)

    x_x_mm = fields.Float(string='X (mm)', required=True)
    x_y_mm = fields.Float(string='Y (mm)', required=True)
    x_pick_angle = fields.Integer(string='Pick Angle', required=True)

    x_product_id = fields.Many2one(comodel_name='product.product', string='Value')
    x_package_id = fields.Many2one(related="x_product_id.x_package_id", readonly=False, store=True)
    x_feed_rate = fields.Selection(related="x_package_id.x_feed_rate", readonly=False, store=True)
    x_pick_height = fields.Float(related="x_package_id.x_pick_height", readonly=False, store=True)
    x_place_height = fields.Float(related="x_package_id.x_place_height", readonly=False, store=True)

    @api.depends('x_package_id')
    def compute_nozzles(self):
        for rec in self:
            nozzle_config_ids = self.env['nozzle.config'].search([])
            nozzle = ''
            for line in nozzle_config_ids:
                if rec.x_package_id.id in line.x_nozzle_id.x_package_ids.ids:
                    nozzle += '%s' % line.x_number
            rec.x_nozzle = nozzle


class Nd4Packages(models.Model):
    _name = "nd4.packages"
    _description = "ND4 Packages"
    _rec_name = "x_name"

    x_name = fields.Char(string='Name', required=False)
    x_feed_rate = fields.Selection(selection=[
        ('0', '0'), ('2', '2'), ('4', '4'), ('8', '8'), ('12', '12')
    ], string='Feed Rate', required=True)
    x_pick_height = fields.Float(string='Pick Height')
    x_place_height = fields.Float(string='Place Height')
    x_tape_width = fields.Float(string='Tape Width')
    x_nozzle_ids = fields.Many2many(comodel_name='nd4.nozzles', string='Nozzles')

    def get_nozzle_ids(self):
        for rec in self:
            nozzle_ids = self.env['nd4.nozzles'].search([('x_package_ids', 'ilike', rec.id)])
            rec.x_nozzle_ids = nozzle_ids.ids


class Nd4Nozzles(models.Model):
    _name = "nd4.nozzles"
    _description = "ND4 Nozzles"
    _rec_name = "x_name"

    x_name = fields.Char(string='Name', required=False)
    x_package_ids = fields.Many2many(comodel_name='nd4.packages', string='Packages')

    @api.onchange('x_package_ids')
    def _onchange_package_ids(self):
        for rec in self:
            rec.x_package_ids.get_nozzle_ids()


class Nd2Feeders(models.Model):
    _name = "nd2.feeders"
    _description = "ND2 Feeders"
    _rec_name = "x_name"
    _order = "x_name"

    x_name = fields.Char(string='Name', readonly=True)
    x_product_id = fields.Many2one(comodel_name='product.product', string='Value')


class PnpLines(models.Model):
    _name = "assembly.processing"
    _description = "Assembly Procesing"

    x_work_order_id = fields.Many2one(comodel_name='mrp.workorder', string='Work Order', required=True)

    x_product_id = fields.Many2one(comodel_name='product.product', string='Product', required=False)
    x_package_id = fields.Many2one(related="x_product_id.x_package_id", readonly=False, store=True)

    x_ref_des = fields.Char(string='RefDes', required=False)
    x_x_axis = fields.Float(string='X (mm)', required=False, digits=(5, 5))
    x_y_axis = fields.Float(string='Y (mm)', required=False, digits=(5, 5))
    x_side = fields.Char(string='Side', required=False)
    x_angle = fields.Float(string='Rotate', required=False, digits=(0, 0))


class NozzleConfig(models.Model):
    _name = "nozzle.config"
    _description = "Nozzle Configuration"

    x_number = fields.Integer(string='Number', required=False)
    x_nozzle_id = fields.Many2one(comodel_name='nd4.nozzles', string='Nozzle', required=False)






