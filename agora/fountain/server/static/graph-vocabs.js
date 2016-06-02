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
                'shape': 'data(shape)',
                'width': 'mapData(width, 10, 500, 10, 500)',
                'height': '40',
                'text-valign': 'center',
                'background-color': 'white',
                'background-opacity': 0.2,
                'font-family': 'Monoxil',
                'font-size': '16px',
                'color': '#484849',
                'border-width': 2,
                'border-opacity': 0.7,
                'font-weight': 'regular',
                'shadow-color': '#484849',
                'shadow-opacity': 0.5,
                'shadow-offset-x': 0,
                'shadow-offset-y': 0,
                'shadow-blur': 2
            })
            .selector('edge')
            .css({
                'target-arrow-shape': 'triangle',
                'line-color': '#484849',
                'target-arrow-color': '#484849',
                'content': 'data(label)',
                'color': '#484849',
                'edge-text-rotation': 'autorotate',
                'text-valign': 'top',
                'text-wrap': 'wrap',
                'curve-style': 'bezier',
                'font-family': 'Monoxil',
                'font-size': '14px'
            }).selector('edge.subclass')
            .css({
                'line-style': 'dashed',
                'source-arrow-shape': 'triangle',
                'source-arrow-fill': 'hollow',
                'target-arrow-shape': 'none',
                'source-arrow-color': '#484849'
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

    var params = {
        name: 'cola',
        animate: true, // whether to transition the node positions
        // animationDuration: 6000, // duration of animation in ms if enabled
        maxSimulationTime: 8000, // max length in ms to run the layout
        nodeSpacing: 100, // min spacing between outside of nodes (used for radius adjustment)
        edgeLengthVal: 80,
        boundingBox: {x1: 0, y1: 0, w: vGraph.nodes.length * 150, h: vGraph.nodes.length * 150},
        // boundingBox: undefined, // constrain layout bounds; { x1, y1, x2, y2 } or { x1, y1, w, h }
        avoidOverlap: false, // prevents node overlap, may overflow boundingBox if not enough space
        infinite: false,
        fit: false,
        randomize: false
    };

    var layout = makeLayout();
    layout.run();

    function makeLayout(opts) {
        params.randomize = false;
        params.edgeLength = function (e) {
            return 200;
            // return params.edgeLengthVal / e.data('weight');
        };

        for (var i in opts) {
            params[i] = opts[i];
        }

        return cy.makeLayout(params);
    }

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

}); // on dom ready