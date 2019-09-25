import React from 'react';
import PropTypes from 'prop-types';
import axios from 'axios';

import { Bar, Chart } from 'react-chartjs-2';
import 'chartjs-plugin-streaming';

import { withStyles } from '@material-ui/core/styles';
import FormGroup from '@material-ui/core/FormGroup';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import Switch from '@material-ui/core/Switch';
import Button from '@material-ui/core/Button';

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
    },
    button: {
        margin: theme.spacing(1)
    }
});

class AnomalyHistory extends React.Component
{
    constructor(props) {
        super(props);
        this.state = {
            pause: false
        };
        this.chartRef = React.createRef();
        this.chart = null;
    }

    onChartRefresh = (chart) => {
        const { ranks } = this.props;
        const keys = Object.keys(ranks);

   
        // add datasets if necessary
        keys.forEach(rank => {
            const label = `Rank-${rank}`;
            let datasetIndex = chart.data.datasets.findIndex(dataset => {
                return dataset.label === label;
            });
            if (datasetIndex == -1) {
                const {r, g, b} = ranks[rank];
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
        if (keys.length !== chart.data.datasets.length) {
            const datasetIndex = chart.data.datasets.findIndex(dataset => {
                return keys.indexOf(dataset.label.split('-')[1]) < 0;
            });
            chart.data.datasets.splice(datasetIndex, 1);
            chart.update();
        }

        // request data & update chart
        const qRanks = chart.data.datasets.map(dataset => {
            return parseInt(dataset.label.split('-')[1], 10);
        });
        const last_step = Math.max(...chart.data.datasets.map(dataset => {
            const last_item = dataset.data.slice(-1).pop();
            if (last_item)
                return last_item.step;
            return -1;
        }));
        axios.post("/events/query_history", {qRanks, last_step})
            .then(resp => {
                const q = resp.data;
                chart.data.datasets.forEach( (dataset, datasetIndex) => {
                    if (q[datasetIndex]) {
                        dataset.data.push({
                            x: Date.now(),
                            y: q[datasetIndex].n_anomalies,
                            ...q[datasetIndex]
                        });
                    }
                });            
                chart.update({preservation: true});            
            })
            .catch(e => {
                console.log('query_history: ', e);
            });
    }

    onLegendClick = (e, legendItem) => {
        const { ranks } = this.props;
        const { text: label } = legendItem;
        const rank = parseInt(label.split('-')[1], 10);
        if (Object.keys(ranks).length > 1 && this.props.onLegendClick)
            this.props.onLegendClick(rank);
    }

    componentDidMount() {
        const { height: _height } = this.props;
        const _data = {datasets: []};
        if (this.chart == null) {
            this.chart = new Chart(this.chartRef.current.getContext("2d"), 
            {
                type: "bar",
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
                        }]
                    },
                    tooltips: {
                        mode: 'nearest',
                        intersect: false,
                        callbacks: {
                            afterBody: (tooltipItem, data) => {
                                const datasetIndex = tooltipItem[0].datasetIndex;
                                const index = tooltipItem[0].index;
                                const item = data.datasets[datasetIndex].data[index];
                                return `step: ${item.step}\nmin_ts: ${item.min_timestamp}\nmax_ts: ${item.max_timestamp}`;
                            }
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

    shouldComponentUpdate(nextProps, nextState) {
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
              // const label = this.chart.data.datasets[datasetIndex].label;
              const item = this.chart.data.datasets[datasetIndex].data[index];

              const pid = item.anomalystat_key.split(":")[0];
              const rid = item.anomalystat_key.split(":")[1];
              const min_timestamp = item.min_timestamp;
              const max_timestamp = item.max_timestamp;
              console.log("clicked: ", pid, rid, min_timestamp, max_timestamp);
              if (this.props.onBarClick)
                this.props.onBarClick(pid, rid, min_timestamp, max_timestamp);
            }            
        }
    }

    render() {
        const { classes } = this.props;
        console.log('render AnomalyHistory view');

        return (
            <div className={classes.root}>
                <div className={classes.row} style={{height: 61}}>
                    <FormGroup row>
                        <FormControlLabel
                            control={
                                <Switch
                                    checked={this.state.pause}
                                    onChange={this.handleSwitch('pause')}
                                    value="pause"
                                />
                            }
                            label="PAUSE"
                        />
                    </FormGroup>
                </div>            
                <div className={classes.row}>
                    <canvas 
                        id="anomaly-history-chart"
                        ref={this.chartRef}
                        height={this.props.height}
                        onClick={this.handleBarClick}
                    />
                </div>
            </div>
        );
    }
}

AnomalyHistory.defaultProps = {
    height: 100,
    ranks: {},
    onLegendClick: (_) => {},
    onBarClick: (pid, rid, min_ts, max_ts) => {}
};

AnomalyHistory.propTypes = {
    width: PropTypes.number,
    height: PropTypes.number.isRequired,
    ranks: PropTypes.object,
    onLegendClick: PropTypes.func,
    onBarClick: PropTypes.func,
};

export default withStyles(useStyles)(AnomalyHistory);


// $('#myChart').click(function (e) {
//     var helpers = Chart.helpers;

//     var eventPosition = helpers.getRelativePosition(e, myRadarChart.chart);
//     var mouseX = eventPosition.x;
//     var mouseY = eventPosition.y;

//     var activePoints = [];
//     helpers.each(myRadarChart.scale.ticks, function (label, index) {
//         for (var i = this.getValueCount() - 1; i >= 0; i--) {
//             var pointLabelPosition = this.getPointPosition(i, this.getDistanceFromCenterForValue(this.options.reverse ? this.min : this.max) + 5);

//             var pointLabelFontSize = helpers.getValueOrDefault(this.options.pointLabels.fontSize, Chart.defaults.global.defaultFontSize);
//             var pointLabeFontStyle = helpers.getValueOrDefault(this.options.pointLabels.fontStyle, Chart.defaults.global.defaultFontStyle);
//             var pointLabeFontFamily = helpers.getValueOrDefault(this.options.pointLabels.fontFamily, Chart.defaults.global.defaultFontFamily);
//             var pointLabeFont = helpers.fontString(pointLabelFontSize, pointLabeFontStyle, pointLabeFontFamily);
//             ctx.font = pointLabeFont;

//             var labelsCount = this.pointLabels.length,
//                 halfLabelsCount = this.pointLabels.length / 2,
//                 quarterLabelsCount = halfLabelsCount / 2,
//                 upperHalf = (i < quarterLabelsCount || i > labelsCount - quarterLabelsCount),
//                 exactQuarter = (i === quarterLabelsCount || i === labelsCount - quarterLabelsCount);
//             var width = ctx.measureText(this.pointLabels[i]).width;
//             var height = pointLabelFontSize;

//             var x, y;

//             if (i === 0 || i === halfLabelsCount)
//                 x = pointLabelPosition.x - width / 2;
//             else if (i < halfLabelsCount)
//                 x = pointLabelPosition.x;
//             else
//                 x = pointLabelPosition.x - width;

//             if (exactQuarter)
//                 y = pointLabelPosition.y - height / 2;
//             else if (upperHalf)
//                 y = pointLabelPosition.y - height;
//             else
//                 y = pointLabelPosition.y
            
//             if ((mouseY >= y && mouseY <= y + height) && (mouseX >= x && mouseX <= x + width))
//                 activePoints.push({ index: i, label: this.pointLabels[i] });
//         }
//     }, myRadarChart.scale);
    
//     var firstPoint = activePoints[0];
//     if (firstPoint !== undefined) {
//         alert(firstPoint.index + ': ' + firstPoint.label);
//     }