import os
import numpy as np
import pandas as pd
from midas import midas


class AlgWrapper:
    algname_list = ['midas', 'sedanspot']

    def __init__(self, alg_name, input_file_path, output_file_path):
        self.alg_name = alg_name
        self.input_file_path = input_file_path
        self.output_file_path = output_file_path

    def run(self):
        if self.alg_name == 'midas':
            self.midas()
        if self.alg_name == 'sedanspot':
            self.sedanspot()

    def midas(self):
        data = pd.read_csv(
            self.input_file_path,
            names=['src', 'dst', 'timestamp'],
        )
        anomaly_score = midas(
            data,
            num_rows=2,
            num_buckets=769,
        )
        data['anomaly_score'] = anomaly_score
        data = data.dropna()
        data['anomaly_score'] = data[['anomaly_score']].apply(lambda x: (x - np.min(x)) * 10 / (np.max(x) - np.min(x)))
        np.savetxt(self.output_file_path, data, delimiter=',', fmt='%f')

    def sedanspot(self):
        cmd = 'SedanSpot.exe  --input {0} --sample-size 500 > {1}'.format(self.input_file_path, self.output_file_path)
        os.system(cmd)
        anomaly_score = pd.read_csv(
            self.output_file_path,
        )
        data = pd.read_csv(
            self.input_file_path,
            names=['src', 'dst', 'timestamp'],
        )
        data['anomaly_score'] = anomaly_score
        data = data.dropna()
        data['anomaly_score'] = data[['anomaly_score']].apply(lambda x: (x - np.min(x)) * 10 / (np.max(x) - np.min(x)))
        np.savetxt(self.output_file_path, data, delimiter=',', fmt='%f')
