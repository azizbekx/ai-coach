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

        // Coaching mode state
        this.coachingStream = null;
        this.coachingInterval = null;
        this.currentSkill = null;
        this.currentSession = 'default';
        this.coachingActive = false;

        this.init();
    }

    init() {
        this.setupModeSelector();
        this.setupUploadMode();
        this.setupWebcamMode();
        this.setupCoachingMode();
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
        if (mode !== 'webcam' && this.webcamStream) {
            this.stopWebcam();
        }

        // Stop coaching if switching away
        if (mode !== 'coaching' && this.coachingActive) {
            this.stopCoaching();
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
        try {
            // Show progress UI
            document.getElementById('uploadArea').style.display = 'none';
            document.getElementById('uploadProgress').style.display = 'block';
            document.getElementById('uploadResults').style.display = 'none';

            // Reset all progress stages
            this.resetProgressStages();

            // Stage 1: Upload with real progress
            this.updateStage('upload', 'in_progress', 'Uploading...', 0);

            const formData = new FormData();
            formData.append('video', file);

            // Use XMLHttpRequest for upload progress
            const xhr = new XMLHttpRequest();

            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    this.updateStage('upload', 'in_progress', `${percentComplete.toFixed(0)}%`, percentComplete);
                }
            });

            const uploadPromise = new Promise((resolve, reject) => {
                xhr.onload = () => {
                    if (xhr.status === 200) {
                        resolve(JSON.parse(xhr.responseText));
                    } else {
                        reject(new Error('Upload failed'));
                    }
                };
                xhr.onerror = () => reject(new Error('Upload failed'));
                xhr.open('POST', '/api/upload');
                xhr.send(formData);
            });

            // Stage 2: Start analysis animation after upload
            setTimeout(() => {
                this.updateStage('upload', 'completed', '100%', 100);
                this.updateStage('analysis', 'in_progress', 'Processing frames...', 10);
                this.startAnalysisSimulation();
            }, 500);

            const result = await uploadPromise();

            // Stage 3: Complete analysis
            this.stopAnalysisSimulation();
            this.updateStage('analysis', 'completed', 'Complete', 100);

            // Stage 4: Gemini (if available)
            if (result.gemini_analysis) {
                document.getElementById('geminiStage').style.display = 'block';
                this.updateStage('gemini', 'in_progress', 'Generating insights...', 50);
                await new Promise(resolve => setTimeout(resolve, 500));
                this.updateStage('gemini', 'completed', 'Complete', 100);
            }

            // Show results
            setTimeout(() => {
                this.displayResults(result);
            }, 500);

        } catch (error) {
            console.error('Upload error:', error);
            alert('Failed to process video: ' + error.message);
            this.resetUploadMode();
        }
    }

    resetProgressStages() {
        this.updateStage('upload', 'waiting', '0%', 0);
        this.updateStage('analysis', 'waiting', 'Waiting...', 0);
        this.updateStage('gemini', 'waiting', 'Waiting...', 0);
        document.getElementById('geminiStage').style.display = 'none';
        document.getElementById('analysisDetails').textContent = '';
    }

    updateStage(stage, status, statusText, progress) {
        const icons = {
            waiting: '⏳',
            in_progress: '⚙️',
            completed: '✅',
            error: '❌'
        };

        const stageIcon = document.getElementById(`${stage}StageIcon`);
        const stageStatus = document.getElementById(`${stage}StageStatus`);
        const progressFill = document.getElementById(`${stage}ProgressFill`);

        if (stageIcon) stageIcon.textContent = icons[status] || '⏳';
        if (stageStatus) stageStatus.textContent = statusText;
        if (progressFill) progressFill.style.width = `${progress}%`;
    }

    startAnalysisSimulation() {
        let progress = 10;
        this.analysisSimInterval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;

            this.updateStage('analysis', 'in_progress', `${Math.floor(progress)}%`, progress);

            const details = document.getElementById('analysisDetails');
            if (details && progress > 30 && progress < 60) {
                details.textContent = 'Detecting poses and measuring angles...';
            } else if (progress >= 60 && progress < 90) {
                details.textContent = 'Calculating scores and identifying errors...';
            }
        }, 800);
    }

    stopAnalysisSimulation() {
        if (this.analysisSimInterval) {
            clearInterval(this.analysisSimInterval);
            this.analysisSimInterval = null;
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

        // Display Gemini analysis if available
        if (data.gemini_analysis && data.gemini_analysis.comprehensive_feedback) {
            const geminiSection = document.getElementById('geminiAnalysis');
            const geminiContent = document.getElementById('geminiContent');

            geminiSection.style.display = 'block';

            // Format Gemini markdown-like feedback
            const feedback = data.gemini_analysis.comprehensive_feedback;
            const formattedFeedback = this.formatGeminiFeedback(feedback);

            geminiContent.innerHTML = formattedFeedback;
        } else {
            document.getElementById('geminiAnalysis').style.display = 'none';
        }

        // Download button
        const downloadBtn = document.getElementById('downloadBtn');
        downloadBtn.onclick = () => {
            window.location.href = data.output_video;
        };
    }

    formatGeminiFeedback(feedback) {
        // Convert markdown-like formatting to HTML
        let formatted = feedback
            // Bold headers
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            // Bullet points
            .replace(/^- (.+)$/gm, '<li>$1</li>')
            // Numbers
            .replace(/^(\d+)\.\s+(.+)$/gm, '<div class="feedback-item"><span class="number">$1.</span> $2</div>')
            // Line breaks
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');

        // Wrap in paragraphs
        formatted = '<div class="gemini-feedback-text"><p>' + formatted + '</p></div>';

        // Clean up empty paragraphs
        formatted = formatted.replace(/<p><\/p>/g, '').replace(/<p><br>/g, '<p>');

        return formatted;
    }

    resetUploadMode() {
        document.getElementById('uploadArea').style.display = 'block';
        document.getElementById('uploadProgress').style.display = 'none';
        document.getElementById('uploadResults').style.display = 'none';
        document.getElementById('videoInput').value = '';
        document.getElementById('progressFill').style.width = '0%';
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

        let isAnalyzing = false;

        // Analyze at ~3 FPS for smooth performance
        this.analysisInterval = setInterval(async () => {
            if (isAnalyzing) return; // Skip if still analyzing previous frame

            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                isAnalyzing = true;

                try {
                    // Set canvas size to match video
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;

                    // Draw current frame
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

                    // Convert to base64 with lower quality for speed
                    const frameData = canvas.toDataURL('image/jpeg', 0.6);

                    // Send for analysis
                    await this.analyzeFrame(frameData);

                    // Update FPS
                    this.updateFPS();
                } finally {
                    isAnalyzing = false;
                }
            }
        }, 333); // ~3 FPS for smooth performance
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

    // Coaching Mode
    setupCoachingMode() {
        this.loadCoachingSkills();

        // Exit coaching button
        document.getElementById('exitCoachingBtn')?.addEventListener('click', () => {
            this.exitActiveCoaching();
        });

        // Start coaching button
        document.getElementById('startCoachingBtn')?.addEventListener('click', () => {
            this.startCoachingWebcam();
        });

        // Stop coaching button
        document.getElementById('stopCoachingBtn')?.addEventListener('click', () => {
            this.stopCoaching();
        });

        // Next step button
        document.getElementById('nextStepBtn')?.addEventListener('click', () => {
            this.advanceToNextStep();
        });

        // Voice toggle for coaching
        document.getElementById('coachingVoiceToggle')?.addEventListener('change', (e) => {
            this.voiceEnabled = e.target.checked;
        });

        // Completion modal buttons
        document.getElementById('tryAnotherSkillBtn')?.addEventListener('click', () => {
            this.exitActiveCoaching();
        });

        document.getElementById('practiceAgainBtn')?.addEventListener('click', () => {
            this.restartCoaching();
        });
    }

    async loadCoachingSkills() {
        try {
            const response = await fetch('/api/coaching/skills');
            const data = await response.json();

            const skillsList = document.getElementById('skillsList');
            skillsList.innerHTML = '';

            // Group skills by difficulty
            const beginnerSkills = data.skills.filter(s => s.difficulty === 'beginner');
            const advancedSkills = data.skills.filter(s => !s.difficulty || s.difficulty !== 'beginner');

            // Add beginner section
            if (beginnerSkills.length > 0) {
                const beginnerHeader = document.createElement('div');
                beginnerHeader.className = 'skills-category-header';
                beginnerHeader.innerHTML = '<h3>🌱 Basic Fundamentals (Start Here!)</h3>';
                skillsList.appendChild(beginnerHeader);

                beginnerSkills.forEach(skill => {
                    this.createSkillCard(skill, skillsList, 'beginner');
                });
            }

            // Add advanced section
            if (advancedSkills.length > 0) {
                const advancedHeader = document.createElement('div');
                advancedHeader.className = 'skills-category-header';
                advancedHeader.innerHTML = '<h3>🏆 Advanced Skills</h3>';
                skillsList.appendChild(advancedHeader);

                advancedSkills.forEach(skill => {
                    this.createSkillCard(skill, skillsList, 'advanced');
                });
            }
        } catch (error) {
            console.error('Error loading coaching skills:', error);
        }
    }

    createSkillCard(skill, container, difficulty) {
        const skillCard = document.createElement('div');
        skillCard.className = `skill-card skill-${difficulty}`;

        const difficultyBadge = difficulty === 'beginner'
            ? '<span class="difficulty-badge beginner">Beginner</span>'
            : '<span class="difficulty-badge advanced">Advanced</span>';

        skillCard.innerHTML = `
            <div class="skill-icon">🤸</div>
            ${difficultyBadge}
            <h3>${skill.display_name}</h3>
            <p>${skill.description}</p>
            <div class="skill-meta">
                <span class="steps-count">${skill.total_steps} Steps</span>
            </div>
        `;
        skillCard.addEventListener('click', () => {
            this.selectSkill(skill.name);
        });
        container.appendChild(skillCard);
    }

    async selectSkill(skillName) {
        try {
            // Start coaching session
            const response = await fetch('/api/coaching/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    skill: skillName,
                    session_id: this.currentSession
                })
            });

            const data = await response.json();

            if (data.success) {
                this.currentSkill = data;

                // Show active coaching interface
                document.getElementById('skillSelection').style.display = 'none';
                document.getElementById('activeCoaching').style.display = 'block';

                // Update UI
                document.getElementById('coachingSkillName').textContent = data.skill_name;
                document.getElementById('totalStepsNum').textContent = data.total_steps;
                this.updateStepDisplay(data.step_info, 1, data.total_steps);

                // Show welcome message
                this.showCoachingMessage(data.welcome_message);
            }
        } catch (error) {
            console.error('Error starting coaching session:', error);
            alert('Failed to start coaching session');
        }
    }

    async startCoachingWebcam() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480 }
            });

            this.coachingStream = stream;
            const video = document.getElementById('coachingVideo');
            video.srcObject = stream;

            // Show video active UI
            document.getElementById('coachingPlaceholder').style.display = 'none';
            document.getElementById('coachingVideoActive').style.display = 'block';

            this.coachingActive = true;

            // Enable voice by default
            this.voiceEnabled = document.getElementById('coachingVoiceToggle').checked;

            // Start analysis loop - slower for coaching to allow for Gemini processing
            let isCoachingAnalyzing = false;
            this.coachingInterval = setInterval(async () => {
                if (isCoachingAnalyzing) return; // Skip if still analyzing

                isCoachingAnalyzing = true;
                try {
                    await this.analyzeCoachingFrame();
                } finally {
                    isCoachingAnalyzing = false;
                }
            }, 1500); // Analyze every 1.5 seconds for coaching

        } catch (error) {
            console.error('Error starting coaching webcam:', error);
            alert('Could not access webcam');
        }
    }

    async analyzeCoachingFrame() {
        const video = document.getElementById('coachingVideo');
        const canvas = document.getElementById('coachingCanvas');
        const ctx = canvas.getContext('2d');

        // Set canvas size
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        // Draw current frame
        ctx.drawImage(video, 0, 0);

        // Convert to base64
        const frameData = canvas.toDataURL('image/jpeg');

        try {
            const response = await fetch('/api/coaching/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    frame: frameData,
                    session_id: this.currentSession
                })
            });

            const data = await response.json();

            if (data.success && data.pose_detected) {
                // Update analyzed frame
                document.getElementById('coachingAnalyzedFrame').src = data.annotated_frame;

                // Update step info
                const stepInfo = data.step_info;
                this.updateStepDisplay(
                    stepInfo,
                    stepInfo.step_number,
                    stepInfo.total_steps
                );

                // Update evaluation
                const evaluation = data.evaluation;
                this.updateStepChecks(evaluation.checks);

                // Show coaching feedback
                const coachingMsg = data.gemini_coaching || evaluation.feedback;
                this.showCoachingMessage(coachingMsg);

                // Speak coaching feedback
                if (this.voiceEnabled && data.audio_text) {
                    this.speakCoaching(data.audio_text);
                }

                // Show next step button if completed
                const nextBtn = document.getElementById('nextStepBtn');
                if (evaluation.step_completed) {
                    nextBtn.style.display = 'block';
                } else {
                    nextBtn.style.display = 'none';
                }

                // Update attempts count
                document.getElementById('attemptsCount').textContent =
                    `Attempt #${evaluation.attempts}`;
            }
        } catch (error) {
            console.error('Error analyzing coaching frame:', error);
        }
    }

    updateStepDisplay(stepInfo, stepNumber, totalSteps) {
        document.getElementById('currentStepNum').textContent = stepNumber;
        document.getElementById('stepName').textContent = stepInfo.name;
        document.getElementById('stepInstruction').textContent = stepInfo.instruction;
        document.getElementById('stepCoachingCue').textContent = stepInfo.coaching_cue;

        // Update progress bar
        const progress = (stepNumber / totalSteps) * 100;
        document.getElementById('stepProgressBar').style.width = `${progress}%`;
    }

    updateStepChecks(checks) {
        const checksContainer = document.getElementById('stepChecks');
        checksContainer.innerHTML = '';

        checks.forEach(check => {
            const checkEl = document.createElement('div');
            checkEl.className = `check-item ${check.status}`;

            const icon = check.status === 'passed' ? '✓' :
                         check.status === 'failed' ? '✗' : '?';

            checkEl.innerHTML = `
                <span class="check-icon">${icon}</span>
                <span class="check-message">${check.message}</span>
            `;
            checksContainer.appendChild(checkEl);
        });
    }

    showCoachingMessage(message) {
        const messageEl = document.getElementById('aiCoachMessage');
        messageEl.innerHTML = `<p>${message}</p>`;
    }

    speakCoaching(text) {
        // Don't spam voice feedback
        if (this.speakCooldown || this.lastSpokenFeedback === text) {
            return;
        }

        // Cancel any ongoing speech
        this.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.9;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        this.currentUtterance = utterance;
        this.lastSpokenFeedback = text;
        this.speechSynthesis.speak(utterance);

        // Cooldown period
        this.speakCooldown = true;
        setTimeout(() => {
            this.speakCooldown = false;
        }, 3000);
    }

    async advanceToNextStep() {
        try {
            const response = await fetch('/api/coaching/next-step', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.currentSession
                })
            });

            const data = await response.json();

            if (data.success) {
                if (data.completed) {
                    // Show completion modal
                    this.showCompletionModal(data.message);
                } else {
                    // Update to next step
                    this.updateStepDisplay(
                        data.step_info,
                        data.step_number,
                        data.total_steps
                    );

                    // Show encouragement
                    this.showCoachingMessage(data.encouragement);

                    if (this.voiceEnabled) {
                        this.speakCoaching(data.encouragement);
                    }

                    // Hide next step button
                    document.getElementById('nextStepBtn').style.display = 'none';

                    // Reset attempts count
                    document.getElementById('attemptsCount').textContent = '';
                }
            }
        } catch (error) {
            console.error('Error advancing to next step:', error);
        }
    }

    showCompletionModal(message) {
        document.getElementById('completionMessage').textContent = message;
        document.getElementById('completionModal').style.display = 'flex';

        // Stop coaching
        this.stopCoaching();

        // Speak completion message
        if (this.voiceEnabled) {
            this.speakCoaching(message);
        }
    }

    exitActiveCoaching() {
        // Stop coaching if active
        if (this.coachingActive) {
            this.stopCoaching();
        }

        // Show skill selection
        document.getElementById('activeCoaching').style.display = 'none';
        document.getElementById('skillSelection').style.display = 'block';

        // Hide completion modal if visible
        document.getElementById('completionModal').style.display = 'none';
    }

    stopCoaching() {
        // Stop webcam stream
        if (this.coachingStream) {
            this.coachingStream.getTracks().forEach(track => track.stop());
            this.coachingStream = null;
        }

        // Stop analysis interval
        if (this.coachingInterval) {
            clearInterval(this.coachingInterval);
            this.coachingInterval = null;
        }

        // Update UI
        document.getElementById('coachingVideoActive').style.display = 'none';
        document.getElementById('coachingPlaceholder').style.display = 'block';

        this.coachingActive = false;

        // Cancel any speech
        this.speechSynthesis.cancel();
    }

    async restartCoaching() {
        // Hide completion modal
        document.getElementById('completionModal').style.display = 'none';

        // Restart the same skill
        if (this.currentSkill) {
            await this.selectSkill(this.currentSkill.skill);
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new GymnasticsCoachApp();
});
