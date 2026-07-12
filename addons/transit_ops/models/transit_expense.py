from odoo import models, fields, api


class TransitExpense(models.Model):
    """
    Expense Log
    ===========
    Owner: Person C

    Records miscellaneous operational expenses (tolls, etc.).
    Cost data contributes to total operational cost reporting.
    """
    _name = 'transit.expense'
    _description = 'Transit Expense'
    _rec_name = 'description'
    _order = 'date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vehicle_id = fields.Many2one(
        comodel_name='transit.vehicle',
        string='Vehicle',
        ondelete='cascade',
        tracking=True,
    )
    trip_id = fields.Many2one(
        comodel_name='transit.trip',
        string='Trip',
        help='Optional: link this expense to a specific trip.',
        tracking=True,
    )
    expense_type = fields.Selection(
        selection=[
            ('toll', 'Toll'),
            ('maintenance', 'Maintenance'),
            ('other', 'Other'),
        ],
        string='Expense Type',
        required=True,
        default='toll',
        tracking=True,
    )
    amount = fields.Float(string='Amount', required=True, tracking=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today, tracking=True)
    description = fields.Char(string='Description', required=True, tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            msg = f"Expense Log Created<br/>Vehicle: {record.vehicle_id.name or 'N/A'}<br/>Type: {record.expense_type}<br/>Amount: {record.amount}"
            record.message_post(body=msg)
            if record.vehicle_id:
                record.vehicle_id.message_post(body=f"Expense Logged: {record.description} ({record.amount})")
        return records
