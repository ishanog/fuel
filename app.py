from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os

app = Flask(__name__)
file_path = os.path.join(os.path.dirname(__file__), 'data.xlsx')

# Create Excel file if it does not exist
if not os.path.exists(file_path):
    df = pd.DataFrame(columns=['ID','Date','Odometer','FuelAdded','Cost','FullTank'])
    df.to_excel(file_path, index=False)

def load_data():
    df = pd.read_excel(file_path)
    if 'ID' not in df.columns:
        df['ID'] = range(1, len(df)+1)
    return df

def save_data(df):
    temp_file = os.path.join(os.path.dirname(__file__), 'data_temp.xlsx')
    df.to_excel(temp_file, index=False)
    os.replace(temp_file, file_path)

@app.route('/', methods=['GET', 'POST'])
def index():
    df = load_data()

    if request.method == 'POST':
        date = request.form['date']
        odo = float(request.form['odo'])
        fuel = float(request.form['fuel'])
        price = float(request.form['price'])  # Current fuel price per liter
        full_tank = request.form.get('full_tank', 'Yes')  # default Yes

        cost = fuel * price  # auto calculate total cost

        new_id = df['ID'].max() + 1 if not df.empty else 1

        new_row = pd.DataFrame([{
            'ID': new_id,
            'Date': date,
            'Odometer': odo,
            'FuelAdded': fuel,
            'Cost': round(cost,0),
            'FullTank': full_tank
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        save_data(df)
        return redirect(url_for('index'))

    charts = prepare_charts(df)
    return render_template('index.html', data=df.to_dict(orient='records'), charts=charts)

@app.route('/delete/<int:record_id>')
def delete_record(record_id):
    df = load_data()
    if 'ID' in df.columns:
        df = df[df['ID'] != record_id]
        save_data(df)
    return redirect(url_for('index'))

def prepare_charts(df):
    charts = {
        'fuel_labels': [],
        'fuel_values': [],
        'mileage_labels': [],
        'mileage_values': []
    }

    if df.empty:
        return charts

    df['Month'] = pd.to_datetime(df['Date']).dt.to_period('M')

    # Monthly fuel
    monthly_fuel = df.groupby('Month')['FuelAdded'].sum().reset_index()
    charts['fuel_labels'] = [str(m) for m in monthly_fuel['Month']]
    charts['fuel_values'] = monthly_fuel['FuelAdded'].tolist()

    # Mileage
    df = df.sort_values('Date')
    df['Distance'] = df['Odometer'].diff().fillna(0)
    df['Mileage'] = df['Distance'] / df['FuelAdded']
    monthly_mileage = df.groupby('Month')['Mileage'].mean().reset_index()
    charts['mileage_labels'] = [str(m) for m in monthly_mileage['Month']]
    charts['mileage_values'] = monthly_mileage['Mileage'].tolist()

    return charts

if __name__ == '__main__':
    app.run(debug=True)
