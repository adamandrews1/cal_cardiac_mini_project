import scipy as sci
import wfdb
import os
import json


class ParseArrhythmiaSignals(object):
    """This class reads and processes ECG signals from MIT-BIH Arrhythmia dataset and labels into batches.

    Data batches account for class imbalance (most heartbeats are normal) by a parameter alpha between 0 and 1. 
    Each batch consists of an approximate proportion (alpha) of positive samples.

    The data batches are windows centered around beat annotations. The size of the window is controlled by the
    window_size parameter"""
    def __init__(self, window_size, record_num):
        """For each record number, there is a data sample with metadata, and an annotation. In aggregate, these
        are stored in the all_patients_data dict. The key is the record number, and the value is a pair or python
        objects for the data signals and annotations.
        """
        # Data Parameters
        self.data_dir = 'MIT-BIH/'
        
        self.record_numbers = set(map(lambda x: x.split('.')[0], os.listdir('MIT-BIH/')))
        self.all_patients_data = dict([(record_num, []) for record_num in self.record_numbers])

        # Model Parameters
        self.window_size = window_size

        self.alpha = 0.5

        self.read_all_records()
        
        self.active_record = record_num

    def read_all_records(self):
        """Aggregates data from all records into a [m,n,2] pseudoimage"""
        for r in self.record_numbers:
            self.read_single_record()

    def read_single_record(self):
        """Updates the records dictionary with data from a given record number. 
        The data_dir should contain the .atr, .dat, and .hea files."""
        try:
            sample = wfdb.rdsamp(self.data_dir + self.active_record)
            annot = wfdb.rdann(self.data_dir + self.active_record, 'atr')
        except ValueError:
            raise ValueError('Record not found') 

        # validation_index = sci.random.choice(range(len(annot.sample)))
        self.all_patients_data[str(self.active_record)] = (sample, annot)

    def get_data_obj(self):
        """Returns the data object for the given record."""
        return self.all_patients_data[str(self.active_record)][0]

    def get_annot_obj(self):
        """Returns the data object for the given record."""
        return self.all_patients_data[str(self.active_record)][1]

    def generate_data_batch(self, n=100, channel=0):
        """Returns data batch of ECG signals centered on heartbeat. Default n=100, channel=1."""
        if not self.all_patients_data[str(self.active_record)]:
            print('Patient number ' + str(self.active_record) + 'has not been read')
            return
        else:
            ch = sci.array(self.get_data_obj(self.active_record).adc()[:, channel])
            idx = sci.array(self.get_annot_obj(self.active_record).sample)
            label = sci.array(self.get_annot_obj(self.active_record).symbol)

            pos_ind = sci.where(label != 'N')[0]
            neg_ind = sci.where(label == 'N')[0]

            # (label, window) kv pairs
            data = []
            k = 0
            while k < int(n/2):
                j = sci.random.choice(pos_ind)
                # Check that the image covers the window
                if not (int(idx[j]+self.window_size/2) < ch.size and int(idx[j]-self.window_size/2) > 0):
                    continue
                data.append((int(idx[j]), label[j],
                             [int(i) for i in ch[(int(idx[j]-self.window_size/2)):(int(idx[j]+self.window_size/2))]]))
                k += 1

            k = 0
            while k < int(n/2):
                j = sci.random.choice(neg_ind)
                # Check that the image covers the window
                if not (int(idx[j]+self.window_size/2) < ch.size and int(idx[j]-self.window_size/2) > 0):
                    continue
                data.append((int(idx[j]), label[j],
                             [int(i) for i in ch[(int(idx[j]-self.window_size/2)):(int(idx[j]+self.window_size/2))]]))
                k += 1

            return data
        
    def to_json(self, n=100, channel=0):
        """Return a sample of windows in JSON"""
        return json.dumps(self.generate_data_batch(self.active_record, n, channel))
