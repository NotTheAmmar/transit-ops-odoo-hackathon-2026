/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/**
 * TransitOps OWL Dashboard
 * =======================
 * Owner: Person D
 *
 * This component fetches KPI metrics and operational stats from the
 * backend controller `/transit_ops/dashboard_data` and displays them
 * in a responsive card grid.
 */
export class TransitDashboard extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            kpi: {
                active_vehicles: 0,
                available_vehicles: 0,
                vehicles_in_maintenance: 0,
                active_trips: 0,
                pending_trips: 0,
                drivers_on_duty: 0,
                fleet_utilization: 0.0,
                fuel_efficiency: 0.0,
                total_operational_cost: 0.0
            },
            filters: {
                vehicle_type: 'all',
                region: 'all'
            }
        });

        onWillStart(async () => {
            await this.loadDashboardData();
        });
    }

    async loadDashboardData() {
        try {
            // TODO (Person D): Pass state.filters to the RPC call once filters are implemented in view
            const data = await this.rpc("/transit_ops/dashboard_data", {});
            this.state.kpi = data;
        } catch (error) {
            console.error("Failed to load dashboard data", error);
        }
    }

    async refreshDashboard() {
        await this.loadDashboardData();
    }
}

// Associate template name
TransitDashboard.template = "transit_ops.DashboardTemplate";

// Register action inside tag action registry (crucial for client actions!)
registry.category("actions").add("transit_ops.Dashboard", TransitDashboard);
