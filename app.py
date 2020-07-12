import json
import os
from flask import Flask, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np
from alg_wrapper import AlgWrapper

UPLOAD_FOLDER = './uploads'
RESULTS_FOLDER = './results'
NEO4J_FOLDER = 'C:/Users/olin/neo4j-community-4.0.4/import'
ALLOWED_EXTENSIONS = {'txt', 'csv'}

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['NEO4J_FOLDER'] = NEO4J_FOLDER
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


@app.route('/run', methods=['POST'])
def run():
    result = {'code': '0', 'errorMsg': '', 'data': ''}
    alg_name = request.form.get("alg_name", type=str, default=None)
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
        prefix = str(filename).split('.')[0]
        score_filename = prefix + '_scores.csv'

        alg_wrapper = AlgWrapper(alg_name, os.path.join(app.config['UPLOAD_FOLDER'], filename),
                                 os.path.join(app.config['RESULTS_FOLDER'], score_filename))
        alg_wrapper.run()

        result['data'] = score_filename
        return json.dumps(result)


@app.route('/download/<score_filename>')
def download_score_file(score_filename):
    return send_from_directory(app.config['RESULTS_FOLDER'],
                               score_filename)


@app.route('/result/<score_filename>')
def get_result(score_filename):
    # timestamp = request.args.get("timestamp")
    df = pd.read_csv(os.path.join(app.config['RESULTS_FOLDER'], score_filename), header=None, sep=',')
    quantile = df[3].quantile(q=0.9)
    # 进行采样，防止前端显示卡顿
    df = df.sample(n=300, replace=True)
    source_nodes = df[0]
    target_nodes = df[1]
    df = df.values
    node_list = np.append(source_nodes.values, target_nodes.values)
    node_list = np.unique(node_list)
    node_json = []
    for node in node_list:
        node_json.append(
            {'id': str(int(node)),
             'label': str(int(node))}
        )
    edge_json = []
    for edge in df:
        color = '#808080'
        if edge[3] > quantile:
            color = '#ff0000'
        edge_json.append(
            {'source': str(int(edge[0])),
             'target': str(int(edge[1])),
             'style': {
                 'stroke': color,
                 'lineWidth': str(edge[3]),
             }})
    return json.dumps({'nodes': node_json, 'edges': edge_json})

if __name__ == '__main__':
    app.run()
