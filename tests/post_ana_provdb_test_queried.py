import sys
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

if __name__ == '__main__':
    argc = len(sys.argv)
    if (argc < 2):
        pre = os.path.join(os.getcwd(), '../../data')
    else:
        pre = sys.argv[1]

    # define which application
    which = 'XGC'

    fname = None
    df = None

    if which == 'NWCHEM':
        fname = pre + '/rank_all.xlsx'
    else:
        fname = pre + '/rank_all_xgc_48.xlsx'

    if os.path.exists(fname):
        df = pd.read_excel(fname)
    else:  # for HBOS NWCHEM only
        fname1 = pre + '/rank_all_1.xlsx'
        fname2 = pre + '/rank_all_2.xlsx'

        df1 = pd.read_excel(fname1, index_col=0)
        df2 = pd.read_excel(fname2, index_col=0)

        frames = [df1, df2]
        df = pd.concat(frames)
        df.to_excel(fname)

    if which == 'NWCHEM':
        # fig = px.bar(df['func'].value_counts())
        # fig.update_layout(title="NWCHEM")
        # fig.show()

        # col = (df['io_step'] // 200 + 1) * 10  # need to change the setting
        # fig = px.scatter(df, x="rid", y="runtime_total", color="func",
        #                  size=col, hover_data=['io_step'],
        #                  marginal_x='histogram', marginal_y='histogram',
        #                  )
        # fig.update_layout(title='NWCHEM with HBOS')
        # fig.show()

        fig = px.parallel_coordinates(df, color="fid",
                                      dimensions=["fid", "rid", "io_step",
                                                  "runtime_total",
                                                  "runtime_exclusive"],
                                      color_continuous_scale=px.colors.
                                                diverging.Tealrose,
                                      title="NWCHEM with HBOS")
        fig.show()
    else:
        # s1 = df.query("is_gpu_event == False",
        #               inplace=False)['func'].value_counts()
        # s2 = df.query("is_gpu_event == True",
        #               inplace=False)['func'].value_counts()
        # fig = go.Figure(data=[
        #         go.Bar(name='CPU', x=s1.index, y=s1),
        #         go.Bar(name='GPU', x=s2.index, y=s2)
        #     ])
        # fig.update_layout(barmode='group', margin_b=200, margin_r=100,
        #                   margin_autoexpand=False)
        # fig.update_layout(title='XGC 48-rank')
        # fig.show()

        # df['is_gpu_event'] = df['is_gpu_event'].astype('int32') * 20 + 10
        # fig = px.scatter(df, x="rid", y="runtime_total", color="fid",
        #                  size='is_gpu_event', hover_data=['func', 'io_step'],
        #                  marginal_x='histogram', marginal_y='histogram')
        # fig.update_layout(title='XGC 48-rank')
        # fig.show()

        df['is_gpu_event'] = df['is_gpu_event'].astype('int32')
        fig = px.parallel_coordinates(df, color="rid",
                                      dimensions=["fid", "rid", "io_step",
                                                  "runtime_total",
                                                  "runtime_exclusive",
                                                  "is_gpu_event"],
                                      color_continuous_scale=px.colors.
                                      diverging.Tealrose,
                                      title="XGC 48 Ranks")
        fig.show()
