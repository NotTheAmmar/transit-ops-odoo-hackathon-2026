from odoo import models, fields


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

    vehicle_id = fields.Many2one(
        comodel_name='transit.vehicle',
        string='Vehicle',
        required=True,
        ondelete='cascade',
    )
    trip_id = fields.Many2one(
        comodel_name='transit.trip',
        string='Trip',
        help='Optional: link this fuel log to a specific trip.',
    )
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    liters = fields.Float(string='Fuel (Litres)', required=True)
    cost = fields.Float(string='Cost', required=True)
    odometer_reading = fields.Float(
        string='Odometer at Fill-up (km)',
        help='Odometer reading when fuel was added.',
    )
    notes = fields.Char(string='Notes')
