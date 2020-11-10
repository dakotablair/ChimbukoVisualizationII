import React from 'react';
import PropTypes from 'prop-types';

import moment from 'moment';

import { Scatter } from 'react-chartjs-2';
import 'chartjs-plugin-zoom';

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
        //console.log("...should component update...");

        // const { config:nextConfig, data:nextData } = nextProps;
        // const { config:currConfig, data:currData } = this.props;

        // const is_same_config = Object.keys(currConfig).map( key => {
        //     return currConfig[key] === nextConfig[key];
        // }).every(v => v);

        // const is_same_data = nextData.length === currData.length;

        // redraw only when it is new axis setting or new data
        // so when zoomed and click one point won't redraw this view
        const {x: xNext, y: yNext, config:nextConfig} = nextProps;
        const {x: xCurr, y: yCurr, config:currConfig} = this.props;
        const is_same_coor = xNext === xCurr && yNext === yCurr;
        const is_same_config = Object.keys(currConfig).map( key => {
            return currConfig[key] === nextConfig[key];
        }).every(v => v);
        
        if (is_same_coor && is_same_config)
            return false;
        return true;
    }

    handleChartClick = elem => {
        if (elem.length == 0 || this.chart == null)
            return;

        const datasetIndex = elem[0]._datasetIndex;
        const index = elem[0]._index;
       
        const item = this.chart.props.data.datasets[datasetIndex].data[index];
        if (this.props.onPointClick)
            this.props.onPointClick(item.event_id);
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
            fill: true,
            //backgroundColor: `rgba(${r}, ${g}, ${b}, 0.8)`,
            pointBorderColor: `rgba(${r}, ${g}, ${b}, 1)`,
            pointBackgroundColor: `rgba(${r}, ${g}, ${b}, 0.3)`, //'#fff',
            pointBorderWidth: 1,
            pointHoverRadius: 8,
            pointHoverBackgroundColor: `rgba(${r}, ${g}, ${b}, 0.1)`,
            pointHoverBorderColor: `rgba(${r}, ${g}, ${b}, 1)`,
            pointHoverBorderWidth: 2,
            pointRadius: 5,
            pointHitRadius: 8,                
        }        
    }

    getValue = (d, i, key, ids) => {
        if (key === 'entry' || key === 'exit')
            return d[key] / 1000;
        else if (key === 'function_id')
            return ids[d['fid']];
        else if (key === 'event_id')
            return i;
        return d[key];        
    }

    getAxis = (key, ids) => {
        // prepare correct axis range for zooming
        let tmin = 0;
        let tmax = 1;
        this.props.data.forEach((d, i) => {
            if (key === 'function_id') { // fid uses index as its axis
                tmin = Math.min(ids[d['fid']], tmin);
                tmax = Math.max(ids[d['fid']], tmax);
            }
            else if (key === 'event_id') { //event_id uses its index as axis
                tmin = Math.min(i, tmin);
                tmax = Math.max(i, tmax);
            } else {
                tmin = Math.min(d[key], tmin);
                tmax = Math.max(d[key], tmax);
            }
        });
        if (key === 'entry' || key === 'exit') {
            tmin = tmin / 1000;
            tmax = tmax / 1000;
        }
        // console.log("min: " + tmin + "max: " + tmax);
        return {
            type: 'linear',
            ticks: {       
                display: true,
                precision: 0, // axis tick must round up
                userCallback: tick => {
                    if (key === 'entry' || key === 'exit')
                        return moment(tick).format('ss.SSS');
                    return Math.floor(tick); // make sure to round up
                    // return moment(tick).format('h:mm:ss.SSS a');
                },
                maxRotation: 0, // prevent tick text rotation
                minRotation: 0, // prevent tick text rotation
                min: tmin,
                max: tmax                 
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

    getDataInfo = d => {
        const entry = moment(d.entry/1000).format('h:mm:ss.SSS a');
        const exit = moment(d.exit/1000).format('h:mm:ss.SSS a');
        const func_mean = d.func_stats.mean/1000;
        const func_stddev = d.func_stats.stddev/1000;

        const info = `pid: ${d.pid} rid: ${d.rid} tid: ${d.tid} function_id: ${d.fid} event_id: ${d.event_id}\n`;
        const time = `entry: ${entry}\nexit: ${exit}\nruntime_total: ${d.runtime_total/1000}ms\nruntime_exclusive: ${d.runtime_exclusive/1000}ms\n`;
        const funcstats = `Normal function info:\nmean runtime: ${func_mean.toPrecision(3)}ms\nstddev: ${func_stddev.toPrecision(3)}ms\nfunctions encountered: ${d.func_stats.count}\n`;
        let other = ``;
        
        if (d.is_gpu_event)
            other = `\nGPU info:\ncontext: ${d.gpu_location.context} device: ${d.gpu_location.device} stream: ${d.gpu_location.stream} thread: ${d.gpu_location.thread}`;
        
        return `${info}${time}\n${funcstats}${other}`;
    }    

    render() {
        const { height, colors, ids, x: xKey, y: yKey } = this.props;

        const datasets = {};
        this.props.data.forEach((d, i) => {
            const fid = d.fid;
            if (!datasets.hasOwnProperty(fid))
                datasets[fid] = {
                    ...this.getCommonOptions(fid, colors[fid]),
                    data: []
                };
            datasets[fid].data.push({
                x: this.getValue(d, i, xKey, ids),
                y: this.getValue(d, i, yKey, ids),
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
                        xAxes: [this.getAxis(xKey, ids)],
                        yAxes: [this.getAxis(yKey, ids)]
                    },
                    tooltips: {
                        callbacks: {
                            label: (tooltipItem, data) => {
                                const {datasetIndex, index} = tooltipItem;
                                const d = data.datasets[datasetIndex].data[index];
                                return this.getDisplayName(d.func);
                            },
                            afterBody: (tooltipItem, data) => {
                                const {datasetIndex, index} = tooltipItem[0];
                                const d = data.datasets[datasetIndex].data[index];
                                return this.getDataInfo(d);
                            }
                        }
                    },
                    legend: {
                        display: false,
                        position: 'bottom',
                        fullWidth: false
                    },
                    pan: {
                        enabled: true,
                        mode: "xy",
                        speed: 1
                      },
                    zoom: {
                        enabled: true,
                        drag: false,
                        mode: "xy",
                        speed: 0.05
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
