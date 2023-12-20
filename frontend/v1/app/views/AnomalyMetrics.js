import React from 'react';
import PropTypes from 'prop-types';

import { Radar } from 'react-chartjs-2';

import { getRandomColor } from '../utils'

class AnomalyMetrics extends React.Component
{
    constructor(props) {
        super(props);
        this.state = { // variables kept as state
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
        const { labels, new_series, all_series } = chartData;
        let { newData, allData } = this.state;

        if (new_series.length === 0)
            return;

        console.log('before:' + newData);

        newData.length = 0;
        allData.length = 0;
        newData = [...new_series];
        allData = [...all_series];

        console.log('after:' + newData);

        this.setState({...this.state, newData, allData});
    }

    render() {
        const { height } = this.props;
        const { newData, allData, colors } = this.state;

        const info = [];
        const radarData = [];
        let maxLen = 0;
        /*
        newData.forEach((d, i) => {
            const rgb = i<colors.length?colors[i]:getRandomColor();
            radarData.push({
                    label: category.name,
                    data: category.stat.map(d => d[2]),
                    backgroundColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.2)`, // const color = 
                    borderColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 1)`,
                    borderWidth: 1,
                    hoverBackgroundColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.4)`,
                    hoverBorderColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 1)`,        
                });
                info.push(category.stat.map(d => `${d[0]}:${d[1]}`));
            }
            else { // funcitons
                lineData.push({
                    label: category.name,
                    data: category.stat.map(d => d[3]),
                    backgroundColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.2)`,
                    borderColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 1)`,
                    borderWidth: 1,
                    hoverBackgroundColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.4)`,
                    hoverBorderColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 1)`,        
                });
                info.push(category.stat.map(d => `${d[0]}:${d[1]}:${d[2]}`));
            }

            if (category.stat.length > maxLen)
                maxLen = category.stat.length;
        });
        */
        const _data = {
            labels: ['app', 'rank', 'severity'], //labels,
            datasets: [{data: [0, 10, 1]}, {data:[1, 2, 10]}, {data:[1, 3, 20]}] // radarData
        };
        //------------
        
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
                                console.log(tooltipItem);
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
