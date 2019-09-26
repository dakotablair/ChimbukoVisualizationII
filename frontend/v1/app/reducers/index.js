import {combineReducers} from 'redux';

const INIT_STATE = {
    // anomaly statistics
    stats: {},
    stats_colors: {},

    // anomaly history
    watched_ranks: {},

    // execution data 
    // - descending order on entry time
    func_colors: {},
    execdata_config: {
        pid: -1,
        rid: -1,
        step: -1,
        min_timestamp: -1,
        max_timestamp: -1
    },
    execdata: []
};

const getRandomColor = () => {
    return {
        r: Math.floor(Math.random() * 255),
        g: Math.floor(Math.random() * 255),
        b: Math.floor(Math.random() * 255)
    }
};

const set_value = (state, payload) => {
    const {key, value} = payload;
    if (state.hasOwnProperty(key))
        return {...state, [key]: value};
    return state;
};

const set_stats = (state, newStats) => {
    if (!newStats.hasOwnProperty('data'))
        return state;

    const { stats_colors } = state;

    newStats.data.forEach(dataset => {
        const name = dataset.name;
        if (dataset.hasOwnProperty('color'))
            stats_colors[name] = {...dataset.color};
        else if (stats_colors.hasOwnProperty(name))
            dataset['color'] = stats_colors[name];
        else {
            const color = getRandomColor();
            stats_colors[name] = color;
            dataset['color'] = color;
        }
    });

    return {...state, stats: newStats, stats_colors: stats_colors};
};

const set_execdata = (state, newData) => {
    const { func_colors:colors } = state;
    newData.forEach(d => {
        if (!colors.hasOwnProperty(d.fid)) {
            colors[d.fid] = getRandomColor();
        }
    });
    return {...state, execdata: newData, func_colors: colors};
}

const set_rank = (state, rank) => {
    const { watched_ranks: ranks } = state;
    if (!ranks.hasOwnProperty(rank))
        ranks[rank] = getRandomColor();
    return {...state, watched_ranks: {...ranks}};
}

const unset_rank = (state, rank) => {
    const { watched_ranks: ranks } = state;
    if (ranks.hasOwnProperty(rank))
        delete ranks[rank];
    return {...state, watched_ranks: {...ranks}};
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
