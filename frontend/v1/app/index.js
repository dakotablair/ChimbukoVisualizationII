import React from 'react';
import ReactDOM from 'react-dom';
import {Provider} from 'react-redux';
import {createStore, applyMiddleware} from 'redux';
import thunk from 'redux-thunk';
import reducers from "./reducers";
import ChimbukoApp from "./appindex";


const middleware = applyMiddleware(thunk);
const store = createStore(reducers, middleware);

function loadApp() {
    return (
        <Provider store={store}>
            <ChimbukoApp />
        </Provider>
    );
};


ReactDOM.render(
    loadApp(), document.getElementById("app")
);

