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

