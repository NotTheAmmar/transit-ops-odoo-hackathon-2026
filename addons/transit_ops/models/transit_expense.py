from odoo import models, fields


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

    vehicle_id = fields.Many2one(
        comodel_name='transit.vehicle',
        string='Vehicle',
        ondelete='cascade',
    )
    trip_id = fields.Many2one(
        comodel_name='transit.trip',
        string='Trip',
        help='Optional: link this expense to a specific trip.',
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
    )
    amount = fields.Float(string='Amount', required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    description = fields.Char(string='Description', required=True)
