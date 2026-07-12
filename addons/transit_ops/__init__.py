from . import models
from . import controllers
from . import wizard


def _post_init_set_home_action(env):
    """Set TransitOps Dashboard as default home action after install."""
    action = env.ref('transit_ops.action_transit_dashboard', raise_if_not_found=False)
    if action:
        # Set for admin user
        admin = env.ref('base.user_admin', raise_if_not_found=False)
        if admin:
            admin.write({'action_id': action.id})
        # Set for default user template (new users inherit this)
        default_user = env.ref('base.default_user', raise_if_not_found=False)
        if default_user:
            default_user.write({'action_id': action.id})
