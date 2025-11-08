// Text Display JavaScript - Premium scrolling and selection handling

class TextDisplay {
    constructor() {
        this.textLines = [];
        this.currentIndex = 0;
        this.isScrolling = false;
        this.selectedText = null;
        
        this.textContainer = document.getElementById('text-container');
        this.textContent = document.getElementById('text-content');
        this.askButton = document.getElementById('ask-btn');
        this.scrollUpBtn = document.getElementById('scroll-up');
        this.scrollDownBtn = document.getElementById('scroll-down');
        
        this.setupEventListeners();
        this.setupScrollIndicators();
    }
    
    setupEventListeners() {
        // Scroll buttons
        this.scrollUpBtn.addEventListener('click', () => this.scrollUp());
        this.scrollDownBtn.addEventListener('click', () => this.scrollDown());
        
        // Mouse wheel scrolling
        this.textContainer.addEventListener('wheel', (e) => {
            e.preventDefault();
            if (e.deltaY > 0) {
                this.scrollDown();
            } else {
                this.scrollUp();
            }
        }, { passive: false });
        
        // Text selection handling
        document.addEventListener('selectionchange', () => this.handleSelectionChange());
        
        // Ask button
        this.askButton.addEventListener('click', () => this.askAboutSelection());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                if (this.selectedText) {
                    this.askAboutSelection();
                }
            }
        });
    }
    
    setupScrollIndicators() {
        // Create scroll indicators
        const topIndicator = document.createElement('div');
        topIndicator.className = 'scroll-indicator scroll-indicator-top';
        this.textContainer.appendChild(topIndicator);
        
        const bottomIndicator = document.createElement('div');
        bottomIndicator.className = 'scroll-indicator scroll-indicator-bottom';
        this.textContainer.appendChild(bottomIndicator);
        
        this.topIndicator = topIndicator;
        this.bottomIndicator = bottomIndicator;
        
        // Update indicators on scroll
        this.textContainer.addEventListener('scroll', () => this.updateScrollIndicators());
    }
    
    updateScrollIndicators() {
        const { scrollTop, scrollHeight, clientHeight } = this.textContainer;
        
        // Show/hide top indicator
        if (scrollTop > 10) {
            this.topIndicator.classList.remove('hidden');
        } else {
            this.topIndicator.classList.add('hidden');
        }
        
        // Show/hide bottom indicator
        if (scrollTop < scrollHeight - clientHeight - 10) {
            this.bottomIndicator.classList.remove('hidden');
        } else {
            this.bottomIndicator.classList.add('hidden');
        }
    }
    
    setText(text, language = 'en') {
        // Split text into lines (sentences/phrases)
        const sentences = text.split(/([.!?]\s+)/);
        this.textLines = [];
        let currentLine = '';
        
        for (let part of sentences) {
            if ((currentLine + part).length < 100) {
                currentLine += part;
            } else {
                if (currentLine.trim()) {
                    this.textLines.push(currentLine.trim());
                }
                currentLine = part;
            }
        }
        
        if (currentLine.trim()) {
            this.textLines.push(currentLine.trim());
        }
        
        // If no good splits, split by newlines
        if (this.textLines.length === 0) {
            this.textLines = text.split('\n').filter(line => line.trim());
        }
        
        // Further break down into shorter segments (max 6-7 words)
        const shortLines = [];
        for (let line of this.textLines) {
            const words = line.split(/\s+/);
            const maxWords = 6;
            for (let i = 0; i < words.length; i += maxWords) {
                const segment = words.slice(i, i + maxWords).join(' ');
                if (segment.trim()) {
                    shortLines.push(segment.trim());
                }
            }
        }
        
        this.textLines = shortLines;
        this.currentIndex = 0;
        
        // Set RTL direction for Hebrew
        if (language === 'he') {
            this.textContainer.setAttribute('dir', 'rtl');
        } else {
            this.textContainer.setAttribute('dir', 'ltr');
        }
        
        this.render();
    }
    
    render() {
        if (this.textLines.length === 0) {
            this.textContent.innerHTML = '<p class="placeholder">Text content not available...</p>';
            return;
        }
        
        // Show 2-3 lines centered
        const linesToShow = [];
        const maxLines = 2;
        
        for (let i = 0; i < maxLines && this.currentIndex + i < this.textLines.length; i++) {
            linesToShow.push(this.textLines[this.currentIndex + i]);
        }
        
        // Add spacing between words (double space)
        const formattedLines = linesToShow.map(line => {
            const words = line.split(/\s+/);
            return words.join('  '); // Double space between words
        });
        
        // Fade out, update, fade in
        this.textContent.classList.add('fade-out');
        
        setTimeout(() => {
            this.textContent.innerHTML = formattedLines
                .map(line => `<p class="text-line">${this.escapeHtml(line)}</p>`)
                .join('');
            
            this.textContent.classList.remove('fade-out');
            this.textContent.classList.add('fade-in');
            
            setTimeout(() => {
                this.textContent.classList.remove('fade-in');
            }, 300);
            
            // Scroll to center
            this.textContainer.scrollTop = 0;
            this.updateScrollIndicators();
        }, 150);
    }
    
    scrollUp() {
        if (this.isScrolling || this.currentIndex <= 0) return;
        
        this.isScrolling = true;
        this.currentIndex--;
        this.render();
        
        setTimeout(() => {
            this.isScrolling = false;
        }, 300);
    }
    
    scrollDown() {
        if (this.isScrolling || this.currentIndex >= this.textLines.length - 1) return;
        
        this.isScrolling = true;
        this.currentIndex++;
        this.render();
        
        setTimeout(() => {
            this.isScrolling = false;
        }, 300);
    }
    
    handleSelectionChange() {
        const selection = window.getSelection();
        
        if (selection.rangeCount > 0 && !selection.isCollapsed) {
            this.selectedText = selection.toString().trim();
            
            if (this.selectedText && this.selectedText.length > 0) {
                this.askButton.disabled = false;
                
                // Notify Python backend via HTTP API
                this.notifyPythonBackend('text-selected', { text: this.selectedText });
            } else {
                this.selectedText = null;
                this.askButton.disabled = true;
            }
        } else {
            this.selectedText = null;
            this.askButton.disabled = true;
        }
    }
    
    askAboutSelection() {
        if (!this.selectedText) return;
        
        // Notify Python backend via HTTP API
        this.notifyPythonBackend('ask-about-selection', { phrase: this.selectedText });
        
        // Clear selection
        window.getSelection().removeAllRanges();
        this.selectedText = null;
        this.askButton.disabled = true;
    }
    
    notifyPythonBackend(endpoint, data) {
        // Send POST request to Python HTTP server
        fetch(`/api/${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            console.log('API call successful:', result);
        })
        .catch(error => {
            console.error('API call failed:', error);
        });
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is ready
let textDisplay;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        textDisplay = new TextDisplay();
    });
} else {
    textDisplay = new TextDisplay();
}

// Expose API for Python
window.setTextContent = function(text, language) {
    if (textDisplay) {
        textDisplay.setText(text, language);
    }
};

window.clearSelection = function() {
    if (textDisplay) {
        window.getSelection().removeAllRanges();
        textDisplay.selectedText = null;
        textDisplay.askButton.disabled = true;
    }
};

// Poll for text updates from file (fallback when webview API not available)
let lastTimestamp = null;
function pollForTextUpdates() {
    fetch('text_data.json?' + Date.now()) // Cache busting
        .then(response => {
            if (!response.ok) throw new Error('Not found');
            return response.json();
        })
        .then(data => {
            // Only update if timestamp changed
            if (data.timestamp !== lastTimestamp && textDisplay && data.text) {
                lastTimestamp = data.timestamp;
                textDisplay.setText(data.text, data.language || 'en');
            }
        })
        .catch(() => {
            // File not found or error - ignore
        });
}

// Poll every 300ms for updates (smooth updates)
setInterval(pollForTextUpdates, 300);

