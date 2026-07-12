from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class TransitDriver(models.Model):
    """
    Driver Management
    =================
    Owner: Person A

    Manages driver profiles, license validity, safety scores,
    and availability status. Status transitions are triggered
    by Trips (Person B).
    """
    _name = 'transit.driver'
    _description = 'Transit Driver'
    _rec_name = 'name'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ── Identity ──────────────────────────────────────────────────────────────
    name = fields.Char(
        string='Full Name',
        required=True,
        tracking=True,
    )
    license_number = fields.Char(
        string='License Number',
        required=True,
    )
    license_category = fields.Selection(
        selection=[
            ('A', 'A — Motorcycle'),
            ('B', 'B — Light Vehicle'),
            ('C', 'C — Heavy Vehicle'),
            ('D', 'D — Passenger Bus'),
            ('E', 'E — Articulated Vehicle'),
        ],
        string='License Category',
        required=True,
        default='B',
    )
    license_expiry = fields.Date(
        string='License Expiry Date',
        required=True,
        tracking=True,
    )
    contact_number = fields.Char(string='Contact Number')

    # ── Safety & Status ────────────────────────────────────────────────────────
    safety_score = fields.Float(
        string='Safety Score',
        default=100.0,
        help='Driver safety score from 0 to 100. Updated by Safety Officer.',
    )
    status = fields.Selection(
        selection=[
            ('available', 'Available'),
            ('on_trip', 'On Trip'),
            ('off_duty', 'Off Duty'),
            ('suspended', 'Suspended'),
        ],
        string='Status',
        default='available',
        required=True,
        tracking=True,
    )

    # ── Computed Fields ────────────────────────────────────────────────────────
    is_license_expired = fields.Boolean(
        string='License Expired',
        compute='_compute_is_license_expired',
        store=True,
        help='True if the license expiry date is in the past.',
    )

    # ── Relations ──────────────────────────────────────────────────────────────
    trip_ids = fields.One2many(
        comodel_name='transit.trip',
        inverse_name='driver_id',
        string='Trips',
    )
    trip_count = fields.Integer(compute='_compute_trip_count', string='Trips')

    # ── Compute Methods ────────────────────────────────────────────────────────
    @api.depends('license_expiry')
    def _compute_is_license_expired(self):
        today = date.today()
        for driver in self:
            if driver.license_expiry:
                driver.is_license_expired = driver.license_expiry < today
            else:
                driver.is_license_expired = False

    @api.depends('trip_ids')
    def _compute_trip_count(self):
        for driver in self:
            driver.trip_count = len(driver.trip_ids)

    # ── Smart Button Action ────────────────────────────────────────────────────
    def action_view_trips(self):
        """TODO (Person A): Return action to open trips filtered by this driver."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Trips',
            'res_model': 'transit.trip',
            'view_mode': 'list,form',
            'domain': [('driver_id', '=', self.id)],
            'context': {'default_driver_id': self.id},
        }

    # ── Scheduled Actions (Cron) ──────────────────────────────────────────────
    @api.model
    def _cron_check_license_expiry(self):
        """
        Runs daily to find drivers whose licenses expire within 5 days.
        """
        warning_date = date.today() + timedelta(days=5)
        drivers_expiring = self.search([
            ('license_expiry', '<=', warning_date),
            ('status', '!=', 'suspended')
        ])
        for driver in drivers_expiring:
            driver.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=f"License Expiring Soon for {driver.name}",
                note=f"License {driver.license_number} expires on {driver.license_expiry}.",
            )
