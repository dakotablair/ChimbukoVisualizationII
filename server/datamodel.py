import os


class DataModel():
    def __init__(self):
        self.filter_run_stats = 'accumulate'  # RunStats fields
        self.filter_metrics = 'severity'  # metrics fields
        self.filter_num = 5  # number of top functions
        self.hist_bins = 11  # number of bins of the histogram
