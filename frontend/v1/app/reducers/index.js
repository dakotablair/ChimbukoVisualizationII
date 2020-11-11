import { combineReducers } from 'redux';
import { getRandomColor } from '../utils';

const INIT_STATE = {
    // anomaly statistics
    stats: {
        statKind: 'mean',
        nQueries: 5
    },
    // stats_colors: {},

    // anomaly history
    watched_ranks: [],
    rank_colors: {},
    history: {},

    // execution data 
    // - descending order on entry time
    func_colors: {},
    func_ids: {},
    execdata_config: {
        app: -1,
        rank: -1,
        step: -1,
        min_timestamp: -1,
        max_timestamp: -1
    },
    execdata: [],
    node_key: null
};

const set_value = (state, payload) => {
    const {key, value} = payload;
    if (state.hasOwnProperty(key))
        return {...state, [key]: value};
    return state;
};

const set_stats = (state, newStats) => {
    return {...state, stats: newStats};
};

const set_execdata = (state, newData) => {
    const { func_colors:colors, func_ids:ids} = state;
    const { config, data } = newData;
    const { exec } = data;
    exec.forEach(d => {
        if (!colors.hasOwnProperty(d.fid)) {
            colors[d.fid] = getRandomColor();
        }
        if (!ids.hasOwnProperty(d.fid)) {
            ids[d.fid] = d.fid;
        }
        d.call_stack.forEach(p => {
            if (!colors.hasOwnProperty(p.fid)) {
                colors[p.fid] = getRandomColor();
            }
        });
        d.event_window.exec_window.forEach(p => {
            if (!colors.hasOwnProperty(p.fid)) {
                colors[p.fid] = getRandomColor();
            }
        });
    });
    let count = 0;
    for (var key of Object.keys(ids)) {
        ids[key] = count++;
    }
    return {...state, 
        execdata: exec, 
        execdata_config: config, 
        func_colors: colors,
        func_ids: ids};
}

const set_rank = (state, rank) => {
    const colors = {...state.rank_colors};
    const ranks = [...state.watched_ranks];
    if (!colors.hasOwnProperty(rank))
        colors[rank] = getRandomColor();
    ranks.push(rank);
    return {...state, watched_ranks: ranks, rank_colors: colors};
}

const unset_rank = (state, rank) => {
    const ranks = [...state.watched_ranks];
    const idx = ranks.indexOf(rank);
    if (idx >= 0)
        ranks.splice(idx, 1);
    return {...state, watched_ranks: [...ranks]};
}


function dataReducers(state = INIT_STATE, action)
{
    const {type, payload} = action;
    
    let _type = type;
    if (_type.includes('REJECTED'))
        _type = "REJECTED"

    switch(_type)
    {
        case "SET_VALUE":
            return set_value(state, payload);

        case "SET_STATS":
            return set_stats(state, payload);

        case "SET_WATCHED_RANK":
            return set_rank(state, payload);

        case "UNSET_WATCHED_RANK":
            return unset_rank(state, payload);

        case "SET_EXECUTION_DATA":
            return set_execdata(state, payload);

        case "REJECTED":
            console.log(payload)
            return state;
        
        default: 
            return state;
    }
}

export default combineReducers({
    data: dataReducers,
});
