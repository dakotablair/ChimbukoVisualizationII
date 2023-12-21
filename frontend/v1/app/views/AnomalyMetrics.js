import React from 'react';
import PropTypes from 'prop-types';

import { Radar } from 'react-chartjs-2';

import { getRandomColor } from '../utils'

class AnomalyMetrics extends React.Component
{
    constructor(props) {
        super(props);
        this.state = { // variables kept as state
            labels: [],
            newData: [],
            allData: [],
            colors: [],
        };
        this.socketio = props.socketio;
        this.pause = false;
    }

    componentDidMount() {
        this.register_io();
    }

    register_io = () => {
        if (this.socketio) {
            this.socketio.on('update_metrics', data => {
                this.updateChartData(data);
            });
        }
    }

    updateChartData = chartData => {
        if (this.pause)
           return;

        const { labels, new_series, all_series } = chartData; //destructuring assignment
        let { labels:labelsState, newData:newDataState, allData:allDataState, colors:colorsState } = this.state; //assign a property to a new name

        if (new_series.length === 0)
            return;

        // console.log('before:' + newDataState);

        newDataState.length = 0;
        allDataState.length = 0;
        labelsState.length = 0;

        newDataState = [...new_series];
        allDataState = [...all_series];
        labelsState = [...labels];
        
        let num = newDataState.length - colorsState.length;
        for (let index = 0; index < num; index++) {
            const rgb = getRandomColor();
            colorsState.push(rgb);
        }

        // console.log('after:' + newDataState);

        this.setState({...this.state, labels:labelsState, newData:newDataState, allData:allDataState, colors:colorsState});
    }

    shouldComponentUpdate(nextProps, nextState) {
        // console.log("test pause update");

        const { pause } = nextProps;
        this.pause = pause
        if (this.chart) {
            if (pause)
                return false;
            else
                return true;
        }
        return false;
    }

    handleSwitch = name => ev => {
        this.setState({...this.state, [name]: ev.target.checked});
    }

    render() {
        const { height } = this.props;
        const { labels:labels, newData:newData, allData:allData, colors:colors } = this.state;

        const info = [];
        const datasets = [];
        
        newData.forEach((d, i) => {
            const rgb = colors[i];
            datasets.push({
                label: `${d[2]}`, //fid
                data: d.slice(0, 6), // (app, rank, fid, s, s, c)
                backgroundColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.2)`,
                borderColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 1)`,
                borderWidth: 1,
                hoverBackgroundColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.4)`,
                hoverBorderColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 1)`,        
            });
            info.push(`${d[6]}`); //fname
        });

        const _data = {
            labels: labels.length>0?labels.slice(0, 6):['app', 'rank', 'fid', 'severity', 'score', 'count'],
            datasets: datasets.length>0?datasets:[],
        };

        // console.log(_data);

        return (
            <Radar 
                ref={ref => this.chart = ref}
                data={_data} //
                height={height}
                options={{
                    maintainAspectRatio: false,
                    tooltips: {
                        callbacks: {
                            title: (tooltipItem, data) => {
                                    // datasetIndex is the index in datasets
                                    // index is the index of labels
                                    const datasetIndex = tooltipItem[0].datasetIndex;
                                    const index = tooltipItem[0].index;
                                    
                                    return `${info[datasetIndex]}`;
                            },
                            label: (tooltipItem, data) => {
                                const datasetIndex = tooltipItem.datasetIndex;
                                const index = tooltipItem.index;
                                var label = 'fid-' + data.datasets[datasetIndex].label + ': ';
                                label += data.labels[index] + '-';
                                label += tooltipItem.yLabel;

                                return label;
                            }
                        }
                    },
                    scale: { // do not show tick
                        ticks: {
                             callback: function() {return ""},
                             backdropColor: "rgba(0, 0, 0, 0)"
                         }
                    },
                    legend: {
                        display: true,
                        position: 'bottom',
                        fullWidth: false
                    }
                }}
            />
        );
    }
}

AnomalyMetrics.defaultProps = {
    height: 100,
};

AnomalyMetrics.propTypes = {
    width: PropTypes.number,
    height: PropTypes.number.isRequired,
};

export default AnomalyMetrics;
