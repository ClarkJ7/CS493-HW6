from google.cloud import datastore
from flask import Flask, request, render_template, request, url_for, redirect
import requests
import random
import string

app = Flask(__name__)
client = datastore.Client()

client_id = "942293111488-9do4e7f5h5mpgu6q4qvciji1po22ijbg.apps.googleusercontent.com"
client_secret = "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"
google_people_api = "https://people.googleapis.com/v1/people/me?personFields=names"
google_Oauth_endpoint = "https://accounts.google.com/o/oauth2/v2/auth?"
google_Oauth_post = "https://www.googleapis.com/oauth2/v4/token"
local_redirect = "http://localhost:8080/oauth"
deployed_redirect = "https://oauth-330917.uw.r.appspot.com/oauth"


@app.route('/', methods=['GET'])
def index():
    return render_template('welcome.html')


@app.route('/initial_request', methods=['GET'])
def initial_request():
    state = generate_state()
    new_state = datastore.Entity(client.key("states"))
    new_state.update({'state': state})
    client.put(new_state)
    return redirect(google_Oauth_endpoint +
                    "response_type=code"
                    "&client_id="+client_id +
                    "&redirect_uri="+deployed_redirect +
                    "&scope=profile"
                    "&state=" + state)


@app.route('/oauth', methods=['GET', 'POST'])
def test():
    # grab state from query string
    state = request.args.get('state')

    # grab all states used from datastore
    query = client.query(kind="states")
    results = list(query.fetch())

    # check if state from query string matches any in datastore
    found = False
    for i in results:
        if i["state"] == state:
            found = True
            target_key = client.key("states", i.key.id)
            client.delete(target_key)
            break
        else:
            return render_template('user_info.html',
                                   firstName="Error",
                                   lastName="Datastore is empty",
                                   state="Please go back and refresh")

    # if no matching state was found, return user info page with error message
    if found is False:
        return render_template('user_info.html',
                               firstName="Error",
                               lastName="Error",
                               state="NO MATCHING STATE")

    # grab code from query string
    code = request.args.get('code')

    # build request for post
    token_request = {'code': code,
                     'client_id': client_id,
                     'client_secret': client_secret,
                     'redirect_uri': deployed_redirect,
                     'grant_type': 'authorization_code'}
    # send token request
    token_response = requests.post(google_Oauth_post, data=token_request)
    response_json = token_response.json()

    # grab token
    token = response_json['access_token']

    # use token to call People API
    name_request = {'Authorization': "Bearer " + token}
    name_response = requests.get(google_people_api, headers=name_request)
    name_json = name_response.json()

    # grab name values
    names = name_json['names'][0]
    first_name = names['givenName']
    last_name = names['familyName']

    # return user info page with correct info
    return render_template('user_info.html',
                           firstName=first_name,
                           lastName=last_name,
                           state=state)


# generate a random state
def generate_state():
    length = 8 # number of characters in state value
    valid_char = string.ascii_letters
    state = ''.join(random.choice(valid_char) for i in range(length))
    return state


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=True)
