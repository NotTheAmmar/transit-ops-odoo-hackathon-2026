import xmlrpc.client

url = 'http://localhost:8069'
db = 'transit_ops'

users = {
    'driver': 'driver',
    'safety': 'safety',
    'analyst': 'analyst',
    'admin': 'admin'
}

models_to_test = [
    'transit.vehicle',
    'transit.driver',
    'transit.trip',
    'transit.maintenance',
    'transit.fuel.log',
    'transit.expense'
]

print(f"{'USER':<10} | {'MODEL':<20} | {'READ':<6} | {'CREATE':<6} | {'UPDATE':<6} | {'DELETE':<6}")
print("-" * 65)

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

for username, password in users.items():
    try:
        uid = common.authenticate(db, username, password, {})
        if not uid:
            print(f"Failed to auth {username}")
            continue
            
        for model in models_to_test:
            # Test Read (check access rights using check_access_rights)
            can_read = models.execute_kw(db, uid, password, model, 'check_access_rights', ['read'], {'raise_exception': False})
            can_create = models.execute_kw(db, uid, password, model, 'check_access_rights', ['create'], {'raise_exception': False})
            can_write = models.execute_kw(db, uid, password, model, 'check_access_rights', ['write'], {'raise_exception': False})
            can_unlink = models.execute_kw(db, uid, password, model, 'check_access_rights', ['unlink'], {'raise_exception': False})
            
            # Format results
            r = "✅" if can_read else "❌"
            c = "✅" if can_create else "❌"
            w = "✅" if can_write else "❌"
            d = "✅" if can_unlink else "❌"
            
            print(f"{username:<10} | {model:<20} | {r:<6} | {c:<6} | {w:<6} | {d:<6}")
            
    except Exception as e:
        print(f"Error testing {username}: {e}")

print("-" * 65)
