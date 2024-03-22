from datetime import datetime, timedelta
from functools import wraps
from flask import session, request, jsonify,redirect,make_response
from settings.config import redirect_uri,okta_org_url,okta_redirect_uri
import time 
from functools import lru_cache
import cachetools
import functools

def logout_2():
    id_token = session.get('id_token')
    if id_token:
        # clear session and logout from logout URL and the redirect to homepage post logout
        session.clear()
        return(redirect(f'{okta_org_url}/oauth2/v1/logout?id_token_hint={id_token}&post_logout_redirect_uri={redirect_uri}'))

    else:
        response = make_response('Logged out')
        session.clear()
        return response

# Function to update user activity and check for inactivity
def update_user_activity(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Check for inactivity (if user has been inactive for more than 1 hour)
        last_activity = session.get('last_activity')
        if last_activity:
            time_since_last_activity = datetime.utcnow() - last_activity
            if time_since_last_activity > timedelta(hours=12):
                logout_2()
                # Return a response indicating inactivity or take appropriate action (e.g., log out the user)
                return jsonify({'message': 'You have been inactive for more than 1 hour. Please log in again.'}), 401

        # Update user activity
        session['last_activity'] = datetime.utcnow()
        return func(*args, **kwargs)

    return wrapper









# Create a cache with a maximum size and a TTL (time to live) in seconds
cache = cachetools.TTLCache(maxsize=100, ttl=2 * 60 * 60)  # 2 hours
def cache_route(seconds):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (request.path, frozenset(request.args.items()))
            try:
                return cache[key]
            except KeyError:
                result = func(*args, **kwargs)
                cache[key] = result
                return result
        return wrapper
    return decorator

