import React from 'react';
import PropTypes from 'prop-types';
import clsx from 'clsx';

import { Bar } from 'react-chartjs-2';

import { withStyles } from '@material-ui/core/styles';
import TextField from '@material-ui/core/TextField';
import MenuItem from '@material-ui/core/MenuItem';

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

class AnomalyStats extends React.Component 
{
    constructor(props) {
        super(props);
        this.state = {
        };
    }

    handleStatChange = key => ev => {
        let {statKind, nQueries} = this.props.stats;
        let q = {
            "statKind": statKind | "stddev",
            "nQueries": nQueries | 5
        }
        if (q[key] !== ev.target.value && this.props.onStatChange)
            this.props.onStatChange({...q, [key]: ev.target.value});
    }

    handleBarClick = elem => {
        if (elem.length == 0)
            return;

        const datasetIndex = elem[0]._datasetIndex;
        const index = elem[0]._index;
        const { data } = this.props.stats;

        const rank = data[datasetIndex].rank[index];
        if (this.props.onBarClick)
            this.props.onBarClick(rank);
    }

    render() {
        const {height, stats, classes} = this.props;

        const statKinds = [
            "min", "max", "mean", "stddev", "kurtosis", "skewness"
        ];

        const {statKind, nQueries, data} = stats;

        let ranks = [];
        let barData = [];
        if (data) {
            data.forEach(category => {
                const getRandomColor = () => {
                    return {
                        r: Math.floor(Math.random() * 255),
                        g: Math.floor(Math.random() * 255),
                        b: Math.floor(Math.random() * 255)
                    }
                }
                const rgb = category.hasOwnProperty('color') ? category.color: getRandomColor();
                barData.push({
                    label: category.name,
                    data: category.value,
                    backgroundColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.2)`,
                    borderColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 1)`,
                    borderWidth: 1,
                    hoverBackgroundColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.4)`,
                    hoverBorderColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 1)`,        
                });
                ranks.push(category.rank);
            });
        }     

        const _data = {
            labels: Array(nQueries).fill(0).map((_, i) => i),
            datasets: barData
        };

        return (
            <div className={classes.root}>
                <div className={classes.row}>
                    <TextField
                        id="stat-kind"
                        label="Statistics"
                        value={statKind || "stddev"}
                        onChange={this.handleStatChange('statKind')}
                        select
                        className={clsx(classes.margin, classes.textField)}
                        margin="dense"
                    >
                    {
                        statKinds.map(kind => (
                            <MenuItem key={kind} value={kind}>
                                {kind}
                            </MenuItem>
                        ))
                    }
                    </TextField>
                    <TextField
                        id="stat-queries"
                        label="# Queries"
                        value={nQueries || 5}
                        onChange={this.handleStatChange('nQueries')}
                        type="number"
                        className={clsx(classes.margin, classes.textField)}
                        margin="dense"
                        inputProps={{min: 0, max: 100, step: 5}}
                    >
                    </TextField>
                </div>
                <div className={classes.row}>
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
                </div>
            </div>
        );
    }
}

AnomalyStats.defaultProps = {
    height: 100,
    stats: {},
    onStatChange: (_) => {},
    onBarClick: (_) => {}
};

AnomalyStats.propTypes = {
    width: PropTypes.number,
    height: PropTypes.number.isRequired,
    stats: PropTypes.object,
    onStatChange: PropTypes.func,
    onBarClick: PropTypes.func
};

export default withStyles(useStyles)(AnomalyStats);