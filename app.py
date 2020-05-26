import json
import os
from flask import Flask, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from midas import midas
import pandas as pd
import numpy as np

UPLOAD_FOLDER = './uploads'
RESULTS_FOLDER = './results'
ALLOWED_EXTENSIONS = {'txt', 'csv'}
app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 上传文件大小


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET'])
def index():
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/upload', methods=['POST'])
def upload_file():
    result = {'code': '0', 'errorMsg': '', 'data': ''}
    # check if the post request has the file part
    if 'file' not in request.files:
        result['code'] = '1'
        result['errorMsg'] = 'No file part'
        return json.dumps(result)
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        result['code'] = '1'
        result['errorMsg'] = 'No selected file'
        return json.dumps(result)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        data = pd.read_csv(
            os.path.join(app.config['UPLOAD_FOLDER'], filename),
            names=['src', 'dst', 'timestamp'],
        )
        anomaly_score = midas(
            data,
            num_rows=2,
            num_buckets=769,
        )
        prefix = str(filename).split('.')[0]
        score_filename = prefix + '_scores.result'
        np.savetxt(os.path.join(app.config['RESULTS_FOLDER'], score_filename), anomaly_score)
        result['data'] = score_filename
        return json.dumps(result)


@app.route('/download/<score_filename>')
def download_score_file(score_filename):
    return send_from_directory(app.config['RESULTS_FOLDER'],
                               score_filename)


if __name__ == '__main__':
    app.run()
