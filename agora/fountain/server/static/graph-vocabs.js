/**
 * Created by fserena on 3/06/15.
 */

$(function () { // on dom ready

    var cy = cytoscape({
        container: document.getElementById('cy'),

        style: cytoscape.stylesheet()
            .selector('node')
            .css({
                'content': 'data(label)',
                'color': '#d0d0d0',
                'shape': 'data(shape)',
                'width': 'mapData(width, 1, 150, 1, 150)',
                'height': '40',
                'text-valign': 'center',
                'text-outline-width': 2,
                'text-outline-color': '#303030',
                'background-color': '#303030'
            })
            .selector('edge')
            .css({
                'target-arrow-shape': 'triangle',
                'width': 3,
                'line-color': '#555',
                'target-arrow-color': '#aaa',
                'content': 'data(label)',
                'color': '#f0f0f0'
            })
            .selector('node.highlighted')
            .css({
                'background-color': '#037',
                'transition-property': 'background-color, line-color, target-arrow-color, color',
                'transition-duration': '0.5s',
                'color': 'white'
            }).selector('edge.subclass')
            .css({
                'line-style': 'dashed',
                'source-arrow-shape': 'triangle',
                'source-arrow-fill': 'hollow',
                'target-arrow-shape': 'none'
            }).selector('node.seed')
            .css({
                'border-color': '#08f',
                'border-width': 5,
                'border-opacity': 0.7,
                'background-color': '#06a'
            }),

        elements: {
            nodes: vGraph.nodes,
            edges: vGraph.edges
        }
    });

    var options = {
        name: 'arbor',

        animate: true, // whether to show the layout as it's running
        maxSimulationTime: 4000, // max length in ms to run the layout
        fit: false, // on every layout reposition of nodes, fit the viewport
        padding: 30, // padding around the simulation
        boundingBox: {x1: 0, y1: 0, w: 3000, h: 3000}, // constrain layout bounds; { x1, y1, x2, y2 } or { x1, y1, w, h }
        ungrabifyWhileSimulating: false, // so you can't drag nodes during layout

        // callbacks on layout events
        ready: undefined, // callback on layoutready
        stop: undefined, // callback on layoutstop

        // forces used by arbor (use arbor default on undefined)
        repulsion: 2500,
        stiffness: undefined,
        friction: 0.9,
        gravity: true,
        fps: undefined,
        precision: 0.9,

        // static numbers or functions that dynamically return what these
        // values should be for each element
        // e.g. nodeMass: function(n){ return n.data('weight') }
        nodeMass: undefined,
        edgeLength: undefined,

        stepSize: 0.2, // smoothing of arbor bounding box

        // function that returns true if the system is stable to indicate
        // that the layout can be stopped
        stableEnergy: function (energy) {
            var e = energy;
            return (e.max <= 0.5) || (e.mean <= 0.3);
        },

        // infinite layout options
        infinite: true // overrides all other options for a forces-all-the-time mode
    };

    cy.layout(options);

    cy.bfs = [];

    vGraph.roots.forEach(function (r, index) {
        cy.bfs.push(
            {
                index: index,
                bfs: cy.elements().bfs('#' + vGraph.roots[index], function () {
                }, true)
            }
        );
    });

    var highlightNextEle = function (b) {
        b.bfs.path[b.index].addClass('highlighted');

        if (b.index < b.bfs.path.length) {
            b.index++;
            setTimeout(function () {
                highlightNextEle(b);
            }, 200);
        }
    };

    // kick off first highlights
    cy.bfs.forEach(function (b) {
        highlightNextEle(b);
    });


}); // on dom ready