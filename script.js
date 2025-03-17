document.addEventListener('DOMContentLoaded', function() {
        // DOM elements
        const assemblyInput = document.getElementById('assembly-input');
        const machineOutput = document.getElementById('machine-output');
        const assembleBtn = document.getElementById('assemble-btn');
        const clearBtn = document.getElementById('clear-btn');
        const loadExampleBtn = document.getElementById('load-example');
        const exampleCode = document.getElementById('example-code');
        const tabButtons = document.querySelectorAll('.tab-btn');
        
        // Event listeners
        assembleBtn.addEventListener('click', assembleCode);
        clearBtn.addEventListener('click', clearAll);
        loadExampleBtn.addEventListener('click', loadExample);
        
        // Tab switching
        tabButtons.forEach(button => {
            button.addEventListener('click', function() {
                const target = this.getAttribute('data-target');
                
                // Hide all tab contents
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                
                // Remove active class from all buttons
                tabButtons.forEach(btn => {
                    btn.classList.remove('active');
                });
                
                // Show target content and mark button as active
                document.getElementById(target).classList.add('active');
                this.classList.add('active');
            });
        });
        
        // Function to assemble code
        function assembleCode() {
            const code = assemblyInput.value.trim();
            
            if (!code) {
                displayOutput("Please enter some assembly code first.", true);
                return;
            }
            
            // Show loading state
            assembleBtn.disabled = true;
            assembleBtn.textContent = "Assembling...";
            machineOutput.textContent = "Processing...";
            
            // Send to backend
            fetch('/api/assemble', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ code: code })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.machine_code.length > 0) {
                        let output = '';
                        data.machine_code.forEach((line, index) => {
                            output += `${(index + 1).toString().padStart(2, '0')}: ${line}\n`;
                        });
                        displayOutput(output);
                    } else {
                        displayOutput("No machine code generated. Check your syntax.", true);
                    }
                } else {
                    let errorMsg = "Errors encountered:\n\n";
                    data.errors.forEach(err => {
                        errorMsg += `${err}\n`;
                    });
                    displayOutput(errorMsg, true);
                }
            })
            .catch(error => {
                displayOutput(`Error: ${error.message}`, true);
            })
            .finally(() => {
                // Reset button state
                assembleBtn.disabled = false;
                assembleBtn.textContent = "Assemble →";
            });
        }
        
        // Function to display output
        function displayOutput(text, isError = false) {
            machineOutput.textContent = text;
            
            if (isError) {
                machineOutput.classList.add('error');
            } else {
                machineOutput.classList.remove('error');
            }
        }
        
        // Clear all input and output
        function clearAll() {
            assemblyInput.value = '';
            machineOutput.textContent = '';
            machineOutput.classList.remove('error');
        }
        
        // Load example code
        function loadExample() {
            assemblyInput.value = exampleCode.textContent;
        }
        
        // Check for keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Ctrl+Enter or Cmd+Enter to assemble
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                assembleCode();
                e.preventDefault();
            }
        });
    });