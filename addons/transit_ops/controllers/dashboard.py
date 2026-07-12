from odoo import http
from odoo.http import request


class TransitDashboardController(http.Controller):

    @http.route('/transit_ops/dashboard_data', type='json', auth='user')
    def get_dashboard_data(self, **kwargs):

        vehicle_type = kwargs.get("vehicle_type", "all")
        region = kwargs.get("region", "all")

        vehicle_domain = []

        if vehicle_type != "all":
            vehicle_domain.append(
                ("vehicle_type", "=", vehicle_type)
            )

        if region != "all":
            vehicle_domain.append(
                ("region", "ilike", region)
            )

        Vehicle = request.env["transit.vehicle"]
        Trip = request.env["transit.trip"]

        active_vehicle_records = Vehicle.search(
            vehicle_domain + [
                ("status", "=", "on_trip")
            ]
        )

        active_vehicles = len(active_vehicle_records)

        available_vehicles = Vehicle.search_count(
            vehicle_domain + [
                ("status", "=", "available")
            ]
        )

        vehicles_in_maintenance = Vehicle.search_count(
            vehicle_domain + [
                ("status", "=", "in_shop")
            ]
        )

        active_trips = Trip.search_count([
            ("vehicle_id", "in", active_vehicle_records.ids)
        ])

        pending_trips = Trip.search_count([
            ("state", "=", "dispatched")
        ])

        total_vehicles = (
            active_vehicles +
            available_vehicles +
            vehicles_in_maintenance
        )

        fleet_utilization = (
            active_vehicles / total_vehicles * 100
            if total_vehicles else 0
        )

        return {
            "active_vehicles": active_vehicles,
            "available_vehicles": available_vehicles,
            "vehicles_in_maintenance": vehicles_in_maintenance,
            "active_trips": active_trips,
            "pending_trips": pending_trips,
            "drivers_on_duty": 0,
            "fleet_utilization": fleet_utilization,
            "fuel_efficiency": 0.0,
            "total_operational_cost": 0.0,
        }