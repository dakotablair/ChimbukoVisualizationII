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
        const { d, showLabel, commScale, xScale, yScale, highlight } = this.props;
        const {r, g, b} = rgb;
        
        const rect_stroke = highlight
            ? {stroke: 'red', strokeWidth: 1, strokeOpacity: 1}
            : {};
        const bg = (d.hasOwnProperty('is_anomaly') ? ((d.is_anomaly === true) ? "red": "black"): "black");
        const text_color = bg;

        // todo: smartly determine tooltip position... how??
        // - depends on mouse cursor position.
        let tooltip_w = Math.max(parseFuncName(d.func).length*6, 156);  // assume 6 is character width
        let tooltip_h = 90;
        let tooltip_offset_y = 0;
        let tooltip_offset_x = 0;
        if (y + tooltip_h + 10 > yScale.range()[1] - height/2) {
            tooltip_offset_y =  -(y + tooltip_h + 10 - yScale.range()[1]);
        }
        if (x + width + tooltip_w + 10 > xScale.range()[1] - tooltip_w/2) {
            //tooltip_w = -150;
            tooltip_offset_x = -tooltip_w;
        }
        console.log(parseFuncName(d.func).length, tooltip_w, tooltip_h, tooltip_offset_x, tooltip_offset_y);
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
                    fillOpacity={opacity}
                    {...rect_stroke}
                />
                <text
                    x={Math.max(x, 0)}
                    y={y + height/2 + 5}
                    {...font}
                    fill={text_color}
                >
                    { (showLabel)
                        ? parseFuncName(d.func)
                        : ""
                    }
                </text>
                <Tooltip triggerRef={this.rect}>
                    <rect x={tooltip_offset_x + 5} y={5 + tooltip_offset_y} width={tooltip_w} height={tooltip_h} rx={0.5} ry={0.5} fill={bg} opacity={0.8}></rect>
                    <text x={tooltip_offset_x + 10} y={10 + tooltip_offset_y} fontSize={12} fontFamily="Verdana" dy={0} fill='white'>
                        <tspan x={tooltip_offset_x + 10} dy=".6em">{parseFuncName(d.func)}</tspan>
                        <tspan x={tooltip_offset_x + 10} dy="1.2em">{`EVENT_ID: ${d.event_id}`}</tspan>
                        <tspan x={tooltip_offset_x + 10} dy="1.2em">{`Entry: ${moment(d.entry/1000).format('h:mm:ss.SSS a') }`}</tspan>
                        <tspan x={tooltip_offset_x + 10} dy="1.2em">{`Exit: ${moment(d.exit/1000).format('h:mm:ss.SSS a')}`}</tspan>
                        <tspan x={tooltip_offset_x + 10} dy="1.2em">{`Runtime: ${(d.exit-d.entry)/1000} ms`}</tspan>
                        <tspan x={tooltip_offset_x + 10} dy="1.2em">{`Label: ${d.is_anomaly}`}</tspan>
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
        const { xScale, yScale, rankScale, colors, font, selected } = this.props;

        const maxLength = xScale.range()[1];
        const nodeHeight = Math.abs(yScale(1) - yScale(0));
        const nodes = [];
        Object.keys(this.props.nodes).forEach(key => {
            const node = this.props.nodes[key];
            const x = xScale(node.entry),
                  y = yScale(node.level),
                  w = Math.max(xScale(node.exit) - x, 1); // at least with width 5
                  //nodeHeight = Math.abs(yScale(node.level + 1) - y);
            const len = Math.min(xScale(node.exit), maxLength)- Math.max(x, 0);
            const showName = xScale(node.exit) > 30 && len >= 50;  
            const highlight = (selected && selected === node.event_id) ? true: false;     
            nodes.push(
                <TreeNode
                    key={`node-${key}`}
                    d={node}
                    x={x}
                    y={y}
                    xScale={xScale}
                    yScale={yScale}
                    commScale={rankScale}
                    width={w}
                    height={nodeHeight}
                    rgb={colors[node.fid]}
                    opacity={0.3}
                    showLabel={showName}
                    highlight={highlight}
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
