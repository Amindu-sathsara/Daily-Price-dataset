# api.py
from flask import Flask, request, jsonify
from predict import predict_price

app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    date = data.get('date')
    market = data.get('market')
    crop = data.get('crop')
    
    if not all([date, market, crop]):
        return jsonify({'error': 'Missing parameters. Provide date, market, crop'}), 400
    
    try:
        price = predict_price(date, market, crop)
        return jsonify({
            'date': date,
            'market': market,
            'crop': crop,
            'predicted_price_rs_per_kg': round(price, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)