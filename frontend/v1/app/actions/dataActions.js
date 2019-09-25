import axios from 'axios';

export function set_value(key, value) {
    return {
        type: "SET_VALUE",
        payload: {key, value}
    };
}

export function set_stats(newStats) {
    return {
        type: "SET_STATS",
        payload: newStats
    };
}

export function set_watched_rank(rank) {
    return {
        type: "SET_WATCHED_RANK",
        payload: rank
    };
}

export function unset_watched_rank(rank) {
    return {
        type: "UNSET_WATCHED_RANK",
        payload: rank
    };
}

export function get_execution(pid, rid, min_timestamp, max_timestamp) {
    return dispatch => {
        const arg1 = `pid=${pid}&rid=${rid}`;
        const arg2 = `min_ts=${min_timestamp}&max_ts=${max_timestamp}`;
        const arg3 = `order=desc&with_comm=0`;
        const url = `/events/query_executions?${arg1}&${arg2}&${arg3}`;
        axios.get(url)
            .then(resp => {
                dispatch({
                    type: "SET_VALUE",
                    payload: {
                        "key": "execdata_config",
                        "value": {pid, rid, min_timestamp, max_timestamp}
                    }
                });
            })
            .catch(e => {
                dispatch({
                    type: "GET_EXECUTION_REJECTED",
                    payload: e
                });
            });
    };
}

export function set_execution(data) {
    return {
        type: "SET_EXECUTION_DATA",
        payload: data
    };
}
