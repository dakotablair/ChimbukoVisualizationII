import React from 'react';
import PropTypes from 'prop-types';

import { Bar } from 'react-chartjs-2';

class AnomalyStats extends React.Component 
{
    constructor(props) {
        super(props);
        this.state = {
            data: [],
            colors: {}
        };

        this.socketio = props.socketio;
    }

    componentDidMount() {
        this.register_io();
    }

    register_io = () => {
        if (this.socketio) {
            this.socketio.on('update_stats', data => {
                this.updateChartData(data);
            });            
        }
    }

    updateChartData = chartData => {
        const { data:newData } = chartData;
        const { nQueries, statKind } = this.props;
        let { colors, data:dataState } = this.state;

        if (dataState.length === 0) {
            newData.forEach(category => {
                const getRandomColor = () => {
                    return {
                        r: Math.floor(Math.random() * 255),
                        g: Math.floor(Math.random() * 255),
                        b: Math.floor(Math.random() * 255)
                    }
                }          
                dataState.push({
                    'color': getRandomColor(),
                    'name': category.name,
                    'stat': []
                });      
            });
        }

        newData.forEach( (category, index) => {
            const keys = new Set([]);
            let stat = [...dataState[index].stat, ...category.stat];
            stat.sort((a, b) => b.created_at - a.created_at);
            stat = stat.filter((d, i) => {
                    if (keys.has(d.key)) 
                        return false;
                    keys.add(d.key);
                    return true;
                });
            stat.sort((a, b) => b[statKind] - a[statKind]);
            if (nQueries < stat.length)
                stat = stat.slice(0, nQueries);
            dataState[index].stat = stat;
        });

        this.setState({...this.state, data: dataState, colors});
    }
                
    handleBarClick = elem => {
        if (elem.length == 0)
            return;

        const datasetIndex = elem[0]._datasetIndex;
        const index = elem[0]._index;
        const rank = this.state.data[datasetIndex].stat[index].rank;

        if (this.props.onBarClick)
            this.props.onBarClick(rank);
    }

    render() {
        const {height, statKind} = this.props;
        const { data } = this.state;

        const ranks = [];
        const barData = [];
        let maxLen = 0;
        data.forEach(category => {
            const rgb = category.color;
            barData.push({
                label: category.name,
                data: category.stat.map(d => d[statKind]),
                backgroundColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.2)`,
                borderColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 1)`,
                borderWidth: 1,
                hoverBackgroundColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.4)`,
                hoverBorderColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 1)`,        
            });
            ranks.push(category.stat.map(d => d.rank));
            if (category.stat.length > maxLen)
                maxLen = category.stat.length;
        });

        const _data = {
            labels: Array(maxLen).fill(0).map((_, i) => i),
            datasets: barData
        };

        return (
            <Bar 
                ref={ref => this.chart = ref}
                data={_data}
                height={height}
                getElementAtEvent={this.handleBarClick}
                options={{
                    maintainAspectRatio: false,
                    tooltips: {
                        callbacks: {
                            title: (tooltipItem, data) => {
                                const datasetIndex = tooltipItem[0].datasetIndex;
                                const index = tooltipItem[0].index;
                                const rank = ranks[datasetIndex][index];
                                return `Rank-${rank}`;
                            }
                        }
                    }         
                }}
            />
        );
    }
}

AnomalyStats.defaultProps = {
    height: 100,
    stats: {},
    onBarClick: (_) => {},
    nQueries: 5,
    statKind: 'stddev'
};

AnomalyStats.propTypes = {
    width: PropTypes.number,
    height: PropTypes.number.isRequired,
    stats: PropTypes.object,
    onBarClick: PropTypes.func
};

export default AnomalyStats;