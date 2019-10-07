import React from 'react';
import PropTypes from 'prop-types';

import * as d3 from 'd3';

class Axis extends React.Component
{
    constructor(props) {
        super(props);
        this.state = {};
        this.g = null;
    }

    componentDidMount() {
        this.renderAxis();
    }

    componentDidUpdate() {
        this.renderAxis();
    }

    renderAxis = () => {
        const { width, domain, title, direction } = this.props;
        const { tick } = this.props.options

        const scale = d3.scaleLinear()
                        .range([0, width])
                        .domain(domain);

        const xAxis = d3.select(this.g);
        
        const createAxis = () => {

        };

        let axis;
        if (direction === 'top')
            axis = d3.axisTop;
        else if (direction === 'bottom')
            axis = d3.axisBottom;
        else
            axis = d3.axisTop;
    

        xAxis.selectAll("text.label").remove();
        xAxis.call(
            axis(scale).ticks(tick.ticks)
                .tickSizeOuter(tick.tickSizeOuter)
                .tickPadding(tick.tickPadding)
                .tickFormat(tick.tickFormat)            
        ).append("text")
            .attr("class", "label")
            .attr("x", width)
            .attr("y", -10)
            .style("text-anchor", "end")
            .text(title)
            .attr("fill", "black");
    }

    render() {
        return (
            <g 
                ref={g => this.g = g} 
                style={this.props.style}
                transform={`translate(${this.props.tx}, ${this.props.ty})`}
            >
            </g>
        );
    }
};

Axis.defaultProps = {
    title: "Axis",
    direction: "top",
    options: {
        tick: {
            ticks: 10,
            tickSizeOuter: 0,
            tickPadding: 10,
            tickFormat: d => d
        }
    },
    tx: 0,
    ty: 0
};

Axis.propTypes = {
    width: PropTypes.number.isRequired,
    domain: PropTypes.arrayOf(PropTypes.number).isRequired,
    title: PropTypes.string,
    direction: PropTypes.oneOf(["top", "bottom"]),
    options: PropTypes.object,
    tx: PropTypes.number,
    ty: PropTypes.number
}

export default Axis;

