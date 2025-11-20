// Text Display JavaScript - Premium scrolling and selection handling

class TextDisplay {
    constructor() {
        this.textLines = [];
        this.currentIndex = 0;
        this.isScrolling = false;
        this.selectedText = null;
        this.selectedSiman = null;  // Track which Siman is selected
        this.structuredContent = null;  // Klal/Siman structure
        this.currentSimanIndex = 0;
        
        this.textContainer = document.getElementById('text-container');
        this.textContent = document.getElementById('text-content');
        this.askButton = document.getElementById('ask-btn');
        this.scrollUpBtn = document.getElementById('scroll-up');
        this.scrollDownBtn = document.getElementById('scroll-down');
        
        // Siman navigation elements
        this.simanNav = document.getElementById('siman-navigation');
        this.prevSimanBtn = document.getElementById('prev-siman');
        this.nextSimanBtn = document.getElementById('next-siman');
        this.simanCounter = document.getElementById('siman-counter');
        this.jumpSimanInput = document.getElementById('jump-siman-input');
        this.jumpSimanBtn = document.getElementById('jump-siman-btn');
        
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
        
        // Siman navigation buttons
        this.prevSimanBtn.addEventListener('click', () => this.goToPreviousSiman());
        this.nextSimanBtn.addEventListener('click', () => this.goToNextSiman());
        this.jumpSimanBtn.addEventListener('click', () => this.handleJumpToSiman());
        this.jumpSimanInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.handleJumpToSiman();
            }
        });
        
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
    
    setText(text, language = 'en', structured = null) {
        // Store structured content if available
        this.structuredContent = structured;
        this.currentSimanIndex = 0;
        
        // If structured content exists, use Simanim
        if (structured && structured.simanim && structured.simanim.length > 0) {
            this.textLines = [];
            structured.simanim.forEach((siman, idx) => {
                // Add Siman marker
                const simanLabel = language === 'he' 
                    ? `סימן ${this.hebrewNumber(siman.siman)}` 
                    : `Siman ${siman.siman}`;
                this.textLines.push({
                    type: 'siman-marker',
                    text: simanLabel,
                    siman: siman.siman,
                    index: idx
                });
                
                // Split Siman text into lines
                const simanLines = this.splitIntoLines(siman.text, language);
                simanLines.forEach(line => {
                    this.textLines.push({
                        type: 'text',
                        text: line,
                        siman: siman.siman,
                        simanIndex: idx
                    });
                });
            });
            
            // Show Siman navigation controls
            this.simanNav.style.display = 'flex';
            this.updateSimanNavigation();
        } else {
            // Fallback to regular text splitting
            const lines = this.splitIntoLines(text, language);
            this.textLines = lines.map(line => ({
                type: 'text',
                text: line
            }));
            
            // Hide Siman navigation controls
            this.simanNav.style.display = 'none';
        }
        
        this.currentIndex = 0;
        
        // Set RTL direction for Hebrew
        if (language === 'he') {
            this.textContainer.setAttribute('dir', 'rtl');
        } else {
            this.textContainer.setAttribute('dir', 'ltr');
        }
        
        this.render();
    }
    
    splitIntoLines(text, language = 'en') {
        // Split text into lines (sentences/phrases)
        const sentences = text.split(/([.!?]\s+)/);
        const lines = [];
        let currentLine = '';
        
        for (let part of sentences) {
            if ((currentLine + part).length < 100) {
                currentLine += part;
            } else {
                if (currentLine.trim()) {
                    lines.push(currentLine.trim());
                }
                currentLine = part;
            }
        }
        
        if (currentLine.trim()) {
            lines.push(currentLine.trim());
        }
        
        // If no good splits, split by newlines
        if (lines.length === 0) {
            lines.push(...text.split('\n').filter(line => line.trim()));
        }
        
        // Further break down into shorter segments (max 6-7 words)
        const shortLines = [];
        for (let line of lines) {
            const words = line.split(/\s+/);
            const maxWords = 6;
            for (let i = 0; i < words.length; i += maxWords) {
                const segment = words.slice(i, i + maxWords).join(' ');
                if (segment.trim()) {
                    shortLines.push(segment.trim());
                }
            }
        }
        
        return shortLines.length > 0 ? shortLines : lines;
    }
    
    hebrewNumber(num) {
        // Convert number to Hebrew letter representation
        const hebrewLetters = ['א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט', 'י'];
        if (num <= 10) {
            return hebrewLetters[num - 1] + "'";
        } else if (num <= 20) {
            return 'י' + hebrewLetters[num - 11] + "'";
        } else {
            return num.toString(); // Fallback to number
        }
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
        
        // Get current Siman for highlighting
        const currentSiman = this.getCurrentSiman();
        
        // Format lines with Siman markers
        const formattedLines = linesToShow.map(lineObj => {
            if (lineObj.type === 'siman-marker') {
                const isCurrent = lineObj.siman === currentSiman;
                const className = isCurrent ? 'siman-marker siman-marker-current' : 'siman-marker';
                return `<p class="${className}">${this.escapeHtml(lineObj.text)}</p>`;
            } else {
                // Add spacing between words (double space)
                const words = lineObj.text.split(/\s+/);
                return `<p class="text-line" data-siman="${lineObj.siman || ''}" data-siman-index="${lineObj.simanIndex || ''}">${this.escapeHtml(words.join('  '))}</p>`;
            }
        });
        
        // Fade out, update, fade in
        this.textContent.classList.add('fade-out');
        
        setTimeout(() => {
            this.textContent.innerHTML = formattedLines.join('');
            
            this.textContent.classList.remove('fade-out');
            this.textContent.classList.add('fade-in');
            
            setTimeout(() => {
                this.textContent.classList.remove('fade-in');
            }, 300);
            
            // Scroll to center
            this.textContainer.scrollTop = 0;
            this.updateScrollIndicators();
            
            // Update Siman navigation if structured content exists
            if (this.structuredContent) {
                this.updateSimanNavigation();
            }
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
    
    // Update navigation when scrolling (called from render)
    // This is already handled in render() via updateSimanNavigation()
    
    handleSelectionChange() {
        const selection = window.getSelection();
        
        if (selection.rangeCount > 0 && !selection.isCollapsed) {
            this.selectedText = selection.toString().trim();
            
            // Find which Siman contains the selection
            let simanNum = null;
            const range = selection.getRangeAt(0);
            const startContainer = range.startContainer;
            
            // Try to find Siman from parent element
            let element = startContainer.nodeType === Node.TEXT_NODE 
                ? startContainer.parentElement 
                : startContainer;
            
            while (element && element !== this.textContent) {
                if (element.dataset && element.dataset.siman) {
                    simanNum = parseInt(element.dataset.siman);
                    break;
                }
                element = element.parentElement;
            }
            
            if (this.selectedText && this.selectedText.length > 0) {
                this.askButton.disabled = false;
                this.selectedSiman = simanNum;
                
                // Notify Python backend via HTTP API
                this.notifyPythonBackend('text-selected', { 
                    text: this.selectedText,
                    siman: simanNum
                });
            } else {
                this.selectedText = null;
                this.selectedSiman = null;
                this.askButton.disabled = true;
            }
        } else {
            this.selectedText = null;
            this.selectedSiman = null;
            this.askButton.disabled = true;
        }
    }
    
    askAboutSelection() {
        if (!this.selectedText) return;
        
        // Include Siman reference if available
        const data = { phrase: this.selectedText };
        if (this.selectedSiman && this.structuredContent) {
            data.siman = this.selectedSiman;
            data.klal = this.structuredContent.klal;
        }
        
        // Notify Python backend via HTTP API
        this.notifyPythonBackend('ask-about-selection', data);
        
        // Clear selection
        window.getSelection().removeAllRanges();
        this.selectedText = null;
        this.selectedSiman = null;
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
    
    // Siman Navigation Methods
    
    getCurrentSiman() {
        // Find Siman of currently displayed line
        const currentLine = this.textLines[this.currentIndex];
        if (currentLine && currentLine.siman) {
            return currentLine.siman;
        }
        // Look backwards for Siman marker
        for (let i = this.currentIndex; i >= 0; i--) {
            if (this.textLines[i].type === 'siman-marker') {
                return this.textLines[i].siman;
            }
        }
        return null;
    }
    
    jumpToSiman(simanNum) {
        if (!this.structuredContent || !this.structuredContent.simanim) {
            return false;
        }
        
        // Find first line of Siman (the marker)
        const simanIndex = this.textLines.findIndex(line => 
            line.type === 'siman-marker' && line.siman === simanNum
        );
        
        if (simanIndex >= 0) {
            this.currentIndex = simanIndex;
            this.render();
            return true;
        }
        
        return false;
    }
    
    goToNextSiman() {
        if (!this.structuredContent || !this.structuredContent.simanim) {
            return;
        }
        
        const currentSiman = this.getCurrentSiman();
        if (!currentSiman) {
            // If no current Siman, go to first
            if (this.structuredContent.simanim.length > 0) {
                this.jumpToSiman(this.structuredContent.simanim[0].siman);
            }
            return;
        }
        
        // Find current Siman index
        const currentIndex = this.structuredContent.simanim.findIndex(s => s.siman === currentSiman);
        if (currentIndex >= 0 && currentIndex < this.structuredContent.simanim.length - 1) {
            const nextSiman = this.structuredContent.simanim[currentIndex + 1].siman;
            this.jumpToSiman(nextSiman);
        }
    }
    
    goToPreviousSiman() {
        if (!this.structuredContent || !this.structuredContent.simanim) {
            return;
        }
        
        const currentSiman = this.getCurrentSiman();
        if (!currentSiman) {
            return;
        }
        
        // Find current Siman index
        const currentIndex = this.structuredContent.simanim.findIndex(s => s.siman === currentSiman);
        if (currentIndex > 0) {
            const prevSiman = this.structuredContent.simanim[currentIndex - 1].siman;
            this.jumpToSiman(prevSiman);
        }
    }
    
    handleJumpToSiman() {
        const simanNum = parseInt(this.jumpSimanInput.value);
        if (isNaN(simanNum) || simanNum < 1) {
            return;
        }
        
        // Validate Siman exists
        if (this.structuredContent && this.structuredContent.simanim) {
            const simanExists = this.structuredContent.simanim.some(s => s.siman === simanNum);
            if (simanExists) {
                this.jumpToSiman(simanNum);
                this.jumpSimanInput.value = '';
            } else {
                // Show error or feedback
                const maxSiman = Math.max(...this.structuredContent.simanim.map(s => s.siman));
                alert(`Siman ${simanNum} not found. Please enter a number between 1 and ${maxSiman}.`);
            }
        }
    }
    
    updateSimanNavigation() {
        if (!this.structuredContent || !this.structuredContent.simanim) {
            return;
        }
        
        const currentSiman = this.getCurrentSiman();
        const simanim = this.structuredContent.simanim;
        
        if (!currentSiman || simanim.length === 0) {
            return;
        }
        
        // Update counter
        const currentIndex = simanim.findIndex(s => s.siman === currentSiman);
        const totalSimanim = simanim.length;
        const simanNum = currentSiman;
        
        this.simanCounter.textContent = `Siman ${simanNum} of ${totalSimanim}`;
        
        // Update button states
        this.prevSimanBtn.disabled = currentIndex <= 0;
        this.nextSimanBtn.disabled = currentIndex >= totalSimanim - 1;
        
        // Update input max value
        const maxSiman = Math.max(...simanim.map(s => s.siman));
        this.jumpSimanInput.max = maxSiman;
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
window.setTextContent = function(text, language, structured) {
    if (textDisplay) {
        textDisplay.setText(text, language, structured);
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
                textDisplay.setText(data.text, data.language || 'en', data.structured || null);
            }
        })
        .catch(() => {
            // File not found or error - ignore
        });
}

// Poll every 300ms for updates (smooth updates)
setInterval(pollForTextUpdates, 300);

