from odoo import http
from odoo.http import request


class TransitDashboardController(http.Controller):
    """
    Dashboard Controller
    ====================
    Owner: Person D

    Exposes JSON-RPC endpoints that calculate and return KPI data
    to the OWL dashboard client side.
    """

    @http.route('/transit_ops/dashboard_data', type='json', auth='user')
    def get_dashboard_data(self, **kwargs):
        """
        TODO (Person D): Implement KPI calculations using Odoo ORM.
        Expected keys in response:
          - active_vehicles
          - available_vehicles
          - vehicles_in_maintenance
          - active_trips
          - pending_trips
          - drivers_on_duty
          - fleet_utilization
        """
        # Placeholder values so dashboard loads without crashing
        return {
            'active_vehicles': 0,
            'available_vehicles': 0,
            'vehicles_in_maintenance': 0,
            'active_trips': 0,
            'pending_trips': 0,
            'drivers_on_duty': 0,
            'fleet_utilization': 0.0,
            'fuel_efficiency': 0.0,
            'total_operational_cost': 0.0,
        }
