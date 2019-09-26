import React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';

import {
    set_value,
    set_stats,
    set_watched_rank,
    unset_watched_rank,
    get_execution,
    set_execution
} from './actions/dataActions'

import io from 'socket.io-client';

import { withStyles } from '@material-ui/core/styles'
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import IconButton from '@material-ui/core/IconButton';
import MenuIcon from '@material-ui/icons/Menu';
import Typography from '@material-ui/core/Typography';

import Grid from '@material-ui/core/Grid';
import Paper from '@material-ui/core/Paper'

import AnomalyStats from './views/AnomalyStats';
import AnomalyHistory from './views/AnomalyHistory';
import AnomalyFunc from './views/AnomalyFunc';


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
        // this.eventSource = new EventSource("stream");
        this.socketio = null;
    }

    componentDidMount() {
        const namespace = '/events';
        const uri = 'http://' + document.domain + ':' + location.port + namespace;

        if (this.socketio == null)
            this.socketio = io(uri);

        this.socketio.on('connect', () => {
            console.log('socket.on.connect');
        });

        this.socketio.on('updated_data', data => {
            // Note that potentially 'updated_data' could be not only 
            // anomaly statistics but also something else. We can check
            // the contents from 'type' field of the data.

            // type == stats
            if (this.props.set_stats && data.type === 'stats')
                this.props.set_stats(data);

            if (this.props.set_value && data.type === 'execution')
                this.props.set_execution(data.data);
        });

        this.socketio.on('connect_error', err => {
            this.socketio.close();
            this.socketio = null;
        });
    }

    handleStatChange = q => {
        if (this.socketio) {
            this.socketio.emit('query_stats', q);
        }
    }

    handleHistoryRequest = rank => {
        if (this.props.set_watched_rank)
            this.props.set_watched_rank(rank);
    }

    handleHistoryRemove = rank => {
        if (this.props.unset_watched_rank)
            this.props.unset_watched_rank(rank);
    }

    handleExecutionRequest = (pid, rid, step, min_timestamp, max_timestamp) => {
        const { execdata_config:config } = this.props;
        const newConfig = {pid, rid, step, min_timestamp, max_timestamp};
        const is_same = Object.keys(config).map(key => {
            return config[key] === newConfig[key];
        }).every(v => v);

        if (!is_same && this.props.get_execution)
            this.props.get_execution(pid, rid, step, min_timestamp, max_timestamp);
    }

    render() {
        const { classes, stats, watched_ranks } = this.props;
        const { execdata, execdata_config, func_colors } = this.props;

        return (
            <div className={classes.root}>
                <AppBar position="static">
                    <Toolbar>
                        <IconButton 
                            className={classes.menuButton}
                            edge="start" 
                            color="inherit" 
                            aria-label="menu"
                        >
                            <MenuIcon />
                        </IconButton>
                        <Typography 
                            className={classes.title} 
                            variant="h6"
                        >
                            Chimbuko Visualization
                        </Typography>
                    </Toolbar>
                </AppBar>
                <Grid container spacing={3}>
                    <Grid item xs={4}>
                        <AnomalyStats 
                            height={200}
                            stats={stats}
                            onStatChange={this.handleStatChange}
                            onBarClick={this.handleHistoryRequest}
                        />
                    </Grid>
                    <Grid item xs={8}>
                        <AnomalyHistory
                            height={200}
                            ranks={watched_ranks}
                            onLegendClick={this.handleHistoryRemove}
                            onBarClick={this.handleExecutionRequest}
                        />
                    </Grid>
                    <Grid item xs={6}>
                        <AnomalyFunc 
                            height={300}
                            data={execdata}
                            config={execdata_config}
                            colors={func_colors}
                            x={"entry"}
                            y={"exit"}
                        />
                    </Grid>
                    <Grid item xs={8}>
                        <Paper className={classes.paper}>xs=8</Paper>
                    </Grid>
                </Grid>                
            </div>
        );
    }
}

function mapStateToProps(state) {
    return {
        stats: state.data.stats,
        watched_ranks: state.data.watched_ranks,
        execdata: state.data.execdata,
        execdata_config: state.data.execdata_config,
        func_colors: state.data.func_colors
    };
}

function mapDispatchToProps(dispatch) {
    return bindActionCreators({
        set_value,
        set_stats,
        set_watched_rank,
        unset_watched_rank,
        get_execution,
        set_execution
    }, dispatch);
}

export default withStyles(styles)(
    connect(
        mapStateToProps, 
        mapDispatchToProps
    )(ChimbukoApp)
);
