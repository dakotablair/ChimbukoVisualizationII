import React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import axis from 'axios';
import {
    set_value,
    set_stats,
    set_watched_rank,
    unset_watched_rank,
    get_execution
} from './actions/dataActions'

import {
    /*executionForest,*/
    executionTree
} from './selectors';

import io from 'socket.io-client';

import { withStyles } from '@material-ui/core/styles'
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import IconButton from '@material-ui/core/IconButton';
import MenuIcon from '@material-ui/icons/Menu';
import MenuItem from '@material-ui/core/MenuItem';
import Typography from '@material-ui/core/Typography';
import TextField from '@material-ui/core/TextField';
import FormGroup from '@material-ui/core/FormGroup';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import Switch from '@material-ui/core/Switch';
import Grid from '@material-ui/core/Grid';
import Chip from '@material-ui/core/Chip';
import Button from '@material-ui/core/Button';

import clsx from 'clsx';

//import Paper from '@material-ui/core/Paper'

import AnomalyStats from './views/AnomalyStats';
import AnomalyHistory from './views/AnomalyHistory';
import AnomalyFunc from './views/AnomalyFunc';
import TemporalCallStack from './views/TemporalCallStack';


const styles = theme => ({
    root: {flexGrow: 1},
    menuButton: {marginRight: theme.spacing(2)},
    title: {flexGrow: 1},

    viewroot: {
        display: 'flex',
        flexWrap: 'wrap'
    },
    row: {
        display: 'flex',
        width: '100%'
    },
    margin: {
        margin: theme.spacing(1)
    },
    textField: {
        flexBasis: 200
    },
    chip: {
        padding: theme.spacing(3, 2),
        flexDirection: "column",
        justifyContent: "center"
    },    
    button: {
        margin: theme.spacing(1)
    },

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
            pause: false,
            funcX: "runtime_total",
            funcY: "fid",
            run_simulate: false
        };
        this.socketio = null;
        this.connectSocket();
    }

    connectSocket = () => {
        const namespace = '/events';
        const uri = 'http://' + document.domain + ':' + location.port + namespace;

        if (this.socketio == null)
            this.socketio = io(uri);

        this.socketio.on('connect', () => {
            console.log('socket.on.connect');
        });

        this.socketio.on('run_simulation', err => {
            console.log(err);
            this.setState({run_simulate: false});
        });

        this.socketio.on('connect_error', err => {
            this.socketio.close();
            this.socketio = null;
        });
    }

    componentDidMount() {
    }

    handleStatChange = key => ev => {
        const { watched_ranks } = this.props;

        if (this.props.stats[key] !== ev.target.value) {
            if (this.props.set_stats)
                this.props.set_stats({
                    ...this.props.stats, 
                    [key]: ev.target.value
                });

            if (this.socketio)
                this.socketio.emit('query_stats', {
                    ...this.props.stats, 
                    [key]: ev.target.value,
                    ranks: watched_ranks
                });
        }
    }

    handleHistoryRequest = rank => {
        const watched_ranks = [...this.props.watched_ranks];

        if (watched_ranks.indexOf(rank) >= 0)
            return;

        watched_ranks.push(rank);
        if (this.socketio && this.props.set_watched_rank) {
            this.socketio.emit('query_stats', {
                ranks: watched_ranks,
                ...this.props.stats
            });
            this.props.set_watched_rank(rank);
        }
    }

    handleHistoryRemove = rank => {
        const watched_ranks = [...this.props.watched_ranks];
        if (watched_ranks.length == 0)
            return;

        const idx = watched_ranks.indexOf(rank);
        if (idx == -1)
            return;

        watched_ranks.splice(idx, 1);

        if (this.socketio && this.props.unset_watched_rank) {
            this.socketio.emit('query_stats', {
                ranks: watched_ranks,
                ...this.props.stats
            });
            this.props.unset_watched_rank(rank);
        }
    }

    handleExecutionRequest = (item) => {
        const { execdata_config:config } = this.props;
        
        const is_same = Object.keys(config).map(key => {
            return config[key] === item[key];
        }).every(v => v);

        if (!is_same && this.props.get_execution) {
            this.props.get_execution(item);
        }
    }

    handleSwitch = name => ev => {
        this.setState({...this.state, [name]: event.target.checked});
    }    

    handleFuncAxisChange = key => ev => {
        this.setState({...this.state, [key]: ev.target.value});
    }

    handleTreeRequest = key => {
        if (this.props.set_value)
            this.props.set_value('node_key', key);
    }

    handleStatRefresh = ev => {
        const url = '/api/get_anomalystats';
        axis.get(url)
            .then(resp => {
                console.log('handleStatRefresh: ', resp);
            })
            .catch(e => {
                console.log('handleStatRefresh: ', e);
            });
    }

    handleRunSimulation = ev => {
        if (this.state.run_simulate)
            return;

        const url = '/api/run_simulation';
        axis.get(url)
            .then(resp => {
                if (resp.status === 202) {
                    this.setState({run_simulate: true});
                }
            })
            .catch(e => {
                console.log('handleRunSimulation: ', e);
            });
    }

    render() {
        const { classes, stats, watched_ranks, rank_colors } = this.props;
        const { execdata, execdata_config, func_colors, func_ids } = this.props;
        const { /*forest, */tree, selected_node } = this.props;

        const statKinds = [
            "minimum", "maximum", "mean", "stddev", "kurtosis", "skewness",
            "count", "accumulate"
        ];
        const funcFeat = [
            "fid", "event_id",
            "entry", "exit", "runtime_total", "runtime_exclusive",
            "is_gpu_event"
        ];

        const { statKind, nQueries } = stats;

        const getSelectedName = () => {
            const {app, rank, step} = execdata_config;
            return `${app}:${rank}:${step}`;
        } 

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
                            Chimbuko Visualization II
                        </Typography>
                    </Toolbar>
                </AppBar>
                <Grid container spacing={3}>
                    <Grid item xs={4}>
                        <div className={classes.viewroot}>
                            <div className={classes.row}>
                                <TextField
                                    id="stat-kind"
                                    label="Anomaly statistics"
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
                                    inputProps={{min: 0, max:100, step: 1}}
                                >
                                </TextField>
                                <Button 
                                    variant="contained" 
                                    className={classes.button} 
                                    onClick={this.handleStatRefresh}
                                >
                                    Refresh
                                </Button>
                            </div>
                            <div className={classes.row}>
                                <AnomalyStats 
                                    height={200}
                                    socketio={this.socketio}
                                    nQueries={nQueries}
                                    statKind={statKind}
                                    onBarClick={this.handleHistoryRequest}
                                />
                            </div>
                        </div>
                    </Grid>
                    <Grid item xs={8}>
                        <div className={classes.viewroot}>
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
                                <Button
                                    variant="contained"
                                    className={classes.button}
                                    color={this.state.run_simulate?"secondary":"primary"}
                                    onClick={this.handleRunSimulation}
                                >
                                    {
                                        (this.state.run_simulate) 
                                            ? "STOP SIMULATION"
                                            : "RUN SIMULATION"
                                    }
                                </Button>                         
                            </div>
                            <div className={classes.row}>
                                <AnomalyHistory
                                    height={200}
                                    ranks={watched_ranks}
                                    colors={rank_colors}
                                    socketio={this.socketio}
                                    onLegendClick={this.handleHistoryRemove}
                                    onBarClick={this.handleExecutionRequest}
                                    pause={this.state.pause}
                                />                            
                            </div>
                        </div>
                    </Grid>

                    <Grid item xs={4}>
                        <div className={classes.viewroot}>
                            <div className={classes.row}>
                                {/*<Chip className={classes.chip} label={getSelectedName()} />*/}
                                <Button 
                                    variant="contained" 
                                    className={classes.button} 
                                    /*onClick={this.chart.resetZoom()}*/
                                >
                                    {getSelectedName()}
                                </Button>
                                <TextField
                                    id="func-x"
                                    label="X-axis"
                                    value={this.state.funcX}
                                    onChange={this.handleFuncAxisChange('funcX')}
                                    select
                                    className={clsx(classes.margin, classes.textField)}
                                    margin="dense"
                                >
                                {
                                    funcFeat.map(feat => (
                                        <MenuItem key={feat} value={feat}>
                                            {feat}
                                        </MenuItem>
                                    ))
                                }
                                </TextField>        
                                <TextField
                                    id="func-y"
                                    label="Y-axis"
                                    value={this.state.funcY}
                                    onChange={this.handleFuncAxisChange('funcY')}
                                    select
                                    className={clsx(classes.margin, classes.textField)}
                                    margin="dense"
                                >
                                {
                                    funcFeat.map(feat => (
                                        <MenuItem key={feat} value={feat}>
                                            {feat}
                                        </MenuItem>
                                    ))
                                }
                                </TextField>                                                       
                            </div>
                            <div className={classes.row} style={{overflow: scroll}}>
                                <AnomalyFunc 
                                    height={400}
                                    data={execdata}
                                    config={execdata_config}
                                    colors={func_colors}
                                    ids={func_ids}
                                    x={this.state.funcX}
                                    y={this.state.funcY}
                                    onPointClick={this.handleTreeRequest}
                                />
                            </div>
                        </div>
                    </Grid>
                    <Grid item xs={8}>
                        <TemporalCallStack
                            id="temporal-callstack"
                            height={400}
                            tree={tree}
                            selected={selected_node}
                            colors={func_colors}
                            config={execdata_config}
                            margin={{
                                top: 40, bottom: 10, 
                                left: 50, right: 50
                            }}
                        />
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
        rank_colors: state.data.rank_colors,
        execdata: state.data.execdata,
        execdata_config: state.data.execdata_config,
        func_colors: state.data.func_colors,
        func_ids: state.data.func_ids,
        /*forest: executionForest(state),*/
        tree: executionTree(state),
        selected_node: state.data.node_key
    };
}

function mapDispatchToProps(dispatch) {
    return bindActionCreators({
        set_value,
        set_stats,
        set_watched_rank,
        unset_watched_rank,
        get_execution
    }, dispatch);
}

export default withStyles(styles)(
    connect(
        mapStateToProps, 
        mapDispatchToProps
    )(ChimbukoApp)
);
