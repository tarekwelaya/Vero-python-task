import requests
import jsonify
import pandas as pd
from flask import Flask, request

app = Flask(__name__)

API_AUTH_BASE_URL = "https://api.baubuddy.de/index.php"
API_DATA_BASE_URL = "https://api.baubuddy.de/dev/index.php"
TOKEN = None



@app.route('/process-csv/', methods=['POST'])
def process_csv():
    
    try:
        if 'csv_file' not in request.files:
            return {"Error": "No csv file was provided in the request."}, 400

        # Get the uploaded CSV file
        csv_file = request.files['csv_file']


        df = pd.read_csv(csv_file, delimiter=';', na_filter= False)
        
        headers = {
            "Authorization": "Bearer {}".format(TOKEN),
            "Content-Type": "application/json"
        }

        # Get resources from API
        data_url = API_DATA_BASE_URL+"/v1/vehicles/select/active"
        data_response = requests.request("GET", data_url, headers=headers)

        # Merge data from csv file and API response and take
        merged_data = pd.merge(pd.DataFrame(data_response.json()), df, left_on='kurzname', right_on='kurzname', how='inner', suffixes=('', '_y'))
        
        # Drop duplicate coloumns and take the value for these coloumns of the API response
        merged_data.drop(merged_data.filter(regex='_y$').columns, axis=1, inplace=True)
        
        # Drop rows that do not have a value set for hu
        merged_data = merged_data.dropna(subset=["hu"])

        merged_data["colorCode"] = ""
        
        # Get color codes for labelIds
        for index, data in merged_data.iterrows():
            if data["labelIds"]:
                response = requests.request("GET", API_DATA_BASE_URL+"/v1/labels/"+str(data["labelIds"]), headers=headers)
                merged_data.loc[index, "colorCode"] = response.json()[0]["colorCode"]

        return pd.DataFrame.to_json(merged_data), 200
    
    except Exception as e:
        print(e)
        return {"Error": str(e)}, 500

with app.app_context():

    # Get Token when the server launches

    payload = {
        "username": "365",
        "password": "1"
    }
    headers = {
    "Authorization": "Basic QVBJX0V4cGxvcmVyOjEyMzQ1NmlzQUxhbWVQYXNz",
    "Content-Type": "application/json"
    }

    response = requests.request("POST", API_AUTH_BASE_URL+"/login", json=payload, headers=headers)
    TOKEN = response.json()["oauth"]["access_token"]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
