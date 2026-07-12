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
        required=True,
        tracking=True,
        # RULE: Only Available vehicles appear in selection
        # TODO (Person B): Add domain=[('status', '=', 'available')] in the view
    )
    driver_id = fields.Many2one(
        comodel_name='transit.driver',
        string='Driver',
        required=True,
        tracking=True,
        # RULE: Only Available, non-expired drivers appear in selection
        # TODO (Person B): Add domain in the view
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

    # ── ORM Overrides ─────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        """
        TODO (Person B): Auto-assign trip reference from ir.sequence.
        Replace 'New' with the next sequence value (e.g. TRIP/0001).

        Example:
            for vals in vals_list:
                if vals.get('name', 'New') == 'New':
                    vals['name'] = self.env['ir.sequence'].next_by_code('transit.trip')
        """
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('transit.trip') or 'New'
        return super().create(vals_list)

    # ── Constraints ────────────────────────────────────────────────────────────
    @api.constrains('cargo_weight', 'vehicle_id')
    def _check_cargo_weight(self):
        """
        RULE 5: Cargo Weight must not exceed the vehicle's maximum load capacity.
        TODO (Person B): Implement this constraint.
        """
        for trip in self:
            if trip.vehicle_id and trip.cargo_weight > trip.vehicle_id.max_load_capacity:
                raise ValidationError(
                    f'Cargo weight ({trip.cargo_weight} kg) exceeds the vehicle\'s '
                    f'maximum load capacity ({trip.vehicle_id.max_load_capacity} kg)!'
                )

    @api.constrains('vehicle_id', 'state')
    def _check_vehicle_availability(self):
        """
        RULE 3 & 4: Vehicle must be available when assigned.
        TODO (Person B): Enhance this constraint as needed.
        """
        for trip in self:
            if trip.vehicle_id and trip.state == 'draft':
                if trip.vehicle_id.status in ('retired', 'in_shop'):
                    raise ValidationError(
                        f'Vehicle "{trip.vehicle_id.registration_number}" is '
                        f'{trip.vehicle_id.status} and cannot be dispatched!'
                    )

    @api.constrains('driver_id', 'state')
    def _check_driver_availability(self):
        """
        RULE 3: Drivers with expired licenses or Suspended status cannot be assigned.
        TODO (Person B): Implement this constraint.
        """
        for trip in self:
            if trip.driver_id and trip.state == 'draft':
                if trip.driver_id.status == 'suspended':
                    raise ValidationError(
                        f'Driver "{trip.driver_id.name}" is suspended and cannot be assigned!'
                    )
                if trip.driver_id.is_license_expired:
                    raise ValidationError(
                        f'Driver "{trip.driver_id.name}" has an expired license!'
                    )

    # ── State Transition Actions ───────────────────────────────────────────────
    def action_dispatch(self):
        """
        RULE 6: Dispatching a trip → vehicle and driver status → 'on_trip'.
        TODO (Person B): Implement dispatch with full validation.
        """
        for trip in self:
            if trip.state != 'draft':
                raise UserError('Only Draft trips can be dispatched.')
            # Re-check vehicle status at dispatch time
            if trip.vehicle_id.status != 'available':
                raise UserError(
                    f'Vehicle "{trip.vehicle_id.registration_number}" is no longer available!'
                )
            # Re-check driver status at dispatch time
            if trip.driver_id.status != 'available':
                raise UserError(
                    f'Driver "{trip.driver_id.name}" is no longer available!'
                )
            if trip.driver_id.is_license_expired:
                raise UserError(
                    f'Driver "{trip.driver_id.name}" has an expired license!'
                )
            # Apply status transitions
            trip.vehicle_id.status = 'on_trip'
            trip.driver_id.status = 'on_trip'
            trip.state = 'dispatched'
            
            msg = f"Trip Dispatched<br/>Vehicle: {trip.vehicle_id.name}<br/>Driver: {trip.driver_id.name}<br/>Destination: {trip.destination}"
            trip.message_post(body=msg)
            trip.vehicle_id.message_post(body=f"Dispatched on Trip: {trip.name}")
            trip.driver_id.message_post(body=f"Dispatched on Trip: {trip.name}")

    def action_complete(self):
        """
        RULE 7: Completing a trip → vehicle and driver status → 'available'.
        TODO (Person B): Also update vehicle odometer from final_odometer.
        """
        for trip in self:
            if trip.state != 'dispatched':
                raise UserError('Only Dispatched trips can be completed.')
            # Update vehicle odometer
            if trip.final_odometer:
                trip.vehicle_id.odometer = trip.final_odometer
            # Restore statuses
            trip.vehicle_id.status = 'available'
            trip.driver_id.status = 'available'
            trip.state = 'completed'
            
            msg = f"Trip Completed<br/>Distance: {trip.actual_distance} km<br/>Fuel: {trip.fuel_consumed} L"
            trip.message_post(body=msg)
            trip.vehicle_id.message_post(body=f"Completed Trip: {trip.name}. Vehicle is now Available.")
            trip.driver_id.message_post(body=f"Completed Trip: {trip.name}. Driver is now Available.")

    def action_cancel(self):
        """
        RULE 8: Cancelling a dispatched trip restores vehicle and driver to 'available'.
        TODO (Person B): Handle cancellation from both draft and dispatched states.
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
