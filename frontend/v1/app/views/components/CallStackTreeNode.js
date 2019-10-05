import React from 'react';
import PropTypes from 'prop-types';

import { parseFuncName } from '../../utils';

// import Tooltip from './Tooltip';
import { Tooltip } from 'react-svg-tooltip';
import moment from 'moment';

class TreeNode extends React.Component
{
    constructor(props) {
        super(props);
        this.state = {};
        this.rect = React.createRef();
    }

    render() {
        const {x, y, width, height, rgb, opacity} = this.props;
        const {d, xExtent, yExtent} = this.props;
        const {r, g, b} = rgb;
        
        const bg = (d.label === 1) ? "black": "red";

        // todo: smartly determine tooltip position... how??
        // - depends on mouse cursor position.

        return (
            <g>
                <rect
                    ref={this.rect} 
                    x={x}
                    y={y}
                    width={width}
                    height={height}
                    fill={`rgb(${r},${g},${b})`}
                    opacity={opacity}
                />
                <Tooltip triggerRef={this.rect}>
                    <rect x={5} y={5} width={150} height={150} rx={0.5} ry={0.5} fill={bg} opacity={0.8}></rect>
                    <text x={10} y={10} fontSize={12} fontFamily="Verdana" dy={0} fill='white'>
                        <tspan x={10} dy=".6em">{parseFuncName(d.name)}</tspan>
                        <tspan x={10} dy="1.2em">{`Rank: ${d.rid}`}</tspan>
                        <tspan x={10} dy="1.2em">{`Thread: ${d.tid}`}</tspan>
                        <tspan x={10} dy="1.2em">{`Entry: ${moment(d.entry/1000).format('h:mm:ss.SSS a') }`}</tspan>
                        <tspan x={10} dy="1.2em">{`Exit: ${moment(d.exit/1000).format('h:mm:ss.SSS a')}`}</tspan>
                        <tspan x={10} dy="1.2em">{`Runtime: ${d.runtime}`}</tspan>
                        <tspan x={10} dy="1.2em">{`Exclusive: ${d.exclusive}`}</tspan>
                        <tspan x={10} dy="1.2em">{`# Children: ${d.n_children}`}</tspan>
                        <tspan x={10} dy="1.2em">{`# Messages: ${d.n_messages}`}</tspan>
                        <tspan x={10} dy="1.2em">{`Label: ${d.label}`}</tspan>
                    </text>
                </Tooltip>
            </g>           
        );
    }
};

class CallStackTreeNode extends React.Component
{
    constructor(props) {
        super(props);
        this.state = {};
    }

    render() {
        const { xScale, yScale, colors, font } = this.props;

        const maxLength = xScale.range()[1];
        const nodes = [], names = [];
        Object.keys(this.props.nodes).forEach(key => {
            const node = this.props.nodes[key];
            const x = xScale(node.entry),
                  y = yScale(node.level),
                  w = xScale(node.exit) - x,
                  h = yScale(node.level + 1) - y;
            nodes.push(
                <TreeNode
                    key={`node-${key}`}
                    d={node}
                    x={x}
                    y={y}
                    width={w}
                    height={h}
                    rgb={colors[node.fid]}
                    opacity={0.3}
                    xExtent={xScale.range()}
                    yExtent={yScale.range()}
                />
            );        

            const len = Math.min(xScale(node.exit), maxLength)- Math.max(x, 0);
            if (xScale(node.exit) > 30 && len >= 50) {
                const name = parseFuncName(node.name);
                names.push(
                    <text
                        key={`node-name-${key}`}
                        x={Math.max(x, 0)}
                        y={y + h/2 + 5}
                        {...font}
                    >
                        {name}
                    </text>
                );            
            }
        });

        return (
            <g 
                transform={`translate(${this.props.tx}, ${this.props.ty})`}
                style={this.props.style}
            >
                {nodes}
                {names}
            </g>
        );
    }
};

CallStackTreeNode.defaultProps ={
    tx: 0,
    ty: 0,
    font: {
        fontFamily: "Verdana",
        fontSize: 10,
        fill: "black"        
    }
}

export default CallStackTreeNode;
