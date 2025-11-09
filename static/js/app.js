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
        this.setupModeSelector();
        this.setupUploadMode();
        this.setupTrainingMode();
        this.setupWebcamMode();
    }

    // Mode Selection
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
        if (mode !== 'webcam' && mode !== 'training' && this.webcamStream) {
            this.stopWebcam();
        }

        // Stop training if switching away
        if (mode !== 'training' && this.trainingStream) {
            this.stopTraining();
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

        // Download button
        const downloadBtn = document.getElementById('downloadBtn');
        downloadBtn.onclick = () => {
            window.location.href = data.output_video;
        };
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

        // Skill selection
        const skillCards = document.querySelectorAll('.skill-card');
        skillCards.forEach(card => {
            card.addEventListener('click', () => {
                const skill = card.dataset.skill;
                this.startSkillTraining(skill);
            });
        });

        // Instruction phase buttons
        document.getElementById('readInstructionBtn').addEventListener('click', () => {
            this.readInstructionAloud();
        });

        document.getElementById('readyToTryBtn').addEventListener('click', () => {
            this.startPreparationPhase();
        });

        // Assessment phase buttons
        document.getElementById('tryAgainBtn').addEventListener('click', () => {
            this.resetToInstruction();
        });

        document.getElementById('newSkillBtn').addEventListener('click', () => {
            this.backToSkillSelection();
        });

        document.getElementById('backToSkillsBtn').addEventListener('click', () => {
            this.backToSkillSelection();
        });
    }

    async startSkillTraining(skill) {
        this.currentSkill = skill;

        // Show training flow, hide skill selection
        document.getElementById('skillSelection').style.display = 'none';
        document.getElementById('trainingFlow').style.display = 'block';

        // Update skill name
        const skillName = skill.replace('_', ' ').charAt(0).toUpperCase() + skill.replace('_', ' ').slice(1);
        document.getElementById('trainingSkillName').textContent = `${skillName} Training`;

        // Load instruction
        await this.loadInstruction(skill);
    }

    async loadInstruction(skill) {
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
            document.getElementById('instructionText').innerHTML =
                data.instruction.replace(/\n/g, '<br>');

            // Automatically read instruction aloud
            setTimeout(() => {
                this.readInstructionAloud();
            }, 500);

        } catch (error) {
            console.error('Error loading instruction:', error);
            document.getElementById('instructionText').textContent =
                'Error loading instruction. Please try again.';
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

    async startPreparationPhase() {
        // Hide instruction, show preparation
        document.getElementById('instructionPhase').style.display = 'none';
        document.getElementById('preparationPhase').style.display = 'block';

        // Start webcam
        try {
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

            // Start countdown
            this.startCountdown();

        } catch (error) {
            console.error('Webcam error:', error);
            alert('Failed to access webcam: ' + error.message);
            this.backToSkillSelection();
        }
    }

    startCountdown() {
        let count = 5;
        const countdownEl = document.getElementById('countdownNumber');

        const interval = setInterval(() => {
            count--;
            countdownEl.textContent = count;

            if (count === 0) {
                clearInterval(interval);
                this.captureAndAssess();
            }
        }, 1000);
    }

    async captureAndAssess() {
        // Hide preparation, show assessment
        document.getElementById('preparationPhase').style.display = 'none';
        document.getElementById('assessmentPhase').style.display = 'block';
        document.getElementById('assessmentResult').style.display = 'none';
        document.getElementById('assessmentStatus').style.display = 'block';

        // Capture frame
        const video = document.getElementById('trainingVideo');
        const canvas = document.getElementById('trainingCanvas');
        const ctx = canvas.getContext('2d');

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);

        const frameData = canvas.toDataURL('image/jpeg', 0.9);

        // Send for assessment
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
                const error = await response.json();
                throw new Error(error.detail || 'Assessment failed');
            }

            const result = await response.json();
            this.displayAssessment(result);

        } catch (error) {
            console.error('Assessment error:', error);
            document.getElementById('assessmentStatus').innerHTML = `
                <div class="status-icon">⚠️</div>
                <h3>Assessment Error</h3>
                <p>${error.message}</p>
                <p>Make sure GEMINI_API_KEY is set in your .env file</p>
            `;
        }
    }

    displayAssessment(result) {
        // Hide status, show result
        document.getElementById('assessmentStatus').style.display = 'none';
        document.getElementById('assessmentResult').style.display = 'block';

        // Update result icon and title
        const resultIcon = document.getElementById('resultIcon');
        const resultTitle = document.getElementById('resultTitle');

        if (result.is_correct) {
            resultIcon.textContent = '✅';
            resultIcon.style.background = 'linear-gradient(135deg, #10b981, #059669)';
            resultTitle.textContent = 'Excellent Form!';
        } else {
            resultIcon.textContent = '📝';
            resultIcon.style.background = 'linear-gradient(135deg, #f59e0b, #d97706)';
            resultTitle.textContent = 'Good Effort! Let\'s Improve';
        }

        // Display full assessment
        document.getElementById('fullAssessment').innerHTML =
            result.assessment.replace(/\n/g, '<br>');

        // Display corrections
        const correctionsList = document.getElementById('correctionsList');
        correctionsList.innerHTML = '';
        result.corrections.forEach(correction => {
            const li = document.createElement('li');
            li.textContent = correction;
            correctionsList.appendChild(li);
        });

        // Display encouragement
        document.getElementById('encouragementText').textContent = result.encouragement;

        // Read encouragement aloud
        setTimeout(() => {
            const utterance = new SpeechSynthesisUtterance(result.encouragement);
            utterance.rate = 1.0;
            this.speechSynthesis.speak(utterance);
        }, 500);
    }

    resetToInstruction() {
        // Stop training stream
        if (this.trainingStream) {
            this.trainingStream.getTracks().forEach(track => track.stop());
            this.trainingStream = null;
        }

        // Reset to instruction phase
        document.getElementById('preparationPhase').style.display = 'none';
        document.getElementById('assessmentPhase').style.display = 'none';
        document.getElementById('instructionPhase').style.display = 'block';

        // Reset countdown
        document.getElementById('countdownNumber').textContent = '5';

        // Read instruction again
        setTimeout(() => {
            this.readInstructionAloud();
        }, 300);
    }

    backToSkillSelection() {
        // Stop training stream
        if (this.trainingStream) {
            this.trainingStream.getTracks().forEach(track => track.stop());
            this.trainingStream = null;
        }

        // Stop any speech
        if (this.speechSynthesis) {
            this.speechSynthesis.cancel();
        }

        // Reset phases
        document.getElementById('instructionPhase').style.display = 'block';
        document.getElementById('preparationPhase').style.display = 'none';
        document.getElementById('assessmentPhase').style.display = 'none';

        // Show skill selection
        document.getElementById('trainingFlow').style.display = 'none';
        document.getElementById('skillSelection').style.display = 'block';

        // Reset countdown
        document.getElementById('countdownNumber').textContent = '5';
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
