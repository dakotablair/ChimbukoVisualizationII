import React from 'react';
import PropTypes from 'prop-types';

import moment from 'moment';

import * as d3 from 'd3';

import { fitWidth, getRandomColor } from '../utils';
import { data } from '../utils/sample'

import { CallStackTreeNode, Axis, Brush } from './components';

// const process_data = fulldata => {
//     const execdata = fulldata.exec;

//     // back-end will send data in descending order based on entry time
//     execdata.sort((a, b) => b.entry - a.entry);

//     // convert to object (hashmap)
//     const nodes = {};
//     execdata.forEach(d => nodes[d.key] = d);

//     const forest = {};
//     const traverse = (d, range) => {
//         if (d == null) {
//             return {level: 0, treeid: "root"};
//         }

//         range[0] = Math.min(range[0], d.entry);
//         range[1] = Math.max(range[1], d.exit);

//         if (d.level != null) {
//             return {level: d.level + 1, treeid: d.treeid};
//         } 

//         let {level, treeid} = traverse(nodes[d.parent], range);
//         if (treeid === "root")
//             treeid = d.key;
//         d.level = level;
//         d.treeid = treeid;
//         return {level: d.level + 1, treeid: d.treeid};
//     };

//     execdata.forEach(d => {
//         const range = [Infinity, -Infinity];
//         const {level, treeid} = traverse(d, range);
//         if (forest[treeid] == null) {
//             forest[treeid] = {
//                 id: treeid,
//                 height: 0,
//                 count: 0,
//                 nodes: {},
//                 min_ts: Infinity,
//                 max_ts: -Infinity
//             };
//         }
//         const tree = forest[treeid];
//         tree.height = Math.max(level, tree.height);
//         tree.count++;
//         tree.min_ts = Math.min(tree.min_ts, range[0]);
//         tree.max_ts = Math.max(tree.max_ts, range[1]);
//         tree.nodes[d.key] = {...d};
//     });

//     // console.log(forest)
//     return forest;
// }

class TemporalCallStack extends React.Component
{
    constructor(props) {
        super(props);
        this.state = {
            focused: null
        };
        this.svg = null;
    }

    setGraph = tree => {
        /*
            tree: {id: -1, nodes: [], edges: [], node_index: ?}
            node: {
                level: number,
                messages: [{
                    'source-node-id': string or unique id,
                    'destination-node-id': string or unique id
                }]
            }
        */
        // this.graph = tree;
        // this.graphId = tree.id;
   
        // if (this.graph.nodes.length == 0)
        //     return;

        // const contextNode = new Set();
        // this.messages = [];

        // let maxLevel = 0;
        // this.graph.nodes.forEach(node => {
        //     maxLevel = Math.max(node.level, maxLevel);
        //     node.messages.forEach(m => {
        //         m.level = node.level;
        //         this.messages.push(m);
        //         contextNode.add(m['src']);
        //         contextNode.add(m['dst']);
        //     });
        // });
        // contextNode.delete(this.graph['node_index']);
        // this.timelines = Array.from(contextNode);
        // this.resetAxis(maxLevel);
        // this.resetSVGs(maxLevel);
    }

    handleTimeSelection = s => {
        if (s == null) {
            this.setState({focused: s});
            return;
        }

        const {focused: f} = this.state;
        const dx0 = f == null ? s[0]: Math.abs(f[0] - s[0]);
        const dx1 = f == null ? s[1]: Math.abs(f[1] - s[1]);
        if ( dx0 + dx1 > 20 )
            this.setState({focused: s});
    }

    render() {
        const { margin, colors } = this.props;
        const { height:treeHeight, min_ts, max_ts, nodes } = this.props.tree;

        const mainWidth = this.props.width - margin.left - margin.right;
        const mainHeight = this.props.height - margin.top - margin.bottom - 30;
        const xScale = d3.scaleLinear()
                        .range([0, mainWidth])
                        .domain([min_ts, max_ts]);

        const yScale = d3.scaleLinear()
                        .range([30, mainHeight])
                        .domain([0, treeHeight]);        

        const focusedDomain = this.state.focused
            ? this.state.focused.map(d => xScale.invert(d))
            : [min_ts, max_ts];
    
        const xScaleFocused = d3.scaleLinear()
                                .range([0, mainWidth])
                                .domain(focusedDomain);

        const brushExtent = [
            [0, -30], [mainWidth, -1]
        ];

        return (
            <svg
                ref={svg => this.svg = svg}
                width={this.props.width}
                height={this.props.height}
            >
                <g transform={`translate(${margin.left}, ${margin.top})`}>
                    <Axis 
                        title={"Time"}
                        width={mainWidth}
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
                        width={mainWidth}
                        domain={focusedDomain}
                        options={{
                            tick: {
                                ticks: 10,
                                tickSizeOuter: 0,
                                tickPadding: 4,
                                tickFormat: d => moment(d/1000).format('ss.SSS')    
                            }
                        }}       
                        ty={30}                 
                    />
                    <defs>
                        <clipPath id="focused-area-clip">
                            <rect x={0} y={30} width={mainWidth} height={mainHeight} />
                        </clipPath>
                    </defs>
                    <CallStackTreeNode 
                        nodes={nodes}
                        xScale={xScaleFocused}
                        yScale={yScale}
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
