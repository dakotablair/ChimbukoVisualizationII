import React from 'react';
import PropTypes from 'prop-types';
import axios from 'axios';

import { Chart } from 'react-chartjs-2';
import 'chartjs-plugin-streaming';

import moment from 'moment';


class AnomalyHistory extends React.Component
{
    constructor(props) {
        super(props);
        this.state = {
            //pause: false
        };
        this.socketio = props.socketio;
        this.chartRef = React.createRef();
        this.chart = null;
        this.chartData = {};
        this.pause = false;
    }

    componentDidMount() {
        this.bulidChart();
        this.register_io();
    }

    register_io = () => {
        if (this.socketio) {
            this.socketio.on('update_history', data => {
                this.updateChartData(data);
            });
        }
    }

    updateChartData = chartData => {
        if (chartData.length === 0)
            return;

        const { ranks } = this.props;
        let minTime = Infinity;

        // get min_timestamp in the currently available data
        Object.keys(this.chartData).forEach(rank => {
            rank = +rank;
            if (this.chartData[rank].length > 0 && this.chartData[rank][0].min_timestamp > 0)
                minTime = Math.min(minTime, this.chartData[rank][0].min_timestamp);
        });

        //console.log(minTime);
        chartData.forEach(d => {
            let {rank, min_timestamp} = d;
            rank = +rank;
            if (ranks.indexOf(rank) >= 0 && (minTime === Infinity || min_timestamp >= minTime))
            {
                if (!this.chartData.hasOwnProperty(rank))
                    this.chartData[rank] = [];
                this.chartData[rank].push({...d});
            }
        });

        // append with empty slot to aling data
        minTime = Infinity;
        Object.keys(this.chartData).forEach(rank => {
            rank = +rank;
            if (ranks.indexOf(rank) >=0 && this.chartData[rank].length > 0)
                console.log(...this.chartData[rank][0])
            if (ranks.indexOf(rank) >= 0 && this.chartData[rank].length > 0 && this.chartData[rank][0].min_timestamp > 0) {
                minTime = Math.min(minTime, this.chartData[rank][0].min_timestamp);
            }
        });

        if (minTime < Infinity) {
            const empty = {
                n_anomalies: 0,
                min_timestamp: -1,
                max_timestamp: -1,
                step: -1
            };
            Object.keys(this.chartData).forEach(rank => {
                rank = +rank;
                const first = this.chartData[rank][0].min_timestamp;
                if (ranks.indexOf(rank) >= 0 && first > 0) {
                    const n_empty = Math.floor((first - minTime) / 1000000);
                    //console.log('rank: ', rank, ' n_empty: ', n_empty, ' first: ', first)
                    if (n_empty > 0) {
                        // console.log(n_empty, first, minTime)
                        this.chartData[rank].unshift(...Array(n_empty).fill(0).map(_=>empty));
                    }
                }
            });        
        }

    }

    tooltips_afterBody = (tooltipItem, data) => {
        const datasetIndex = tooltipItem[0].datasetIndex;
        const index = tooltipItem[0].index;
        const item = data.datasets[datasetIndex].data[index];
        let {step, min_timestamp, max_timestamp, n_anomalies} = item;
        const duration = Number.parseFloat((max_timestamp - min_timestamp) / 1000).toFixed(3);
        min_timestamp = moment(min_timestamp/1000).format('h:mm:ss.SSS a');
        max_timestamp = moment(max_timestamp/1000).format('h:mm:ss.SSS a');
        
        return `# anomalies: ${n_anomalies}\nstep: ${step}\nmin_ts: ${min_timestamp}\nmax_ts: ${max_timestamp}\nduration: ${duration} msec`;
    }

    bulidChart = () => {
        const { height: _height } = this.props;
        const _data = {datasets: []};
        if (this.chart == null) {
            this.chart = new Chart(this.chartRef.current.getContext("2d"), 
            {
                type: "bubble",
                data: _data,
                height: _height,
                options: {
                    maintainAspectRatio: false,
                    scales: {
                        xAxes: [{
                            type: 'realtime',
                            realtime: {
                                duration: 60000,
                                refresh: 1000,
                                delay: 1000,
                                onRefresh: this.onChartRefresh
                            }
                        }],
                        yAxes: [{
                            scaleLabel: {
                                display: true,
                                labelString: '# Anomalies'
                            }
                        }]
                    },
                    tooltips: {
                        mode: 'nearest',
                        intersect: false,
                        callbacks: {
                            afterBody: this.tooltips_afterBody
                        }
                    },
                    hover: {
                        mode: 'nearest',
                        intersect: false
                    },
                    legend: {
                        onClick: this.onLegendClick
                    }
                }
            });
        }
    }

    onChartRefresh = (chart) => {
        const { ranks, colors } = this.props;

        // add datasets if necessary
        ranks.forEach(rank => {
            const label = `Rank-${rank}`;
            let datasetIndex = chart.data.datasets.findIndex(dataset => {
                return dataset.label === label;
            });
            if (datasetIndex == -1) {
                const {r, g, b} = colors[rank];
                chart.data.datasets.push({
                    data: [],
                    label: label,
                    borderColor: `rgb(${r}, ${g}, ${b})`,
                    backgroundColor: `rgba(${r}, ${g}, ${b}, 0.5)`,
                    borderWidth: 1
                });
            }
        });

        // remove dataset, if necessary
        // Note that there must be at least one to avoid error!!
        // this is ensured in onLegendClick callback function.
        if (ranks.length !== chart.data.datasets.length) {
            const datasetIndex = chart.data.datasets.findIndex(dataset => {
                return ranks.indexOf(dataset.label.split('-')[1]) < 0;
            });
            chart.data.datasets.splice(datasetIndex, 1);
            chart.update();
        }

        // add new data
        chart.data.datasets.forEach( (dataset, datasetIndex) => {
            const rank = parseInt(dataset.label.split('-')[1], 10);
            if (this.chartData.hasOwnProperty(rank) && this.chartData[rank].length) {
                const d = this.chartData[rank].shift();
                if (d && d.hasOwnProperty('n_anomalies'))
                    dataset.data.push({
                        x: Date.now(),
                        y: d.n_anomalies,
                        r: (d.n_anomalies > 0) ? 5: 0,
                        ...d
                    });
            }
        });
        chart.update({preservation: true});
    }

    onLegendClick = (e, legendItem) => {
        const { ranks } = this.props;
        const { text: label } = legendItem;
        const rank = parseInt(label.split('-')[1], 10);
        if (ranks.length > 1 && this.props.onLegendClick)
            this.props.onLegendClick(rank);
    }

    shouldComponentUpdate(nextProps, nextState) {
        const { pause } = nextProps;
        if (this.chart) {
            if (this.pause !== pause) {
                this.pause = pause;
                this.chart.options.plugins.streaming.pause = this.pause;
                this.chart.chart.update({duration: 0});
            }
        }
        return false;
    }

    handleSwitch = name => ev => {
        this.setState({...this.state, [name]: event.target.checked});
    }

    handleBarClick = ev => {
        if (this.chart) {
            const activePoint = this.chart.getElementAtEvent(ev);
            if (activePoint.length > 0) {
              const datasetIndex = activePoint[0]._datasetIndex;
              const index = activePoint[0]._index;
              const item = this.chart.data.datasets[datasetIndex].data[index];

              if (this.props.onBarClick)
                this.props.onBarClick(item);
            }            
        }
    }

    render() {
        return (
            <canvas 
                id="anomaly-history-chart"
                ref={this.chartRef}
                height={this.props.height}
                onClick={this.handleBarClick}
            />
        );
    }
}

AnomalyHistory.defaultProps = {
    height: 100,
    ranks: [],
    colors: {},
    onLegendClick: (_) => {},
    onBarClick: (pid, rid, min_ts, max_ts) => {}
};

AnomalyHistory.propTypes = {
    width: PropTypes.number,
    height: PropTypes.number.isRequired,
    ranks: PropTypes.array,
    colors: PropTypes.object,
    onLegendClick: PropTypes.func,
    onBarClick: PropTypes.func,
};

export default AnomalyHistory;
