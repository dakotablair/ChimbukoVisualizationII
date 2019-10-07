import React from 'react';
import PropTypes from 'prop-types';

import { parseFuncName } from '../../utils';

// import Tooltip from './Tooltip';
import { Tooltip } from 'react-svg-tooltip';
import moment from 'moment';


class CommArrow extends React.Component
{
    constructor(props) {
        super(props);
        this.state = {};
        this.line = React.createRef();
    }

    render() {
        const {d, x, y1, y2} = this.props;
        return (
            <g>
                <line
                    ref={this.line}
                    x1={x} y1={y1}
                    x2={x} y2={y2}
                    stroke={'black'}
                    strokeWidth={1}
                    markerEnd="url(#arrow)"
                />            
                <Tooltip triggerRef={this.line}>
                    <rect x={5} y={5} width={80} height={50} rx={0.5} ry={0.5} fill={'black'} opacity={0.8}></rect>
                    <text x={10} y={10} fontSize={12} fontFamily="Verdana" dy={0} fill='white'>
                        <tspan x={10} dy=".6em">{`type: ${d.type}`}</tspan>
                        <tspan x={10} dy="1.2em">{`tag: ${d.tag}`}</tspan>
                        <tspan x={10} dy="1.2em">{`size: ${d.bytes} bytes`}</tspan>
                        {/* <tspan x={10} dy="1.2em">{`${moment(d.timestamp/1000).format('h:mm:ss.SSS a')}`}</tspan> */}
                    </text>
                </Tooltip>
            </g>
        );
    }
}


class TreeNode extends React.Component
{
    constructor(props) {
        super(props);
        this.state = {};
        this.rect = React.createRef();
    }

    render() {
        const {x, y, width, height, rgb, opacity, font} = this.props;
        const { d, showLabel, commScale, xScale } = this.props;
        const {r, g, b} = rgb;
        
        const bg = (d.label === 1) ? "black": "red";

        // todo: smartly determine tooltip position... how??
        // - depends on mouse cursor position.
        
        const comm = [];
        d.comm.forEach( (_comm, i) => {
            const {rid, src, tar, timestamp} = _comm;
            const _x = xScale(timestamp);
            let y1 = (rid === src) ? y + height: commScale(src);
            let y2 = (rid === tar) ? y + height: commScale(tar);            
            comm.push(
                <CommArrow 
                    key={`comm-${i}`}
                    d={_comm}
                    x={_x}
                    y1={y1}
                    y2={y2}
                />
            );
            // comm.push(<line
            //     key={`comm-${i}`}
            //     x1={_x}
            //     y1={y1}
            //     x2={_x}
            //     y2={y2}
            //     stroke={'black'}
            //     strokeWidth={1}
            //     markerEnd="url(#arrow)"
            // />);
        });

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
                <text
                    x={Math.max(x, 0)}
                    y={y + height/2 + 5}
                    {...font}
                >
                    { (showLabel)
                        ? parseFuncName(d.name)
                        : ""
                    }
                </text>
                <Tooltip triggerRef={this.rect}>
                    <rect x={5} y={5} width={150} height={150} rx={0.5} ry={0.5} fill={bg} opacity={0.8}></rect>
                    <text x={10} y={10} fontSize={12} fontFamily="Verdana" dy={0} fill='white'>
                        <tspan x={10} dy=".6em">{parseFuncName(d.name)}</tspan>
                        <tspan x={10} dy="1.2em">{`Rank: ${d.rid}`}</tspan>
                        <tspan x={10} dy="1.2em">{`Thread: ${d.tid}`}</tspan>
                        <tspan x={10} dy="1.2em">{`Entry: ${moment(d.entry/1000).format('h:mm:ss.SSS a') }`}</tspan>
                        <tspan x={10} dy="1.2em">{`Exit: ${moment(d.exit/1000).format('h:mm:ss.SSS a')}`}</tspan>
                        <tspan x={10} dy="1.2em">{`Runtime: ${d.runtime} usec`}</tspan>
                        <tspan x={10} dy="1.2em">{`Exclusive: ${d.exclusive} usec`}</tspan>
                        <tspan x={10} dy="1.2em">{`# Children: ${d.n_children}`}</tspan>
                        <tspan x={10} dy="1.2em">{`# Messages: ${d.n_messages}`}</tspan>
                        <tspan x={10} dy="1.2em">{`Label: ${d.label}`}</tspan>
                    </text>
                </Tooltip>
                
                {comm}
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
        const { xScale, yScale, rankScale, colors, font } = this.props;

        const maxLength = xScale.range()[1];
        const nodeHeight = yScale(1) - yScale(0);
        const nodes = [];
        Object.keys(this.props.nodes).forEach(key => {
            const node = this.props.nodes[key];
            const x = xScale(node.entry),
                  y = yScale(node.level),
                  w = xScale(node.exit) - x;
            const len = Math.min(xScale(node.exit), maxLength)- Math.max(x, 0);
            const showName = xScale(node.exit) > 30 && len >= 50;       
            nodes.push(
                <TreeNode
                    key={`node-${key}`}
                    d={node}
                    x={x}
                    y={y}
                    xScale={xScale}
                    commScale={rankScale}
                    width={w}
                    height={nodeHeight}
                    rgb={colors[node.fid]}
                    opacity={0.3}
                    showLabel={showName}
                    font={font}
                />
            );        
        });

        return (
            <g 
                transform={`translate(${this.props.tx}, ${this.props.ty})`}
                style={this.props.style}
            >
                {nodes}
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
