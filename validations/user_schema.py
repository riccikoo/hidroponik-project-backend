def validate_register(data):
    errors = {}
    if not data.get('email'):
        errors['email'] = 'Email is required.'
    if not data.get('name'):
        errors['name'] = 'Name is required.'
    if not data.get('password'):
        errors['password'] = 'Password is required.'
    if data.get('password') != data.get('password_confirmation'):
        errors['password_confirmation'] = 'Password confirmation does not match.'
    return errors

def validate_login(data):
    errors = {}
    if not data.get('email'):
        errors['email'] = 'Email is required.'
    if not data.get('password'):
        errors['password'] = 'Password is required.'
    return errors