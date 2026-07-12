from odoo import models, fields, api
from odoo.exceptions import ValidationError


class TransitVehicle(models.Model):
    """
    Vehicle Registry
    ================
    Owner: Person A

    Stores all fleet vehicles with their operational status,
    capacities, and financial data. Status transitions are triggered
    by Trips (Person B) and Maintenance (Person C).
    """
    _name = 'transit.vehicle'
    _description = 'Transit Vehicle'
    _rec_name = 'registration_number'
    _order = 'registration_number'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ── Identity ──────────────────────────────────────────────────────────────
    registration_number = fields.Char(
        string='Registration Number',
        required=True,
        tracking=True,
        help='Unique vehicle registration plate number.',
    )
    name = fields.Char(
        string='Vehicle Name / Model',
        required=True,
        help='e.g. "Toyota Hiace Van" or "Van-05"',
    )
    vehicle_type = fields.Selection(
        selection=[
            ('truck', 'Truck'),
            ('van', 'Van'),
            ('sedan', 'Sedan'),
            ('bus', 'Bus'),
            ('other', 'Other'),
        ],
        string='Vehicle Type',
        required=True,
        default='van',
    )
    region = fields.Char(
        string='Region',
        help='Operational region for filtering (e.g. North, South, City Centre).',
    )

    # ── Capacity & Odometer ───────────────────────────────────────────────────
    max_load_capacity = fields.Float(
        string='Max Load Capacity (kg)',
        required=True,
        help='Maximum cargo weight this vehicle can carry, in kilograms.',
    )
    odometer = fields.Float(
        string='Odometer (km)',
        help='Current odometer reading in kilometres.',
    )
    acquisition_cost = fields.Float(
        string='Acquisition Cost',
        help='Original purchase/acquisition price of the vehicle.',
    )

    # ── Status ─────────────────────────────────────────────────────────────────
    status = fields.Selection(
        selection=[
            ('available', 'Available'),
            ('on_trip', 'On Trip'),
            ('in_shop', 'In Shop'),
            ('retired', 'Retired'),
        ],
        string='Status',
        default='available',
        required=True,
        tracking=True,
    )

    # ── Relations ──────────────────────────────────────────────────────────────
    trip_ids = fields.One2many(
        comodel_name='transit.trip',
        inverse_name='vehicle_id',
        string='Trips',
    )
    maintenance_ids = fields.One2many(
        comodel_name='transit.maintenance',
        inverse_name='vehicle_id',
        string='Maintenance Logs',
    )
    fuel_log_ids = fields.One2many(
        comodel_name='transit.fuel.log',
        inverse_name='vehicle_id',
        string='Fuel Logs',
    )
    expense_ids = fields.One2many(
        comodel_name='transit.expense',
        inverse_name='vehicle_id',
        string='Expenses',
    )

    # ── Computed Financial Fields ──────────────────────────────────────────────
    total_fuel_cost = fields.Float(
        string='Total Fuel Cost',
        compute='_compute_costs',
        store=True,
    )
    total_maintenance_cost = fields.Float(
        string='Total Maintenance Cost',
        compute='_compute_costs',
        store=True,
    )
    total_operational_cost = fields.Float(
        string='Total Operational Cost',
        compute='_compute_costs',
        store=True,
        help='Sum of all fuel and maintenance costs.',
    )
    vehicle_roi = fields.Float(
        string='Vehicle ROI',
        compute='_compute_costs',
        store=True,
        help='(Revenue - (Maintenance + Fuel)) / Acquisition Cost',
    )

    # ── Smart Button Counts ───────────────────────────────────────────────────
    trip_count = fields.Integer(compute='_compute_counts', string='Trips')
    maintenance_count = fields.Integer(compute='_compute_counts', string='Maintenance')

    # ── Constraints ────────────────────────────────────────────────────────────
    _sql_constraints = [
        (
            'registration_unique',
            'UNIQUE(registration_number)',
            'A vehicle with this registration number already exists!',
        ),
    ]

    # ── Compute Methods ────────────────────────────────────────────────────────
    @api.depends('fuel_log_ids.cost', 'maintenance_ids.cost', 'acquisition_cost')
    def _compute_costs(self):
        """
        TODO (Person A): Implement cost aggregation.

        For each vehicle:
          - total_fuel_cost       = sum of fuel_log_ids.cost
          - total_maintenance_cost= sum of maintenance_ids.cost
          - total_operational_cost= total_fuel_cost + total_maintenance_cost
          - vehicle_roi           = (revenue - total_operational_cost) / acquisition_cost
            (revenue field not in spec — leave as 0 or add a revenue field)
        """
        for vehicle in self:
            vehicle.total_fuel_cost = sum(vehicle.fuel_log_ids.mapped('cost'))
            vehicle.total_maintenance_cost = sum(vehicle.maintenance_ids.mapped('cost'))
            vehicle.total_operational_cost = (
                vehicle.total_fuel_cost + vehicle.total_maintenance_cost
            )
            if vehicle.acquisition_cost:
                vehicle.vehicle_roi = (
                    -vehicle.total_operational_cost / vehicle.acquisition_cost
                )
            else:
                vehicle.vehicle_roi = 0.0

    @api.depends('trip_ids', 'maintenance_ids')
    def _compute_counts(self):
        for vehicle in self:
            vehicle.trip_count = len(vehicle.trip_ids)
            vehicle.maintenance_count = len(vehicle.maintenance_ids)

    # ── Smart Button Actions ───────────────────────────────────────────────────
    def action_view_trips(self):
        """TODO (Person A): Return action to open trips filtered by this vehicle."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Trips',
            'res_model': 'transit.trip',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    def action_view_maintenance(self):
        """TODO (Person A): Return action to open maintenance filtered by this vehicle."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Maintenance Logs',
            'res_model': 'transit.maintenance',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }
