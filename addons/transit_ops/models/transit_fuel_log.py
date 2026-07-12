from odoo import models, fields, api


class TransitFuelLog(models.Model):
    """
    Fuel Log
    =========
    Owner: Person C

    Records fuel fill-ups per vehicle, optionally linked to a trip.
    Cost data feeds into Vehicle.total_fuel_cost computed field (Person A).
    """
    _name = 'transit.fuel.log'
    _description = 'Fuel Log'
    _rec_name = 'vehicle_id'
    _order = 'date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vehicle_id = fields.Many2one(
        comodel_name='transit.vehicle',
        string='Vehicle',
        required=True,
        ondelete='cascade',
        tracking=True,
    )
    trip_id = fields.Many2one(
        comodel_name='transit.trip',
        string='Trip',
        help='Optional: link this fuel log to a specific trip.',
        tracking=True,
    )
    date = fields.Date(string='Date', required=True, default=fields.Date.today, tracking=True)
    liters = fields.Float(string='Fuel (Litres)', required=True, tracking=True)
    cost = fields.Float(string='Cost', required=True, tracking=True)
    odometer_reading = fields.Float(
        string='Odometer at Fill-up (km)',
        help='Odometer reading when fuel was added.',
        tracking=True,
    )
    notes = fields.Char(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            msg = f"Fuel Log Created<br/>Vehicle: {record.vehicle_id.name or 'N/A'}<br/>Fuel: {record.liters} L<br/>Cost: {record.cost}"
            record.message_post(body=msg)
            if record.vehicle_id:
                record.vehicle_id.message_post(body=f"Fuel Logged: {record.liters} L ({record.cost})")
        return records
