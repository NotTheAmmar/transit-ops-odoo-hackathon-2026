from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class TransitTrip(models.Model):
    """
    Trip Management
    ===============
    Owner: Person B

    Manages the full trip lifecycle: Draft → Dispatched → Completed / Cancelled.
    Enforces all 10 mandatory business rules from the problem statement.

    This is the most complex model — it orchestrates status changes across
    vehicles (transit.vehicle) and drivers (transit.driver).
    """
    _name = 'transit.trip'
    _description = 'Transit Trip'
    _rec_name = 'name'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ── Identity ──────────────────────────────────────────────────────────────
    name = fields.Char(
        string='Trip Reference',
        readonly=True,
        default='New',
        copy=False,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('dispatched', 'Dispatched'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        copy=False,
    )

    # ── Route ─────────────────────────────────────────────────────────────────
    source = fields.Char(string='Source / Origin', required=True)
    destination = fields.Char(string='Destination', required=True)
    planned_distance = fields.Float(string='Planned Distance (km)', required=True)
    actual_distance = fields.Float(
        string='Actual Distance (km)',
        help='Filled in when completing the trip.',
    )

    # ── Cargo ─────────────────────────────────────────────────────────────────
    cargo_weight = fields.Float(
        string='Cargo Weight (kg)',
        required=True,
        help='Must not exceed the selected vehicle\'s maximum load capacity.',
    )

    # ── Assignments ───────────────────────────────────────────────────────────
    vehicle_id = fields.Many2one(
        comodel_name='transit.vehicle',
        string='Vehicle',
        tracking=True,
    )
    driver_id = fields.Many2one(
        comodel_name='transit.driver',
        string='Driver',
        tracking=True,
    )

    # ── Dates ─────────────────────────────────────────────────────────────────
    date_planned = fields.Datetime(
        string='Planned Date',
        default=fields.Datetime.now,
        required=True,
        tracking=True,
        help='Scheduled departure date and time.',
    )
    date_dispatched = fields.Datetime(
        string='Dispatched At',
        readonly=True,
        tracking=True,
        help='Timestamp when the trip was dispatched.',
    )
    date_completed = fields.Datetime(
        string='Completed At',
        readonly=True,
        tracking=True,
        help='Timestamp when the trip was completed.',
    )

    # ── Completion Fields ─────────────────────────────────────────────────────
    final_odometer = fields.Float(
        string='Final Odometer (km)',
        help='Odometer reading at trip completion. Updates the vehicle odometer.',
    )
    fuel_consumed = fields.Float(
        string='Fuel Consumed (L)',
        help='Total fuel used during the trip.',
    )
    fuel_efficiency = fields.Float(
        string='Fuel Efficiency (km/L)',
        compute='_compute_fuel_efficiency',
        store=True,
    )

    # ── Financial ─────────────────────────────────────────────────────────────
    trip_revenue = fields.Float(
        string='Trip Revenue',
        help='Revenue earned for this trip.',
    )
    trip_cost = fields.Float(
        string='Total Trip Cost',
        compute='_compute_trip_cost',
        store=True,
        help='Sum of fuel costs + expenses linked to this trip.',
    )

    # ── Relations ──────────────────────────────────────────────────────────────
    fuel_log_ids = fields.One2many(
        comodel_name='transit.fuel.log',
        inverse_name='trip_id',
        string='Fuel Logs',
    )
    expense_ids = fields.One2many(
        comodel_name='transit.expense',
        inverse_name='trip_id',
        string='Expenses',
    )

    # ── Compute Methods ────────────────────────────────────────────────────────
    @api.depends('actual_distance', 'fuel_consumed')
    def _compute_fuel_efficiency(self):
        for trip in self:
            if trip.fuel_consumed:
                trip.fuel_efficiency = trip.actual_distance / trip.fuel_consumed
            else:
                trip.fuel_efficiency = 0.0

    @api.depends('fuel_log_ids.cost', 'expense_ids.amount')
    def _compute_trip_cost(self):
        for trip in self:
            fuel_total = sum(trip.fuel_log_ids.mapped('cost'))
            expense_total = sum(trip.expense_ids.mapped('amount'))
            trip.trip_cost = fuel_total + expense_total

    # ── ORM Overrides ─────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-assign trip reference from ir.sequence (e.g. TRIP/0001)."""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('transit.trip') or 'New'
        return super().create(vals_list)

    # ── Constraints ────────────────────────────────────────────────────────────
    @api.constrains('cargo_weight', 'vehicle_id')
    def _check_cargo_weight(self):
        """
        RULE 5: Cargo Weight must not exceed the vehicle's maximum load capacity.
        """
        for trip in self:
            if (
                trip.vehicle_id
                and trip.cargo_weight > 0
                and trip.cargo_weight > trip.vehicle_id.max_load_capacity
            ):
                raise ValidationError(
                    f'Cargo weight ({trip.cargo_weight:.1f} kg) exceeds the vehicle\'s '
                    f'maximum load capacity ({trip.vehicle_id.max_load_capacity:.1f} kg)!'
                )

    @api.constrains('vehicle_id', 'state')
    def _check_vehicle_availability(self):
        """
        RULE 3: Vehicle must be available when saved to draft.
        Retired or In Shop vehicles cannot be assigned.
        """
        for trip in self:
            if trip.vehicle_id and trip.state == 'draft':
                if trip.vehicle_id.status in ('retired', 'in_shop'):
                    raise ValidationError(
                        f'Vehicle "{trip.vehicle_id.registration_number}" is '
                        f'{trip.vehicle_id.status.replace("_", " ")} and cannot be assigned!'
                    )

    @api.constrains('driver_id', 'state')
    def _check_driver_availability(self):
        """
        RULE 4: Drivers with expired licenses or Suspended status cannot be assigned.
        """
        for trip in self:
            if trip.driver_id and trip.state == 'draft':
                if trip.driver_id.status == 'suspended':
                    raise ValidationError(
                        f'Driver "{trip.driver_id.name}" is suspended and cannot be assigned!'
                    )
                if trip.driver_id.is_license_expired:
                    raise ValidationError(
                        f'Driver "{trip.driver_id.name}" has an expired license '
                        f'(expired on {trip.driver_id.license_expiry})!'
                    )

    @api.constrains('vehicle_id', 'state')
    def _check_vehicle_not_double_booked(self):
        """
        RULE 3 (safety net): Prevent assigning a vehicle that already has an
        active dispatched trip. Catches concurrent or API-level assignments
        that bypass the view domain filter.
        """
        for trip in self:
            if trip.state in ('draft', 'dispatched') and trip.vehicle_id:
                conflicting = self.search([
                    ('vehicle_id', '=', trip.vehicle_id.id),
                    ('state', '=', 'dispatched'),
                    ('id', '!=', trip.id),
                ], limit=1)
                if conflicting:
                    raise ValidationError(
                        f'Vehicle "{trip.vehicle_id.registration_number}" is already '
                        f'assigned to active trip "{conflicting.name}"!'
                    )

    @api.constrains('driver_id', 'state')
    def _check_driver_not_double_booked(self):
        """
        RULE 4 (safety net): Prevent assigning a driver who already has an
        active dispatched trip.
        """
        for trip in self:
            if trip.state in ('draft', 'dispatched') and trip.driver_id:
                conflicting = self.search([
                    ('driver_id', '=', trip.driver_id.id),
                    ('state', '=', 'dispatched'),
                    ('id', '!=', trip.id),
                ], limit=1)
                if conflicting:
                    raise ValidationError(
                        f'Driver "{trip.driver_id.name}" is already '
                        f'on active trip "{conflicting.name}"!'
                    )

    # ── State Transition Actions ───────────────────────────────────────────────
    def action_dispatch(self):
        """
        RULE 6: Dispatching a trip → vehicle and driver status → 'on_trip'.

        Validates that both vehicle and driver are still available at dispatch
        time (a second-layer check beyond the domain filter).
        """
        for trip in self:
            if trip.state != 'draft':
                raise UserError('Only Draft trips can be dispatched.')

            if not trip.vehicle_id:
                raise UserError('Please assign a vehicle before dispatching the trip.')
            if not trip.driver_id:
                raise UserError('Please assign a driver before dispatching the trip.')

            # Re-check vehicle status at dispatch time
            if trip.vehicle_id.status != 'available':
                raise UserError(
                    f'Vehicle "{trip.vehicle_id.registration_number}" is no longer '
                    f'available (current status: {trip.vehicle_id.status.replace("_", " ")})!'
                )

            # Re-check driver status at dispatch time
            if trip.driver_id.status != 'available':
                raise UserError(
                    f'Driver "{trip.driver_id.name}" is no longer '
                    f'available (current status: {trip.driver_id.status.replace("_", " ")})!'
                )
            if trip.driver_id.is_license_expired:
                raise UserError(
                    f'Driver "{trip.driver_id.name}" has an expired license '
                    f'and cannot be dispatched!'
                )

            # Apply status transitions
            trip.vehicle_id.status = 'on_trip'
            trip.driver_id.status = 'on_trip'
            trip.date_dispatched = fields.Datetime.now()
            trip.state = 'dispatched'
            
            msg = f"Trip Dispatched<br/>Vehicle: {trip.vehicle_id.name}<br/>Driver: {trip.driver_id.name}<br/>Destination: {trip.destination}"
            trip.message_post(body=msg)
            trip.vehicle_id.message_post(body=f"Dispatched on Trip: {trip.name}")
            trip.driver_id.message_post(body=f"Dispatched on Trip: {trip.name}")

    def action_complete(self):
        """
        RULE 7: Completing a trip → vehicle and driver status → 'available'.

        Also updates vehicle odometer from final_odometer and records
        the completion timestamp. Requires actual completion data.
        """
        for trip in self:
            if trip.state != 'dispatched':
                raise UserError('Only Dispatched trips can be completed.')

            # Require completion data before marking complete
            if not trip.actual_distance:
                raise UserError(
                    'Please enter the Actual Distance (km) before completing the trip.'
                )
            if not trip.fuel_consumed:
                raise UserError(
                    'Please enter the Fuel Consumed (L) before completing the trip.'
                )
            if not trip.final_odometer:
                raise UserError(
                    'Please enter the Final Odometer reading before completing the trip.'
                )

            # Validate final odometer is not less than current odometer
            if trip.final_odometer < trip.vehicle_id.odometer:
                raise UserError(
                    f'Final odometer ({trip.final_odometer:.1f} km) cannot be less than '
                    f'the vehicle\'s current odometer ({trip.vehicle_id.odometer:.1f} km)!'
                )

            # Update vehicle odometer
            trip.vehicle_id.odometer = trip.final_odometer

            # Restore statuses
            trip.vehicle_id.status = 'available'
            trip.driver_id.status = 'available'

            # Record completion timestamp
            trip.date_completed = fields.Datetime.now()
            trip.state = 'completed'
            
            msg = f"Trip Completed<br/>Distance: {trip.actual_distance} km<br/>Fuel: {trip.fuel_consumed} L"
            trip.message_post(body=msg)
            trip.vehicle_id.message_post(body=f"Completed Trip: {trip.name}. Vehicle is now Available.")
            trip.driver_id.message_post(body=f"Completed Trip: {trip.name}. Driver is now Available.")

    def action_cancel(self):
        """
        RULE 8: Cancelling a trip restores vehicle and driver to 'available'
        if the trip was dispatched. Draft trips can also be cancelled.
        """
        for trip in self:
            if trip.state not in ('draft', 'dispatched'):
                raise UserError('Only Draft or Dispatched trips can be cancelled.')
            if trip.state == 'dispatched':
                # Restore statuses only if we were dispatched
                trip.vehicle_id.status = 'available'
                trip.driver_id.status = 'available'
                trip.vehicle_id.message_post(body=f"Trip Cancelled: {trip.name}. Vehicle is now Available.")
                trip.driver_id.message_post(body=f"Trip Cancelled: {trip.name}. Driver is now Available.")
            trip.state = 'cancelled'
            trip.message_post(body="Trip Cancelled")

    def action_reset_draft(self):
        """
        Reset a cancelled trip back to Draft so it can be re-dispatched
        after correcting any issues.
        """
        for trip in self:
            if trip.state != 'cancelled':
                raise UserError('Only Cancelled trips can be reset to Draft.')
            trip.state = 'draft'
