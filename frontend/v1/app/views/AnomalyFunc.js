import React from 'react';
import PropTypes from 'prop-types';
import clsx from 'clsx';
// import * as moment from 'moment';
import moment from 'moment';

import { Scatter, Chart } from 'react-chartjs-2';
//import { Chart } from 'chart.js';

import { withStyles } from '@material-ui/core/styles';

const useStyles = theme => ({
    root: {
        display: 'flex',
        flexWrap: 'wrap'
    },
    row: {
        display: 'flex',
        width: '100%'
    },
    margin: {
        margin: theme.spacing(1),
    },
    withoutLabel: {
        marginTop: theme.spacing(3)
    },
    textField: {
        flexBasis: 200
    }
});


class AnomalyFunc extends React.Component
{
    constructor(props) {
        super(props);
        this.state = {

        };
        this.chartRef = React.createRef();
        this.chart = null;
    }

    shouldComponentUpdate(nextProps, nextState) {
        const { config:nextConfig, data:nextData } = nextProps;
        const { config:currConfig, data:currData } = this.props;

        const is_same_config = Object.keys(currConfig).map( key => {
            return currConfig[key] === nextConfig[key];
        }).every(v => v);

        const is_same_data = nextData.length === currData.length;

        if (is_same_config && is_same_data)
            return false;
        return true;
    }

    buildChart = () => {
        const { classes, height, colors, x: xKey, y: yKey, config } = this.props;

        const getCommonOptions = (label, rgb) => {
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
        };

        const getValue = (d, key) => {
            return d[key];
            // if (key === 'runtime' || key === 'exclusive')
            //     return d[key];
            // return d[key] - config.min_timestamp;
        };

        const getAxis = (key) => {
            return {
                ticks: {
                    userCallback: (label, index, labels) => {
                        console.log(label, index, labels)
                        return moment(label).format('h:mm:ss.SSS a');
                    }
                }
                //type: 'time',
                // time: {
                //     unit: "millisecond",
                //     displayFormat: {
                //         millisecond: 'h:mm:ss.SSS a',
                //         second: 'h:mm:ss a'
                //     }
                // }
            };
        };

        const datasets = {};
        this.props.data.forEach(d => {
            const fid = d.fid;
            if (!datasets.hasOwnProperty(fid))
                datasets[fid] = {
                    ...getCommonOptions(fid, colors[fid]),
                    data: []
                };
            datasets[fid].data.push({
                x: getValue(d, xKey),
                y: getValue(d, yKey)
            });
        });

        if (this.chart)
            this.chart.destroy();

        this.chart = new Chart(this.chartRef.current.getContext("2d"),
        {
            type: "scatter",
            height,
            data: {
                "datasets": Object.keys(datasets).map(key => datasets[key])
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    xAxes: [{
                        type: 'linear',
                        ticks: {       
                            display: true,
                            userCallback: tick => {
                                return moment(tick).format('mm:ss');
                                //return moment(tick).format('h:mm:ss.SSS a');
                            },                     
                        },
                        scaleLabel: {
                            display: true,
                            labelString: 'x-axis'
                        }                                 
                    }],
                    yAxes: [{
                        type: 'linear',
                        ticks: {       
                            display: true,
                            userCallback: tick => {
                                return moment(tick).format('mm:ss');
                                //return moment(tick).format('h:mm:ss.SSS a');
                            },                     
                        },
                        scaleLabel: {
                            display: true,
                            labelString: 'y-axis'
                        }                              
                    }],
                },
                tooltips: {
                    callbacks: {
                        label: (tooltipItem, data) => {
                            return "mylabel";
                        }
                    }
                },
                legend: {
                    display: true,
                    position: 'right',
                }                                    
            }     
        });
    }

    componentDidMount() {
        this.buildChart();
    }

    componentDidUpdate(prevProps, prevState) {
        this.buildChart();
    }

    handleChartClick = ev => {
        if (this.chart == null) 
            return;

        const activePoint = this.chart.getElementAtEvent(ev);
        if (activePoint && activePoint.length) {
            // clicked on a point
            return;
        }        

        const mousePoint = Chart.helpers.getRelativePosition(ev, this.chart.chart);
        console.log(this.chart.chart)

        /*
         for x-axis (167, 286)
          min_y = bottom (== height) - height + tickheight (12) + fontheight (12)
          max_y = bottom
        */
       const xaxis = this.chart.chart.scales['x-axis-1']
       const max_y = xaxis.bottom - 5;
       const min_y = max_y - 12;

       let min_x = xaxis.left;
       let max_x = xaxis.right;
       const cx = (max_x - min_x) / 2 + min_x;
        min_x = cx - 20;
        max_x = cx + 20;

        if (mousePoint.x > min_x && mousePoint.x < max_x && 
            mousePoint.y > min_y && mousePoint.y < max_y)
        {
            console.log('hit x-axis label!')
        }

       console.log(mousePoint, min_y, max_y, min_x, max_x);
       
    }

    render() {
        const { classes, height, colors, x: xKey, y: yKey, config } = this.props;

        console.log("render AnomalyFunc view")
        console.log(this.props.data);
        return (
            <div className={classes.root}>
                <div className={classes.row}>
                    <canvas 
                        id="anomaly-func-chart"
                        ref={this.chartRef}
                        height={height}
                        onClick={this.handleChartClick}
                    />
                </div>
            </div>    
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

export default withStyles(useStyles)(AnomalyFunc);


        // const data = {
        //     labels: ['Scatter'],
        //     datasets: [
        //       {
        //         label: 'My First dataset',
        //         fill: false,
        //         backgroundColor: 'rgba(75,192,192,0.4)',
        //         pointBorderColor: 'rgba(75,192,192,1)',
        //         pointBackgroundColor: '#fff',
        //         pointBorderWidth: 1,
        //         pointHoverRadius: 5,
        //         pointHoverBackgroundColor: 'rgba(75,192,192,1)',
        //         pointHoverBorderColor: 'rgba(220,220,220,1)',
        //         pointHoverBorderWidth: 2,
        //         pointRadius: 5,
        //         pointHitRadius: 10,
        //         data: [
        //           { x: 65, y: 75 },
        //           { x: 59, y: 49 },
        //           { x: 80, y: 90 },
        //           { x: 81, y: 29 },
        //           { x: 56, y: 36 },
        //           { x: 55, y: 25 },
        //           { x: 40, y: 18 },
        //         ]
        //       },
        //       {
        //         label: 'My Second dataset',
        //         fill: false,
        //         backgroundColor: 'rgba(75,0,192,0.4)',
        //         pointBorderColor: 'rgba(75,0,192,1)',
        //         pointBackgroundColor: '#fff',
        //         pointBorderWidth: 1,
        //         pointHoverRadius: 5,
        //         pointHoverBackgroundColor: 'rgba(75,0,192,1)',
        //         pointHoverBorderColor: 'rgba(220,220,220,1)',
        //         pointHoverBorderWidth: 2,
        //         pointRadius: 5,
        //         pointHitRadius: 10,
        //         data: [
        //           { x: 85, y: 35 },
        //           { x: 39, y: 69 },
        //           { x: 40, y: 60 },
        //           { x: 21, y: 29 },
        //           { x: 36, y: 16 },
        //           { x: 15, y: 45 },
        //           { x: 70, y: 78 },
        //         ]
        //       }              
        //     ]
        //   };
