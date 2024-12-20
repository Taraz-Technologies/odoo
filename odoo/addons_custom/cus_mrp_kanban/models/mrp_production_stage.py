from odoo import models, fields, api, _


class MrpProductionStage(models.Model):
    _name = 'mrp.production.stage'
    _description = 'Manufacturing Kanban Stage'
    _rec_name = 'x_name'
    _order = 'sequence, id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    x_name = fields.Char(string='Stage Name', required=True, translate=True)
    x_description = fields.Text(string="Description", translate=True)
    sequence = fields.Integer(default=1)
    fold = fields.Boolean(
        string='Folded in Kanban',
        help='This stage is folded in the kanban view when there are no records in that stage to display.')

    x_manufacturing_state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('planned', 'Planned'),
        ('progress', 'In Progress'),
        ('to_close', 'To Close'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='Manufacturing State', copy=False, tracking=True, required=False,
        help="* Draft: The MO is not confirmed yet.\n"
             "* Confirmed: The MO is confirmed, materials can be reserved.\n"
             "* Planned: The MO is planned, production can start.\n"
             "* In Progress: The production is started.\n"
             "* To Close: The production is done, the MO will be closed.\n"
             "* Done: The MO is closed.\n"
             "* Cancelled: The MO is cancelled."
    )
    # x_reservation_state = fields.Selection(selection=[
    #     ('confirmed', 'Waiting'),
    #     ('assigned', 'Ready'),
    #     ('waiting', 'Waiting Another Operation')],
    #     string='Material Availability', copy=False, tracking=True,
    #     help=" * Ready: The material is available to start the production.\n\
    #            * Waiting: The material is not available to start the production.\n\
    #            The material availability is impacted by the manufacturing readiness\
    #            defined on the BoM.")
    #
    # x_picking_state = fields.Selection(selection=[
    #     ('draft', 'Draft'),
    #     ('confirmed', 'Waiting'),
    #     ('assigned', 'Ready'),
    #     ('done', 'Done'),
    #     ('cancel', 'Cancelled')], string='Pickings State', copy=False, tracking=True,
    #     help="* Draft: The picking is not confirmed yet.\n"
    #          "* Waiting: The picking is waiting for another move to proceed.\n"
    #          "* Ready: The picking is ready to be processed.\n"
    #          "* Done: The picking is done.\n"
    #          "* Cancelled: The picking is cancelled."
    # )
    # x_picking_state_for = fields.Selection(selection=[
    #     ('any', 'Any'),
    #     ('all', 'All')], string='Pickings State For', copy=False, tracking=True,
    #     help="* Any: The picking state is for any one of the picking.\n"
    #          "* All: The picking state is for all pickings of Manufacturing Order."
    # )
    # x_show_check_availability = fields.Boolean(
    #     string='Show Check Availability',
    #     help='Check "Show Check Availability" button in pickings',
    #     required=False
    # )
    #
    # x_workorder_state = fields.Selection(selection=[
    #     ('pending', 'Waiting for another WO'),
    #     ('ready', 'Ready'),
    #     ('progress', 'In Progress'),
    #     ('done', 'Done'),
    #     ('cancel', 'Cancelled')], string='Work Orders State', copy=False, tracking=True,
    #     help="* Waiting for another WO: The work order is waiting for another work order to proceed.\n"
    #          "* Ready: The work order is ready to be processed.\n"
    #          "* In Progress: The work order is in progress.\n"
    #          "* Done: The work order is done.\n"
    #          "* Cancelled: The work order is cancelled."
    # )
    # x_workorder_state_for = fields.Selection(selection=[
    #     ('any', 'Any'),
    #     ('all', 'All')], string='Work Order State For', copy=False, tracking=True,
    #     help="* Any: The picking state is for any one of the work order.\n"
    #          "* All: The picking state is for all work orders of Manufacturing Order."
    # )

