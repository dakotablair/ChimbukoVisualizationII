import {combineReducers} from 'redux';

const INIT_STATE = {
    /*
     *  in-situ mode
     */
    anomaly_stats: []
};

const set_value = (state, payload) => {
    const {key, value} = payload;
    if (state.hasOwnProperty(key))
        return {...state, [key]: value};
    return state;
};

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
