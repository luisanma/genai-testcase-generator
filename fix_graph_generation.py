#!/usr/bin/env python
"""
Script to fix the graph.html generation
"""
import os
import json
import networkx as nx

def generate_graph_html():
    # Check if the website structure file exists
    structure_file = "app/static/website_structure.json"
    if not os.path.exists(structure_file):
        print("Error: No website structure found.")
        return False
        
    # Load the website structure
    with open(structure_file, 'r', encoding='utf-8') as f:
        structure = json.load(f)
    
    print(f"Loaded structure for website: {structure['url']}")
    
    # Create a directed graph
    G = nx.DiGraph()
    
    # Add nodes
    nodes_data = []
    for url, page_info in structure['pages'].items():
        title = page_info.get('title', 'No Title')
        path = page_info.get('path', '/')
        depth = page_info.get('depth', 0)
        
        # Use shortened labels for better visualization
        label = path[:15] + "..." if len(path) > 15 else path
        if label == "" or label == "/":
            label = "Home"
        
        # Add node to graph
        G.add_node(url, title=title, path=path, depth=depth)
        
        # Create node object for visualization
        tooltip = f"<div><strong>{title}</strong><br>{url}</div>"
        node_obj = {
            "id": url,
            "label": label,
            "title": tooltip,
            "value": (10-depth) * 2,
            "level": depth,
            "url": url,
            "color": "#4CAF50" if depth == 0 else "#2196F3"
        }
        nodes_data.append(node_obj)
    
    # Add edges
    edges_data = []
    for url, page_info in structure['pages'].items():
        parent = page_info.get('parent')
        if parent:
            G.add_edge(parent, url)
            edges_data.append({
                "from": parent,
                "to": url
            })
    
    # Create the HTML template
    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Website Structure Visualization</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/vis-network@9.1.2/dist/dist/vis-network.min.css">
    <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vis-network@9.1.2/dist/vis-network.min.js"></script>
    <style type="text/css">
        html, body {
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
        }
        #mynetwork {
            width: 100%;
            height: 100%;
        }
        #debug-info {
            position: absolute;
            top: 5px;
            right: 5px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 5px;
            font-size: 12px;
            z-index: 1000;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <div id="debug-info">Vis.js Network Graph</div>
    <div id="mynetwork"></div>
    <script type="text/javascript">
        // Create nodes and edges
        var nodes = new vis.DataSet({nodes});
        var edges = new vis.DataSet({edges});
        
        // Create container and data
        var container = document.getElementById("mynetwork");
        var data = {
            nodes: nodes,
            edges: edges
        };
        
        // Create network
        var options = {options};
        window.network = new vis.Network(container, data, options);
        
        // Network events
        window.network.on("click", function(params) {
            if (params.nodes.length > 0) {
                var nodeId = params.nodes[0];
                var node = window.network.body.data.nodes.get(nodeId);
                console.log("Node clicked:", node);
                
                // Send message to parent window
                window.parent.postMessage({
                    type: 'nodeClick',
                    nodeId: nodeId,
                    nodeName: node.label || 'Unknown',
                    nodeUrl: node.url || nodeId
                }, '*');
                
                // Highlight selected node
                var allNodes = nodes.get();
                var updatedNodes = [];
                
                allNodes.forEach(function(n) {
                    if (n.id === nodeId) {
                        n.color = '#e91e63';
                        n.font = { color: '#ffffff' };
                        n.borderWidth = 2;
                    } else {
                        n.color = n.level === 0 ? '#4CAF50' : '#2196F3';
                        n.font = { color: '#000000' };
                        n.borderWidth = 1;
                    }
                    updatedNodes.push(n);
                });
                
                nodes.update(updatedNodes);
            }
        });
        
        // Log that network is ready
        console.log('Graph loaded and network initialized');
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded, checking network');
            setTimeout(function() {
                if (typeof window.network !== 'undefined') {
                    console.log('Network is available');
                    document.getElementById('debug-info').innerHTML = 'Network loaded successfully';
                    document.getElementById('debug-info').style.background = 'rgba(0,128,0,0.7)';
                }
            }, 1000);
        });
    </script>
</body>
</html>
    """
    
    # Options for the visualization
    options = {
        "nodes": {
            "font": {"size": 12},
            "borderWidth": 1,
            "shadow": True
        },
        "edges": {
            "color": {
                "color": "#1E90FF",
                "highlight": "#FF0000"
            },
            "smooth": {
                "type": "continuous"
            },
            "arrows": {
                "to": {
                    "enabled": True,
                    "scaleFactor": 0.5
                }
            }
        },
        "physics": {
            "barnesHut": {
                "gravitationalConstant": -80000,
                "springLength": 250,
                "springConstant": 0.001
            },
            "maxVelocity": 50
        },
        "interaction": {
            "hover": True,
            "navigationButtons": True,
            "keyboard": True,
            "selectConnectedEdges": True
        }
    }
    
    # Replace placeholders with actual JSON data
    html_content = html_template.replace("{nodes}", json.dumps(nodes_data))
    html_content = html_content.replace("{edges}", json.dumps(edges_data))
    html_content = html_content.replace("{options}", json.dumps(options))
    
    # Save the HTML file
    graph_file = "app/static/graph.html"
    with open(graph_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Graph visualization saved to {graph_file}")
    return True

if __name__ == "__main__":
    print("Generating graph visualization...")
    if generate_graph_html():
        print("Graph visualization generated successfully!")
    else:
        print("Failed to generate graph visualization.") 