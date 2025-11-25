# Medical Emergency Detection & Voice Integration Plan

**Timestamp**: 2025-01-17  
**Status**: PLANNING - Research Complete  
**Tags**: emergency-detection, computer-vision, voice-control, medical-alerts, ai-safety

## Overview

This document outlines the plan for implementing AI-powered medical emergency detection using camera feeds and comprehensive voice input/output capabilities for emergency response, system control, and user interaction.

## Part 1: Medical Emergency Detection (PoL - Person on Location)

### Use Cases

1. **Fall Detection**
   - Person collapsed on floor
   - Person collapsed in bathtub
   - Unconscious person detection

2. **Lack of Movement Detection**
   - Person immobile for suspiciously long time
   - No movement in expected activity areas
   - Extended absence from view

3. **Medical Emergency Indicators**
   - Unusual posture (indicating distress)
   - Seizure detection
   - Distress signals

### Detection Architecture

#### Phase 1: Basic Detection (Weeks 1-4)

**Technology Stack:**
- **Computer Vision**: YOLOv8 or similar for person detection
- **Pose Estimation**: MediaPipe or OpenPose for body pose analysis
- **Motion Analysis**: OpenCV for movement tracking
- **AI Model**: Fine-tuned model for fall detection

**Detection Pipeline:**
```
Camera Feed → Person Detection → Pose Estimation → Movement Analysis → Alert Decision
```

**Key Components:**

1. **Person Detection Module**
   - Detect humans in frame
   - Track person IDs across frames
   - Filter out false positives (pets, objects)

2. **Pose Estimation Module**
   - Extract body keypoints (head, shoulders, hips, knees, ankles)
   - Calculate body orientation and angles
   - Detect unusual postures

3. **Movement Analysis Module**
   - Track movement velocity
   - Detect sudden changes (falls)
   - Monitor stationary periods
   - Calculate time since last movement

4. **Alert Decision Engine**
   - Multi-factor analysis:
     - Body position (horizontal = potential fall)
     - Movement velocity (sudden stop = fall)
     - Time stationary (extended = emergency)
     - Location context (bathroom = higher risk)

#### Phase 2: Advanced Detection (Weeks 5-8)

**Enhanced Features:**
- **Multi-camera fusion**: Correlate detections across cameras
- **Temporal analysis**: Pattern recognition over time
- **Context awareness**: Room-specific rules (bathroom vs living room)
- **False positive reduction**: Machine learning to reduce false alarms

**AI Models:**
- Fine-tuned YOLOv8 for person detection
- Custom fall detection model (trained on fall datasets)
- LSTM for temporal pattern recognition

### Response System

#### Intelligent Staging

**Stage 1: Detection & Verification (0-30 seconds)**
1. AI detects potential emergency
2. System captures snapshot/video clip
3. Verify detection (reduce false positives)
4. Check for movement/response

**Stage 2: Attempt to Rouse (30-60 seconds)**
1. **Voice Alert**: "Are you okay? Do you need help?"
2. **Wait for Response**: Listen for voice response
3. **Visual Check**: Monitor for movement
4. **Repeat**: If no response, escalate

**Stage 3: Contact Relatives (60-90 seconds)**
1. **Primary Contact**: Call/text primary caregiver
2. **Send Alert**: Include snapshot, location, timestamp
3. **Wait for Response**: Allow time for relative to respond
4. **Status Update**: If relative responds, update status

**Stage 4: Emergency Services (90+ seconds or immediate if critical)**
1. **Critical Detection**: Immediate 911 call for obvious emergencies
2. **Escalation**: If no response from relatives
3. **Information Package**: Send location, medical info, access codes
4. **Continuous Monitoring**: Keep monitoring until help arrives

#### Response Configuration

```yaml
emergency_detection:
  enabled: true
  cameras:
    - camera_id: "living_room"
      enabled: true
      zones: ["main_area", "bathroom"]
      sensitivity: "medium"
    - camera_id: "bedroom"
      enabled: true
      zones: ["bed", "bathroom"]
      sensitivity: "high"
  
  detection:
    fall_detection:
      enabled: true
      confidence_threshold: 0.85
      min_duration_seconds: 5  # Person down for 5+ seconds
    
    immobility_detection:
      enabled: true
      max_stationary_minutes: 30  # Alert if no movement for 30 min
      check_interval_seconds: 60
    
    bathroom_monitoring:
      enabled: true
      max_time_minutes: 45  # Alert if in bathroom >45 min
  
  response:
    voice_alert:
      enabled: true
      message: "Are you okay? Do you need help?"
      repeat_count: 3
      repeat_interval_seconds: 10
    
    contacts:
      primary:
        name: "Primary Caregiver"
        phone: "+1234567890"
        sms: true
        call: true
        priority: 1
      
      secondary:
        name: "Secondary Contact"
        phone: "+1234567891"
        sms: true
        call: false
        priority: 2
    
    emergency_services:
      enabled: true
      auto_call: false  # Require confirmation
      critical_auto_call: true  # Auto-call for critical detections
      location: "123 Main St, City, State"
      medical_info: "See medical_info section"
  
  medical_info:
    allergies: []
    medications: []
    conditions: []
    emergency_contact: "+1234567890"
```

### Implementation Details

#### Database Schema

```sql
-- Emergency detections table
CREATE TABLE emergency_detections (
    id SERIAL PRIMARY KEY,
    camera_id VARCHAR(255),
    detection_type VARCHAR(50), -- 'fall', 'immobility', 'distress'
    confidence FLOAT,
    timestamp TIMESTAMP WITH TIME ZONE,
    location VARCHAR(255),
    snapshot_path VARCHAR(500),
    video_clip_path VARCHAR(500),
    status VARCHAR(50), -- 'detected', 'verifying', 'alerted', 'resolved', 'false_positive'
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(255), -- 'user', 'relative', 'emergency_services'
    metadata JSONB
);

-- Emergency response log
CREATE TABLE emergency_responses (
    id SERIAL PRIMARY KEY,
    detection_id INTEGER REFERENCES emergency_detections(id),
    stage VARCHAR(50), -- 'detection', 'voice_alert', 'contact_relative', 'emergency_services'
    action VARCHAR(100), -- 'voice_alert_sent', 'sms_sent', 'call_made'
    timestamp TIMESTAMP WITH TIME ZONE,
    success BOOLEAN,
    response_received BOOLEAN,
    response_text TEXT,
    metadata JSONB
);
```

#### API Endpoints

```python
# Emergency detection endpoints
GET /api/emergency/detections - List recent detections
GET /api/emergency/detections/{id} - Get detection details
POST /api/emergency/detections/{id}/acknowledge - Acknowledge detection
POST /api/emergency/detections/{id}/resolve - Mark as resolved
POST /api/emergency/test - Trigger test detection

# Response endpoints
POST /api/emergency/response/voice - Send voice alert
POST /api/emergency/response/contact - Contact relative
POST /api/emergency/response/911 - Call emergency services
```

## Part 2: Voice Input/Output & Voice Control

### Voice Stack Analysis (Based on Veogen)

**Veogen Stack:**
- **Speech Recognition**: Web Speech API (browser-native)
- **Text-to-Speech**: Web Speech API (browser-native)
- **Audio Management**: Windows PowerShell backend
- **Personality**: Cowboy character with custom responses

**Limitations:**
- Browser-only (requires web interface)
- Limited offline capability
- No wake word detection
- Basic voice control only

### Recommended Enhanced Voice Stack

#### Option 1: Local/Offline Stack (Recommended for Privacy)

**Components:**

1. **Wake Word Detection**
   - **Porcupine** (Picovoice): Lightweight, offline, multiple wake words
   - **Mycroft Precise**: Open-source, customizable
   - **Snowboy** (deprecated but still usable)

2. **Speech Recognition (STT)**
   - **Whisper** (OpenAI): Best accuracy, offline capable, multiple languages
   - **Vosk**: Lightweight, offline, fast
   - **DeepSpeech** (Mozilla): Open-source alternative

3. **Text-to-Speech (TTS)**
   - **Coqui TTS**: High-quality, open-source, multiple voices
   - **Piper**: Fast, lightweight, offline
   - **eSpeak-NG**: Basic but very lightweight

4. **Voice Assistant Framework**
   - **Rhasspy**: Complete offline voice assistant framework
   - **Home Assistant Voice**: Integrated with Home Assistant
   - **Custom Framework**: Build on top of components

#### Option 2: Hybrid Stack (Cloud + Local)

**Components:**

1. **Wake Word**: Porcupine (local, always listening)
2. **STT**: Whisper (local) or Google Speech-to-Text (cloud, better accuracy)
3. **TTS**: Coqui TTS (local) or Google Text-to-Speech (cloud, better quality)
4. **NLU**: Rasa or custom intent recognition

### Voice Control Architecture

```
Wake Word Detection (Always On) 
  ↓
Speech Recognition (STT)
  ↓
Intent Recognition / Command Parsing
  ↓
Action Execution
  ↓
Response Generation
  ↓
Text-to-Speech (TTS)
```

### Voice Commands for Emergency System

#### Emergency Commands
- "Help!" / "Emergency!" → Immediate alert
- "I'm okay" → Cancel false alarm
- "Call [name]" → Call specific contact
- "Call 911" → Emergency services

#### System Control Commands
- "Turn on camera [name]" → Enable camera
- "Show me [location]" → Display camera feed
- "What's my blood pressure?" → Health query
- "What's my glucose?" → Health query
- "Set alert for [time]" → Reminder

#### General Commands
- "What time is it?"
- "What's the weather?"
- "Turn on lights"
- "Play music"

### Implementation Plan

#### Phase 1: Basic Voice I/O (Weeks 1-3)

**Components:**
1. **Whisper Integration**
   - Install Whisper (OpenAI)
   - Create STT service
   - Real-time transcription

2. **Coqui TTS Integration**
   - Install Coqui TTS
   - Create TTS service
   - Voice selection and configuration

3. **Basic Voice Interface**
   - Microphone input handling
   - Speaker output handling
   - Simple command parsing

#### Phase 2: Wake Word Detection (Weeks 4-5)

**Components:**
1. **Porcupine Integration**
   - Install Porcupine
   - Configure wake words ("Hey Home", "Computer", etc.)
   - Always-on listening service

2. **Wake Word Service**
   - Background service
   - Low CPU usage
   - Trigger main voice processing

#### Phase 3: Command Processing (Weeks 6-8)

**Components:**
1. **Intent Recognition**
   - Command parser
   - Intent classification
   - Parameter extraction

2. **Action Execution**
   - System control actions
   - Emergency actions
   - Health queries

3. **Response Generation**
   - Natural language responses
   - Context-aware replies
   - Error handling

#### Phase 4: Emergency Integration (Weeks 9-10)

**Components:**
1. **Emergency Voice Alerts**
   - "Are you okay?" voice prompts
   - Response listening
   - Escalation logic

2. **Voice-Controlled Emergency Response**
   - "Help!" detection
   - "I'm okay" cancellation
   - Voice confirmation for 911 calls

### Voice Stack Dependencies

```python
# requirements-voice.txt
# Speech Recognition
openai-whisper>=20231117  # Best accuracy, offline
# Alternative: vosk>=0.3.45  # Lighter weight

# Text-to-Speech
TTS>=0.20.0  # Coqui TTS
# Alternative: piper-tts  # Faster, lighter

# Wake Word Detection
pvporcupine>=3.0.0  # Porcupine (requires API key, but free tier available)
# Alternative: precise-runner  # Mycroft Precise (fully open-source)

# Audio Processing
pyaudio>=0.2.14  # Audio I/O
sounddevice>=0.4.6  # Alternative audio I/O
webrtcvad>=2.0.10  # Voice Activity Detection

# Voice Assistant Framework (Optional)
# rhasspy-hermes>=2.5.0  # If using Rhasspy
```

### Configuration

```yaml
voice:
  enabled: true
  
  wake_word:
    enabled: true
    engine: "porcupine"  # or "precise"
    keywords: ["hey home", "computer", "assistant"]
    sensitivity: 0.5  # 0.0 to 1.0
  
  speech_recognition:
    engine: "whisper"  # or "vosk", "google"
    model: "base"  # tiny, base, small, medium, large
    language: "en"
    offline: true
  
  text_to_speech:
    engine: "coqui"  # or "piper", "google"
    voice: "default"
    speed: 1.0
    offline: true
  
  emergency:
    voice_alerts:
      enabled: true
      voice: "calm_female"  # Calm, reassuring voice
      volume: 0.8
      repeat_count: 3
    
    response_listening:
      enabled: true
      timeout_seconds: 30
      keywords: ["okay", "help", "yes", "no"]
    
    voice_commands:
      help_keywords: ["help", "emergency", "911"]
      cancel_keywords: ["okay", "false alarm", "cancel"]
```

### Database Schema for Voice

```sql
-- Voice commands log
CREATE TABLE voice_commands (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE,
    audio_file_path VARCHAR(500),
    transcription TEXT,
    intent VARCHAR(100),
    parameters JSONB,
    action_taken VARCHAR(255),
    success BOOLEAN,
    response_text TEXT,
    response_audio_path VARCHAR(500)
);

-- Voice interactions
CREATE TABLE voice_interactions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255),
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    commands_count INTEGER,
    wake_word_detected BOOLEAN,
    metadata JSONB
);
```

## Integration Points

### Emergency Detection → Voice

1. **Detection triggers voice alert**
2. **System listens for response**
3. **Voice response determines escalation**

### Voice → Emergency Response

1. **User says "Help!"**
2. **System immediately triggers emergency protocol**
3. **Voice confirmation for critical actions**

### Voice → System Control

1. **User controls cameras via voice**
2. **User queries health data via voice**
3. **User manages alerts via voice**

## Security & Privacy

### Voice Data Privacy
- **Local Processing**: Prefer offline STT/TTS
- **No Cloud Storage**: Voice data stays local
- **Encryption**: Encrypt stored voice recordings
- **User Consent**: Explicit consent for voice monitoring
- **Data Retention**: Automatic deletion of old recordings

### Emergency Data
- **HIPAA Compliance**: Medical emergency data handling
- **Secure Storage**: Encrypted emergency detection data
- **Access Control**: Restricted access to emergency logs
- **Audit Trail**: Complete logging of all emergency actions

## Testing Strategy

### Emergency Detection Testing
1. **Simulated Falls**: Test with mannequins or actors
2. **False Positive Testing**: Ensure pets/objects don't trigger
3. **Response Time Testing**: Measure detection to alert time
4. **Multi-Camera Testing**: Test across multiple camera feeds

### Voice System Testing
1. **Wake Word Accuracy**: Test false positive rate
2. **Command Recognition**: Test command accuracy
3. **Response Quality**: Test TTS output quality
4. **Emergency Voice Alerts**: Test voice alert delivery

## Timeline

### Phase 1: Emergency Detection (Weeks 1-8)
- Weeks 1-4: Basic detection (fall, immobility)
- Weeks 5-8: Advanced detection (multi-camera, context)

### Phase 2: Response System (Weeks 9-12)
- Weeks 9-10: Voice alerts and response listening
- Weeks 11-12: Contact system and escalation

### Phase 3: Voice Control (Weeks 13-20)
- Weeks 13-15: Basic voice I/O (Whisper + Coqui)
- Weeks 16-17: Wake word detection
- Weeks 18-19: Command processing
- Week 20: Emergency voice integration

**Total Estimated Time**: 20 weeks (5 months)

## Cost Analysis

### Development Costs
- Developer time: ~20 weeks
- Testing equipment: ~$500-1000
- AI model training: ~$200-500 (cloud GPU time)

### Operational Costs
- Porcupine API: Free tier available, paid for commercial
- Cloud STT/TTS (if used): ~$0.006 per minute
- Storage: Minimal (voice recordings, detection data)

### Hardware Costs
- Microphones: $50-200 (quality dependent)
- Speakers: $50-200 (quality dependent)
- Processing: Existing hardware should suffice

## Success Metrics

1. **Detection Accuracy**: >95% true positive rate, <5% false positive rate
2. **Response Time**: <30 seconds from detection to first alert
3. **Voice Recognition**: >90% command accuracy
4. **Wake Word**: <1% false positive rate
5. **User Satisfaction**: Positive feedback on emergency system

## References

- [Whisper (OpenAI)](https://github.com/openai/whisper)
- [Coqui TTS](https://github.com/coqui-ai/TTS)
- [Porcupine (Picovoice)](https://github.com/Picovoice/porcupine)
- [Rhasspy](https://rhasspy.readthedocs.io/)
- [YOLOv8](https://github.com/ultralytics/ultralytics)
- [MediaPipe](https://mediapipe.dev/)
- [Kami Vision Fall Detection](https://www.kamivision.com/)
- [IntelliSee Fall Detection](https://intellisee.com/)

## Related Documents

- `docs/HUMAN_HEALTH_MONITORING_PLAN.md` - Health monitoring integration
- `docs/development/HUMAN_HEALTH_MONITORING_ADN.md` - Health monitoring ADN

---

**Last Updated**: 2025-01-17  
**Next Review**: When Phase 1 implementation begins

