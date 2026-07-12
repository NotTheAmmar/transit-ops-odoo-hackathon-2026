from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.home import Home


class TransitOpsHome(Home):
    """Override the default /odoo and /web landing to redirect straight
    to the TransitOps Dashboard client action."""

    @http.route(['/web', '/odoo', '/odoo/<path:subpath>'], type='http', auth='user', sitemap=False)
    def web_client(self, s_action=None, **kw):
        # If the user already clicked a specific action link, honour it
        if s_action:
            return super().web_client(s_action=s_action, **kw)

        # If navigating to a specific sub-path (like /odoo/settings), let it through
        if kw.get('subpath'):
            return super().web_client(s_action=s_action, **kw)

        # Otherwise, look up our dashboard action and redirect to it
        action = request.env.ref(
            'transit_ops.action_transit_dashboard', raise_if_not_found=False
        )
        if action:
            return super().web_client(s_action=str(action.id), **kw)

        return super().web_client(s_action=s_action, **kw)
