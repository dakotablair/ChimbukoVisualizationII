import { createSelector } from 'reselect';

const empty_tree = (treeid="root") => {
    return {
        id: treeid,
        height: 0,
        count: 0,
        nodes: {},
        min_ts: Infinity,
        max_ts: -Infinity,
        ranks: new Set()
    };
}

export const executionTree = createSelector(
    [
        state => state.data.node_key,
        state => state.data.execdata,
    ],
    (node_key, execdata) => {
        console.log("...run executionTree...");

        let exec = null; 
        execdata.forEach(d => {
            // console.log("node_key " + node_key);
            // console.log(d.event_id);
            if (d.event_id == node_key)
                exec = d;
        });

        if (exec == null)
            return empty_tree();

        console.log("...continued...");
        console.log(exec);

        // merge call_stack and exec_window
        const nodes = [];
        const seen = {}; // hash table for duplicity check
        const max_height = 15; // to control the level of call stack
        exec.call_stack.forEach( (d, i) => {
            if (i < max_height) {
                if (d.exit == 0)
                    d.exit = exec.io_step_tend;
                seen[d.event_id] = true;
                nodes.push(d);
            }
        });
        const range = [exec.entry, exec.exit]; // range of the local window
        exec.event_window['exec_window'].forEach(d => {
            if (d.exit == 0)
                d.exit = exec.io_step_tend;
            if (!seen.hasOwnProperty(d.event_id)) {
                nodes.push(d);
                seen[d.event_id] = true;
            }
            if (d.entry < range[0])
                range[0] = d.entry;
            if (d.exit > range[1])
                range[1] = d.exit;
        });
        // when no event_window events, restore range to time frame
        if (range[0] == exec.entry && range[1] == exec.exit) {
            range[0] = exec.io_step_tstart;
            range[1] = exec.io_step_tend;
        }

        // prepare time list
        const times = [];
        nodes.forEach((d, i) => {
            times.push([d.entry, 'entry', i]);
            times.push([d.exit, 'exit', i]);
        });
        // sort the time list
        times.sort((a, b) => a[0] - b[0]); // ASC order

        // prepare comm by key
        const comm = {};
        exec.event_window['comm_window'].forEach(d => {
            const key = d.execdata_key;
            if (comm[key] == null)
                comm[key] = [];
            comm[key].push(d); // key and comm is one-to-many
        });
        
        //console.log("nodes:");
        //console.log(nodes);
        //console.log("comm");
        //console.log(comm);

        const tree = empty_tree(nodes[times[0][2]].event_id);
        tree.count = nodes.length;

        let level = 0;
        let max_level = 0;
        
        for (let i = 0; i < times.length; i++) {
            const t = times[i];
            if (t[1] == 'entry') {
                const _node = nodes[t[2]];
                //_node.key = _node.event_id;
                //_node.name = _node.func;
                _node.level = level++;
                if (max_level < level)
                    max_level = level; 
                let _comm = [];
                if (comm[_node.event_id] != null)
                    _comm = comm[_node.event_id];
                tree.nodes[_node.event_id] = {
                    ..._node,
                    'comm': [..._comm]
                };
                // console.log("added ", _node.key);
                _comm.forEach(c => {
                    tree.ranks.add(c.src);
                    tree.ranks.add(c.tar);
                });
            }
            else // 'exit'
                level--;       
        }

        tree.height = max_level;
        tree.min_ts = range[0];
        tree.max_ts = range[1];

        // console.log("tree: ");
        // console.log(tree);
        return tree;
    }
);
