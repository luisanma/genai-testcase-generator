import json
import os
import logging
from datetime import datetime

# Set up logger
logger = logging.getLogger("web-analysis-framework.test-generator")

class TestCaseGenerator:
    def __init__(self, website_analysis):
        self.analysis = website_analysis
        self.test_cases = []
        self.test_case_dir = "app/static/test_cases"
        
        # Create directory if it doesn't exist
        os.makedirs(self.test_case_dir, exist_ok=True)
        logger.info(f"Test case directory: {self.test_case_dir}")

    def generate_test_cases(self):
        """Generate test cases based on website analysis"""
        logger.info("Starting test case generation for entire website")
        # Clear previous test cases
        self.test_cases = []
        
        # Generate basic test cases based on site category and structure
        self._generate_navigation_tests()
        self._generate_category_specific_tests()
        
        # Save test cases to files
        self._save_test_cases()
        
        logger.info(f"Generated {len(self.test_cases)} test cases")
        return self.test_cases
    
    def generate_test_cases_for_node(self, node_url):
        """Generate test cases specific to a selected node/page"""
        logger.info(f"Starting test case generation for specific node: {node_url}")
        # Clear previous test cases
        self.test_cases = []
        
        # First, verify if the node exists in the analysis
        if node_url not in self.analysis.get("pages", []):
            logger.warning(f"Node URL {node_url} not found in analysis")
            # Return empty test cases
            return self.test_cases
            
        # Extract path information from the analysis
        paths = self.analysis.get("paths", {}).get(node_url, [])
        logger.info(f"Found {len(paths)} paths to node {node_url}")
        
        # Generate basic accessibility test for the node using path information
        self._generate_node_accessibility_test(node_url, paths)
        
        # Generate node-specific tests based on content
        page_content = self.analysis.get("page_content", {}).get(node_url, {})
        self._generate_node_specific_tests(node_url, page_content)
        
        # Generate tests for the subgraph (paths to this node)
        if paths:
            self._generate_subgraph_tests(node_url, paths)
        
        # Save test cases to files
        self._save_test_cases(prefix=f"node_{self._get_safe_filename(node_url)}")
        
        logger.info(f"Generated {len(self.test_cases)} test cases for node {node_url}")
        return self.test_cases
    
    def _get_safe_filename(self, url):
        """Convert URL to a safe filename"""
        # Replace non-alphanumeric characters with underscores
        return ''.join(c if c.isalnum() else '_' for c in url)
    
    def _generate_node_accessibility_test(self, node_url, paths=None):
        """Generate basic accessibility test for a specific node using path information"""
        # Get node info
        page_content = self.analysis.get("page_content", {}).get(node_url, {})
        title = page_content.get("title", "Unknown Page")
        
        # If paths not provided, try to get from analysis
        if paths is None:
            paths = self.analysis.get("paths", {}).get(node_url, [])
        
        # If we have paths to the node, generate a navigation test
        if paths and len(paths) > 0:
            # Find the shortest path
            shortest_path = min(paths, key=len) if paths else [self.analysis["url"], node_url]
            
            # Create steps to navigate to this node
            steps = [f"Navigate to {self.analysis['url']}"]
            
            # For each step in the path (except the first and last), create a navigation step
            for i in range(1, len(shortest_path)-1):
                current_url = shortest_path[i]
                current_content = self.analysis.get("page_content", {}).get(current_url, {})
                
                steps.append(f"Find and click the link to '{current_content.get('title', 'Unknown Page')}'")
                steps.append(f"Wait for the page to load")
            
            # Last step to the target node
            if len(shortest_path) > 1:
                steps.append(f"Find and click the link to '{title}'")
                steps.append(f"Wait for the page to load completely")
        else:
            # Direct navigation if no path
            steps = [
                f"Navigate directly to {node_url}",
                "Wait for the page to load completely"
            ]
        
        # Create a test case for basic accessibility
        self.test_cases.append({
            "id": 1,
            "title": f"Accessibility Test for {title}",
            "description": f"Verify that the page at {node_url} is accessible and loads correctly",
            "steps": steps,
            "expected_results": [
                "Page loads without errors",
                "All elements are visible and properly rendered",
                f"Page title contains '{title}'"
            ]
        })
    
    def _generate_node_specific_tests(self, node_url, page_content):
        """Generate tests specific to the content of this node"""
        # Check if page has a form
        if page_content.get("forms", 0) > 0:
            self._generate_form_test(node_url, page_content)
            
        # Check if page has many links
        if len(page_content.get("links", [])) > 3:
            self._generate_links_test(node_url, page_content)
            
        # Check if page has inputs
        if page_content.get("inputs", 0) > 0:
            self._generate_input_test(node_url, page_content)
            
        # Check if page has buttons
        if page_content.get("buttons", 0) > 0:
            self._generate_button_test(node_url, page_content)
            
        # Generate tests based on site category
        category = self.analysis.get("category", "unknown")
        
        if category == "e-commerce":
            self._generate_ecommerce_page_test(node_url, page_content)
        elif category == "blog" or category == "news":
            self._generate_content_page_test(node_url, page_content)
    
    def _generate_form_test(self, node_url, page_content):
        """Generate a form submission test for a page"""
        title = page_content.get("title", "Unknown Page")
        
        self.test_cases.append({
            "id": len(self.test_cases) + 1,
            "title": f"Form Submission Test for {title}",
            "description": f"Verify that forms on the page at {node_url} can be submitted correctly",
            "steps": [
                f"Navigate to {node_url}",
                "Identify the form on the page",
                "Fill in all required fields with valid test data",
                "Submit the form"
            ],
            "expected_results": [
                "Form accepts the input data",
                "Form validation works correctly",
                "Form submission is successful",
                "Appropriate confirmation or next step is displayed"
            ]
        })
    
    def _generate_links_test(self, node_url, page_content):
        """Generate a links test for a page"""
        title = page_content.get("title", "Unknown Page")
        
        self.test_cases.append({
            "id": len(self.test_cases) + 1,
            "title": f"Links Test for {title}",
            "description": f"Verify that all important links on the page at {node_url} work correctly",
            "steps": [
                f"Navigate to {node_url}",
                "Identify all important navigation links",
                "Click on each link one by one",
                "Verify each destination page loads",
                "Navigate back to the original page after each verification"
            ],
            "expected_results": [
                "All links are clickable",
                "Destination pages load without errors",
                "Navigation back to the original page works"
            ]
        })
    
    def _generate_input_test(self, node_url, page_content):
        """Generate an input validation test for a page"""
        title = page_content.get("title", "Unknown Page")
        
        self.test_cases.append({
            "id": len(self.test_cases) + 1,
            "title": f"Input Validation Test for {title}",
            "description": f"Verify that input fields on the page at {node_url} validate correctly",
            "steps": [
                f"Navigate to {node_url}",
                "Identify all input fields",
                "Test each input field with valid data",
                "Test each input field with invalid data",
                "Observe validation behavior"
            ],
            "expected_results": [
                "Input fields accept valid data",
                "Input fields reject invalid data",
                "Validation errors are displayed appropriately",
                "Error messages are clear and descriptive"
            ]
        })
    
    def _generate_button_test(self, node_url, page_content):
        """Generate a button functionality test for a page"""
        title = page_content.get("title", "Unknown Page")
        
        self.test_cases.append({
            "id": len(self.test_cases) + 1,
            "title": f"Button Functionality Test for {title}",
            "description": f"Verify that buttons on the page at {node_url} function correctly",
            "steps": [
                f"Navigate to {node_url}",
                "Identify all actionable buttons",
                "Click each button one by one",
                "Observe the response to each button click"
            ],
            "expected_results": [
                "All buttons are clickable",
                "Each button triggers the expected action",
                "UI responds appropriately to button interactions",
                "No errors occur during button operations"
            ]
        })
    
    def _generate_ecommerce_page_test(self, node_url, page_content):
        """Generate e-commerce specific tests for a page"""
        title = page_content.get("title", "Unknown Page")
        
        # Try to determine if this is a product page, category page, or cart page
        text_content = page_content.get("text_content", "").lower()
        
        if any(term in text_content for term in ["add to cart", "buy now", "price", "product"]):
            # Likely a product page
            self.test_cases.append({
                "id": len(self.test_cases) + 1,
                "title": f"Product Page Test for {title}",
                "description": f"Verify that the product page at {node_url} functions correctly",
                "steps": [
                    f"Navigate to {node_url}",
                    "Verify product information is displayed correctly",
                    "Select product options if available (size, color, etc.)",
                    "Click the 'Add to Cart' button",
                    "Verify the product was added to the cart"
                ],
                "expected_results": [
                    "Product information is accurate and complete",
                    "Product options can be selected",
                    "Product can be added to cart",
                    "Cart is updated with the correct product"
                ]
            })
        elif "cart" in text_content or "basket" in text_content or "checkout" in text_content:
            # Likely a cart or checkout page
            self.test_cases.append({
                "id": len(self.test_cases) + 1,
                "title": f"Cart/Checkout Test for {title}",
                "description": f"Verify that the cart/checkout page at {node_url} functions correctly",
                "steps": [
                    f"Navigate to {node_url}",
                    "Verify cart contents are displayed correctly",
                    "Update product quantities",
                    "Proceed to checkout",
                    "Fill in required checkout information"
                ],
                "expected_results": [
                    "Cart contents are accurate",
                    "Product quantities can be updated",
                    "Prices and totals are calculated correctly",
                    "Checkout process works correctly"
                ]
            })
    
    def _generate_content_page_test(self, node_url, page_content):
        """Generate content-specific tests for a blog or news page"""
        title = page_content.get("title", "Unknown Page")
        
        self.test_cases.append({
            "id": len(self.test_cases) + 1,
            "title": f"Content Display Test for {title}",
            "description": f"Verify that the content on the page at {node_url} displays correctly",
            "steps": [
                f"Navigate to {node_url}",
                "Verify all content elements load correctly",
                "Check images, videos, and embedded content",
                "Test social sharing features if available",
                "Test comments section if available"
            ],
            "expected_results": [
                "All content displays correctly",
                "Images and media load properly",
                "Interactive elements work as expected",
                "Content is readable and properly formatted"
            ]
        })

    def _generate_navigation_tests(self):
        """Generate basic navigation test cases"""
        pages = self.analysis.get("pages", [])
        
        # Basic site accessibility test
        self.test_cases.append({
            "id": 1,
            "title": "Homepage Accessibility Test",
            "description": f"Verify that the homepage at {self.analysis['url']} is accessible and loads correctly",
            "steps": [
                f"Navigate to {self.analysis['url']}",
                "Wait for the page to load completely"
            ],
            "expected_results": [
                "Page loads without errors",
                "All elements are visible and properly rendered"
            ]
        })
        
        # Navigation path tests (if there are multiple pages)
        if len(pages) > 1:
            self.test_cases.append({
                "id": 2,
                "title": "Basic Navigation Path Test",
                "description": "Verify that navigation between key pages works correctly",
                "steps": [
                    f"Navigate to {self.analysis['url']}",
                    "Find and click on the first link in the navigation menu",
                    "Wait for the new page to load",
                    "Navigate back to the homepage"
                ],
                "expected_results": [
                    "Navigation to new page is successful",
                    "Back navigation returns to the homepage",
                    "No errors occur during navigation"
                ]
            })

    def _generate_category_specific_tests(self):
        """Generate test cases specific to the website category"""
        category = self.analysis.get("category", "unknown")
        
        if category == "e-commerce":
            self._generate_ecommerce_tests()
        elif category == "blog":
            self._generate_blog_tests()
        elif category == "news":
            self._generate_news_tests()
        elif category == "portfolio":
            self._generate_portfolio_tests()
        elif category == "corporate":
            self._generate_corporate_tests()
        elif category == "educational":
            self._generate_educational_tests()
        else:
            # Generic tests for unknown category
            self._generate_generic_tests()

    def _generate_ecommerce_tests(self):
        """Generate e-commerce specific test cases"""
        self.test_cases.append({
            "id": len(self.test_cases) + 1,
            "title": "Product Search Test",
            "description": "Verify that the product search functionality works correctly",
            "steps": [
                f"Navigate to {self.analysis['url']}",
                "Locate the search box",
                "Enter a common product name (e.g., 'shirt')",
                "Submit the search"
            ],
            "expected_results": [
                "Search results page loads",
                "Results related to the search term are displayed",
                "Number of results is indicated"
            ]
        })
        
        self.test_cases.append({
            "id": len(self.test_cases) + 1,
            "title": "Add Product to Cart Test",
            "description": "Verify that adding a product to the shopping cart works correctly",
            "steps": [
                f"Navigate to {self.analysis['url']}",
                "Browse to a product page",
                "Click the 'Add to Cart' button",
                "Navigate to the shopping cart"
            ],
            "expected_results": [
                "Product is added to the cart",
                "Cart count is updated",
                "Product appears correctly in the cart with the right quantity and price"
            ]
        })

    def _generate_blog_tests(self):
        """Generate blog specific test cases"""
        self.test_cases.append({
            "id": len(self.test_cases) + 1,
            "title": "Blog Post Navigation Test",
            "description": "Verify that navigation between blog posts works correctly",
            "steps": [
                f"Navigate to {self.analysis['url']}",
                "Click on a blog post title",
                "Verify the post content loads",
                "Navigate back to the blog list"
            ],
            "expected_results": [
                "Blog post opens correctly",
                "Post content is displayed",
                "Navigation back to the list works"
            ]
        })

    def _generate_news_tests(self):
        """Generate news site specific test cases"""
        self.test_cases.append({
            "id": len(self.test_cases) + 1,
            "title": "News Category Navigation Test",
            "description": "Verify that navigation between news categories works correctly",
            "steps": [
                f"Navigate to {self.analysis['url']}",
                "Identify and click on a news category (e.g., 'Sports', 'Politics')",
                "Verify that category-specific news loads",
                "Navigate back to the main page"
            ],
            "expected_results": [
                "Category page loads correctly",
                "News articles in the selected category are displayed",
                "Navigation back to main page works"
            ]
        })

    def _generate_portfolio_tests(self):
        """Generate portfolio site specific test cases"""
        self.test_cases.append({
            "id": len(self.test_cases) + 1,
            "title": "Portfolio Project Showcase Test",
            "description": "Verify that portfolio projects are displayed correctly",
            "steps": [
                f"Navigate to {self.analysis['url']}",
                "Navigate to the projects or portfolio section",
                "Click on a specific project",
                "Examine project details"
            ],
            "expected_results": [
                "Portfolio section loads correctly",
                "Projects are displayed with thumbnails/titles",
                "Project detail view shows correct information",
                "Images and media load properly"
            ]
        })

    def _generate_corporate_tests(self):
        """Generate corporate site specific test cases"""
        self.test_cases.append({
            "id": len(self.test_cases) + 1,
            "title": "Contact Form Validation Test",
            "description": "Verify that the contact form validates inputs correctly",
            "steps": [
                f"Navigate to {self.analysis['url']}",
                "Navigate to the contact page",
                "Submit the form without filling any fields",
                "Observe validation errors"
            ],
            "expected_results": [
                "Form submission is prevented",
                "Validation errors are displayed for required fields",
                "Error messages are clear and descriptive"
            ]
        })

    def _generate_educational_tests(self):
        """Generate educational site specific test cases"""
        self.test_cases.append({
            "id": len(self.test_cases) + 1,
            "title": "Course Catalog Test",
            "description": "Verify that the course catalog displays correctly",
            "steps": [
                f"Navigate to {self.analysis['url']}",
                "Navigate to the course catalog or courses section",
                "Apply filters if available (e.g., by subject)",
                "Click on a specific course"
            ],
            "expected_results": [
                "Course catalog loads correctly",
                "Filtering works as expected",
                "Course details page displays complete information",
                "Navigation between catalog and course details works"
            ]
        })

    def _generate_generic_tests(self):
        """Generate generic test cases for unknown site categories"""
        self.test_cases.append({
            "id": len(self.test_cases) + 1,
            "title": "Main Menu Navigation Test",
            "description": "Verify that all main menu items navigate to the correct pages",
            "steps": [
                f"Navigate to {self.analysis['url']}",
                "Identify all main menu items",
                "Click on each menu item one by one",
                "Verify each destination page loads",
                "Navigate back to the homepage after each verification"
            ],
            "expected_results": [
                "All menu items are clickable",
                "Destination pages load correctly",
                "Navigation back to homepage works"
            ]
        })
        
        # If there are forms on the site
        page_with_forms = next((page for page, content in enumerate(self.analysis.get("page_content", {}).values()) 
                                if content.get("forms", 0) > 0), None)
        if page_with_forms:
            self.test_cases.append({
                "id": len(self.test_cases) + 1,
                "title": "Form Submission Test",
                "description": "Verify that forms can be submitted correctly",
                "steps": [
                    f"Navigate to {self.analysis['url']}",
                    "Navigate to a page with a form",
                    "Fill in all required fields with valid data",
                    "Submit the form"
                ],
                "expected_results": [
                    "Form accepts the input data",
                    "Submission is successful",
                    "Appropriate confirmation or next step is displayed"
                ]
            })

    def _generate_subgraph_tests(self, node_url, paths):
        """Generate tests based on the subgraph (paths to this node)"""
        logger.info(f"Generating subgraph tests for {node_url} with {len(paths)} paths")
        
        page_content = self.analysis.get("page_content", {}).get(node_url, {})
        title = page_content.get("title", "Unknown Page")
        
        # Generate a test for each unique path
        for idx, path in enumerate(paths[:3]):  # Limit to first 3 paths to avoid too many tests
            path_nodes = []
            for url in path:
                content = self.analysis.get("page_content", {}).get(url, {})
                path_nodes.append(content.get("title", "Unknown Page"))
            
            # Create navigation steps for this path
            steps = [f"Navigate to {self.analysis['url']}"]
            
            for i in range(1, len(path)):
                steps.append(f"Find and click the link to '{path_nodes[i]}'")
                steps.append(f"Wait for the page to load completely")
                
                # Add verification steps
                steps.append(f"Verify the page title contains '{path_nodes[i]}'")
            
            # Create the test case
            self.test_cases.append({
                "id": len(self.test_cases) + 1,
                "title": f"Path Navigation Test {idx + 1} to {title}",
                "description": f"Verify navigation through path {idx + 1} to reach {title}",
                "steps": steps,
                "expected_results": [
                    "All links in the path are working",
                    "Navigation completes successfully",
                    f"Destination page '{title}' loads correctly"
                ]
            })
        
        # Create a test for testing all outbound links from this node
        if page_content.get("links", []):
            outbound_links = []
            for link in page_content.get("links", []):
                if link in self.analysis.get("pages", []):
                    link_content = self.analysis.get("page_content", {}).get(link, {})
                    outbound_links.append(link_content.get("title", "Unknown Page"))
            
            if outbound_links:
                self.test_cases.append({
                    "id": len(self.test_cases) + 1,
                    "title": f"Outbound Links Test for {title}",
                    "description": f"Verify all outbound links from {title} work correctly",
                    "steps": [
                        f"Navigate to {node_url}",
                        "Identify all outbound links",
                        "Click on each link and verify it loads",
                        "Return to the original page after testing each link"
                    ],
                    "expected_results": [
                        "All outbound links are clickable",
                        "Destination pages load without errors",
                        "Navigation back to the original page works"
                    ]
                })

    def _save_test_cases(self, prefix=""):
        """Save test cases to JSON files"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Create filename with prefix if provided
        filename_base = f"{prefix}_" if prefix else ""
        
        # Save all test cases to a single file
        with open(f"{self.test_case_dir}/{filename_base}test_cases_{timestamp}.json", "w") as f:
            json.dump(self.test_cases, f, indent=2)
        
        # Also save individual test cases
        for test_case in self.test_cases:
            with open(f"{self.test_case_dir}/{filename_base}test_case_{test_case['id']}_{timestamp}.json", "w") as f:
                json.dump(test_case, f, indent=2) 