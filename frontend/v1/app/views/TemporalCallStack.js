import React from 'react';
import PropTypes from 'prop-types';

import moment from 'moment';

import * as d3 from 'd3';

import { fitWidth } from '../utils';

import { CallStackTreeNode, Axis, Brush } from './components';

class TemporalCallStack extends React.Component
{
    constructor(props) {
        super(props);
        this.state = {
            focused: null
        };
        this.svg = null;
    }

    handleTimeSelection = s => {
        if (s == null) {
            this.setState({focused: s});
            return;
        }

        const {focused: f} = this.state;
        const dx0 = f == null ? s[0]: Math.abs(f[0] - s[0]);
        const dx1 = f == null ? s[1]: Math.abs(f[1] - s[1]);
        if ( dx0 + dx1 > 5 )
            this.setState({focused: s});
    }

    render() {
        const { margin, colors, selected } = this.props;
        const { app: mainApp, rank: mainRank } = this.props.config;
        const { height:treeHeight, min_ts, max_ts, nodes, ranks } = this.props.tree;
        /*
            layout

            (margin.top) overall axis
            (xAxifOffset) focused axis
            (call stack tree area) for main rank (what would be good size, i.e. height for this area??)
            rank axis as many as in 'ranks'
        */
        //console.log(nodes);
        ranks.delete(mainRank);
        const comm_ranks = Array.from(ranks).sort((a, b) => a - b);
        ranks.add(mainRank);

        const axisOffset = 30;  
        const rankAxisOffset = 20;
        const mainWidth = this.props.width - margin.left - margin.right;
        const mainHeight = this.props.height - margin.top - margin.bottom - axisOffset; 

        const cstWidth = mainWidth;
        const cstHeight =  mainHeight - rankAxisOffset * comm_ranks.length;
        const xScale = d3.scaleLinear().range([0, cstWidth]).domain([min_ts, max_ts]);
        const yScale = d3.scaleLinear().range([axisOffset, cstHeight]).domain([0, treeHeight]);        

        comm_ranks.unshift(mainRank);
        const rankScale = d3.scaleOrdinal()
                            .range(comm_ranks.map((_, i) => {
                                if (i === 0)
                                    return axisOffset;
                                return axisOffset + cstHeight + (i-1)*rankAxisOffset;
                            }))
                            .domain(comm_ranks);


        const focusedDomain = this.state.focused
            ? this.state.focused.map(d => xScale.invert(d))
            : [min_ts, max_ts];
    
        const xScaleFocused = d3.scaleLinear().range([0, cstWidth]).domain(focusedDomain);

        const brushExtent = [
            [0, -axisOffset], [cstWidth, -1]
        ];

        const rankAxis = [];
        const rankLabel = [];
        rankLabel.push(<text
            key={`time-axis-label`}
            x={margin.left}
            y={0}
            fontFamily="Verdana"
            fontSize="12"
            textAnchor="end"    
        >
            {"Time"}
        </text>)
        comm_ranks.forEach( (_rank, _i) => {
            if (_rank !== mainRank) {
                const _key = `comm-axis-${_rank}`;
                if (_i < comm_ranks.length - 1)
                {
                    rankAxis.push(<line
                        key={_key}
                        x1={0}
                        y1={rankScale(_rank)}
                        x2={mainWidth}
                        y2={rankScale(_rank)}
                        stroke={"black"}
                    ></line>)
                }
                else
                {
                    rankAxis.push(<Axis
                        key={_key}
                        title={""}
                        width={cstWidth}
                        domain={focusedDomain}
                        options={{
                            tick: {
                                ticks: 10,
                                tickSizeOuter: 0,
                                tickPadding: 2,
                                tickFormat: d => moment(d/1000).format('ss.SSS')
                            }
                        }}
                        ty={rankScale(_rank)}
                        direction={'bottom'}
                    />);    
                }
            }

            rankLabel.push(<text
                key={`Rank-${_rank}`}
                x={margin.left}
                y={rankScale(_rank)}
                fontFamily="Verdana"
                fontSize="12"
                textAnchor="end"
            >
                {`R${_rank}`}
            </text>);
        });

        

        return (
            <svg
                ref={svg => this.svg = svg}
                width={this.props.width}
                height={this.props.height}
            >
                <g transform={`translate(${margin.left}, ${margin.top})`}>
                    <defs>
                        <clipPath id="focused-area-clip">
                            <rect x={0} y={axisOffset} width={mainWidth} height={mainHeight} />
                        </clipPath>
                        <marker 
                            id="arrow"
                            viewBox="0 -4 8 8"
                            refX="8"
                            refY="0"
                            markerWidth="4"
                            markerHeight="4"
                            orient="auto"
                        >
                            <path d="M0,-4L8,0L0,4" />
                        </marker>
                    </defs>
                    <Axis 
                        title={""}
                        width={cstWidth}
                        domain={[min_ts, max_ts]}
                        style={{dominantBaseline: "central"}}
                        options={{
                            tick: {
                                ticks: 5,
                                tickSizeOuter: 0,
                                tickPadding: 10,
                                tickFormat: d => moment(d/1000).format('h:mm:ss.SSS a')    
                            }
                        }}
                    />
                    <Brush 
                        extent={brushExtent}
                        selection={this.state.brushed}
                        onSelection={this.handleTimeSelection}
                    />
                    <Axis
                        title={""}
                        width={cstWidth}
                        domain={focusedDomain}
                        options={{
                            tick: {
                                ticks: 10,
                                tickSizeOuter: 0,
                                tickPadding: 4,
                                tickFormat: d => moment(d/1000).format('ss.SSS')    
                            }
                        }}       
                        ty={axisOffset}                 
                    />
                    {rankAxis}
                    <g transform={`translate(${-margin.left}, 0)`}>
                        {rankLabel}
                    </g>
                    <CallStackTreeNode 
                        nodes={nodes}
                        selected={selected}
                        xScale={xScaleFocused}
                        yScale={yScale}
                        rankScale={rankScale}
                        colors={colors}
                        ty={0}
                        style={{clipPath: "url(#focused-area-clip)"}}
                    />
                </g>
            </svg>
        );
    }
};

TemporalCallStack.defaultProps ={

};

TemporalCallStack.propTypes ={ 

};

TemporalCallStack = fitWidth(TemporalCallStack);
export default TemporalCallStack;
