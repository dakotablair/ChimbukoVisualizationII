export function set_value(key, value) {
    return {
        type: "SET_VALUE",
        payload: {key, value}
    };
}

