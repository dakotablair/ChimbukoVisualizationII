import React from 'react';
import PropTypes from 'prop-types';
import clsx from 'clsx';

import { makeStyles, withStyles } from '@material-ui/core/styles';
import Grid from '@material-ui/core/Grid';
import TextField from '@material-ui/core/TextField';
import MenuItem from '@material-ui/core/MenuItem';
import Input from '@material-ui/core/Input';
import Slider from '@material-ui/core/Slider';

const useStyles = theme => ({
    root: {
        display: 'flex',
        flexWrap: 'wrap'
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
            orderBy: "rank",
            N: 5
        };
    }

    handleChange = key => ev => {
        //console.log('handleChange: ', ev, key);
        this.setState({...this.state, [key]: ev.target.value});
    }

    handleSliderChange = (ev, newValue) => {
        //console.log('handleSliderChange: ', ev, newValue);
        this.setState({...this.state, N: newValue});
    }

    handleInputChange = ev => {
        //console.log('handleInputChange: ', ev, ev.target.value);
        this.setState({...this.state, N: Number(ev.target.value)});
    }

    handleBlur = (ev) => {
        console.log('handleBlur: ', ev);
    }

    render() {
        const {height, stats, classes} = this.props;

        // assuming all items in stats array has the same format.
        // also assume that each item must contain at least two entries
        // and one of them must be 'rank'.
        console.log('AnomalyStatProps: ', this.props);

        // collect available entries and total number of stats
        const keys = (stats.length) ? Object.keys(stats[0]): [];
        const n_items = stats.length;



        return (
            <div className={classes.root}>
                <TextField
                    select
                    label="Order By"
                    className={clsx(classes.margin, classes.textField)}
                    value={this.state.orderBy}
                    onChange={this.handleChange('orderBy')}
                >
                {
                    keys.map(option => (
                        <MenuItem key={option} value={option}>
                            {option}
                        </MenuItem>
                    ))
                }
                </TextField>
                <Slider 
                    value={this.state.N}
                    onChange={this.handleSliderChange}
                    min={5}
                    max={n_items}
                    aria-labelledby="input-slider"
                />
                <Input 
                    value={this.state.N}
                    margin="dense"
                    onChange={this.handleInputChange}
                    onBlur={this.handleBlur}
                    inputProps={{
                        step: 5,
                        min: 5,
                        max: n_items,
                        type: 'number',
                        'aria-labelledby': 'input-slider'
                    }}
                />
            </div>
        );
    }
}

AnomalyStats.defaultProps = {
    height: 100,
    stats: []
};

AnomalyStats.propTypes = {
    width: PropTypes.number,
    height: PropTypes.number.isRequired,
    stats: PropTypes.arrayOf(PropTypes.object)
};

export default withStyles(useStyles)(AnomalyStats);