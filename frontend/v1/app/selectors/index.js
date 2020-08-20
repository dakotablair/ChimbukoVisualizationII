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

export const executionForest = createSelector(
    [
        state => state.data.execdata,
        state => state.data.commdata
    ],
    (execdata, commdata) => {
        const nodes = {}, comm = {};
        execdata.forEach(d.key}); // key and exec is one-to-one
        //---commdata untouched yet
        commdata.forEach(d => {
            const key = d.execdata_key;
            if (comm[key] == null)
                comm[key] = [];
            comm[key].push(d); // key and comm is one-to-many
        });

        const forest = {};
        const traverse = (d, range) => {
            if (d == null)
                return {level: 0, treeid: "root"};
            
            range[0] = Math.min(range[0], d.entry);
            range[1] = Math.max(range[1], d.exit);

            if (d.level != null)
                return {level: d.level + 1, treeid: d.treeid};

            // d.parent must exist in execdata
            let {level, treeid} = traverse(nodes[d.parent], range);
            if (treeid === "root")
                treeid = d.key;
            d.level = level;
            d.treeid = treeid;
            return {level: d.level + 1, treeid: d.treeid};
        };

        execdata.forEach(d => {
            const range = [Infinity, -Infinity];
            const {level, treeid} = traverse(d, range);
            if (forest[treeid] == null) 
                forest[treeid] = empty_tree(treeid);
            
            const tree = forest[treeid];
            tree.height = Math.max(level, tree.height);
            tree.count++;
            tree.min_ts = Math.min(tree.min_ts, range[0]);
            tree.max_ts = Math.max(tree.max_ts, range[1]);
            
            let _comm = [];
            if (comm[d.key] != null)
                _comm = comm[d.key];

            tree.nodes[d.key] = {
                ...d, 
                'comm': [..._comm]
            };
            
            _comm.forEach(c => {
                tree.ranks.add(c.src);
                tree.ranks.add(c.tar);
            });
        });

        return forest;
    }
);

export const executionTree = createSelector(
    [
        state => state.data.node_key,
        state => executionForest(state)
    ],
    (node_key, forest) => {
        let treeid = null;
        Object.keys(forest).forEach(_treeid => {
            const tree = forest[_treeid];
            if (tree.nodes[node_key] != null)
                treeid = tree.id;
        });

        return treeid != null ? forest[treeid]: empty_tree();
    }
);
