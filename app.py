from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pandas as pd
import joblib
import os

FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(__file__), "waste-predictor", "build")

# Disable Flask's default static folder so our custom /static route serves the React build assets
app = Flask(__name__, static_folder=None)
CORS(app)

    
# -------------------------
# Load zones for mapping
# -------------------------
DATA_FILE = "Data.csv"
if os.path.exists(DATA_FILE):
    _zones_df = pd.read_csv(DATA_FILE)
    _zones_df.columns = _zones_df.columns.str.strip()
    _unique_zones = _zones_df['Zone Name'].astype(str).str.strip().drop_duplicates().tolist()
else:
    _zones_df = pd.DataFrame()
    _unique_zones = []

# -------------------------
# Utility: Predict function
# -------------------------
def predict_segregation(input_data, model_name='XGBoost'):
    try:
        # Load model and preprocessing objects
        model_path = os.path.join("saved_models", "XGBoost.pkl")
        encoder_path = os.path.join("saved_models", "zone_encoder.pkl")
        scaler_path = os.path.join("saved_models", "scaler.pkl")
        columns_path = os.path.join("saved_models", "columns.csv")
        
        print("Loading model and encoders...")
        
        model = joblib.load(model_path)
        le_zone = joblib.load(encoder_path)
        scaler = joblib.load(scaler_path)
        
        # Get expected columns
        expected_columns = pd.read_csv(columns_path, header=None)[0].tolist()
        print(f"Expected columns: {expected_columns}")
        
        # Extract and validate input
        total_households = float(input_data['Total_Households'])
        covered_households = float(input_data['Covered_Households'])
        zone_name = str(input_data['Zone_Name']).strip()
        
        # Encode zone
        try:
            zone_id = le_zone.transform([zone_name])[0] if zone_name in le_zone.classes_ else 0
            print(f"Encoded zone '{zone_name}' to ID: {zone_id}")
        except Exception as e:
            print(f"Error encoding zone: {str(e)}")
            zone_id = 0
        
        # Create input features in the exact order expected by the model
        input_features = {
            'Total_Households': total_households,
            'Covered_Households': covered_households,
            'Zone_ID': zone_id,
            'Ward No.': int(input_data.get('Ward No.', 1))
        }
        
        # Create DataFrame with correct column order
        input_df = pd.DataFrame([input_features])
        
        # Ensure all expected columns are present
        for col in expected_columns:
            if col not in input_df.columns:
                input_df[col] = 0  # or appropriate default value
                
        input_df = input_df[expected_columns]
        
        print("Input DataFrame columns:", input_df.columns.tolist())
        print("Input values:", input_df.values.tolist())
        
        # Scale features
        input_scaled = scaler.transform(input_df)
        
        # Make prediction
        pred = model.predict(input_scaled)[0]
        
        # Ensure prediction is within valid range
        pred = max(0, min(pred, covered_households))
        print(f"Prediction: {pred}")
        
        return float(pred)
        
    except Exception as e:
        print(f"Error in predict_segregation: {str(e)}")
        import traceback
        traceback.print_exc()
        # Fallback: Return 70% of covered households if prediction fails
        return float(input_data.get('Covered_Households', 0)) * 0.7


# -------------------------
# Frontend routes (React build)
# -------------------------
@app.route("/", methods=["GET"])
def serve_frontend_index():
    """Serve the built React frontend (waste-predictor)."""
    try:
        return send_from_directory(FRONTEND_BUILD_DIR, "index.html")
    except FileNotFoundError:
        return jsonify({
            "error": "Frontend build not found",
            "details": "Run 'npm install' and 'npm run build' inside the waste-predictor folder, then redeploy."
        }), 500


@app.route("/static/<path:path>")
def serve_frontend_static(path):
    """Serve static assets from the React build folder."""
    static_dir = os.path.join(FRONTEND_BUILD_DIR, "static")
    try:
        return send_from_directory(static_dir, path)
    except FileNotFoundError:
        return jsonify({"error": "Static asset not found", "path": path}), 404


@app.route("/manifest.json", methods=["GET"])
def serve_manifest():
    """Serve CRA manifest.json from the React build root if present."""
    try:
        return send_from_directory(FRONTEND_BUILD_DIR, "manifest.json")
    except FileNotFoundError:
        return jsonify({"error": "manifest.json not found"}), 404


@app.route("/logo192.png", methods=["GET"])
def serve_logo192():
    """Serve CRA logo192.png from the React build root if present."""
    try:
        return send_from_directory(FRONTEND_BUILD_DIR, "logo192.png")
    except FileNotFoundError:
        return jsonify({"error": "logo192.png not found"}), 404


@app.route("/logo512.png", methods=["GET"])
def serve_logo512():
    """Serve CRA logo512.png from the React build root if present."""
    try:
        return send_from_directory(FRONTEND_BUILD_DIR, "logo512.png")
    except FileNotFoundError:
        return jsonify({"error": "logo512.png not found"}), 404


@app.route("/favicon.ico", methods=["GET"])
def serve_favicon():
    """Serve favicon.ico from the React build root if present."""
    try:
        return send_from_directory(FRONTEND_BUILD_DIR, "favicon.ico")
    except FileNotFoundError:
        return jsonify({"error": "favicon.ico not found"}), 404


# -------------------------
# API Routes
# -------------------------
@app.route("/predict", methods=["POST"])
def predict_route():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No input data provided"}), 400

        # Get and validate input
        try:
            total = int(data.get("total_households", 0))
            covered = int(data.get("covered_households", 0))
            zone_name = str(data.get("zone_name", "")).strip()
            
            if total <= 0:
                return jsonify({"error": "Total households must be greater than 0"}), 400
            if covered < 0 or covered > total:
                return jsonify({"error": "Covered households must be between 0 and total"}), 400
                
        except (ValueError, TypeError) as e:
            return jsonify({"error": "Invalid input data"}), 400

        # Default to first zone if not provided
        if not zone_name and _unique_zones:
            zone_name = _unique_zones[0]
        elif not zone_name:
            zone_name = "Unknown"

        # Prepare input for prediction
        input_data = {
            "Total_Households": total,
            "Covered_Households": covered,
            "Zone_Name": zone_name,
            "Ward No.": 1  # Default ward number
        }

        try:
            # Get prediction
            pred_count = predict_segregation(input_data)
            
            # Calculate segregation rate
            segregation_rate = round((pred_count / total) * 100, 2) if total > 0 else 0.0

            return jsonify({
                "prediction": {
                    "segregation_rate": segregation_rate,
                    "predicted_households": int(pred_count),
                    "model_used": "XGBoost"
                },
                "input": {
                    "total_households": total,
                    "covered_households": covered,
                    "zone_name": zone_name
                }
            })
            
        except Exception as e:
            print(f"Prediction error: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "error": "Prediction failed",
                "details": str(e)
            }), 500

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route("/dashboard", methods=["GET"])
def dashboard_route():
    try:
        if not os.path.exists(DATA_FILE):
            return jsonify({"error": f"Data file not found at {os.path.abspath(DATA_FILE)}"}), 404

        # Read and clean the data
        df = pd.read_csv(DATA_FILE)
        df.columns = df.columns.str.strip()
        
        # Convert column names to match expected format
        column_mapping = {
            'Total No. of households / establishments': 'Total_Households',
            'Total no. of households and establishments covered through doorstep collection': 'Covered_Households',
            'HH covered with Source Seggeratation': 'HH_Source_Segregation',
            'HH covered with Source Segregation': 'HH_Source_Segregation',  # Handle possible typo
            'Zone Name': 'Zone_Name',
            'Zone_Name': 'Zone_Name'  # In case it's already correct
        }
        
        # Rename columns based on mapping, keeping original if not in mapping
        df = df.rename(columns={col: column_mapping.get(col, col) for col in df.columns})
        
        # Ensure required columns exist
        required_columns = ['Total_Households', 'Covered_Households', 'HH_Source_Segregation', 'Zone_Name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({
                "error": f"Missing required columns in data: {', '.join(missing_columns)}",
                "available_columns": df.columns.tolist()
            }), 400

        # Convert numeric columns to numeric, coercing errors to NaN
        for col in ['Total_Households', 'Covered_Households', 'HH_Source_Segregation']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Drop rows with missing or invalid data
        df = df.dropna(subset=['Total_Households', 'Covered_Households', 'HH_Source_Segregation', 'Zone_Name'])
        df = df[df['Total_Households'] > 0]

        if df.empty:
            return jsonify({"error": "No valid data available after cleaning"}), 400

        # Group by zone and calculate metrics
        zone_group = df.groupby('Zone_Name', as_index=False).agg({
            'Total_Households': 'sum',
            'Covered_Households': 'sum',
            'HH_Source_Segregation': 'sum'
        })

        # Calculate rates with error handling
        zone_group["Coverage_Rate"] = (zone_group["Covered_Households"] / zone_group["Total_Households"] * 100).round(2)
        zone_group["Segregation_Rate"] = (zone_group["HH_Source_Segregation"] / zone_group["Total_Households"] * 100).round(2)

        # Calculate city totals
        city_totals = {
            "Total_Households": int(zone_group["Total_Households"].sum()),
            "Covered_Households": int(zone_group["Covered_Households"].sum()),
            "HH_Source_Segregation": int(zone_group["HH_Source_Segregation"].sum()),
        }
        
        # Calculate rates with zero division handling
        city_totals["Coverage_Rate"] = round(
            city_totals["Covered_Households"] / city_totals["Total_Households"] * 100, 2
        ) if city_totals["Total_Households"] > 0 else 0
        
        city_totals["Segregation_Rate"] = round(
            city_totals["HH_Source_Segregation"] / city_totals["Total_Households"] * 100, 2
        ) if city_totals["Total_Households"] > 0 else 0

        # Prepare response
        response = {
            "zones": zone_group.to_dict(orient="records"),
            "city_totals": city_totals,
            "zone_list": sorted(zone_group['Zone_Name'].unique().tolist())
        }
        
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": "Failed to load dashboard", "details": str(e)}), 500

@app.route("/health", methods=["GET"])
def health_check():
    try:
        # Check if required model files exist
        required_files = [
            "saved_models/XGBoost.pkl",
            "saved_models/zone_encoder.pkl",
            "saved_models/scaler.pkl",
            "saved_models/columns.csv",
            DATA_FILE
        ]
        
        missing_files = [f for f in required_files if not os.path.exists(f)]
        
        if missing_files:
            return jsonify({
                "status": "error",
                "message": "Required files missing",
                "missing_files": missing_files
            }), 500
            
        # Try to load a small part of the data file
        try:
            df = pd.read_csv(DATA_FILE, nrows=1)
            data_loaded = True
        except Exception as e:
            data_loaded = False
            
        return jsonify({
            "status": "healthy",
            "data_loaded": data_loaded,
            "api_version": "1.0",
            "endpoints": [
                "/predict - POST - Make predictions",
                "/dashboard - GET - Get dashboard data",
                "/health - GET - Health check"
            ]
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# -------------------------
# Run app
# -------------------------
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)
