import React from 'react';
import PropTypes from 'prop-types';

import moment from 'moment';

import { Scatter } from 'react-chartjs-2';
// import 'chartjs-plugin-zoom';

import { parseFuncName } from '../utils';


class AnomalyFunc extends React.Component
{
    constructor(props) {
        super(props);
        this.state = {

        };
        this.chart = null;
    }

    shouldComponentUpdate(nextProps, nextState) {
        return true;
        // const { config:nextConfig, data:nextData } = nextProps;
        // const { config:currConfig, data:currData } = this.props;

        // const is_same_config = Object.keys(currConfig).map( key => {
        //     return currConfig[key] === nextConfig[key];
        // }).every(v => v);

        // const is_same_data = nextData.length === currData.length;

        // if (is_same_config && is_same_data)
        //     return false;
        // return true;
    }

    handleChartClick = elem => {
        if (elem.length == 0 || this.chart == null)
            return;

        const datasetIndex = elem[0]._datasetIndex;
        const index = elem[0]._index;
       
        const item = this.chart.props.data.datasets[datasetIndex].data[index];
        if (this.props.onPointClick)
            this.props.onPointClick(item.key);
        // if (this.chart == null) 
        //     return;

        // const activePoint = this.chart.getElementAtEvent(ev);
        // if (activePoint && activePoint.length) {
        //     // clicked on a point
        //     console.log(activePoint)
        //     return;
        // }        

        // const mousePoint = Chart.helpers.getRelativePosition(ev, this.chart.chart);

        /*
         for x-axis (167, 286)
          min_y = bottom (== height) - height + tickheight (12) + fontheight (12)
          max_y = bottom
        */
        // const xaxis = this.chart.chart.scales['x-axis-1'];
        // const max_y = xaxis.bottom - 5;
        // const min_y = max_y - 12;

        // let min_x = xaxis.left;
        // let max_x = xaxis.right;
        // const cx = (max_x - min_x) / 2 + min_x;
        // min_x = cx - 20;
        // max_x = cx + 20;

        // if (mousePoint.x > min_x && mousePoint.x < max_x && 
        //     mousePoint.y > min_y && mousePoint.y < max_y)
        // {
        //     console.log('hit x-axis label!');

        // }

    //    console.log(mousePoint, min_y, max_y, min_x, max_x);
       
    }

    getCommonOptions = (label, rgb) => {
        const {r, g, b} = rgb;
        return {
            label,
            fill: false,
            backgroundColor: `rgba(${r}, ${g}, ${b}, 0.5)`,
            pointBorderColor: `rgba(${r}, ${g}, ${b}, 1)`,
            pointBackgroundColor: '#fff',
            pointBorderWidth: 1,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: `rgba(${r}, ${g}, ${b}, 0.8)`,
            pointHoverBorderColor: `rgba(${r}, ${g}, ${b}, 1)`,
            pointHoverBorderWidth: 2,
            pointRadius: 5,
            pointHitRadius: 10,                
        }        
    }

    getValue = (d, key) => {
        if (key === 'entry' || key === 'exit')
            return d[key] / 1000;
        return d[key];        
    }

    getAxis = (key) => {
        return {
            type: 'linear',
            ticks: {       
                display: true,
                userCallback: tick => {
                    if (key === 'entry' || key === 'exit')
                        return moment(tick).format('ss.SSS');
                    return tick;
                    //return moment(tick).format('h:mm:ss.SSS a');
                },                     
            },
            scaleLabel: {
                display: true,
                labelString: key
            }                                 
        };
    }   

    getDisplayName = name => {
        return parseFuncName(name);
    }    

    //------need to update--------
    getDataInfo = d => {
        const info = `pid: ${d.pid}\nrid: ${d.rid}\ntid: ${d.tid}\nfid: ${d.fid}`;
        const time = `inclusive: ${d.runtime}\nexclusive: ${d.exclusive}`;
        const other = `# children: ${d.n_children}\n# messages: ${d.n_messages}\nlabel: ${d.label}`; 
        return `${info}\n${time}\n${other}`;
    }    

    render() {
        const { height, colors, x: xKey, y: yKey } = this.props;

        const datasets = {};
        this.props.data.forEach(d => {
            const fid = d.fid;
            if (!datasets.hasOwnProperty(fid))
                datasets[fid] = {
                    ...this.getCommonOptions(fid, colors[fid]),
                    data: []
                };
            datasets[fid].data.push({
                x: this.getValue(d, xKey),
                y: this.getValue(d, yKey),
                ...d
            });
        });

        return (
            <Scatter 
                ref={ref => this.chart = ref}
                data={{"datasets": Object.keys(datasets).map(key => datasets[key])}}
                height={height}
                getElementAtEvent={this.handleChartClick}
                options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        xAxes: [this.getAxis(xKey)],
                        yAxes: [this.getAxis(yKey)]
                    },
                    tooltips: {
                        callbacks: {
                            label: (tooltipItem, data) => {
                                const {datasetIndex, index} = tooltipItem;
                                const d = data.datasets[datasetIndex].data[index];
                                return this.getDisplayName(d.name);
                            },
                            afterBody: (tooltipItem, data) => {
                                const {datasetIndex, index} = tooltipItem[0];
                                const d = data.datasets[datasetIndex].data[index];
                                return this.getDataInfo(d);
                            }
                        }
                    },
                    legend: {
                        display: true,
                        position: 'right'
                    },
                    pan: {
                        enabled: true,
                        mode: "xy",
                        speed: 0.01,
                        // threshold: 10
                      },
                    zoom: {
                        enabled: true,
                        drag: false,
                        mode: "xy",
                        speed: 0.01
                        // limits: {
                        //   max: 10,
                        //   min: 0.5
                        // }
                    }                    
                }}
            />
        );
    }
};

AnomalyFunc.defaultProps = {
    height: 100,
    data: [],
    config: {
        pid: -1,
        rid: -1,
        min_timestamp: -1,
        max_timestamp: -1
    },
    colors: {}
};

AnomalyFunc.propTypes = {
    width: PropTypes.number,
    height: PropTypes.number,
    data: PropTypes.arrayOf(PropTypes.object),
    config: PropTypes.object,
    colors: PropTypes.object
};

export default AnomalyFunc;
