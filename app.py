from flask import Flask, request, render_template, send_file
import pandas as pd
from sklearn.feature_selection import VarianceThreshold
import subprocess
import os
import base64
import pickle
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure static folders exist
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('static/images', exist_ok=True)

# Molecular descriptor calculator
def desc_calc():
    bashCommand = "java -Xms2G -Xmx2G -Djava.awt.headless=true -jar ./PaDEL-Descriptor/PaDEL-Descriptor.jar -removesalt -standardizenitro -fingerprints -descriptortypes ./PaDEL-Descriptor/PubchemFingerprinter.xml -dir ./ -file descriptors_output.csv"
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    os.remove('molecule.smi')

# File download
def filedownload(df):
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'prediction.csv')
    df.to_csv(output_path, index=False)
    return output_path

# Model building
def build_model(input_data):
    load_model = pickle.load(open('cckA_gpr_model.pkl', 'rb'))
    prediction = load_model.predict(input_data)
    prediction_output = pd.Series(prediction, name='pIC50')
    molecule_name = pd.Series(input_data.index, name='molecule_name')
    df = pd.concat([molecule_name, prediction_output], axis=1)
    return df

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('index.html', error='No file uploaded')
        file = request.files['file']
        if file.filename == '':
            return render_template('index.html', error='No selected file')
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        load_data = pd.read_table(file_path, sep=' ', header=None)
        load_data.to_csv('molecule.smi', sep='\t', header=False, index=False)
        
        desc_calc()
        
        desc = pd.read_csv('descriptors_output.csv')
        Xlist = list(pd.read_csv('descriptor_list_cckA.csv').columns)
        desc_subset = desc[Xlist]
        
        df = build_model(desc_subset)
        prediction_file = filedownload(df)
        
        return render_template('index.html', tables=[df.to_html(classes='data')], download_link=prediction_file)
    
    return render_template('index.html')

@app.route('/download')
def download_file():
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], 'prediction.csv'), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
