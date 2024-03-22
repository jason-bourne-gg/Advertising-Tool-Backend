
from flask import Blueprint, jsonify, g, request
import logging
from flask import request, Blueprint, render_template, redirect, session, make_response
from flask_login import login_user, login_required, logout_user, current_user
from apis.user import user_store, User
from settings.config import redirect_uri, okta_client_id,okta_client_secret,okta_org_url,okta_redirect_uri
import base64
import hashlib
import requests
import secrets
from database import *
import urllib.parse



# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)



auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route("/api/login")
def login():
    # store app state and code verifier in session
    session['app_state'] = secrets.token_urlsafe(64)
    session['code_verifier'] = secrets.token_urlsafe(64)

    # calculate code challenge
    hashed = hashlib.sha256(session['code_verifier'].encode('ascii')).digest()
    encoded = base64.urlsafe_b64encode(hashed)
    code_challenge = encoded.decode('ascii').strip('=')

    # print ("hi", request.headers.get('request_cookies'))

    # get request params
    query_params = {'client_id': okta_client_id,
                    'redirect_uri': okta_redirect_uri,
                    'scope': "openid email profile",
                    'state': session['app_state'],
                    'code_challenge': code_challenge,
                    'code_challenge_method': 'S256',
                    'response_type': 'code',
                    'response_mode': 'query'}

    # build request_uri
    request_uri = "{base_url}?{query_params}".format(
        base_url=okta_org_url + "oauth2/v1/authorize",
        query_params=requests.compat.urlencode(query_params)
    )

    return redirect(request_uri)





@auth_blueprint.route("/authorization-code/callback")
def callback():
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    code = request.args.get("code")
    app_state = request.args.get("state")
    if app_state != session['app_state']:
        return "The app state does not match"
    if not code:
        return "The code was not returned or is not accessible", 403
    query_params = {'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': okta_redirect_uri,
                    'code_verifier': session['code_verifier'],
                    }
    query_params = requests.compat.urlencode(query_params)
    exchange = requests.post(
        okta_org_url + "oauth2/v1/token",
        headers=headers,
        data=query_params,
        auth=(okta_client_id, okta_client_secret),
    ).json()

    # Get tokens and validate
    if not exchange.get("token_type"):
        return "Unsupported token type. Should be 'Bearer'.", 403
    access_token = exchange["access_token"]
    id_token = exchange["id_token"]
    
    session["id_token"] = id_token
    session["access_token"] = access_token

    print ("\n in callback \n")
    print(access_token)
    print(id_token)
    # Authorization flow successful, get userinfo and login user
    userinfo_response = requests.get(okta_org_url + "oauth2/v1/userinfo",
                                     headers={'Authorization': f'Bearer {access_token}'}).json()
    print(userinfo_response)

    unique_id = userinfo_response["sub"]
    user_email = userinfo_response["email"]
    user_name = userinfo_response["given_name"]
    session["okta_attributes"] = userinfo_response

    if user_name not in user_store:
        user_store[user_name] = {
            'name': user_name,
            'email': user_email,
        }
    user = User(user_name)

    login_user(user)

    url = redirect_uri
    return redirect(url)


@auth_blueprint.route("/api/logout", methods=["GET", "POST"])
@login_required
def logout():
    id_token = session.get('id_token')
    if id_token:
        # clear session and logout from logout URL and the redirect to homepage post logout
        session.clear()
        return(redirect(f'{okta_org_url}/oauth2/v1/logout?id_token_hint={id_token}&post_logout_redirect_uri={redirect_uri}'))

    else:
        response = make_response('Logged out')
        session.clear()
        return response
        
    
    