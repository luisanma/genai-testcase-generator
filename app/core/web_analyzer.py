import requests
from bs4 import BeautifulSoup
import networkx as nx
import re
import json
import os
import logging
from urllib.parse import urlparse, urljoin
from pyvis.network import Network

# Cambiar la importación para usar ruta relativa
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ml_categorizer import categorizer as ml_categorizer

# Set up logger
logger = logging.getLogger("web-analysis-framework.analyzer")

class WebAnalyzer:
    def __init__(self, url):
        self.url = url
        self.domain = urlparse(url).netloc
        self.graph = nx.DiGraph()
        self.visited = set()
        self.page_content = {}
        self.site_category = None
        self.max_pages = 500  # Aumentado de 10 a 100
        self.hierarchy = {}  # Store hierarchical structure
        self.paths = {}      # Store paths to each node

    def analyze(self):
        """Main analysis method that scrapes the site and builds the graph"""
        logger.info(f"Starting analysis of {self.url}")
        try:
            self._crawl(self.url, depth=0)
            self._categorize_site()
            self._build_hierarchy()
            self._calculate_paths()
            self._generate_graph_visualization()
            self._save_structure_to_json()
            
            logger.info(f"Analysis complete. Found {self.graph.number_of_nodes()} pages")
            
            return {
                "url": self.url,
                "domain": self.domain,
                "category": self.site_category,
                "node_count": self.graph.number_of_nodes(),
                "edge_count": self.graph.number_of_edges(),
                "pages": list(self.graph.nodes()),
                "visualization_path": "static/graph.html",
                "page_content": self.page_content,
                "hierarchy": self.hierarchy,
                "paths": self.paths
            }
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}", exc_info=True)
            raise
    
    def _crawl(self, url, depth=0, parent_url=None):
        """Crawl the website to build the graph"""
        if url in self.visited or depth > 10 or len(self.visited) >= self.max_pages:
            return
        
        self.visited.add(url)
        logger.info(f"Crawling page: {url} (depth: {depth})")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }
            
            # Add timeout and verify=False for testing
            response = requests.get(url, timeout=30, headers=headers, verify=False)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch {url}: HTTP {response.status_code}")
                return
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Store page content for analysis
            page_title = soup.title.text.strip() if soup.title else "No Title"
            page_path = urlparse(url).path or "/"
            
            # Get all text content for better analysis
            text_content = ' '.join([text.strip() for text in soup.stripped_strings])
            
            self.page_content[url] = {
                "title": page_title,
                "path": page_path,
                "depth": depth,
                "headers": [h.text.strip() for h in soup.find_all(['h1', 'h2', 'h3'])],
                "links": [],
                "forms": len(soup.find_all('form')),
                "images": len(soup.find_all('img')),
                "buttons": len(soup.find_all('button')),
                "inputs": len(soup.find_all('input')),
                "text_content": text_content[:1000],  # Increased to 1000 chars for better analysis
                "parent": parent_url
            }
            
            # Add the node to the graph
            self.graph.add_node(url, title=page_title, path=page_path, depth=depth)
            
            # Add edge from parent if exists
            if parent_url:
                self.graph.add_edge(parent_url, url)
            
            # Find all links
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if not href or href.startswith('#') or href.startswith('javascript:'):
                    continue
                    
                # Make absolute URL
                full_url = urljoin(url, href)
                
                # Clean URL fragments and parameters
                full_url = full_url.split('#')[0]
                full_url = full_url.split('?')[0]
                
                # Only follow links within the same domain
                if self.domain not in full_url:
                    continue
                
                # Store the link
                self.page_content[url]["links"].append(full_url)
                
                # Recursively crawl
                self._crawl(full_url, depth + 1, url)
                
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL Error for {url}: {str(e)}")
            # Try again without SSL verification
            try:
                response = requests.get(url, timeout=30, headers=headers, verify=False)
                # Continue with the rest of the processing...
            except Exception as e2:
                logger.error(f"Failed to fetch {url} even without SSL verification: {str(e2)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {str(e)}")
        except Exception as e:
            logger.error(f"Error crawling {url}: {str(e)}")
    
    def _build_hierarchy(self):
        """Build hierarchical structure of the website"""
        logger.info("Building website hierarchy")
        
        # Start with the root URL
        root = self.url
        self.hierarchy = self._build_node_hierarchy(root)
        
    def _build_node_hierarchy(self, node_url):
        """Recursively build hierarchy for a node"""
        children = []
        
        # Find all direct children
        for source, target in self.graph.edges():
            if source == node_url:
                child_hierarchy = self._build_node_hierarchy(target)
                children.append(child_hierarchy)
        
        # Create node representation
        node_info = self.page_content.get(node_url, {})
        return {
            "url": node_url,
            "title": node_info.get("title", "Unknown"),
            "path": node_info.get("path", "/"),
            "depth": node_info.get("depth", 0),
            "children": children
        }
    
    def _calculate_paths(self):
        """Calculate all paths to each node"""
        logger.info("Calculating paths to each node")
        
        # Start with the root URL
        self.paths = {}
        root = self.url
        
        # For each node, find all paths from root
        for node in self.graph.nodes():
            try:
                paths = list(nx.all_simple_paths(self.graph, root, node))
                self.paths[node] = paths
            except nx.NetworkXNoPath:
                self.paths[node] = []
    
    def _save_structure_to_json(self):
        """Save the website structure to a JSON file"""
        try:
            structure = {
                "url": self.url,
                "domain": self.domain,
                "category": self.site_category,
                "hierarchy": self.hierarchy,
                "pages": {}
            }
            
            # Add detailed page info
            for url, content in self.page_content.items():
                structure["pages"][url] = {
                    "title": content.get("title", "Unknown"),
                    "path": content.get("path", "/"),
                    "depth": content.get("depth", 0),
                    "headers": content.get("headers", []),
                    "forms": content.get("forms", 0),
                    "images": content.get("images", 0),
                    "inputs": content.get("inputs", 0),
                    "buttons": content.get("buttons", 0),
                    "parent": content.get("parent", None),
                    "paths": self.paths.get(url, [])
                }
            
            # Ensure directory exists
            os.makedirs("app/static", exist_ok=True)
            
            # Save to file
            with open("app/static/website_structure.json", "w", encoding="utf-8") as f:
                json.dump(structure, f, indent=2)
                
            logger.info("Website structure saved to JSON file")
        except Exception as e:
            logger.error(f"Error saving website structure to JSON: {str(e)}", exc_info=True)
    
    def _categorize_site(self):
        """Determine the category of the website based on its content"""
        logger.info("Categorizing website")
        
        # Combine all text content from pages
        all_text = " ".join([content["text_content"] for content in self.page_content.values()])
        
        # Use ML categorizer if there's enough text
        if len(all_text) > 100:
            # Use ML-based categorization
            self.site_category = ml_categorizer.categorize(all_text)
            logger.info(f"Site categorized as '{self.site_category}' using ML model")
        else:
            # Fallback to keyword-based for very small sites
            logger.info("Insufficient text for ML categorization, using keyword-based method")
            self.site_category = self._keyword_based_categorization(all_text)
        
        # Store category probabilities for UI display
        try:
            # Get category confidence scores if available
            if hasattr(ml_categorizer.model, 'classes_') and len(all_text) > 100:
                processed_text = ml_categorizer.preprocess_text(all_text)
                proba = ml_categorizer.model.predict_proba([processed_text])[0]
                classes = ml_categorizer.model.classes_
                
                # Create sorted list of (category, probability) tuples
                self.category_probabilities = sorted(
                    [{"category": cat, "probability": float(prob)} for cat, prob in zip(classes, proba)],
                    key=lambda x: x["probability"],
                    reverse=True
                )
            else:
                # Fallback if ML model not available
                self.category_probabilities = [{"category": self.site_category, "probability": 1.0}]
        except Exception as e:
            logger.warning(f"Could not calculate category probabilities: {str(e)}")
            self.category_probabilities = [{"category": self.site_category, "probability": 1.0}]

    def _keyword_based_categorization(self, text_content):
        """Traditional keyword-based categorization"""
        # Simple keyword-based categorization for demo
        categories = {
            "e-commerce": ["shop", "cart", "product", "buy", "price", "store", "checkout", "payment"],
            "blog": ["blog", "post", "article", "comment", "author", "publish", "tags", "archive"],
            "news": ["news", "article", "headline", "reporter", "editor", "breaking", "latest", "update"],
            "portfolio": ["portfolio", "project", "work", "skill", "resume", "cv", "showcase", "gallery"],
            "corporate": ["company", "business", "service", "client", "team", "about us", "mission", "values"],
            "educational": ["course", "learn", "student", "teacher", "education", "school", "university", "training"],
            "social": ["profile", "friend", "follow", "share", "connect", "community", "network", "message"],
            "entertainment": ["entertainment", "game", "movie", "music", "play", "stream", "video", "show"],
            "banking": ["banking", "bank", "account", "transfer", "deposit", "withdraw", "atm", "branch", "checking", "savings"],
            "financial": ["financial", "investment", "portfolio", "stocks", "bonds", "market", "wealth", "advisor", "retirement", "fund"],
            "consulting": ["consulting", "consultant", "strategy", "analysis", "implementation", "optimization", "assessment", "recommendation", "expertise", "solutions"],
            "government": ["government", "public", "citizen", "official", "regulation", "compliance", "agency", "municipal", "federal", "permit"]
        }
        
        # Convert text to lowercase
        text_content = text_content.lower()
        
        # Count keywords for each category
        scores = {}
        for category, keywords in categories.items():
            score = sum([text_content.count(keyword) for keyword in keywords])
            scores[category] = score
        
        # Determine the highest scoring category
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        else:
            return "unknown"
    
    def _generate_graph_visualization(self):
        """Generate a visual representation of the site graph"""
        logger.info("Generating graph visualization")
        
        # Create the static directory if it doesn't exist
        os.makedirs("app/static", exist_ok=True)
        
        try:
            # First, try to use PyVis to generate the graph
            self._generate_pyvis_graph()
            logger.info("PyVis graph generation successful")
        except Exception as e:
            # If PyVis fails, fall back to manual HTML generation
            logger.error(f"PyVis graph generation failed: {str(e)}, trying fallback method", exc_info=True)
            try:
                self._generate_basic_graph_html()
                logger.info("Fallback graph generation successful")
            except Exception as e2:
                logger.error(f"Fallback graph generation also failed: {str(e2)}", exc_info=True)
    
    def _generate_pyvis_graph(self):
        """Generate graph visualization using PyVis"""
        # Create a network
        net = Network(height="750px", width="100%", directed=True, notebook=False)
        
        # Configure to use CDN resources instead of local files
        net.use_DOT = True
        net.set_options("""
        var options = {
            "nodes": {
                "font": {
                    "size": 12
                }
            },
            "edges": {
                "color": {
                    "color": "#1E90FF",
                    "highlight": "#FF0000"
                },
                "smooth": {
                    "type": "continuous"
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
                "hover": true,
                "navigationButtons": true,
                "keyboard": true
            }
        }
        """)
        
        # Add nodes
        for node in self.graph.nodes():
            title = self.graph.nodes[node].get('title', 'No Title')
            path = self.graph.nodes[node].get('path', '/')
            depth = self.graph.nodes[node].get('depth', 0)
            
            # Use shortened labels for better visualization
            label = path[:15] + "..." if len(path) > 15 else path
            if label == "" or label == "/":
                label = "Home"
                
            # Add custom attributes for node identification
            net.add_node(
                node, 
                label=label, 
                title=f"{title}\n{node}",
                value=(10-depth) * 2,  # Size based on depth (higher nodes are bigger)
                level=depth,           # Hierarchical level
                url=node,              # Store the URL for later use
                color="#4CAF50" if depth == 0 else "#2196F3"  # Root is green, others blue
            )
        
        # Add edges
        for edge in self.graph.edges():
            net.add_edge(edge[0], edge[1])
        
        # Add custom JS to handle node clicks
        net.set_options("""
        var options = {
            "configure": {
                "enabled": false
            },
            "nodes": {
                "font": {
                    "size": 12
                }
            },
            "physics": {
                "hierarchicalRepulsion": {
                    "centralGravity": 0
                },
                "minVelocity": 0.75,
                "solver": "hierarchicalRepulsion"
            },
            "interaction": {
                "navigationButtons": true,
                "selectConnectedEdges": true
            }
        }
        """)
        
        # Save the graph
        net.save_graph("app/static/graph.html")
        
        # Fix the HTML after saving
        self._fix_graph_html_for_cdn()
        
        # Add custom click event handler
        self._add_node_click_handler()
        
    def _generate_basic_graph_html(self):
        """Generate a basic HTML with the graph using custom template"""
        logger.info("Generating basic graph HTML using custom template")
        
        # Create a list of nodes
        nodes_data = []
        for node in self.graph.nodes():
            title = self.graph.nodes[node].get('title', 'No Title')
            path = self.graph.nodes[node].get('path', '/')
            depth = self.graph.nodes[node].get('depth', 0)
            
            # Use shortened labels for better visualization
            label = path[:15] + "..." if len(path) > 15 else path
            if label == "" or label == "/":
                label = "Home"
            
            # Create node object with tooltip and hover info
            tooltip = f"<div><strong>{title}</strong><br>{node}</div>"
            
            node_obj = {
                "id": node,
                "label": label,
                "title": tooltip,
                "value": (10-depth) * 2,
                "level": depth,
                "url": node,
                "color": "#4CAF50" if depth == 0 else "#2196F3"
            }
            
            nodes_data.append(node_obj)
        
        # Create a list of edges - make them directional
        edges_data = []
        for edge in self.graph.edges():
            edge_obj = {
                "from": edge[0],
                "to": edge[1],
                "arrows": {
                    "to": {"enabled": True, "scaleFactor": 0.5}
                },
                "color": {
                    "color": "#1E90FF",
                    "highlight": "#FF0000"
                }
            }
            edges_data.append(edge_obj)
        
        # Define physics options
        options = {
            "nodes": {
                "font": {
                    "size": 12
                },
                "borderWidth": 2,
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
                "maxVelocity": 50,
                "solver": "barnesHut",
                "stabilization": {
                    "iterations": 1000
                }
            },
            "interaction": {
                "hover": True,
                "hoverConnectedEdges": True,
                "navigationButtons": True,
                "keyboard": True,
                "selectConnectedEdges": True,
                "tooltipDelay": 300
            }
        }
        
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
        #path-info {
            position: absolute;
            top: 5px;
            left: 5px;
            background: rgba(255,255,255,0.9);
            color: #333;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 1000;
            max-width: 300px;
            max-height: 400px;
            overflow-y: auto;
            font-family: Arial, sans-serif;
            font-size: 12px;
            display: none;
        }
    </style>
</head>
<body>
    <div id="debug-info">Vis.js Network Graph</div>
    <div id="path-info"></div>
    <div id="mynetwork"></div>
    <script type="text/javascript">
        // Create nodes and edges
        var nodes = new vis.DataSet({nodes_json});
        var edges = new vis.DataSet({edges_json});
        
        // Create container and data
        var container = document.getElementById("mynetwork");
        var data = {
            nodes: nodes,
            edges: edges
        };
        
        // Store all paths data
        var allPathsData = {paths_json};
        var rootNode = {root_node};
        
        // Create network
        var options = {options_json};
        window.network = new vis.Network(container, data, options);
        
        // Function to find all paths from root to a node
        function findAllPaths(targetNode) {
            if (allPathsData && allPathsData[targetNode] && allPathsData[targetNode].length > 0) {
                return allPathsData[targetNode];
            } 
            return [];
        }
        
        // Function to highlight paths
        function highlightPaths(paths) {
            // Reset all nodes and edges
            var allNodes = nodes.get();
            var allEdges = edges.get();
            var updatedNodes = [];
            var updatedEdges = [];
            
            // First reset all to default
            allNodes.forEach(function(n) {
                n.color = n.level === 0 ? '#4CAF50' : '#2196F3';
                n.font = { color: '#000000' };
                n.borderWidth = 1;
                n.shadow = false;
                n.hidden = true;  // Hide all nodes by default
                updatedNodes.push(n);
            });
            
            allEdges.forEach(function(e) {
                e.color = '#1E90FF';
                e.width = 1;
                e.shadow = false;
                e.hidden = true;  // Hide all edges by default
                updatedEdges.push(e);
            });
            
            // Update all nodes and edges with default styles
            nodes.update(updatedNodes);
            edges.update(updatedEdges);
            
            // No paths to highlight
            if (!paths || paths.length === 0) {
                return;
            }
            
            // Get the target node URL
            var targetNode = paths[0][paths[0].length - 1];
            var targetNodeData = nodes.get(targetNode);
            
            // Show and highlight root node
            var rootNodeData = nodes.get(rootNode);
            if (rootNodeData) {
                rootNodeData.color = '#4CAF50';
                rootNodeData.shadow = true;
                rootNodeData.borderWidth = 2;
                rootNodeData.hidden = false;
                nodes.update(rootNodeData);
            }
            
            // Show and highlight target node
            if (targetNodeData) {
                targetNodeData.color = '#e91e63';
                targetNodeData.shadow = true;
                targetNodeData.borderWidth = 2;
                targetNodeData.hidden = false;
                nodes.update(targetNodeData);
            }
            
            // Show and highlight all nodes and edges in the paths
            paths.forEach(function(path) {
                for (var i = 0; i < path.length - 1; i++) {
                    var fromNode = path[i];
                    var toNode = path[i + 1];
                    
                    // Show and highlight nodes in path
                    var nodeData = nodes.get(fromNode);
                    if (nodeData) {
                        nodeData.hidden = false;
                        nodeData.color = '#2196F3';
                        nodes.update(nodeData);
                    }
                    
                    // Show and highlight edges in path
            var edgeIds = edges.getIds({
                filter: function(edge) {
                    return edge.from === fromNode && edge.to === toNode;
                }
            });
                    
                    edgeIds.forEach(function(edgeId) {
                        var edgeData = edges.get(edgeId);
                        if (edgeData) {
                            edgeData.hidden = false;
                            edgeData.color = '#FF0000';
                            edgeData.width = 2;
                            edges.update(edgeData);
                        }
                    });
                }
            });
            
            // Display path information
            showPathInfo(paths);
        }
        
        // Function to reset the view
        function resetView() {
            var allNodes = nodes.get();
            var allEdges = edges.get();
            
            allNodes.forEach(function(n) {
                n.hidden = false;
                n.color = n.level === 0 ? '#4CAF50' : '#2196F3';
                n.borderWidth = 1;
                n.shadow = false;
                nodes.update(n);
            });
            
            allEdges.forEach(function(e) {
                e.hidden = false;
                e.color = '#1E90FF';
                e.width = 1;
                e.shadow = false;
                edges.update(e);
            });
            
            document.getElementById('path-info').style.display = 'none';
        }
        
        // Show path information
        function showPathInfo(paths) {
            var pathInfo = document.getElementById('path-info');
            if (!pathInfo) return;
            
            if (!paths || paths.length === 0) {
                pathInfo.style.display = 'none';
                return;
            }
            
            var html = '<h3>Selected Node</h3>';
            var targetNode = paths[0][paths[0].length - 1];
            var targetNodeData = nodes.get(targetNode);
            
                html += '<div style="margin-bottom: 10px;">';
            html += '<strong>URL:</strong> ' + targetNodeData.url + '<br>';
            html += '<strong>Title:</strong> ' + targetNodeData.title + '<br>';
            html += '<button onclick="resetView()" style="margin-top: 10px; padding: 5px 10px;">Reset View</button>';
                html += '</div>';
            
            pathInfo.innerHTML = html;
            pathInfo.style.display = 'block';
        }
        
        // Network events
        window.network.on("click", function(params) {
            if (params.nodes.length > 0) {
                var nodeId = params.nodes[0];
                var node = window.network.body.data.nodes.get(nodeId);
                console.log("Node clicked:", node);
                
                // Find all paths from root to selected node
                var paths = findAllPaths(nodeId);
                
                // Highlight the paths
                highlightPaths(paths);
                
                // Send message to parent window
                window.parent.postMessage({
                    type: 'nodeClick',
                    nodeId: nodeId,
                    nodeName: node.label || 'Unknown',
                    nodeUrl: node.url || nodeId,
                    paths: paths
                }, '*');
            } else {
                // Clicked on empty space - reset view
                resetView();
            }
        });
        
        // Double click to focus on a node
        window.network.on("doubleClick", function(params) {
            if (params.nodes.length > 0) {
                var nodeId = params.nodes[0];
                window.network.focus(nodeId, {
                    scale: 1.2,
                    animation: true
                });
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
        
        # Prepare paths data for the visualization
        paths_data = {}
        for node_url, node_paths in self.paths.items():
            paths_data[node_url] = node_paths
        
        # Replace placeholders with actual JSON data
        html = html_template.replace("{nodes_json}", json.dumps(nodes_data))
        html = html.replace("{edges_json}", json.dumps(edges_data))
        html = html.replace("{options_json}", json.dumps(options))
        html = html.replace("{paths_json}", json.dumps(paths_data))
        html = html.replace("{root_node}", json.dumps(self.url))
        
        # Save the HTML file
        with open("app/static/graph.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        logger.info("Basic graph HTML generated successfully") 
    
    def _add_node_click_handler(self):
        """Add custom JS to handle node clicks - Disabled as now included in template"""
        logger.info("Node click handler functionality is now included in the HTML template")
        # This method has been superseded by embedded click handler in the HTML template
        pass

    def _fix_graph_html_for_cdn(self):
        """Fix the HTML to use CDN resources - Disabled as now included in template"""
        logger.info("CDN resources now included in the HTML template")
        # This method has been superseded by the correct CDN links in the HTML template
        pass 