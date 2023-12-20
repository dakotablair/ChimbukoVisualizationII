import React from 'react';
import PropTypes from 'prop-types';

import { Radar } from 'react-chartjs-2';

import { getRandomColor } from '../utils'

class AnomalyMetrics extends React.Component
{
    constructor(props) {
        super(props);
        this.state = {
            data: [],
            labels: [],
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
        // if (chartData.length === 0)
        //    return;

        console.log(chartData);

        //--------
        /*
        const { data:newData } = chartData;
        let { labels, data:dataState } = this.state;

        if (dataState.length == 0) {
            newData.forEach( (category, i) => {
                const color = 
                dataState.push({ // define as need in render function
                    'color': color[i],
                    'name': category.name,
                    'stat': []
                }); 
            });
        }

        newData.forEach((category, index) => {
            dataState[index].stat = category.stat;
        });

        //---------
        this.setState({...this.state, data: dataState, labels});
        */
    }

    render() {
        const { height } = this.props;
        const { data, labels } = this.state;

        //------------
        /*
        const info = [];
        const lineData = [];
        let maxLen = 0;
        data.forEach((category, index) => { // one category is one dataset
            const rgb = category.color;
            if (index == 0) { // ranks
                lineData.push({
                    label: category.name,
                    data: category.stat.map(d => d[2]),
                    backgroundColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.2)`,
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
            datasets: [[0, 10, 1], [1, 2, 10], [1, 3, 20]] // radarData
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
