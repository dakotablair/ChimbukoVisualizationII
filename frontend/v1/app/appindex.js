import React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';

import {
    set_value
} from './actions/dataActions'

import { withStyles, makeStyles } from '@material-ui/core/styles'
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import IconButton from '@material-ui/core/IconButton';
import MenuIcon from '@material-ui/icons/Menu';
import Typography from '@material-ui/core/Typography';

import Grid from '@material-ui/core/Grid';
import Paper from '@material-ui/core/Paper'

// import Dashboard from './views/Dashboard';
import BarExample from './views/BarExample';
import AnomalyStats from './views/AnomalyStats';

const styles = theme => ({
    root: {flexGrow: 1},
    menuButton: {marginRight: theme.spacing(2)},
    title: {flexGrow: 1},
    paper: {
        padding: theme.spacing(2),
        textAlign: 'center',
        color: theme.palette.text.secondary
    }
});

class ChimbukoApp extends React.Component {
    constructor(props) {
        super(props);
        this.state = {

        };
        this.eventSource = new EventSource("stream");
    }

    componentDidMount() {
        // this.eventSource.onmessage = ev => {
        //     const data = JSON.parse(ev.data);
        //     console.log(data);
        // };
        if (this.eventSource == null)
            this.eventSource = new EventSource("stream");

        this.eventSource.addEventListener("anomalyStatUpdate", ev => {
            if (this.props.set_value)
                this.props.set_value("anomaly_stats", JSON.parse(ev.data));
        });
        this.eventSource.onerror = e => {
            // todo: error handling
            console.log(e, e.readyState)
            if (e.readyState == EventSource.CLOSED)
            {
                this.eventSource.close();
                this.eventSource = null;
                console.log('close eventSource')
            }
        }
    }

    render() {
        const { classes, stats } = this.props;

        console.log(this.props);

        return (
            <div className={classes.root}>
                <AppBar position="static">
                    <Toolbar>
                        <IconButton className={classes.menuButton}
                            edge="start" color="inherit" aria-label="menu"
                        >
                            <MenuIcon />
                        </IconButton>
                        <Typography className={classes.title} variant="h6">
                            Chimbuko Visualization
                        </Typography>
                    </Toolbar>
                </AppBar>
                <Grid container spacing={3}>
                    <Grid item xs={6}>
                        <AnomalyStats 
                            height={100}
                            stats={stats}
                        />
                    </Grid>
                    <Grid item xs={6}>
                        {/* <BarExample /> */}
                    </Grid>
                    <Grid item xs={3}>
                        <Paper className={classes.paper}>xs=3</Paper>
                    </Grid>
                    <Grid item xs={3}>
                        <Paper className={classes.paper}>xs=3</Paper>
                    </Grid>
                    <Grid item xs={3}>
                        <Paper className={classes.paper}>xs=3</Paper>
                    </Grid>
                    <Grid item xs={3}>
                        <Paper className={classes.paper}>xs=3</Paper>
                    </Grid>
                </Grid>                
            </div>
        );
    }
}

function mapStateToProps(state) {
    return {
        stats: state.data.anomaly_stats
    };
}

function mapDispatchToProps(dispatch) {
    return bindActionCreators({
        set_value
    }, dispatch);
}

export default withStyles(styles)(
    connect(
        mapStateToProps, 
        mapDispatchToProps
    )(ChimbukoApp)
);
