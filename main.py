from flask import Flask, request, jsonify, redirect, url_for, g, make_response
from flask_cors import CORS, cross_origin
import requests
import json
import jwt
from datetime import timedelta, datetime as dt

from flask_httpauth import HTTPTokenAuth, HTTPBasicAuth
auth = HTTPTokenAuth('Bearer')

app = Flask(__name__)

# during local dev, Python API was set to port 5000 and JS frontend was set to port 8080

# configuring CORS extension: specifying domain for origins (as opposed to using wildcard "*" ) is necessary when supports_credentials is True.
# including "Access-Control-Allow-Credentials" in headers to allow for
# cookies with credentials submitted across domains.
CORS(
    app,
    origins="URL of your frontend domain",
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Access-Control-Allow-Credentials"],
    supports_credentials=True)

# for JWT
# this should be changed to environ variable
app.config['SECRET_KEY'] = 'super-secret'


# 23andMe login redirect endpoint
@app.route("/23ndMeLoginRedirect", methods=["GET"])
@cross_origin()
def redirect_to_login():
    """
    Frontend client is redirect to this endpoint momentarily via window.location.href = "/[your frontend url]" and then instantnly redirected to 23andMe login page
    """
    return redirect("https://api.23andme.com/authorize/?redirect_uri=URLForWhereThisAPIisHosted/receive_code/&response_type=code&client_id=[your clint ID of your registered client with 23andme's API]&scope=basic%20names%20email%20ancestry%20family_tree%20relatives%20relatives:write%20analyses%20haplogroups%20report:all%20report:wellness.alcohol_flush%20report:wellness.caffeine_consumption%20report:wellness.deep_sleep%20report:wellness.lactose%20report:wellness.muscle_composition%20report:wellness.saturated_fat_and_weight%20report:wellness.sleep_movement%20genomes%20phenotypes:read:weight_g%20phenotypes:read:sex%20phenotypes:read:family_tree_url%20phenotypes:read:date_of_birth%20phenotypes:read:height_mm%20phenotypes:read:bd_pgen_patient_id")


# endpoint to received the code granted after user authorizes via web browser to grant access
@app.route('/receive_code/', methods=["GET", "POST"])
def receive_auth_code():
    auth_code = request.args.get('code', '')
    # hit callback to request 10-hour token

    get_token(auth_code)
    current_user_JWT = store_user_assign_JWT()

    # build response header with JWT in cookie
    #resp = make_response(redirect("http://127.0.0.1:8080"))

    resp = make_response(redirect("[your frontend url]"))

    # if you try setting the cookie with httponly flag as False, then it means
    # that the cookie is not accessible to only just the server but is
    # available to JS as well via document.cookie. The default for Flask is to
    # set cookies to httponly=True for the obvious security benefits (fight
    # off XSS to some extent, etc)
    resp.set_cookie('access_token', current_user_JWT, httponly=True)
    return resp


# object for storing final access token and user account info for API
# authentication dev purposes
auth_user_store = {}


def get_token(auth_code):
    print("get_token called...")
    """
    This callback takes the auth code provided after user authenticates via 23andMe redirect
    and then requests access token, which specified scopes, that can then be used to make the
    authenticated calls for user's account via 23andMe API endpoints
    """

    url = "https://api.23andme.com/token/"
    payload = {
        'client_id': 'the client ID of your app registered with 23andme API',
        'client_secret': 'the client secret of your app registered with 23andme API',
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': 'url of your API/receive_code/',
        'scope': 'basic rs123'  # appearently we can leave the scope as-is here as the scope is already articulated in the redirect URL for login that provides the auth code required for acccess token retrieval
    }

    r = requests.post(url, payload)
    response = r.json()
    global access_token
    access_token = response["access_token"]
    print(access_token)

    # get account data for recently authenticated user
    account_endpoint()

    # store access_token in dev object
    auth_user_store["access_token"] = access_token

    print("auth_user_store object: ")
    print(json.dumps(auth_user_store, sort_keys=True, indent=4))

    return access_token


################################### NEW JWT #################################

# access token received from 23andMe API after get_token() so we store User
# instance containing info stored in auth_user_store object in dict tables

def store_user_assign_JWT():
    """
    callback that is passed 23andMe account info after redirect and authentication
    and then returns these three values to global scope of this module for instantiation with
    User class and availabilty with flask_jwt processes
    """

    global account_password, account_username, account_id
    account_password = auth_user_store["access_token"]
    account_username = auth_user_store[
        "current_user_account_info"]["data"][0]["first_name"]
    account_id = auth_user_store["current_user_account_info"]["data"][0]["id"]

    global users, username_table, userid_table
    g.current_user = User(account_id, account_username, account_password)

    username_table = {g.current_user.account_username: g.current_user}
    userid_table = {g.current_user.account_id: g.current_user}

    current_user_JWT = g.current_user.generate_jwt(account_id)
    print("current_user_JWT: {}".format(current_user_JWT))
    return current_user_JWT


# JWT encoding and decoding

# using dict for temporary user storage vs database
class User(object):

    def __init__(self, account_id, account_username, account_password):
        self.account_id = account_id
        self.account_username = account_username
        self.account_password = account_password

    def generate_jwt(self, account_id):
        """
        Generates JWT based on user's acccount_id provided by 23andMe
        """
        JWT_token = jwt.encode({'id': account_id, 'exp': dt.utcnow(
        ) + timedelta(seconds=3600)}, 'secret', algorithm='HS256')

        #JWT_token = jwt.encode({'id': account_id}, 'secret', algorithm='HS256')
        return JWT_token

    # original method, leaving as alternative implementation
    @staticmethod
    def verify_JWT(JWT_token):
        print("Inside verify_JWT()....")
        try:
            print("inside try in verify_JWT()...")
            decoded_jwt = jwt.decode(JWT_token, 'secret', algorithms=['HS256'])
            print("decoded_jwt: {}".format(decoded_jwt))
            print("getting id from userid_table...")
            print(userid_table.get(decoded_jwt["id"]))
        except:
            print("inside except in verify_JWT()...")
            return False
        if 'id' in decoded_jwt:
            g.current_user = userid_table.get(decoded_jwt['id'])
            print("g.current_user: {}".format(g.current_user))
            return True
        return False


# current verify_token method, not using staticmethod in User
@auth.verify_token
def verify_token(token):
    print("this is token inside verify_token(): {}".format(token))

    # try to retrieve access_token from httponly cookie
    if 'access_token' in request.cookies:
        print(request.cookies)
        token = str(request.cookies['access_token'])

    g.current_user = None
    # leaving this conditional as standalone to allow for ajax calls or other API calls to this API vs current SPA implementation that just uses httponly cookie
    # if token is not None:
    if token != '':
        try:
            print("inside try")
            print("token: {}".format(token))
            #data = jwt.loads(token)
            decoded_jwt = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            print("expired")
            return False
        if 'id' in decoded_jwt:
            try:
                g.current_user = userid_table.get(decoded_jwt['id'])
                print(g.current_user)
                if g.current_user is not None:
                    return True
                else:
                    return False
            except NameError:
                return False
    else:
        print(
            "token is empty or no httponly cookie with token was present: {}".format(token))
        return False


@auth.error_handler
def auth_error():
    return jsonify(authorization_error='INVALID CREDENTIALS')
    # return unauthorized('INVALID CREDENTIALS')

# test endpoint for JWT
@app.route('/testjwt/')
@auth.login_required
def jwt_test():
    # commented out but leaving in for debugging
    #if 'access_token' in request.cookies:
    #    print(request.cookies)
    #print("request: {}".format(request))
    return jsonify(authorized=True)


@app.route('/logout/')
def logout():
    # redeclare global dicts that were initially setup to store user info as empty dicts
    global username_table, userid_table
    username_table = {}
    userid_table = {}
    return jsonify(message="user logged out")

@app.route('/testendpoint')
def testendpoint():
    return jsonify(message="this is test endpoint")

###############################API ENDPOINTS#################################
#############################################################################

@app.route('/23andMe/api/v1.0/account', methods=["GET"])
# commenting out auth decorator because currently the token generation process requires this endpoint, so it is a pre-token API endpoint call
#@auth.login_required
def account_endpoint():
    print("account_endpoint called...")

    url = "https://api.23andme.com/3/account/"
    headers = {"Authorization": "Bearer %s" % access_token}
    r = requests.get(url, headers=headers)
    # print(r.json())
    account_object = r.json()

    # store user account info in dev obj
    auth_user_store["current_user_account_info"] = account_object
    print("auth_user_store saving current_user_account_info in account_endpoint()")
    print(account_object)

    return jsonify(account_object)


@app.route('/23andMe/api/v1.0/profile/<account_id>', methods=["GET"])
@auth.login_required
def profile_endpoint(account_id):
    url = "https://api.23andme.com/3/profile/?account_id={}".format(account_id)
    headers = {"Authorization": "Bearer %s" % access_token}
    r = requests.get(url, headers=headers)
    print(r.json())
    account_object = r.json()
    return jsonify(account_object)


# Genetic Data Endpoints
@app.route('/23andMe/api/v1.0/accession/', methods=["GET"])
@auth.login_required
def accession_endpoint():
    if request.args.get('chromosome', ''):
        url = "https://api.23andme.com/3/accession/?chromosome={}".format(
            request.args.get('chromosome', ''))

    elif request.args.get('accession_id', ''):
        url = "https://api.23andme.com/3/accession/{}".format(
            request.args.get('accession_id', ''))
    else:
        url = "https://api.23andme.com/3/accession/"
    headers = {"Authorization": "Bearer %s" % access_token}
    r = requests.get(url, headers=headers)
    print(r.json())
    account_object = r.json()
    return jsonify(account_object)


@app.route('/23andMe/api/v1.0/marker/', methods=["GET"])
@auth.login_required
def marker_endpoint():
    if request.args.get('gene_name', ''):
        url = "https://api.23andme.com/3/marker/?gene_name={}".format(
            request.args.get('gene_name', ''))
    elif (request.args.get('accession_id', '') and request.args.get('start', '') and request.args.get('end', '') and request.args.get('offset', '')):
        url = "https://api.23andme.com/3/marker/?accession_id={0}&start={1}&end={2}&limit={3}&offset={4}".format(
            request.args.get(
                'accession_id', ''), request.args.get(
                'start', ''), request.args.get(
                'end', ''), request.args.get(
                    'limit', ''), request.args.get(
                        'offset', ''))
    elif request.args.get('accession_id', ''):
        url = "https://api.23andme.com/3/marker/?accession_id={}".format(
            request.args.get('accession_id', ''))
    elif request.args.get('marker_id', ''):
        url = "https://api.23andme.com/3/marker/?marker_id={}".format(
            request.args.get('marker_id', ''))
    else:
        url = "https://api.23andme.com/3/marker/"
    headers = {"Authorization": "Bearer %s" % access_token}
    r = requests.get(url, headers=headers)
    print(r.json())
    account_object = r.json()
    return jsonify(account_object)


@app.route('/23andMe/api/v1.0/profile/<profile_id>/marker/', methods=["GET"])
@auth.login_required
def profile_marker_endpoint(profile_id):
    if request.args.get('gene_name', ''):
        url = "https://api.23andme.com/3/profile/{0}/marker/?gene_name={1}".format(
            profile_id, request.args.get('gene_name', ''))
    elif (request.args.get('accession_id', '') and request.args.get('start', '') and request.args.get('end', '') and request.args.get('offset', '')):
        url = "https://api.23andme.com/3/profile/{0}/marker/?accession_id={1}&start={2}&end={3}&limit={4}&offset={5}".format(
            profile_id, request.args.get(
                'accession_id', ''), request.args.get(
                'start', ''), request.args.get(
                'end', ''), request.args.get(
                    'limit', ''), request.args.get(
                        'offset', ''))

    elif (request.args.get('accession_id', '')):
        url = "https://api.23andme.com/3/profile/{0}/marker/?accession_id={1}".format(
            profile_id, request.args.get('accession_id', ''))

    headers = {"Authorization": "Bearer %s" % access_token}
    r = requests.get(url, headers=headers)
    print(r.json())
    account_object = r.json()
    return jsonify(account_object)


@app.route('/23andMe/api/v1.0/variant/', methods=["GET"])
@auth.login_required
def variant_endpoint():
    if (request.args.get('accession_id', '') and request.args.get('start', '')
            and request.args.get('end', '') and request.args.get('platform_label', '')):
        url = "https://api.23andme.com/3/variant/?accession_id={0}&start={1}&end={2}&limit={3}&offset={4}".format(
            request.args.get(
                'accession_id', ''), request.args.get(
                'start', ''), request.args.get(
                'end', ''), request.args.get(
                    'limit', ''), request.args.get(
                        'paltform_label', ''))
    elif request.args.get('accession_id', ''):
        print("accession_id inside variant view point")
        url = "https://api.23andme.com/3/variant/?accession_id={}".format(
            request.args.get('accession_id', ''))
        print(url)

    elif (request.args.get('chromosome_id', '') and request.args.get('start', '') and request.args.get('end', '') and request.args.get('platform_label', '')):
        url = "https://api.23andme.com/3/variant/?chromosome_id={0}&start={1}&end={2}&limit={3}&offset={4}".format(
            request.args.get(
                'accession_id', ''), request.args.get(
                'start', ''), request.args.get(
                'end', ''), request.args.get(
                    'limit', ''), request.args.get(
                        'platform_label', ''))
    elif request.args.get('chromosome_id', ''):
        url = "https://api.23andme.com/3/variant/?chromosome_id={}".format(
            request.args.get('chromosome_id', ''))
    elif request.args.get('gene_name', ''):
        url = "https://api.23andme.com/3/variant/?gene_name={}".format(
            request.args.get('gene_name', ''))

    headers = {"Authorization": "Bearer %s" % access_token}

    r = requests.get(url, headers=headers)

    if r.status_code == 200:
        account_object = r.json()
        return jsonify(account_object)
    # 23andme API's cloudflare timeout response, seems to happen with some
    # accession_id searches
    elif r.status_code == 524:
        response = jsonify({"error": '23andMe API timeout'})
        print(type(response))
        print(dir(response))
        response.status_code = 524
        return response
    else:
        response = jsonify({'error': 'please see 23andMe API server response'})
        response.status_code = r.status_code
        return response


@app.route('/23andMe/api/v1.0/profile/<profile_id>/variant/', methods=["GET"])
@auth.login_required
def profile_variant_endpoint(profile_id):
    if (request.args.get('accession_id', '') and request.args.get('start', '')
            and request.args.get('end', '') and request.args.get('offset', '')):
        url = "https://api.23andme.com/3/profile/{0}/variant/?accession_id={1}&start={2}&end={3}&limit={4}&offset={5}".format(
            profile_id, request.args.get(
                'accession_id', ''), request.args.get(
                'start', ''), request.args.get(
                'end', ''), request.args.get(
                    'limit', ''), request.args.get(
                        'offset', ''))
    elif request.args.get('accession_id', ''):
        url = "https://api.23andme.com/3/profile/{0}/variant/?accession_id={1}".format(
            profile_id, request.args.get('accession_id', ''))

    headers = {"Authorization": "Bearer %s" % access_token}
    r = requests.get(url, headers=headers)
    print(r.json())
    account_object = r.json()
    return jsonify(account_object)


@app.route('/23andMe/api/v1.0/report/', methods=["GET"])
@auth.login_required
def report_endpoint():

    if request.args.get('report_id', ''):
        url = "https://api.23andme.com/3/report/{0}".format(
            request.args.get('report_id', ''))
    else:
        url = "https://api.23andme.com/3/report/"

    headers = {"Authorization": "Bearer %s" % access_token}
    r = requests.get(url, headers=headers)
    print(r.json())
    account_object = r.json()
    return jsonify(account_object)


@app.route('/23andMe/api/v1.0/profile/<profile_id>/report/', methods=["GET"])
@auth.login_required
def profile_report_endpoint(profile_id):

    if request.args.get('report_id', ''):
        url = "https://api.23andme.com/3/profile/{0}/report/{1}".format(
            profile_id, request.args.get('report_id', ''))
    else:
        url = "https://api.23andme.com/3/profile/{}/report/".format(profile_id)

    headers = {"Authorization": "Bearer %s" % access_token}
    r = requests.get(url, headers=headers)
    print(r.json())
    account_object = r.json()
    return jsonify(account_object)


if __name__ == '__main__':
    app.run(debug=True) # do not user debug=True for production!!!
