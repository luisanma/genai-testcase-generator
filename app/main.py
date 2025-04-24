import uvicorn
import logging
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from app.api.routes import router as api_router
from app.utils.directory_setup import setup as setup_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger("web-analysis-framework")

# Set up required directories
setup_directories()

app = FastAPI(title="Web Analysis Framework")

# Mount static files directory - first set up the main static dir
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Mount Pyvis libs directory to handle the library's script references
if os.path.exists("app/static/pyvis_libs"):
    app.mount("/lib", StaticFiles(directory="app/static/pyvis_libs/lib"), name="pyvis-lib")

# Also serve pyvis's dependencies directly
# This is needed because pyvis generates HTML that references these files
@app.middleware("http")
async def catch_pyvis_js_requests(request: Request, call_next):
    path = request.url.path
    
    # Log all requests for debugging
    logger.debug(f"Request: {request.method} {path}")
    
    # Handle vis.js library requests by redirecting them to CDN
    if path.startswith("/lib/") and ("bindings" in path or "network" in path):
        logger.warning(f"Redirecting vis.js resource to CDN: {path}")
        cdn_path = f"https://cdn.jsdelivr.net/npm/vis-network@9.1.2/dist{path}"
        return RedirectResponse(url=cdn_path)
    
    response = await call_next(request)
    
    # Log 404 errors
    if response.status_code == 404:
        logger.warning(f"404 Not Found: {request.method} {request.url}")
    
    return response

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Include API routes
app.include_router(api_router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    logger.info("Home page requested")
    return templates.TemplateResponse("index.html", {"request": request})

# Add a health check endpoint
@app.get("/health")
async def health_check():
    logger.info("Health check requested")
    return {"status": "healthy"}

# Serve graph directly
@app.get("/graph", response_class=HTMLResponse)
async def get_graph(request: Request):
    logger.info("Graph visualization requested")
    try:
        graph_file = "app/static/graph.html"
        if os.path.exists(graph_file):
            with open(graph_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Inject script to communicate with parent window
            # This script sends node click events to the parent window
            script = """
            <script>
            console.log('Graph iframe loaded - Setting up message handlers');
            
            // Function to check if network is ready
            function checkNetwork() {
                console.log('Checking if network is available...');
                if (typeof window.network !== 'undefined') {
                    console.log('Network found!', window.network);
                    setupNetworkHandlers();
                    return true;
                }
                return false;
            }
            
            // Function to set up network handlers
            function setupNetworkHandlers() {
                console.log('Setting up network handlers');
                
                // Add click event listener to the network
                window.network.on('click', function(params) {
                    console.log('Network click event', params);
                    if (params.nodes.length > 0) {
                        const nodeId = params.nodes[0];
                        console.log('Node clicked:', nodeId);
                        
                        try {
                            const node = window.network.body.data.nodes.get(nodeId);
                            console.log('Node data:', node);
                            
                            // Send message to parent window
                            window.parent.postMessage({
                                type: 'nodeClick',
                                nodeId: nodeId,
                                nodeName: node.label || 'Unknown',
                                nodeUrl: node.url || nodeId  // Use nodeId as fallback
                            }, '*');
                        } catch (e) {
                            console.error('Error getting node data:', e);
                            window.parent.postMessage({
                                type: 'error',
                                message: 'Error getting node data: ' + e.message
                            }, '*');
                        }
                    }
                });
                
                // Add hover event listeners
                window.network.on('hoverNode', function(params) {
                    console.log('Node hover:', params.node);
                    try {
                        const node = window.network.body.data.nodes.get(params.node);
                        // Send message to parent
                        window.parent.postMessage({
                            type: 'nodeHover',
                            nodeId: params.node,
                            nodeName: node.label || 'Unknown',
                            nodeUrl: node.url || params.node
                        }, '*');
                    } catch (e) {
                        console.error('Error in hover handler:', e);
                    }
                });
                
                window.network.on('blurNode', function(params) {
                    console.log('Node hover end');
                    window.parent.postMessage({
                        type: 'nodeHoverEnd'
                    }, '*');
                });
                
                console.log('Network handlers setup complete');
            }
            
            // Function to wait for network to be initialized
            function waitForNetwork() {
                console.log('Waiting for network initialization...');
                
                // Try to find the network object in different contexts
                // 1. Try the global window.network
                if (checkNetwork()) return;
                
                // 2. Try to find if vis.Network has been instantiated
                if (typeof vis !== 'undefined' && document.getElementById('mynetwork')) {
                    console.log('vis.js found, checking for network instance');
                    
                    // Wait a moment and check again to allow for initialization
                    setTimeout(function() {
                        // Check window.network again
                        if (checkNetwork()) return;
                        
                        // If network is still not found, try to locate it another way
                        // Some implementations assign network to a different variable
                        // Look through window properties for a Network instance
                        for (let prop in window) {
                            if (window[prop] instanceof vis.Network) {
                                console.log('Found network instance at window.' + prop);
                                window.network = window[prop];
                                setupNetworkHandlers();
                                return;
                            }
                        }
                        
                        // If we still can't find it, report the error
                        console.error('Network not found after checking for vis.Network instances');
                        window.parent.postMessage({
                            type: 'error',
                            message: 'Network visualization exists but not accessible'
                        }, '*');
                    }, 1000);
                    
                    return;
                }
                
                // If no network found after 5 seconds, give up
                setTimeout(function() {
                    if (!window.network) {
                        console.error('Network not found after 5 seconds');
                        window.parent.postMessage({
                            type: 'error',
                            message: 'Network visualization not initialized after waiting'
                        }, '*');
                    }
                }, 5000);
            }
            
            // Main initialization when DOM is loaded
            document.addEventListener('DOMContentLoaded', function() {
                console.log('DOM loaded, looking for network');
                
                // Start the process to find the network
                waitForNetwork();
                
                // Also set up a periodic check every second for 10 seconds
                let attempts = 0;
                const checkInterval = setInterval(function() {
                    attempts++;
                    if (checkNetwork()) {
                        clearInterval(checkInterval);
                        console.log('Network found on attempt ' + attempts);
                    } else if (attempts >= 10) {
                        clearInterval(checkInterval);
                        console.error('Giving up after 10 attempts');
                    }
                }, 1000);
            });
            </script>
            """
            
            # Insert the script right before the closing body tag
            if '</body>' in content:
                content = content.replace('</body>', script + '</body>')
            else:
                content += script
                
            return HTMLResponse(content=content)
        else:
            return HTMLResponse(content="""
            <html>
                <head><title>No Graph Available</title></head>
                <body>
                    <h1>No graph available yet</h1>
                    <p>Please analyze a website first.</p>
                    <script>
                        console.log('No graph available, sending message to parent');
                        window.parent.postMessage({
                            type: 'error',
                            message: 'No graph available yet. Please analyze a website first.'
                        }, '*');
                    </script>
                </body>
            </html>
            """)
    except Exception as e:
        logger.error(f"Error serving graph: {str(e)}", exc_info=True)
        error_html = f"""
        <html>
            <head><title>Error Loading Graph</title></head>
            <body>
                <h1>Error</h1>
                <p>{str(e)}</p>
                <script>
                    console.error('Error in graph iframe: {str(e)}');
                    window.parent.postMessage({
                        type: 'error',
                        message: 'Error loading graph: {str(e)}'
                    }, '*');
                </script>
            </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=500)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 