from odoo import models, fields, api
from odoo.exceptions import UserError


class TransitMaintenance(models.Model):
    """
    Maintenance Log
    ===============
    Owner: Person C

    Tracks vehicle maintenance records. Opening a maintenance record
    automatically sets the vehicle status to 'In Shop', hiding it from
    dispatch. Closing restores the vehicle to 'Available'.

    RULES 9 & 10 are implemented here.
    """
    _name = 'transit.maintenance'
    _description = 'Maintenance Log'
    _rec_name = 'name'
    _order = 'date_start desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Maintenance Description',
        required=True,
        help='e.g. "Oil Change", "Brake Inspection"',
    )
    vehicle_id = fields.Many2one(
        comodel_name='transit.vehicle',
        string='Vehicle',
        required=True,
        tracking=True,
    )
    maintenance_type = fields.Selection(
        selection=[
            ('preventive', 'Preventive'),
            ('corrective', 'Corrective'),
            ('emergency', 'Emergency'),
        ],
        string='Maintenance Type',
        required=True,
        default='preventive',
    )
    description = fields.Text(string='Details')
    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Date')
    cost = fields.Float(string='Cost')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('open', 'Open / In Progress'),
            ('done', 'Done'),
        ],
        string='State',
        default='draft',
        required=True,
        tracking=True,
    )

    # ── State Transitions ─────────────────────────────────────────────────────
    def action_open(self):
        """
        RULE 9: Creating/opening a maintenance record → vehicle status → 'in_shop'.
        TODO (Person C): Implement and also handle edge cases
        (e.g. vehicle already in_shop from another maintenance record).
        """
        for record in self:
            if record.state != 'draft':
                raise UserError('Only Draft maintenance records can be opened.')
            if record.vehicle_id.status == 'retired':
                raise UserError('Cannot perform maintenance on a retired vehicle.')
            record.vehicle_id.status = 'in_shop'
            record.state = 'open'
            
            record.message_post(body=f"Maintenance Started: {record.name}")
            record.vehicle_id.message_post(body=f"Vehicle moved to In Shop for Maintenance: {record.name}")

    def action_close(self):
        """
        RULE 10: Closing maintenance → vehicle status → 'available'
        (unless the vehicle is retired).
        TODO (Person C): Implement this.
        """
        for record in self:
            if record.state != 'open':
                raise UserError('Only Open maintenance records can be closed.')
            # Only restore to available if not retired and no other open maintenance logs
            if record.vehicle_id.status != 'retired':
                open_logs_count = self.search_count([
                    ('vehicle_id', '=', record.vehicle_id.id),
                    ('state', '=', 'open'),
                    ('id', '!=', record.id)
                ])
                if open_logs_count == 0:
                    record.vehicle_id.status = 'available'
                    record.vehicle_id.message_post(body=f"Maintenance Completed: {record.name}. Vehicle is now Available.")
                else:
                    record.vehicle_id.message_post(body=f"Maintenance Completed: {record.name}. Vehicle remains In Shop due to other open records.")
            record.date_end = fields.Date.today()
            record.state = 'done'
            record.message_post(body=f"Maintenance Completed: {record.name}")
