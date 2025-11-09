// AI Gymnastics Coach - Frontend Application

class GymnasticsCoachApp {
    constructor() {
        this.currentMode = 'upload';
        this.webcamStream = null;
        this.analysisInterval = null;
        this.fpsCounter = 0;
        this.lastFrameTime = Date.now();

        // Voice feedback settings
        this.voiceEnabled = false;
        this.speechSynthesis = window.speechSynthesis;
        this.currentUtterance = null;
        this.lastSpokenFeedback = '';
        this.speakCooldown = false;

        this.init();
    }

    init() {
        this.setupSectionSelector();
        this.setupModeSelector();
        this.setupUploadMode();
        this.setupTrainingMode();
        this.setupWebcamMode();
    }

    // Section Selection (Video Scoring vs AI Training)
    setupSectionSelector() {
        const sectionBtns = document.querySelectorAll('.section-btn');
        sectionBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const section = btn.dataset.section;
                this.switchSection(section);
            });
        });
    }

    switchSection(section) {
        // Update section buttons
        document.querySelectorAll('.section-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.section === section);
        });

        // Update section content
        document.querySelectorAll('.section-content').forEach(content => {
            content.classList.remove('active');
        });

        const targetSection = document.getElementById(`${section}Content`);
        if (targetSection) {
            targetSection.classList.add('active');
        }

        // Stop any active streams when switching sections
        if (section !== 'scoring' && this.webcamStream) {
            this.stopWebcam();
        }
        if (section !== 'training' && this.trainingStream) {
            this.stopTraining();
        }
    }

    // Mode Selection (within sections)
    setupModeSelector() {
        const modeBtns = document.querySelectorAll('.mode-btn');
        modeBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const mode = btn.dataset.mode;
                this.switchMode(mode);
            });
        });
    }

    switchMode(mode) {
        // Update buttons
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mode === mode);
        });

        // Update content
        document.querySelectorAll('.mode-content').forEach(content => {
            content.classList.remove('active');
        });

        const targetContent = document.getElementById(`${mode}Mode`);
        if (targetContent) {
            targetContent.classList.add('active');
        }

        // Stop webcam if switching away
        if (mode !== 'webcam' && this.webcamStream) {
            this.stopWebcam();
        }

        this.currentMode = mode;
    }

    // Upload Mode
    setupUploadMode() {
        const uploadArea = document.getElementById('uploadArea');
        const videoInput = document.getElementById('videoInput');

        // Click to upload
        uploadArea.addEventListener('click', () => {
            videoInput.click();
        });

        // File selection
        videoInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.handleVideoUpload(file);
            }
        });

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');

            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('video/')) {
                this.handleVideoUpload(file);
            } else {
                alert('Please drop a valid video file');
            }
        });

        // New analysis button
        document.getElementById('newAnalysisBtn').addEventListener('click', () => {
            this.resetUploadMode();
        });
    }

    async handleVideoUpload(file) {
        // Hide upload area, show progress
        document.getElementById('uploadArea').style.display = 'none';
        document.getElementById('uploadProgress').style.display = 'block';
        document.getElementById('uploadResults').style.display = 'none';

        const formData = new FormData();
        formData.append('video', file);

        try {
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');

            progressText.textContent = 'Uploading video...';
            progressFill.style.width = '10%';

            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Upload failed');
            }

            progressText.textContent = 'Processing video with AI...';
            progressFill.style.width = '50%';

            const result = await response.json();

            progressFill.style.width = '100%';
            progressText.textContent = 'Analysis complete!';

            setTimeout(() => {
                this.displayResults(result);
            }, 500);

        } catch (error) {
            console.error('Upload error:', error);
            alert('Failed to process video: ' + error.message);
            this.resetUploadMode();
        }
    }

    displayResults(data) {
        document.getElementById('uploadProgress').style.display = 'none';
        document.getElementById('uploadResults').style.display = 'block';

        const results = data.results;

        // Score overview
        document.getElementById('avgScore').textContent = results.average_score.toFixed(2);
        document.getElementById('bestScore').textContent =
            `${results.best_frame.score.toFixed(2)} (${results.best_frame.timestamp})`;
        document.getElementById('worstScore').textContent =
            `${results.worst_frame.score.toFixed(2)} (${results.worst_frame.timestamp})`;

        // Stats
        document.getElementById('detectedSkill').textContent =
            results.detected_skill.replace('_', ' ').toUpperCase();
        document.getElementById('analyzedFrames').textContent = results.analyzed_frames;
        document.getElementById('totalFrames').textContent = results.total_frames;
        document.getElementById('videoFps').textContent = results.fps;

        // Common errors
        const errorsList = document.getElementById('errorsList');
        errorsList.innerHTML = '';

        if (results.common_errors && results.common_errors.length > 0) {
            results.common_errors.slice(0, 5).forEach(error => {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'error-item';
                errorDiv.innerHTML = `
                    <span class="error-name">${error.error.replace('_', ' ')}</span>
                    <span class="error-count">${error.count} times</span>
                `;
                errorsList.appendChild(errorDiv);
            });
        } else {
            errorsList.innerHTML = '<p style="color: var(--text-muted);">No common errors detected</p>';
        }

        // Generate Gemini AI Summary
        this.generateGeminiSummary(results);

        // Download button
        const downloadBtn = document.getElementById('downloadBtn');
        downloadBtn.onclick = () => {
            window.location.href = data.output_video;
        };
    }

    async generateGeminiSummary(results) {
        const summarySection = document.getElementById('geminiSummary');
        const summaryContent = document.getElementById('geminiSummaryContent');

        // Show section with loading state
        summarySection.style.display = 'block';
        summaryContent.innerHTML = '<div class="loading-spinner">🤖 Generating AI coaching summary...</div>';

        try {
            const response = await fetch('/api/upload/summary', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ results })
            });

            if (!response.ok) {
                throw new Error('Failed to generate summary');
            }

            const data = await response.json();

            if (data.success && data.summary) {
                summaryContent.innerHTML = `<div class="gemini-summary-text">${data.summary.replace(/\n/g, '<br>')}</div>`;
            } else {
                summaryContent.innerHTML = '<p style="color: var(--text-muted);">AI summary not available</p>';
            }

        } catch (error) {
            console.error('Error generating Gemini summary:', error);
            summaryContent.innerHTML = '<p style="color: var(--text-muted);">Could not generate AI summary. Ensure GEMINI_API_KEY is set.</p>';
        }
    }

    resetUploadMode() {
        document.getElementById('uploadArea').style.display = 'block';
        document.getElementById('uploadProgress').style.display = 'none';
        document.getElementById('uploadResults').style.display = 'none';
        document.getElementById('videoInput').value = '';
        document.getElementById('progressFill').style.width = '0%';
    }

    // AI Training Mode
    setupTrainingMode() {
        this.currentSkill = null;
        this.trainingStream = null;
        this.currentInstruction = null;
        this.coachingInterval = null;
        this.lastFeedbackTime = 0;

        // Warm-up specific
        this.currentSequence = null;
        this.currentActionIndex = 0;
        this.warmupStartTime = null;

        // Training mode toggle (Single vs Warm-Up)
        const trainingModeBtns = document.querySelectorAll('.training-mode-btn');
        trainingModeBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const mode = btn.dataset.trainingMode;
                this.switchTrainingMode(mode);
            });
        });

        // Skill selection (single action)
        const skillCards = document.querySelectorAll('.skill-card');
        skillCards.forEach(card => {
            card.addEventListener('click', () => {
                const skill = card.dataset.skill;
                this.startRealTimeCoaching(skill);
            });
        });

        // Load warm-up sequences
        this.loadWarmupSequences();

        // Control buttons
        const readBtn = document.getElementById('readInstructionBtn');
        if (readBtn) {
            readBtn.addEventListener('click', () => {
                this.readInstructionAloud();
            });
        }

        const stopBtn = document.getElementById('stopCoachingBtn');
        if (stopBtn) {
            stopBtn.addEventListener('click', () => {
                this.stopCoaching();
            });
        }

        // Warm-up buttons
        const readWarmupBtn = document.getElementById('readWarmupInstructionBtn');
        if (readWarmupBtn) {
            readWarmupBtn.addEventListener('click', () => {
                this.readInstructionAloud();
            });
        }

        const stopWarmupBtn = document.getElementById('stopWarmupBtn');
        if (stopWarmupBtn) {
            stopWarmupBtn.addEventListener('click', () => {
                this.stopWarmup();
            });
        }

        const doAnotherBtn = document.getElementById('doAnotherWarmupBtn');
        if (doAnotherBtn) {
            doAnotherBtn.addEventListener('click', () => {
                this.backToWarmupSelection();
            });
        }

        const backToMenuBtn = document.getElementById('backToMenuBtn');
        if (backToMenuBtn) {
            backToMenuBtn.addEventListener('click', () => {
                this.stopWarmup();
                this.switchTrainingMode('single');
            });
        }
    }

    switchTrainingMode(mode) {
        // Update buttons
        document.querySelectorAll('.training-mode-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.trainingMode === mode);
        });

        // Show/hide sections
        if (mode === 'single') {
            document.getElementById('skillSelection').style.display = 'block';
            document.getElementById('warmupSelection').style.display = 'none';
        } else {
            document.getElementById('skillSelection').style.display = 'none';
            document.getElementById('warmupSelection').style.display = 'block';
        }
    }

    async loadWarmupSequences() {
        try {
            const response = await fetch('/api/warmup/sequences');
            const data = await response.json();

            const grid = document.getElementById('warmupGrid');
            grid.innerHTML = '';

            data.sequences.forEach(seq => {
                const card = document.createElement('div');
                card.className = 'warmup-card';
                card.dataset.sequenceId = seq.id;
                card.innerHTML = `
                    <div class="warmup-icon">${seq.icon}</div>
                    <h3>${seq.name}</h3>
                    <p>${seq.description}</p>
                    <div class="warmup-meta">${seq.action_count} actions</div>
                `;
                card.addEventListener('click', () => {
                    this.startWarmup(seq.id);
                });
                grid.appendChild(card);
            });
        } catch (error) {
            console.error('Error loading warm-up sequences:', error);
        }
    }

    async startWarmup(sequenceId) {
        try {
            const response = await fetch(`/api/warmup/${sequenceId}`);
            const data = await response.json();

            this.currentSequence = data.sequence;
            this.currentActionIndex = 0;
            this.warmupStartTime = Date.now();

            // Hide selection, show flow
            document.getElementById('warmupSelection').style.display = 'none';
            document.getElementById('warmupFlow').style.display = 'block';
            document.getElementById('warmupCompletion').style.display = 'none';

            // Update header
            document.getElementById('warmupSequenceName').textContent = this.currentSequence.name;

            // Update progress
            document.getElementById('totalActions').textContent = this.currentSequence.actions.length;

            // Build actions list
            this.updateWarmupActionsList();

            // Start first action
            await this.startWarmupAction();

        } catch (error) {
            console.error('Error starting warm-up:', error);
            alert('Failed to start warm-up: ' + error.message);
        }
    }

    async startWarmupAction() {
        const action = this.currentSequence.actions[this.currentActionIndex];
        this.currentSkill = action.skill;

        // Update UI
        document.getElementById('currentActionNumber').textContent = this.currentActionIndex + 1;
        const skillName = action.skill.replace('_', ' ').split('_').map(word =>
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
        document.getElementById('currentActionName').textContent = skillName;
        document.getElementById('currentActionDuration').textContent = action.duration;

        // Update progress bar
        const progress = ((this.currentActionIndex) / this.currentSequence.actions.length) * 100;
        document.getElementById('warmupProgressBar').style.width = `${progress}%`;

        // Update actions list highlighting
        this.updateWarmupActionsList();

        // Load instruction
        await this.loadInstruction(action.skill, 'warmupInstructionText');

        // Start webcam and coaching if not already started
        if (!this.trainingStream) {
            await this.startWarmupCoaching();
        }
    }

    updateWarmupActionsList() {
        const list = document.getElementById('warmupActionsList');
        list.innerHTML = '';

        this.currentSequence.actions.forEach((action, index) => {
            const li = document.createElement('li');
            li.className = 'warmup-action-item';

            if (index < this.currentActionIndex) {
                li.classList.add('completed');
            } else if (index === this.currentActionIndex) {
                li.classList.add('current');
            }

            const skillName = action.skill.replace('_', ' ').split('_').map(word =>
                word.charAt(0).toUpperCase() + word.slice(1)
            ).join(' ');

            li.innerHTML = `
                <span class="action-status">${index < this.currentActionIndex ? '✅' : index === this.currentActionIndex ? '▶' : '○'}</span>
                <span class="action-name">${skillName}</span>
            `;
            list.appendChild(li);
        });
    }

    async startWarmupCoaching() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user'
                }
            });

            this.trainingStream = stream;
            const video = document.getElementById('warmupVideo');
            video.srcObject = stream;

            await new Promise(resolve => {
                video.onloadedmetadata = () => {
                    video.play();
                    resolve();
                };
            });

            // Start coaching (every 3 seconds for warm-up)
            this.coachingInterval = setInterval(() => {
                this.analyzeWarmupAction();
            }, 3000);

            // First analysis after 1 second
            setTimeout(() => this.analyzeWarmupAction(), 1000);

        } catch (error) {
            console.error('Webcam error:', error);
            alert('Failed to access webcam: ' + error.message);
            this.stopWarmup();
        }
    }

    async analyzeWarmupAction() {
        if (!this.trainingStream || !this.currentSkill) return;

        const video = document.getElementById('warmupVideo');
        const canvas = document.getElementById('warmupCanvas');
        const ctx = canvas.getContext('2d');

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);

        const frameData = canvas.toDataURL('image/jpeg', 0.8);

        const feedbackEl = document.getElementById('warmupFeedbackText');
        feedbackEl.innerHTML = '<div class="feedback-waiting"><span class="pulse-dot"></span> Analyzing...</div>';

        try {
            const response = await fetch('/api/training/assess', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    skill: this.currentSkill,
                    frame: frameData
                })
            });

            if (!response.ok) {
                throw new Error('Assessment failed');
            }

            const result = await response.json();
            this.displayWarmupFeedback(result);

        } catch (error) {
            console.error('Warm-up coaching error:', error);
            feedbackEl.innerHTML = `<div class="feedback-error">⚠️ ${error.message}<br><small>Make sure GEMINI_API_KEY is set</small></div>`;
        }
    }

    displayWarmupFeedback(result) {
        const feedbackEl = document.getElementById('warmupFeedbackText');
        const correctIndicator = document.getElementById('warmupCorrectIndicator');

        let feedbackHTML = '';

        if (result.is_correct) {
            feedbackHTML = '<div class="feedback-positive">✅ <strong>Perfect!</strong> ' + (result.encouragement || 'Great job!') + '</div>';

            // Show correct indicator
            correctIndicator.style.display = 'block';

            // Auto-advance to next action after 2 seconds
            setTimeout(() => {
                this.advanceToNextAction();
            }, 2000);
        } else {
            feedbackHTML = '<div class="feedback-improve">📝 <strong>Keep trying!</strong> ';
            if (result.corrections && result.corrections.length > 0) {
                feedbackHTML += result.corrections[0];
            }
            feedbackHTML += '</div>';

            correctIndicator.style.display = 'none';
        }

        feedbackEl.innerHTML = feedbackHTML;

        // Voice feedback (throttled)
        const nowTime = Date.now();
        if (nowTime - this.lastFeedbackTime > 8000) {
            this.lastFeedbackTime = nowTime;

            const textToSpeak = result.is_correct ?
                (result.encouragement || 'Perfect! Moving to next action') :
                (result.corrections[0] || 'Keep trying!');

            const utterance = new SpeechSynthesisUtterance(textToSpeak);
            utterance.rate = 0.95;
            this.speechSynthesis.speak(utterance);
        }
    }

    async advanceToNextAction() {
        this.currentActionIndex++;

        if (this.currentActionIndex >= this.currentSequence.actions.length) {
            // Sequence complete!
            this.completeWarmup();
        } else {
            // Load next action
            await this.startWarmupAction();
        }
    }

    completeWarmup() {
        // Stop coaching
        if (this.coachingInterval) {
            clearInterval(this.coachingInterval);
            this.coachingInterval = null;
        }

        if (this.trainingStream) {
            this.trainingStream.getTracks().forEach(track => track.stop());
            this.trainingStream = null;
        }

        // Calculate time
        const totalTime = Math.floor((Date.now() - this.warmupStartTime) / 1000);
        const minutes = Math.floor(totalTime / 60);
        const seconds = totalTime % 60;

        // Show completion screen
        document.getElementById('warmupFlow').querySelector('.live-coaching-container').style.display = 'none';
        document.getElementById('warmupFlow').querySelector('.current-action-banner').style.display = 'none';
        document.getElementById('warmupCompletion').style.display = 'block';

        document.getElementById('completionTime').textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        document.getElementById('completionActions').textContent = this.currentSequence.actions.length;

        // Speak completion
        const utterance = new SpeechSynthesisUtterance('Congratulations! You\'ve completed the warm-up sequence!');
        this.speechSynthesis.speak(utterance);
    }

    backToWarmupSelection() {
        document.getElementById('warmupFlow').style.display = 'none';
        document.getElementById('warmupCompletion').style.display = 'none';
        document.getElementById('warmupSelection').style.display = 'block';

        // Reset state
        this.currentSequence = null;
        this.currentActionIndex = 0;
    }

    stopWarmup() {
        if (this.coachingInterval) {
            clearInterval(this.coachingInterval);
            this.coachingInterval = null;
        }

        if (this.trainingStream) {
            this.trainingStream.getTracks().forEach(track => track.stop());
            this.trainingStream = null;
        }

        if (this.speechSynthesis) {
            this.speechSynthesis.cancel();
        }

        document.getElementById('warmupFlow').style.display = 'none';
        document.getElementById('warmupCompletion').style.display = 'none';
        document.getElementById('warmupSelection').style.display = 'block';

        this.currentSequence = null;
        this.currentActionIndex = 0;
    }

    async startRealTimeCoaching(skill) {
        this.currentSkill = skill;

        // Show training flow, hide skill selection
        document.getElementById('skillSelection').style.display = 'none';
        document.getElementById('trainingFlow').style.display = 'block';

        // Update skill name
        const skillName = skill.replace('_', ' ').split('_').map(word =>
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
        document.getElementById('trainingSkillName').textContent = `${skillName} - Live Coaching`;

        // Load instruction
        await this.loadInstruction(skill);

        // Start webcam and coaching
        await this.startLiveCoaching();
    }

    async loadInstruction(skill, targetElementId = 'instructionText') {
        try {
            const response = await fetch('/api/training/instruction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ skill })
            });

            if (!response.ok) {
                throw new Error('Failed to load instruction');
            }

            const data = await response.json();
            this.currentInstruction = data.instruction;

            // Display instruction
            const element = document.getElementById(targetElementId);
            if (element) {
                element.innerHTML = data.instruction.replace(/\n/g, '<br>');
            }

            // Automatically read instruction aloud (only for initial load, not warmup transitions)
            if (targetElementId === 'instructionText') {
                setTimeout(() => {
                    this.readInstructionAloud();
                }, 500);
            }

        } catch (error) {
            console.error('Error loading instruction:', error);
            const element = document.getElementById(targetElementId);
            if (element) {
                element.textContent = 'Error loading instruction. Please try again.';
            }
        }
    }

    readInstructionAloud() {
        if (!this.currentInstruction) return;

        // Stop any ongoing speech
        if (this.speechSynthesis) {
            this.speechSynthesis.cancel();
        }

        const utterance = new SpeechSynthesisUtterance(this.currentInstruction);
        utterance.rate = 0.9;  // Slightly slower for clarity
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        // Try to use a natural voice
        const voices = this.speechSynthesis.getVoices();
        const preferredVoice = voices.find(voice =>
            voice.lang.startsWith('en') &&
            (voice.name.includes('Google') || voice.name.includes('Natural') || voice.name.includes('Female'))
        );
        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }

        this.speechSynthesis.speak(utterance);
    }

    async startLiveCoaching() {
        try {
            // Start webcam
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user'
                }
            });

            this.trainingStream = stream;
            const video = document.getElementById('trainingVideo');
            video.srcObject = stream;

            // Wait for video to be ready
            await new Promise(resolve => {
                video.onloadedmetadata = () => {
                    video.play();
                    resolve();
                };
            });

            // Start continuous coaching (analyze every 4 seconds)
            this.coachingInterval = setInterval(() => {
                this.analyzeAndCoach();
            }, 4000);

            // Do first analysis after 1 second
            setTimeout(() => this.analyzeAndCoach(), 1000);

        } catch (error) {
            console.error('Webcam error:', error);
            alert('Failed to access webcam: ' + error.message);
            this.stopCoaching();
        }
    }

    async analyzeAndCoach() {
        if (!this.trainingStream || !this.currentSkill) return;

        const video = document.getElementById('trainingVideo');
        const canvas = document.getElementById('trainingCanvas');
        const ctx = canvas.getContext('2d');

        // Capture current frame
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);

        const frameData = canvas.toDataURL('image/jpeg', 0.8);

        // Update UI to show analyzing
        const feedbackEl = document.getElementById('liveFeedbackText');
        feedbackEl.innerHTML = '<div class="feedback-waiting"><span class="pulse-dot"></span> Analyzing...</div>';

        try {
            const response = await fetch('/api/training/assess', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    skill: this.currentSkill,
                    frame: frameData
                })
            });

            if (!response.ok) {
                throw new Error('Assessment failed');
            }

            const result = await response.json();
            this.displayLiveCoachingFeedback(result);

        } catch (error) {
            console.error('Coaching error:', error);
            feedbackEl.innerHTML = `<div class="feedback-error">⚠️ ${error.message}<br><small>Make sure GEMINI_API_KEY is set</small></div>`;
        }
    }

    displayLiveCoachingFeedback(result) {
        const feedbackEl = document.getElementById('liveFeedbackText');
        const timestampEl = document.getElementById('feedbackTimestamp');

        // Format feedback based on what we have
        let feedbackHTML = '';

        if (result.is_correct) {
            feedbackHTML += '<div class="feedback-positive">✅ <strong>Great!</strong> ';
        } else {
            feedbackHTML += '<div class="feedback-improve">📝 <strong>Keep going!</strong> ';
        }

        // Add main feedback
        if (result.corrections && result.corrections.length > 0) {
            feedbackHTML += result.corrections[0];
        } else if (result.encouragement) {
            feedbackHTML += result.encouragement;
        }

        feedbackHTML += '</div>';

        // Add full assessment if available
        if (result.assessment && result.assessment.length > 50) {
            feedbackHTML += `<div class="feedback-details"><small>${result.assessment.substring(0, 200)}...</small></div>`;
        }

        feedbackEl.innerHTML = feedbackHTML;

        // Update timestamp
        const now = new Date();
        timestampEl.textContent = `Last updated: ${now.toLocaleTimeString()}`;

        // Speak the first correction or encouragement (throttled)
        const nowTime = Date.now();
        if (nowTime - this.lastFeedbackTime > 8000) { // At most every 8 seconds
            this.lastFeedbackTime = nowTime;

            const textToSpeak = result.corrections[0] || result.encouragement || 'Looking good!';
            const utterance = new SpeechSynthesisUtterance(textToSpeak);
            utterance.rate = 0.95;
            this.speechSynthesis.speak(utterance);
        }
    }

    stopCoaching() {
        // Stop coaching interval
        if (this.coachingInterval) {
            clearInterval(this.coachingInterval);
            this.coachingInterval = null;
        }

        // Stop webcam
        if (this.trainingStream) {
            this.trainingStream.getTracks().forEach(track => track.stop());
            this.trainingStream = null;
        }

        // Stop speech
        if (this.speechSynthesis) {
            this.speechSynthesis.cancel();
        }

        // Back to skill selection
        document.getElementById('trainingFlow').style.display = 'none';
        document.getElementById('skillSelection').style.display = 'block';
    }

    stopTraining() {
        if (this.trainingStream) {
            this.trainingStream.getTracks().forEach(track => track.stop());
            this.trainingStream = null;
        }

        if (this.speechSynthesis) {
            this.speechSynthesis.cancel();
        }

        // Reset to skill selection
        this.backToSkillSelection();
    }

    // Webcam Mode
    setupWebcamMode() {
        document.getElementById('startWebcamBtn').addEventListener('click', () => {
            this.startWebcam();
        });

        document.getElementById('stopWebcamBtn').addEventListener('click', () => {
            this.stopWebcam();
        });

        // Voice feedback toggle
        const voiceToggle = document.getElementById('voiceToggle');
        if (voiceToggle) {
            // Load saved preference
            this.voiceEnabled = localStorage.getItem('voiceEnabled') === 'true';
            voiceToggle.checked = this.voiceEnabled;

            voiceToggle.addEventListener('change', (e) => {
                this.voiceEnabled = e.target.checked;
                localStorage.setItem('voiceEnabled', this.voiceEnabled);

                if (!this.voiceEnabled && this.currentUtterance) {
                    this.speechSynthesis.cancel();
                }

                console.log('Voice feedback:', this.voiceEnabled ? 'enabled' : 'disabled');
            });
        }
    }

    async startWebcam() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user'
                }
            });

            this.webcamStream = stream;

            const video = document.getElementById('webcamVideo');
            video.srcObject = stream;

            // Show webcam interface
            document.getElementById('webcamPlaceholder').style.display = 'none';
            document.getElementById('webcamActive').style.display = 'block';

            // Start analysis
            this.startLiveAnalysis();

        } catch (error) {
            console.error('Webcam error:', error);
            alert('Failed to access webcam: ' + error.message);
        }
    }

    stopWebcam() {
        if (this.webcamStream) {
            this.webcamStream.getTracks().forEach(track => track.stop());
            this.webcamStream = null;
        }

        if (this.analysisInterval) {
            clearInterval(this.analysisInterval);
            this.analysisInterval = null;
        }

        // Stop any ongoing speech
        if (this.speechSynthesis) {
            this.speechSynthesis.cancel();
        }
        this.speakCooldown = false;
        this.lastSpokenFeedback = '';

        document.getElementById('webcamPlaceholder').style.display = 'block';
        document.getElementById('webcamActive').style.display = 'none';

        // Reset feedback
        this.resetLiveFeedback();
    }

    startLiveAnalysis() {
        const video = document.getElementById('webcamVideo');
        const canvas = document.getElementById('webcamCanvas');
        const ctx = canvas.getContext('2d');

        // Analyze at ~10 FPS to reduce load
        this.analysisInterval = setInterval(async () => {
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                // Set canvas size to match video
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;

                // Draw current frame
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

                // Convert to base64
                const frameData = canvas.toDataURL('image/jpeg', 0.8);

                // Send for analysis
                await this.analyzeFrame(frameData);

                // Update FPS
                this.updateFPS();
            }
        }, 100); // 10 FPS
    }

    async analyzeFrame(frameData) {
        try {
            const response = await fetch('/api/webcam/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ frame: frameData })
            });

            if (!response.ok) {
                console.error('Analysis failed');
                return;
            }

            const result = await response.json();

            if (result.success && result.pose_detected) {
                this.updateLiveFeedback(result);
            } else {
                this.showNoPoseDetected();
            }

        } catch (error) {
            console.error('Analysis error:', error);
        }
    }

    updateLiveFeedback(result) {
        const analysis = result.analysis;

        // Update annotated frame
        const analyzedFrame = document.getElementById('analyzedFrame');
        const noAnalysis = document.getElementById('noAnalysis');

        analyzedFrame.src = result.annotated_frame;
        analyzedFrame.style.display = 'block';
        noAnalysis.style.display = 'none';

        // Update skill and score
        const skillText = analysis.skill.replace('_', ' ').toUpperCase();
        const feedbackSource = analysis.feedback_source === 'hybrid' ? ' (AI Enhanced)' : '';
        document.getElementById('liveSkill').textContent = skillText + feedbackSource;
        document.getElementById('liveScore').textContent =
            `${analysis.score.toFixed(1)}/10`;

        // Color code score badge
        const scoreBadge = document.getElementById('liveScore');
        if (analysis.score >= 9.0) {
            scoreBadge.style.background = 'linear-gradient(135deg, #10b981, #059669)';
        } else if (analysis.score >= 8.0) {
            scoreBadge.style.background = 'linear-gradient(135deg, #f59e0b, #d97706)';
        } else {
            scoreBadge.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)';
        }

        // Update strengths
        const strengthsDiv = document.getElementById('liveStrengths');
        if (analysis.feedback.strengths.length > 0) {
            strengthsDiv.innerHTML = '<ul>' +
                analysis.feedback.strengths.map(s => `<li>✓ ${s}</li>`).join('') +
                '</ul>';
        } else {
            strengthsDiv.innerHTML = '<p class="placeholder">Keep going!</p>';
        }

        // Update corrections
        const correctionsDiv = document.getElementById('liveCorrections');
        if (analysis.feedback.corrections.length > 0) {
            correctionsDiv.innerHTML = '<ul>' +
                analysis.feedback.corrections.map(c => `<li>${c}</li>`).join('') +
                '</ul>';
        } else {
            correctionsDiv.innerHTML = '<p class="placeholder">Great form!</p>';
        }

        // Update tips
        const tipsDiv = document.getElementById('liveTips');
        if (analysis.feedback.tips.length > 0) {
            tipsDiv.innerHTML = '<ul>' +
                analysis.feedback.tips.map(t => `<li>${t}</li>`).join('') +
                '</ul>';
        } else {
            tipsDiv.innerHTML = '<p class="placeholder">No tips needed</p>';
        }

        // Update warnings
        const warningsSection = document.getElementById('liveWarnings');
        const warningsList = document.getElementById('warningsList');

        if (analysis.feedback.warnings.length > 0) {
            warningsSection.style.display = 'block';
            warningsList.innerHTML = '<ul>' +
                analysis.feedback.warnings.map(w => `<li>⚠️ ${w}</li>`).join('') +
                '</ul>';
        } else {
            warningsSection.style.display = 'none';
        }

        // Display Gemini AI enhanced feedback if available
        let geminiSection = document.getElementById('geminiEnhanced');
        if (!geminiSection) {
            // Create Gemini section if it doesn't exist
            geminiSection = document.createElement('div');
            geminiSection.id = 'geminiEnhanced';
            geminiSection.className = 'gemini-enhanced';
            geminiSection.innerHTML = '<h4>🤖 AI Enhanced Feedback</h4><div id="geminiContent"></div>';
            document.getElementById('liveFeedback').appendChild(geminiSection);
        }

        if (analysis.gemini_feedback) {
            geminiSection.style.display = 'block';
            document.getElementById('geminiContent').innerHTML =
                '<pre style="white-space: pre-wrap; font-family: inherit; margin: 0;">' +
                analysis.gemini_feedback +
                '</pre>';
        } else {
            geminiSection.style.display = 'none';
        }

        // Speak feedback if voice is enabled (with smart timing)
        const spokenFeedback = this.generateSpokenFeedback(analysis);
        if (spokenFeedback && this.voiceEnabled) {
            // Only speak every 5 seconds to avoid overwhelming the user
            if (!this.speakCooldown) {
                setTimeout(() => {
                    this.speakFeedback(spokenFeedback);
                }, 500); // Small delay to let rendering complete
            }
        }
    }

    showNoPoseDetected() {
        const analyzedFrame = document.getElementById('analyzedFrame');
        const noAnalysis = document.getElementById('noAnalysis');

        analyzedFrame.style.display = 'none';
        noAnalysis.style.display = 'block';

        // Reset feedback to placeholders
        this.resetLiveFeedback();
    }

    resetLiveFeedback() {
        document.getElementById('liveSkill').textContent = '-';
        document.getElementById('liveScore').textContent = '-';

        document.getElementById('liveStrengths').innerHTML =
            '<p class="placeholder">Perform a gymnastics move to see analysis...</p>';
        document.getElementById('liveCorrections').innerHTML =
            '<p class="placeholder">No corrections yet...</p>';
        document.getElementById('liveTips').innerHTML =
            '<p class="placeholder">Tips will appear here...</p>';

        document.getElementById('liveWarnings').style.display = 'none';
    }

    updateFPS() {
        const now = Date.now();
        const delta = now - this.lastFrameTime;
        this.lastFrameTime = now;

        const fps = Math.round(1000 / delta);
        document.getElementById('fpsCounter').textContent = fps;
    }

    speakFeedback(text) {
        // Check if voice is enabled and speech synthesis is available
        if (!this.voiceEnabled || !this.speechSynthesis || this.speakCooldown) {
            return;
        }

        // Avoid repeating the same feedback
        if (text === this.lastSpokenFeedback) {
            return;
        }

        // Cancel any ongoing speech
        this.speechSynthesis.cancel();

        // Create new utterance
        this.currentUtterance = new SpeechSynthesisUtterance(text);

        // Configure voice settings
        this.currentUtterance.rate = 1.0;  // Normal speed
        this.currentUtterance.pitch = 1.0; // Normal pitch
        this.currentUtterance.volume = 0.9; // Slightly lower volume

        // Try to use a more natural voice (English)
        const voices = this.speechSynthesis.getVoices();
        const preferredVoice = voices.find(voice =>
            voice.lang.startsWith('en') &&
            (voice.name.includes('Google') || voice.name.includes('Natural'))
        );
        if (preferredVoice) {
            this.currentUtterance.voice = preferredVoice;
        }

        // Event handlers
        this.currentUtterance.onend = () => {
            this.speakCooldown = false;
        };

        this.currentUtterance.onerror = (error) => {
            console.error('Speech synthesis error:', error);
            this.speakCooldown = false;
        };

        // Speak the text
        this.speechSynthesis.speak(this.currentUtterance);
        this.lastSpokenFeedback = text;
        this.speakCooldown = true;
    }

    generateSpokenFeedback(analysis) {
        // Create concise spoken feedback from Gemini or analysis
        if (analysis.gemini_feedback) {
            // Use Gemini feedback directly (it's already conversational)
            return analysis.gemini_feedback;
        }

        // Fallback: Create spoken feedback from standard analysis
        const skill = analysis.skill.replace('_', ' ');
        const score = analysis.score.toFixed(1);
        const quality = analysis.quality;

        let spokenText = `${skill}. Score: ${score} out of 10. ${quality}. `;

        // Add top correction if available
        if (analysis.feedback.corrections.length > 0) {
            const topCorrection = analysis.feedback.corrections[0]
                .replace(/🔴|🟠|🟡|⚪/g, '')  // Remove emoji
                .replace(/CRITICAL:|MAJOR:|FIX:|IMPROVE:/g, ''); // Remove severity labels
            spokenText += topCorrection;
        }

        return spokenText;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new GymnasticsCoachApp();
});
