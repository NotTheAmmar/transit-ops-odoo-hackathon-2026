from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta


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
        tracking=True,
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
    total_other_expenses = fields.Float(
        string='Total Other Expenses',
        compute='_compute_costs',
        store=True,
    )
    total_operational_cost = fields.Float(
        string='Total Operational Cost',
        compute='_compute_costs',
        store=True,
        help='Sum of all fuel, maintenance, and other expenses.',
    )
    vehicle_roi = fields.Float(
        string='Vehicle ROI',
        compute='_compute_costs',
        store=True,
        help='(Revenue - Operational Cost) / Acquisition Cost',
    )

    # ── Smart Button Counts ───────────────────────────────────────────────────
    trip_count = fields.Integer(compute='_compute_counts', string='Trips')
    maintenance_count = fields.Integer(compute='_compute_counts', string='Maintenance')
    fuel_log_count = fields.Integer(compute='_compute_counts', string='Fuel Logs')
    expense_count = fields.Integer(compute='_compute_counts', string='Expenses')

    # ── Enterprise Analytics & Intelligence ────────────────────────────────────
    average_fuel_efficiency = fields.Float(
        string='Avg Fuel Efficiency (km/L)',
        compute='_compute_enterprise_metrics',
        store=True,
    )
    health_score = fields.Float(
        string='Health Score (%)',
        compute='_compute_enterprise_metrics',
        store=True,
    )
    health_badge = fields.Selection(
        selection=[
            ('healthy', '🟢 Healthy'),
            ('warning', '🟡 Service Due'),
            ('critical', '🔴 Critical'),
        ],
        string='Health Status',
        compute='_compute_enterprise_metrics',
        store=True,
    )
    fleet_recommendation = fields.Char(
        string='Operational Insight',
        compute='_compute_enterprise_metrics',
        store=True,
    )

    # ── Predictive Maintenance ────────────────────────────────────────────────
    last_maintenance_date = fields.Date(
        string='Last Maintenance',
        compute='_compute_maintenance_schedule',
        store=True,
    )
    last_maintenance_odometer = fields.Float(
        string='Last Maintenance Odometer',
        compute='_compute_maintenance_schedule',
        store=True,
    )
    next_recommended_maintenance = fields.Date(
        string='Next Maintenance Due',
        compute='_compute_maintenance_schedule',
        store=True,
    )
    service_interval_km = fields.Float(
        string='Service Interval (km)',
        default=10000.0,
    )
    maintenance_due = fields.Boolean(
        string='Maintenance Due',
        compute='_compute_maintenance_due',
        store=True,
    )

    # ── Constraints ────────────────────────────────────────────────────────────
    _sql_constraints = [
        (
            'registration_unique',
            'UNIQUE(registration_number)',
            'A vehicle with this registration number already exists!',
        ),
    ]

    # ── Compute Methods ────────────────────────────────────────────────────────
    @api.depends('fuel_log_ids.cost', 'maintenance_ids.cost', 'expense_ids.amount', 'acquisition_cost')
    def _compute_costs(self):
        for vehicle in self:
            vehicle.total_fuel_cost = sum(vehicle.fuel_log_ids.mapped('cost'))
            vehicle.total_maintenance_cost = sum(vehicle.maintenance_ids.mapped('cost'))
            vehicle.total_other_expenses = sum(vehicle.expense_ids.mapped('amount'))
            vehicle.total_operational_cost = (
                vehicle.total_fuel_cost + vehicle.total_maintenance_cost + vehicle.total_other_expenses
            )
            if vehicle.acquisition_cost:
                vehicle.vehicle_roi = (
                    -vehicle.total_operational_cost / vehicle.acquisition_cost
                )
            else:
                vehicle.vehicle_roi = 0.0

    @api.depends('trip_ids', 'maintenance_ids', 'fuel_log_ids', 'expense_ids')
    def _compute_counts(self):
        for vehicle in self:
            vehicle.trip_count = len(vehicle.trip_ids)
            vehicle.maintenance_count = len(vehicle.maintenance_ids)
            vehicle.fuel_log_count = len(vehicle.fuel_log_ids)
            vehicle.expense_count = len(vehicle.expense_ids)

    @api.depends('maintenance_ids.date_end', 'maintenance_ids.state')
    def _compute_maintenance_schedule(self):
        for vehicle in self:
            done_maintenance = vehicle.maintenance_ids.filtered(lambda m: m.state == 'done' and m.date_end)
            if done_maintenance:
                last_m = done_maintenance.sorted(key=lambda m: m.date_end, reverse=True)[0]
                vehicle.last_maintenance_date = last_m.date_end
                # Odometer roughly mapped from when maintenance happened. Since maintenance doesn't track odometer currently, 
                # we'll approximate with current vehicle odometer or trip records.
                vehicle.last_maintenance_odometer = vehicle.odometer
                vehicle.next_recommended_maintenance = last_m.date_end + timedelta(days=180)
            else:
                vehicle.last_maintenance_date = False
                vehicle.last_maintenance_odometer = 0.0
                vehicle.next_recommended_maintenance = fields.Date.today() + timedelta(days=180)

    @api.depends('odometer', 'last_maintenance_odometer', 'service_interval_km')
    def _compute_maintenance_due(self):
        for vehicle in self:
            if vehicle.odometer - vehicle.last_maintenance_odometer >= vehicle.service_interval_km:
                vehicle.maintenance_due = True
            else:
                vehicle.maintenance_due = False

    @api.depends('trip_ids.actual_distance', 'trip_ids.fuel_consumed', 'maintenance_count', 'status')
    def _compute_enterprise_metrics(self):
        for vehicle in self:
            # 1. Fuel Efficiency
            total_dist = sum(vehicle.trip_ids.mapped('actual_distance'))
            total_fuel = sum(vehicle.trip_ids.mapped('fuel_consumed'))
            eff = total_dist / total_fuel if total_fuel > 0 else 0.0
            vehicle.average_fuel_efficiency = eff

            # 2. Health Score (Weighted Formula)
            # Maintenance Penalty: 5 points per maintenance record
            maint_penalty = vehicle.maintenance_count * 5.0
            
            # Downtime Penalty: 4 points if currently in shop, plus 1 point per maintenance log (as proxy for downtime)
            downtime_penalty = 15.0 if vehicle.status == 'in_shop' else (vehicle.maintenance_count * 2.0)
            
            # Fuel Penalty: if efficiency is less than 8 km/L
            fuel_penalty = 12.0 if (eff > 0 and eff < 8.0) else 0.0

            score = 100.0 - maint_penalty - downtime_penalty - fuel_penalty
            vehicle.health_score = max(0.0, min(100.0, score))

            # 3. Health Badge
            if vehicle.health_score >= 80:
                vehicle.health_badge = 'healthy'
            elif vehicle.health_score >= 50:
                vehicle.health_badge = 'warning'
            else:
                vehicle.health_badge = 'critical'

            # 4. Fleet Recommendation
            if vehicle.health_badge == 'critical':
                vehicle.fleet_recommendation = f"Immediate action required. Health score critical ({vehicle.health_score}%)."
            elif vehicle.maintenance_due:
                vehicle.fleet_recommendation = f"Service interval exceeded. Schedule maintenance."
            elif fuel_penalty > 0:
                vehicle.fleet_recommendation = f"Fuel efficiency ({eff:.1f} km/L) below fleet standards. Inspect engine."
            else:
                vehicle.fleet_recommendation = "Vehicle is performing optimally."

    # ── Smart Button Actions ───────────────────────────────────────────────────
    def action_view_trips(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Trips',
            'res_model': 'transit.trip',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    def action_view_maintenance(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Maintenance Logs',
            'res_model': 'transit.maintenance',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    def action_view_fuel_logs(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Fuel Logs',
            'res_model': 'transit.fuel.log',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    def action_view_expenses(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Expenses',
            'res_model': 'transit.expense',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    # ── Scheduled Actions (Cron) ──────────────────────────────────────────────
    @api.model
    def _cron_check_maintenance_due(self):
        """
        Runs daily to find vehicles due for maintenance and creates an Odoo activity.
        """
        vehicles_due = self.search([('maintenance_due', '=', True)])
        for vehicle in vehicles_due:
            # Create a mail.activity for the fleet manager
            vehicle.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=f"Maintenance Due for {vehicle.registration_number}",
                note=f"Vehicle odometer ({vehicle.odometer} km) exceeds service interval.",
            )
