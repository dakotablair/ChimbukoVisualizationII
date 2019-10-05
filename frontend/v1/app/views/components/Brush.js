import React from 'react';
import PropTypes from 'prop-types';

import * as d3 from 'd3';

class Brush extends React.Component
{
    constructor(props) {
        super(props);
        this.state ={};
        this.g = null;
    }

    componentDidMount() {
        this.renderBrush();
    }

    componentDidUpdate() {
        this.renderBrush();
    }

    shouldComponentUpdate(nextProps, nextState){
        return false;
    }

    renderBrush = () => {
        const { extent, selection, onSelection } = this.props;
        const brush = 
            d3.brushX()
                .extent(extent)
                .on("brush end", () => {
                    const s = d3.event.selection || selection;
                    if (selection == null || s[0] !== selection[0] || s[1] !== selection[1]) {
                        if (onSelection)
                            onSelection(s);
                    }
                });
        const g = d3.select(this.g);
        g.attr("class", "brush")
            .call(brush)
            .call(brush.move, selection);
    }

    render() {
        return (
            <g ref={g => this.g=g}>

            </g>
        );
    }
};

export default Brush;
