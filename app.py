from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import pickle
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Use a strong secret key in production

# Initialize SQLite3 database
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Create a table for users if it doesn't already exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template('home.html')

# Decorator to ensure user is logged in
def login_required(route_function):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return route_function(*args, **kwargs)
    wrapper.__name__ = route_function.__name__
    return wrapper

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            with sqlite3.connect('users.db') as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
                conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return 'Username already exists. Please choose another one.'
        except sqlite3.OperationalError as e:
            return f'Database error: {e}'
    return render_template('signup.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Verify user credentials
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]  # Store user ID in session
            return redirect(url_for('predict'))
        else:
            return 'Invalid username or password'
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user ID from session
    return redirect(url_for('home'))

def predict_loan_approval(income_annum,no_of_dependents, education, self_employed,loan_amount, loan_term, cibil_score, residential_assets_value, commercial_assets_value,luxury_assets_value, bank_asset_value):
    with open('DT.pkl', 'rb') as model_file:
            model = pickle.load(model_file)
    new_data = {
        'income_annum': income_annum,
        'no_of_dependents': no_of_dependents,
        'education': education,
        'self_employed': self_employed,
        'loan_amount': loan_amount,
        'loan_term': loan_term,
        'cibil_score': cibil_score,
        'residential_assets_value': residential_assets_value,
        'commercial_assets_value': commercial_assets_value,
        'luxury_assets_value': luxury_assets_value,
        'bank_asset_value': bank_asset_value
    }

    # Convert to DataFrame
    new_df = pd.DataFrame([new_data])

    # Ensure columns match model training data
    prediction_result = model.predict(new_df)
    
    return prediction_result[0]

# Prediction route
@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    if request.method == 'POST':
        income_annum = float(request.form['income_annum'])
        no_of_dependents = int(request.form['no_of_dependents'])
        education = request.form['education']
        self_employed = request.form['self_employed']
        loan_amount = float(request.form['loan_amount'])
        loan_term = int(request.form['loan_term'])
        cibil_score = int(request.form['cibil_score'])
        residential_assets_value = float(request.form['residential_assets_value'])
        commercial_assets_value = float(request.form['commercial_assets_value'])
        luxury_assets_value = float(request.form['luxury_assets_value'])
        bank_asset_value = float(request.form['bank_asset_value'])

        # Predict loan approval
        prediction_result = predict_loan_approval(income_annum,no_of_dependents, education, self_employed,loan_amount, loan_term, cibil_score, residential_assets_value, commercial_assets_value,luxury_assets_value, bank_asset_value)
        print(prediction_result)
        return render_template('result.html', prediction=prediction_result)

    return render_template('predict.html')


if __name__ == '__main__':
    init_db() 
    app.run(debug=True)
