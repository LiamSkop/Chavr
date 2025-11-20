// Text Display JavaScript - Premium scrolling and selection handling

class SpeechBubble {
    constructor(rootId = 'speech-bubble-root') {
        this.root = document.getElementById(rootId) || this.createRoot(rootId);
        this.bubbleEl = null;
        this.contentEl = null;
        this.loadingEl = null;
        this.visible = false;
        this.currentRect = null;
        this.scrollTargets = new Set([window]);
        this.hideCallback = null;
        this.handleDocumentClick = this.handleDocumentClick.bind(this);
        this.handleScroll = this.handleScroll.bind(this);
    }

    createRoot(rootId) {
        const root = document.createElement('div');
        root.id = rootId;
        document.body.appendChild(root);
        return root;
    }

    registerScrollTarget(target) {
        if (target) {
            this.scrollTargets.add(target);
        }
    }

    ensureElements() {
        if (this.bubbleEl) return;

        const bubble = document.createElement('div');
        bubble.className = 'speech-bubble';

        const content = document.createElement('div');
        content.className = 'speech-bubble-content';
        bubble.appendChild(content);

        const loading = document.createElement('div');
        loading.className = 'speech-bubble-loading';
        loading.innerHTML = '<span></span><span></span><span></span>';
        bubble.appendChild(loading);

        this.root.appendChild(bubble);
        this.bubbleEl = bubble;
        this.contentEl = content;
        this.loadingEl = loading;
    }

    setHideCallback(callback) {
        this.hideCallback = callback;
    }

    showAt(rect) {
        if (!rect) return;
        this.ensureElements();
        this.currentRect = rect;
        this.bubbleEl.classList.remove('speech-bubble--below', 'hiding');
        this.bubbleEl.classList.add('visible');
        this.positionBubble(rect);
        this.attachListeners();
        this.visible = true;
    }

    positionBubble(rect) {
        if (!this.bubbleEl) return;
        const bubbleRect = this.bubbleEl.getBoundingClientRect();
        const viewportWidth = document.documentElement.clientWidth;
        const halfWidth = bubbleRect.width / 2;
        const scrollX = window.scrollX || 0;
        const scrollY = window.scrollY || 0;
        let left = rect.left + rect.width / 2 - halfWidth;
        left = Math.min(Math.max(left, 8), viewportWidth - bubbleRect.width - 8);

        let top = rect.top - bubbleRect.height - 12;
        let placementBelow = false;

        if (top < 8) {
            top = rect.bottom + 12;
            placementBelow = true;
        }

        this.bubbleEl.style.left = `${Math.round(left + scrollX)}px`;
        this.bubbleEl.style.top = `${Math.round(top + scrollY)}px`;

        this.bubbleEl.classList.toggle('speech-bubble--below', placementBelow);
    }

    setContent(text) {
        this.ensureElements();
        this.loadingEl.classList.remove('visible');
        this.contentEl.textContent = text;
        if (this.currentRect) {
            this.positionBubble(this.currentRect);
        }
        if (!this.visible && this.currentRect) {
            this.showAt(this.currentRect);
        }
    }

    showLoading() {
        if (!this.bubbleEl || !this.loadingEl) return;
        this.loadingEl.classList.add('visible');
        this.contentEl.textContent = '';
        if (this.currentRect) {
            this.positionBubble(this.currentRect);
        }
    }

    hide(reason = 'manual') {
        if (!this.bubbleEl || !this.visible) return;
        this.visible = false;
        this.currentRect = null;
        this.bubbleEl.classList.add('hiding');
        this.bubbleEl.classList.remove('visible');
        setTimeout(() => {
            if (this.bubbleEl) {
                this.bubbleEl.classList.remove('hiding');
                this.bubbleEl.style.top = '-9999px';
            }
        }, 150);
        this.detachListeners();
        if (this.hideCallback) {
            this.hideCallback(reason);
        }
    }

    attachListeners() {
        document.addEventListener('mousedown', this.handleDocumentClick);
        this.scrollTargets.forEach(target => {
            target.addEventListener('scroll', this.handleScroll, { passive: true });
        });
    }

    detachListeners() {
        document.removeEventListener('mousedown', this.handleDocumentClick);
        this.scrollTargets.forEach(target => {
            target.removeEventListener('scroll', this.handleScroll);
        });
    }

    handleDocumentClick(event) {
        if (!this.bubbleEl) return;
        if (this.bubbleEl.contains(event.target)) {
            return;
        }
        this.hide('click-away');
    }

    handleScroll() {
        this.hide('scroll');
    }

    containsNode(node) {
        return !!(this.bubbleEl && node && this.bubbleEl.contains(node));
    }
}

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
        this.scrollUpBtn = document.getElementById('scroll-up');
        this.scrollDownBtn = document.getElementById('scroll-down');
        
        // Siman navigation elements
        this.simanNav = document.getElementById('siman-navigation');
        this.prevSimanBtn = document.getElementById('prev-siman');
        this.nextSimanBtn = document.getElementById('next-siman');
        this.simanCounter = document.getElementById('siman-counter');
        this.jumpSimanInput = document.getElementById('jump-siman-input');
        this.jumpSimanBtn = document.getElementById('jump-siman-btn');
        
        this.selectionRect = null;
        this.autoExplainTimer = null;
        this.loadingTimer = null;
        this.requestCounter = 0;
        
        this.speechBubble = new SpeechBubble();
        this.speechBubble.registerScrollTarget(this.textContainer);
        this.speechBubble.setHideCallback((reason) => this.handleBubbleHide(reason));
        
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
        document.addEventListener('mouseup', () => this.handleMouseUp());
        
        // Siman navigation buttons
        this.prevSimanBtn.addEventListener('click', () => this.goToPreviousSiman());
        this.nextSimanBtn.addEventListener('click', () => this.goToNextSiman());
        this.jumpSimanBtn.addEventListener('click', () => this.handleJumpToSiman());
        this.jumpSimanInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.handleJumpToSiman();
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
        if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
            this.clearSelectionState({ hideBubble: true, incrementRequest: true });
            return;
        }
        
        const range = selection.getRangeAt(0);
        if (this.speechBubble.containsNode(range.commonAncestorContainer)) {
            return;
        }
        
        if (!this.textContent.contains(range.commonAncestorContainer)) {
            this.clearSelectionState({ hideBubble: true, incrementRequest: true });
            return;
        }
        
        const text = selection.toString().trim();
        if (!text) {
            this.clearSelectionState({ hideBubble: true, incrementRequest: true });
            return;
        }
        
        this.selectedText = text;
        this.selectedSiman = this.getSimanFromRange(range);
        this.selectionRect = range.getBoundingClientRect();
        
        if (!this.selectionRect || (this.selectionRect.width === 0 && this.selectionRect.height === 0)) {
            return;
        }
        
        this.sendSelectionUpdate(text, this.selectedSiman);
    }
    
    handleMouseUp() {
        this.cancelAutoExplainTimer();
        
        if (!this.selectedText || this.selectedText.length < 2 || !this.selectionRect) {
            return;
        }
        
        const snapshot = {
            text: this.selectedText,
            rect: this.selectionRect,
            siman: this.selectedSiman
        };
        
        this.autoExplainTimer = setTimeout(() => {
            if (!this.selectedText || this.selectedText !== snapshot.text) {
                return;
            }
            this.handleAutoExplain(snapshot);
        }, 300);
    }
    
    handleAutoExplain(snapshot) {
        if (!snapshot.rect || snapshot.text.length < 2) return;
        
        this.requestCounter += 1;
        const requestId = this.requestCounter;
        
        this.cancelLoadingTimer();
        this.speechBubble.hide('manual');
        this.speechBubble.showAt(snapshot.rect);
        this.speechBubble.setContent('');
        
        const payload = this.buildSelectionPayload(snapshot);
        
        this.loadingTimer = setTimeout(() => {
            if (this.requestCounter === requestId) {
                this.speechBubble.showLoading();
            }
        }, 500);
        
        fetchSelectionExplanation(payload)
            .then((result) => {
                if (this.requestCounter !== requestId) return;
                this.cancelLoadingTimer();
                
                if (result.status === 'ok' && result.response) {
                    this.speechBubble.setContent(result.response);
                } else {
                    this.speechBubble.hide();
                    console.error('Selection explanation failed', result);
                }
            })
            .catch((error) => {
                if (this.requestCounter !== requestId) return;
                this.cancelLoadingTimer();
                this.speechBubble.hide('error');
                console.error('Selection explanation error', error);
            });
    }
    
    handleBubbleHide(reason) {
        if (reason === 'manual') {
            return;
        }
        this.cancelLoadingTimer();
        this.requestCounter += 1;
    }
    
    buildSelectionPayload(snapshot) {
        const data = { phrase: snapshot.text };
        if (snapshot.siman && this.structuredContent) {
            data.siman = snapshot.siman;
            if (this.structuredContent.klal) {
                data.klal = this.structuredContent.klal;
            }
        }
        return data;
    }
    
    getSimanFromRange(range) {
        let element = range.startContainer.nodeType === Node.TEXT_NODE 
            ? range.startContainer.parentElement 
            : range.startContainer;
        
        while (element && element !== this.textContent) {
            if (element.dataset && element.dataset.siman) {
                const parsed = parseInt(element.dataset.siman, 10);
                if (!Number.isNaN(parsed)) {
                    return parsed;
                }
            }
            element = element.parentElement;
        }
        return null;
    }
    
    sendSelectionUpdate(text, siman) {
        if (!text) return;
        fetch('/api/text-selected', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, siman })
        }).catch(() => {});
    }
    
    cancelAutoExplainTimer() {
        if (this.autoExplainTimer) {
            clearTimeout(this.autoExplainTimer);
            this.autoExplainTimer = null;
        }
    }
    
    cancelLoadingTimer() {
        if (this.loadingTimer) {
            clearTimeout(this.loadingTimer);
            this.loadingTimer = null;
        }
    }
    
    clearSelectionState({ hideBubble = false, incrementRequest = false } = {}) {
        this.selectedText = null;
        this.selectedSiman = null;
        this.selectionRect = null;
        this.cancelAutoExplainTimer();
        if (hideBubble) {
            this.speechBubble.hide('manual');
        }
        if (incrementRequest) {
            this.requestCounter += 1;
        }
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

async function fetchSelectionExplanation(payload) {
    const response = await fetch('/api/ask-about-selection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    
    const data = await response.json().catch(() => ({}));
    
    if (!response.ok) {
        throw new Error(data.message || 'Failed to fetch explanation');
    }
    
    return data;
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
        textDisplay.clearSelectionState({ hideBubble: true, incrementRequest: true });
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

