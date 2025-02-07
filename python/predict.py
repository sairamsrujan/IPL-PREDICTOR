from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import pandas as pd
import os

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing (CORS)

print("Current working directory:", os.getcwd())
# Path to your model (update this to the correct path if needed)
path = os.path.join(os.getcwd(), 'models', 'pipe.pkl')
print(f"Model path: {path}") 

# Load the model
try:
    lr_model = pickle.load(open(path, 'rb'))
    print("Model loaded successfully")
except Exception as e:
    print(f"Error loading model: {e}")
        
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "Welcome to the Cricket Prediction API. Use POST /predict to get predictions."
    }), 200

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get the incoming JSON data
        data = request.get_json()
        print("Received data:", data)  # Log the received data

        if not data:
            return jsonify({'error': 'No JSON data received'}), 400

        # Extract necessary values from the data
        batting_team = data.get('batting_team')
        bowling_team = data.get('bowling_team')
        city = data.get('city')
        runs_left = data.get('runs_left')
        balls_left = data.get('balls_left')
        wickets_remaining = data.get('wickets_remaining')
        total_run_x = data.get('total_run_x')

        # Debugging: Log the extracted values
        print(f"Extracted values: batting_team={batting_team}, bowling_team={bowling_team}, city={city}, runs_left={runs_left}, balls_left={balls_left}, wickets_remaining={wickets_remaining}, total_run_x={total_run_x}")

        # Validate input data
        if any(v is None for v in [batting_team, bowling_team, city, runs_left, balls_left, wickets_remaining, total_run_x]):
            return jsonify({'error': 'Missing required fields in input data'}), 400

        # Check and adjust probabilities based on special cases
        if wickets_remaining == 0:
            return jsonify({
                "batting_team": {
                    "team_name": batting_team,
                    "winning_probability": 0.00
                },
                "bowling_team": {
                    "team_name": bowling_team,
                    "winning_probability": 100.00
                }
            })
        
        if runs_left > 1 and balls_left == 0:
            return jsonify({
                "batting_team": {
                    "team_name": batting_team,
                    "winning_probability": 0.00
                },
                "bowling_team": {
                    "team_name": bowling_team,
                    "winning_probability": 100.00  # Set to 100% correctly
                }
            })
        
        if balls_left == 0 and runs_left == 1:
            return jsonify({
                "batting_team": {
                    "team_name": batting_team,
                    "winning_probability": 50.00  # Set to 50% correctly
                },
                "bowling_team": {
                    "team_name": bowling_team,
                    "winning_probability": 50.00  # Set to 50% correctly
                }
            })
        
        if runs_left == 0 and balls_left >0:
            return jsonify({
                "batting_team": {
                    "team_name": batting_team,
                    "winning_probability": 100.00  # Set to 50% correctly
                },
                "bowling_team": {
                    "team_name": bowling_team,
                    "winning_probability": 0.00  # Set to 50% correctly
                }
            })

        # Calculate CRR and RRR (current run rate and required run rate)
        crr = (total_run_x - runs_left) / ((120 - balls_left) / 6) if balls_left < 120 else 0
        rrr = (runs_left * 6) / balls_left if balls_left > 0 else 0

        # Prepare data for prediction
        input_data = pd.DataFrame({
            'batting_team': [batting_team],
            'bowling_team': [bowling_team],
            'city': [city],
            'runs_left': [runs_left],
            'balls_left': [balls_left],
            'wickets_remaining': [wickets_remaining],
            'total_run_x': [total_run_x],
            'crr': [crr],
            'rrr': [rrr]
        })

        # Debugging: Log the input data passed to the model
        print("Input data for model prediction:")
        print(input_data)

        # Make prediction
        lr_prediction = lr_model.predict_proba(input_data)[0]
        print("Prediction (LR):", lr_prediction)  # Log the prediction values

        # Construct response data with correct probabilities (multiply by 100 to get percentage)
        response = {
            "batting_team": {
                "team_name": batting_team,
                "winning_probability": round(lr_prediction[1] * 100, 2)  # Convert to percentage
            },
            "bowling_team": {
                "team_name": bowling_team,
                "winning_probability": round(lr_prediction[0] * 100, 2)  # Convert to percentage
            }
        }
        print("Response being sent:", response)

        return jsonify(response)

    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)  # Ensure Flask runs on port 5000
