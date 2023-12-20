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
        const { labels:labels, new_series:new_series, all_series:all_series } = chartData;
        let { labels:labelsState, newData:newDataState, allData:allDataState } = this.state;

        if (new_series.length === 0)
            return;

        console.log('before:' + newDataState);

        newDataState.length = 0;
        allDataState.length = 0;
        labelsState.length = 0;

        newDataState = [...new_series];
        allDataState = [...all_series];
        labelsState = [...labels];

        console.log('after:' + newDataState);

        this.setState({...this.state, labels:labelsState, newData:newDataState, allData:allDataState});
    }

    render() {
        const { height } = this.props;
        const { labels:labels, newData:newData, allData:allData, colors:colors } = this.state;

        const info = [];
        const datasets = [];
        
        newData.forEach((d, i) => {
            const rgb = i<colors.length?colors[i]:getRandomColor();
            if (i >= colors.length) {
                colors.push(rgb);
            }

            datasets.push({
                label: `${d.fid}`,
                data: d,
                backgroundColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.2)`,
                borderColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 1)`,
                borderWidth: 1,
                hoverBackgroundColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.4)`,
                hoverBorderColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 1)`,        
            });
            info.push(`${d.fname}`);
        });

        const _data = {
            labels: labels,
            datasets: datasets,
        };
        
        this.setState({...this.state, colors:colors});

        console.log(_data);

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
                            }
                        }
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
