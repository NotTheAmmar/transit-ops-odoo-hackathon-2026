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

        Driver = request.env["transit.driver"]
        Vehicle = request.env["transit.vehicle"]

        drivers_on_duty = Driver.search_count([("status", "=", "on_trip")])

        # Average fuel efficiency across all completed trips (distance/fuel)
        completed_trips = Trip.search([("state", "=", "completed"), ("fuel_consumed", ">", 0)])
        total_dist = sum(completed_trips.mapped("actual_distance"))
        total_fuel = sum(completed_trips.mapped("fuel_consumed"))
        fuel_efficiency = round(total_dist / total_fuel, 2) if total_fuel > 0 else 0.0

        # Total operational cost across entire fleet
        all_vehicles = Vehicle.search([])
        total_operational_cost = sum(all_vehicles.mapped("total_operational_cost"))

        return {
            "active_vehicles": active_vehicles,
            "available_vehicles": available_vehicles,
            "vehicles_in_maintenance": vehicles_in_maintenance,
            "active_trips": active_trips,
            "pending_trips": pending_trips,
            "drivers_on_duty": drivers_on_duty,
            "fleet_utilization": round(fleet_utilization, 1),
            "fuel_efficiency": fuel_efficiency,
            "total_operational_cost": round(total_operational_cost, 2),
        }