import os
import sys
import glob
import json
import numpy as np
import pandas as pd
import pickle
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from sklearn.manifold import TSNE


def countAnomalyStats(files, fname):
    f1 = "{}_stats.xlsx".format(fname)
    f2 = str(fname) + '_x_axis.txt'

    if os.path.exists(f1) and os.path.exists(f2):
        return

    df = pd.DataFrame(columns=['ts', 'stream_id', 'key', 'app', 'rank',
                               'accumulate',
                               'count', 'kurtosis', 'maximum', 'mean',
                               'minimum', 'skewness', 'stddev'])
    x_axis = {}
    for filename in files:
        print("File {} out of {} files.".format(filename, max(ids)))
        with open(filename) as f:
            loaded = json.load(f)
            anomaly_stats = loaded.get('anomaly_stats', None)
            counter_stats = loaded.get('counter_stats', None)

            if anomaly_stats is None:
                continue

            stream_id = int(filename.split('_')[-1][:-5])
            x_axis[stream_id] = 1
            ts = anomaly_stats.get('created_at', None)
            anomaly_array = anomaly_stats.get('anomaly', None)
            for item in anomaly_array:
                # {key, data, stats} in this stream step
                # make sure not all data items are zero n_anomalies
                flag_data = False
                for item_data in item['data']:
                    if item_data['n_anomalies'] != 0:
                        flag_data = True
                        break
                if not flag_data:  # all data items are zero
                    continue

                d = {'ts': datetime.fromtimestamp(ts/1000),  # in ms
                     'stream_id': int(stream_id),
                     'key': item['key'],
                     'app': int(item['key'].split(':')[0]),
                     'rank': int(item['key'].split(':')[1]),
                     'accumulate': int(item['stats']['accumulate']),
                     'count': int(item['stats']['count']),
                     'kurtosis': float(item['stats']['kurtosis']),
                     'maximum': int(item['stats']['maximum']),
                     'mean': float(item['stats']['mean']),
                     'minimum': int(item['stats']['minimum']),
                     'skewness': float(item['stats']['skewness']),
                     'stddev': float(item['stats']['stddev'])
                     }
                df = df.append(d, ignore_index=True)

    x_axis = sorted([_ for _ in x_axis.keys()])

    df.to_excel("{}_stats.xlsx".format(fname))
    with open(str(fname) + '_x_axis.txt', 'wb') as fp:
        pickle.dump(x_axis, fp)


def visAnomalyStats(fname, attr):
    with open(str(fname) + '_x_axis.txt', 'rb') as fp:
        x_axis = pickle.load(fp)

    df = pd.read_excel("{}_stats.xlsx".format(fname), index_col=0)
    fig = go.Figure(data=go.Scatter(
                        x=df['stream_id'],
                        y=df['rank'],
                        mode='markers',
                        marker=dict(
                            color=df[attr].to_numpy(dtype=float),
                            showscale=True,
                        ),
                        text=df[attr]))  # hover text goes here

    fig.update_layout(title='data: {}, attr: {}'.format(
                        fname, attr))
    fig.update_xaxes(type='category', categoryorder='array',
                     categoryarray=x_axis)
    fig.show()

    y_axis = [_ for _ in range(df['rank'].min(), df['rank'].max()+1)]
    fig = go.Figure(data=go.Heatmap(
                   z=df[attr].to_numpy(dtype=float),
                   x=df['stream_id'],
                   y=df['rank'],
                   hoverongaps=False
                   ))
    fig.update_layout(title='data: {}, attr: {}'.format(
                        pre.split('/')[-1], attr))
    fig.update_xaxes(type='category', categoryorder='array',
                     categoryarray=x_axis)
    # fig.update_yaxes(type='category', categoryorder='array',
    #                  categoryarray=y_axis)
    fig.show()


def countAnomalyData(files, fname):
    '''For all the stream files, count the overall anomalies
    and form the global anomaly table:
    (stream_i, key_j, step_k, n_anomalies, min_ts, max_ts)
    '''
    if os.path.exists("{}_data.xlsx".format(fname)):
        return

    df = pd.DataFrame(columns=['stream_id', 'app', 'rank', 'step',
                               'n_anomalies'])
    for filename in files:
        print("File {} out of {} files.".format(filename, len(files)))
        with open(filename) as f:
            loaded = json.load(f)
            anomaly_stats = loaded.get('anomaly_stats', None)
            counter_stats = loaded.get('counter_stats', None)

            if anomaly_stats is None:
                continue

            stream_id = int(filename.split('_')[-1][:-5])
            ts = anomaly_stats.get('created_at', None)
            anomaly_array = anomaly_stats.get('anomaly', None)
            for anomaly in anomaly_array:
                for item in anomaly['data']:
                    if item['n_anomalies'] == 0:
                        continue

                    d = {'stream_id': stream_id,
                         'app': item['app'],
                         'rank': item['rank'],
                         'step': item['step'],
                         'n_anomalies': item['n_anomalies']
                         }
                    df = df.append(d, ignore_index=True)
    df.to_excel("{}_data.xlsx".format(fname))


def visAnomalyData(fname, attr):
    df = pd.read_excel("{}_data.xlsx".format(fname), index_col=0)

    attr = 'n_anomalies'
    x_axis = [_ for _ in range(df['step'].max())]
    fig = go.Figure(data=go.Heatmap(
                   z=df[attr].to_numpy(dtype=int),
                   x=df['step'],
                   y=df['rank'],
                   hoverongaps=False
                   ))
    fig.update_layout(title='data: {}, attr: {}'.format(
                        pre.split('/')[-1], attr))
    fig.update_xaxes(type='category', categoryorder='array',
                     categoryarray=x_axis)
    fig.show()


def calcTSNE(files, n_rank):
    '''For all the stream files, prepare the numpy matrix
    (n_samples, n_iosteps) and apply dimension reduction
    '''
    data = [[] for _ in range(n_rank)]
    for filename in files:
        # print("File {} out of {} files.".format(filename, len(files)))
        with open(filename) as f:
            loaded = json.load(f)
            anomaly_stats = loaded.get('anomaly_stats', None)

            if anomaly_stats is None:
                continue

            stream_id = int(filename.split('_')[-1][:-5])
            ts = anomaly_stats.get('created_at', None)
            anomaly_array = anomaly_stats.get('anomaly', None)
            for anomaly in anomaly_array:
                for item in anomaly['data']:
                    data[int(item['rank'])].append(item['n_anomalies'])
    data = np.array(data)
    print("Done data preparation...")
    init = 'random'
    for i in range(5):  # n_iostep
        tsne = TSNE(n_components=2)  # , init=init)
        features = data[:, i:i+1]
        df = pd.DataFrame(features, columns=['step'])
        projections = tsne.fit_transform(df)
        # init = projections

        fig = px.scatter(projections, x=0, y=1,
                         color=df.index, labels={'color': 'rank'}
                         )
        fig.show()


def calcMockUp(files):
    '''For all the stream files, prepare the numpy matrix
    (n_samples, n_iosteps) and apply dimension reduction
    '''
    data = []
    for id, filename in enumerate(files):
        with open(filename) as f:
            loaded = json.load(f)
            anomaly_stats = loaded.get('anomaly_stats', None)

            if anomaly_stats is None:
                continue

            data.append([])
            # stream_id = int(filename.split('_')[-1][:-5])
            ts = anomaly_stats.get('created_at', None)
            anomaly_array = anomaly_stats.get('anomaly', None)
            for anomaly in anomaly_array:  # by rank
                for item in anomaly['data']:
                    item['timestamp'] = ts
                    data[-1].append(item)
    print("Done data preparation...")

    all_df = pd.DataFrame(columns=['stream', 'rank', 'app',
                                   'min_timestamp', 'max_timestamp',
                                   'n_anomalies', 'timestamp',
                                   'stat_id', 'step'])
    for i, ranks in enumerate(data):
        print('Stream:', i)
        df = pd.DataFrame(ranks)
        df['stream'] = np.zeros(df['n_anomalies'].shape) + i
        all_df = all_df.append(df, ignore_index=True)

    fig = px.scatter(all_df, x='rank', y='n_anomalies',
                     color=all_df['timestamp'].to_numpy(dtype=int),
                     size=all_df['n_anomalies'].to_numpy(dtype=float),
                    #  color_continuous_scale='balance',
                     hover_name='n_anomalies',
                     labels={'color': 'timestamp'}
                     )
    fig.show()

    fig = px.scatter(all_df, x='rank', y='n_anomalies',
                     animation_frame='stream',
                     animation_group='rank',
                     color=all_df['rank'].to_numpy(dtype=int),
                     size=all_df['n_anomalies'].to_numpy(dtype=int),
                     range_y=[0, 65],
                    #  color_continuous_scale='balance',
                     labels={'color': 'rank'}
                     )
    fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1500
    fig.show()

    # Show t-SNE results
    # all_df = pd.DataFrame(columns=['x', 'y', 'stream', 'rank', 'app',
    #                                'min_timestamp', 'max_timestamp',
    #                                'n_anomalies', 'timestamp',
    #                                'stat_id', 'step'])
    # for i, ranks in enumerate(data):
    #     print('Stream:', i)
    #     df = pd.DataFrame(ranks)
    #     # 1. Using t-SNE to change 1D to 2D projection
    #     features = df.loc[:, ['n_anomalies']].to_numpy() \
    #         .reshape(-1, 1)  # for single feature case
    #     tsne = TSNE(n_components=2)
    #     projections = tsne.fit_transform(features)
    #     df['x'] = projections[:, 0]
    #     df['y'] = projections[:, 1]
    #     df['stream'] = np.zeros(projections[:, 0].shape) + i
    #     all_df = all_df.append(df, ignore_index=True)

    # Show scatter plot of streams
    # In each stream plot, scatter plot of all ranks
    # fig = px.scatter(all_df, x='x', y='y',
    #                  animation_frame='stream',
    #                 #  animation_group='stream',
    #                  color=all_df['rank'].to_numpy(dtype=int),
    #                  size=all_df['n_anomalies'].to_numpy(dtype=int),
    #                  hover_name='stat_id',
    #                  color_continuous_scale='balance',
    #                  labels={'color': 'rank'})
    # fig.show()


if __name__ == '__main__':
    argc = len(sys.argv)
    if (argc < 2):
        pre = os.path.join(os.getcwd(), '../../data/hbos_results')
    else:
        pre = sys.argv[1]

    ###### 1. Prepare files ######
    path = pre + '/stats/'
    json_files = glob.glob(path + '*.json')
    # extract number as index
    ids = [int(f.split('_')[-1][:-5]) for f in json_files]
    # sort as numeric values
    inds = sorted(range(len(ids)), key=lambda k: ids[k])
    files = [json_files[i] for i in inds]  # files in correct order
    fname = pre.split('/')[-1]

    ###### 2. Count stats info per stream ######
    countAnomalyStats(files, fname)
    visAnomalyStats(fname, 'mean')

    ###### 3. Count data info per stream and step ######
    countAnomalyData(files, fname)
    visAnomalyData(fname, 'n_anomalies')

    # calcTSNE(files, int(pre.split('/')[-1][:2]))
    
    calcMockUp(files)
