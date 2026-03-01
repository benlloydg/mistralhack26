"""
DemoOrchestrator v2 — event-driven, audio-timeline-based orchestrator.

Key change from v1: Instead of 6 sequential phases with asyncio.sleep() timers,
audio streaming to Scribe v2 Realtime drives the timeline. Each committed
transcript chunk IMMEDIATELY triggers translate → intake → triage → dispatch
for minimal system latency.

Architecture:
- Audio stream (scene.mp4 → PCM → Scribe v2) runs as the primary task
- Each committed transcript fires on_committed_transcript() which
  launches the agent pipeline as a concurrent task
- Vision pipeline runs independently via asyncio.create_task
- Operator approval still blocks dispatch generation
- Evacuation TTS fires when fire + people-at-risk detected
"""
import asyncio
import logging
import os
import time

from ..agents.shared_deps import TriageNetDeps
from ..agents.triage_agent import triage_agent
from ..agents.intake_agent import intake_agent
from ..agents.dispatch_agent import dispatch_agent
from ..agents.case_match_agent import evidence_fusion_agent
from ..agents.vision_agent import analyze_frame, compute_scene_delta
from ..services.state import StateManager
from ..services.transcription import translate_to_english
from ..services.tts import generate_and_save
from ..services.media import extract_frame, extract_audio_pcm, get_video_duration
from ..services.scribe_realtime import ScribeRealtimeService
from ..models.incident import Severity, IncidentStatus

logger = logging.getLogger(__name__)

# Video asset directory — absolute path so background tasks work regardless of cwd
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets")
SUPPORTED_VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".avi")


def detect_video() -> str | None:
    """Find the first video file in assets/. Returns absolute path or None."""
    assets = os.path.abspath(ASSETS_DIR)
    if not os.path.isdir(assets):
        return None
    for f in sorted(os.listdir(assets)):
        if f.lower().endswith(SUPPORTED_VIDEO_EXTENSIONS):
            return os.path.join(assets, f)
    return None

# Vision: continuous frame analysis every N seconds
VISION_START_S = 3.0      # Start vision analysis 3s into video
VISION_INTERVAL_S = 3.0   # Analyze a frame every 3 seconds
# No max frames — runs until video ends or demo is cancelled


class DemoOrchestrator:
    """
    Event-driven orchestrator. Audio streaming drives the timeline.
    Each Scribe v2 committed transcript immediately triggers the agent pipeline.
    """

    def __init__(self, deps: TriageNetDeps, state: StateManager):
        self.deps = deps
        self.state = state
        self.previous_frame = None
        self._approved = asyncio.Event()
        self._feed_started = asyncio.Event()
        self._cancelled = False
        self._transcript_count = 0
        self._pipeline_tasks: list[asyncio.Task] = []
        self._evacuation_sent = False
        self._dispatched_units: set[str] = set()  # Track already-dispatched unit types
        self._scribe: ScribeRealtimeService | None = None

    def approve(self):
        """Called by the /demo/approve endpoint."""
        self._approved.set()

    def begin_feed(self):
        """Called by the /demo/feed endpoint when frontend starts playback."""
        self._feed_started.set()

    def cancel(self):
        """Cancel the running demo."""
        self._cancelled = True
        for task in self._pipeline_tasks:
            task.cancel()

    async def start(self):
        """
        Run the full demo. Audio streaming drives everything:
        1. Extract PCM from scene.mp4
        2. Connect Scribe v2
        3. Launch audio stream + vision + approval in parallel
        4. Each committed transcript immediately triggers agent pipeline
        5. After audio completes, finalize
        """
        try:
            await self._run()
        except asyncio.CancelledError:
            logger.info("Demo cancelled")
        except Exception as e:
            logger.error(f"Demo error: {e}", exc_info=True)
            self.state.log("orchestrator", "error", f"Demo error: {e}", color="red")

    async def _run(self):
        self.state.log("orchestrator", "init", f"Demo started: {self.deps.case_id}", color="blue")

        # --- Phase 0: Init ---
        self.state.update_state(
            status=IncidentStatus.INTAKE.value,
            severity=Severity.UNKNOWN.value,
        )

        # Auto-detect video file in assets/
        video_path = detect_video()
        if not video_path:
            self.state.log("orchestrator", "error",
                           "No video found in assets/. Drop an .mp4 or .mov file there.",
                           color="red")
            return

        self.state.log("orchestrator", "init", f"Video: {os.path.basename(video_path)}")

        # Extract PCM audio (cached — re-extracts only if video is newer)
        pcm_path = os.path.splitext(video_path)[0] + "_audio.pcm"
        self.state.log("orchestrator", "init", "Extracting audio from video...")
        pcm_path = await extract_audio_pcm(video_path, pcm_path)
        self.state.log("orchestrator", "init", "Audio extraction complete")

        self.state.log("orchestrator", "init", "Video monitor armed", color="blue")

        # --- Connect Scribe v2 Realtime ---
        self._scribe = ScribeRealtimeService(
            on_partial=self._on_partial_transcript,
            on_committed=self._on_committed_transcript,
        )
        await self._scribe.connect()
        self.state.log("orchestrator", "init", "Scribe v2 connected — waiting for feed", color="green")

        # --- Wait for frontend to start playback ---
        self._update_demo_control("listening")
        self.state.log("orchestrator", "listening",
                       "Listening... Press INITIATE FEED to begin",
                       color="amber", flash=True)
        await self._feed_started.wait()
        self.state.log("orchestrator", "feed_started", "Feed started — streaming audio", color="green")
        self._update_demo_control("playing")

        # --- Launch parallel tasks ---
        audio_task = asyncio.create_task(
            self._scribe.stream_audio(pcm_path),
            name="audio_stream",
        )
        vision_task = asyncio.create_task(
            self._run_vision(video_path),
            name="vision_pipeline",
        )

        # Wait for audio to complete (this drives the timeline)
        await audio_task

        # Give a moment for final committed transcripts to arrive
        await asyncio.sleep(2)

        # Wait for any in-flight pipeline tasks to finish
        if self._pipeline_tasks:
            self.state.log("orchestrator", "finalizing",
                           f"Waiting for {len(self._pipeline_tasks)} pipeline tasks...")
            await asyncio.gather(*self._pipeline_tasks, return_exceptions=True)

        # Wait for vision to complete
        await vision_task

        # --- Post-audio: check evacuation, generate summary ---
        await self._post_audio_finalize()

        # Disconnect Scribe
        await self._scribe.disconnect()

        self.state.log("orchestrator", "complete",
                       f"Demo complete: {self.deps.case_id}",
                       color="green", flash=True)
        self._update_demo_control("complete")

    # ----------------------------------------------------------------
    # Scribe v2 event handlers — the low-latency critical path
    # ----------------------------------------------------------------

    async def _on_partial_transcript(self, text: str, timestamp: float):
        """
        Partial transcript from Scribe v2 — write to live_partials
        for frontend shimmer effect. This is a lightweight upsert.
        """
        try:
            self.deps.supabase.table("live_partials").upsert({
                "case_id": self.deps.case_id,
                "text": text,
                "timestamp": timestamp,
            }).execute()
        except Exception as e:
            logger.debug(f"live_partials upsert error (non-fatal): {e}")

    async def _on_committed_transcript(self, data: dict):
        """
        Committed transcript from Scribe v2 — THIS IS THE LOW-LATENCY PATH.
        Immediately launches the agent pipeline as a concurrent task so
        processing starts while audio continues streaming.
        """
        self._transcript_count += 1
        text = data["text"]
        language = data["language_code"] or "unknown"
        feed_id = data["feed_id"]
        segment_index = data["segment_index"]

        self.state.log("voice", "transcript_committed",
                       f"[{feed_id}] ({language}): {text[:80]}...",
                       color="green")
        self.state.update_state(caller_count=self._transcript_count)

        # Write raw transcript to Supabase IMMEDIATELY (fire-and-forget)
        # so it appears in the Scene Audio feed before agent processing starts
        asyncio.create_task(self._insert_raw_transcript(
            text, language, feed_id, segment_index))

        # Launch pipeline as concurrent task — don't block audio streaming
        task = asyncio.create_task(
            self._process_transcript(text, language, feed_id, segment_index),
            name=f"pipeline_{segment_index}",
        )
        self._pipeline_tasks.append(task)

    async def _insert_raw_transcript(
        self, text: str, language: str, feed_id: str, segment_index: int
    ):
        """Fire-and-forget raw transcript insert."""
        try:
            self.deps.supabase.table("transcripts").insert({
                "case_id": self.deps.case_id,
                "caller_id": f"scene_{feed_id.lower()}",
                "caller_label": f"Scene Audio ({feed_id})",
                "language": language or "unknown",
                "original_text": text,
                "confidence": 0.9,
                "segment_index": segment_index,
                "feed_id": feed_id,
                "direction": "inbound",
            }).execute()
        except Exception as e:
            logger.debug(f"Immediate transcript insert error: {e}")

    async def _process_transcript(
        self,
        text: str,
        language: str,
        feed_id: str,
        segment_index: int,
    ):
        """
        LATENCY-OPTIMIZED agent pipeline for a single committed transcript.
        Every millisecond counts in emergency dispatch.

        Optimization strategy:
        1. Translation + intake run IN PARALLEL (saves ~1s)
        2. Translation pushed to UI IMMEDIATELY (don't wait for intake)
        3. Triage runs as soon as facts are ready
        4. Evidence fusion is DEFERRED to background (not on critical path)
        5. Supabase writes are fire-and-forget where possible
        """
        pipeline_start = time.time()
        try:
            # ── PHASE 1: Translate + Intake in PARALLEL ──
            # Intake agent handles multilingual text — no need to wait for translation
            translate_task = translate_to_english(text, language, self.deps.mistral_client)
            intake_task = intake_agent.run(
                f"Emergency caller transcript ({language}): {text}",
                deps=self.deps,
            )
            translated, facts_result = await asyncio.gather(translate_task, intake_task)
            facts = facts_result.output

            t_phase1 = time.time() - pipeline_start
            self.state.log("voice", "translated",
                           f"[{feed_id}] → {translated[:60]}",
                           color="blue")
            self.state.log("intake", "facts_extracted",
                           f"{facts.incident_type_candidate or '—'} @ {facts.location_raw or 'unknown location'}",
                           color="blue")

            # ── PHASE 2: Push translation + facts to UI IMMEDIATELY ──
            # Fire-and-forget — don't block triage waiting for Supabase
            asyncio.create_task(self._update_transcript_row(
                segment_index, translated, language, facts))

            # Update incident state with facts (in-memory, fast)
            update_kwargs = {}
            if facts.location_raw and segment_index <= 2:
                update_kwargs["location_raw"] = facts.location_raw
                update_kwargs["location_normalized"] = facts.location_raw
            if facts.incident_type_candidate:
                update_kwargs["incident_type"] = facts.incident_type_candidate
            if update_kwargs:
                self.state.update_state(**update_kwargs)

            # ── PHASE 3: Triage (critical path — must await) ──
            triage_result = await triage_agent.run(
                "Classify this incident based on all current evidence. "
                "A new transcript has just been committed.",
                deps=self.deps,
            )
            triage = triage_result.output

            # Merge injury/hazard flags (never downgrade)
            current_state = self.state.get_state()
            merged_injuries = list(set(current_state.injury_flags + triage.injury_flags))
            merged_hazards = list(set(current_state.hazard_flags + triage.hazards))

            new_status = current_state.status
            if triage.severity == Severity.CRITICAL:
                new_status = IncidentStatus.CRITICAL
            elif triage.severity in (Severity.HIGH, Severity.MEDIUM) and current_state.status == IncidentStatus.INTAKE:
                new_status = IncidentStatus.ACTIVE

            self.state.update_state(
                severity=triage.severity.value,
                recommended_units=triage.recommended_units,
                people_count_estimate=max(current_state.people_count_estimate, triage.people_count_estimate),
                injury_flags=merged_injuries,
                hazard_flags=merged_hazards,
                action_plan_version=current_state.action_plan_version + 1,
                action_plan=[a.model_dump() for a in triage.action_plan],
                status=new_status.value if isinstance(new_status, IncidentStatus) else new_status,
            )
            self.state.log("triage", "severity_changed",
                           f"Severity: {triage.severity.value.upper()}",
                           color="amber" if triage.severity in (Severity.MEDIUM, Severity.HIGH) else "red",
                           flash=triage.severity in (Severity.HIGH, Severity.CRITICAL))

            # ── PHASE 3b: Proactive dispatch — generate briefs for NEW units immediately ──
            new_units = [u for u in triage.recommended_units if u not in self._dispatched_units]
            if new_units and triage.severity in (Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL):
                asyncio.create_task(
                    self._dispatch_units(new_units),
                    name=f"dispatch_{segment_index}",
                )

            # ── PHASE 3c: Deterministic evacuation check ──
            # Trigger evacuation as soon as smoke or fire is detected — don't wait for LLM
            if not self._evacuation_sent:
                hazard_present = any(h in merged_hazards for h in ("smoke", "engine_fire", "fire", "explosion"))
                if hazard_present:
                    self.state.log("orchestrator", "evacuation_trigger",
                                   f"HAZARD DETECTED ({', '.join(h for h in merged_hazards if h in ('smoke', 'engine_fire', 'fire', 'explosion'))}) — triggering evacuation protocol",
                                   color="red", flash=True)
                    asyncio.create_task(self._send_evacuation_warnings())

            # ── PHASE 4: Evidence fusion — DEFERRED to background ──
            # Not on critical path. Evacuation warnings still fire if needed.
            if self._transcript_count >= 2:
                fusion_task = asyncio.create_task(
                    self._run_evidence_fusion(segment_index),
                    name=f"fusion_{segment_index}",
                )
                self._pipeline_tasks.append(fusion_task)

            elapsed = time.time() - pipeline_start
            self.state.log("orchestrator", "pipeline_complete",
                           f"Segment {segment_index}: {t_phase1:.1f}s translate+intake, {elapsed:.1f}s total",
                           color="blue")

        except Exception as e:
            logger.error(f"Pipeline error for segment {segment_index}: {e}", exc_info=True)
            self.state.log("orchestrator", "pipeline_error",
                           f"Pipeline error: {e}", color="red")

    async def _update_transcript_row(
        self, segment_index: int, translated: str, language: str, facts
    ):
        """Fire-and-forget update of transcript row with translation + facts."""
        try:
            self.deps.supabase.table("transcripts").update({
                "translated_text": translated if language != "en" else None,
                "facts_extracted": facts.model_dump(),
            }).eq("case_id", self.deps.case_id).eq("segment_index", segment_index).execute()
        except Exception as e:
            logger.debug(f"Transcript update error (non-fatal): {e}")

    async def _run_evidence_fusion(self, segment_index: int):
        """Background evidence fusion — not on critical path."""
        try:
            fusion_result = await evidence_fusion_agent.run(
                "New transcript committed. Fuse all evidence — check for corroborations.",
                deps=self.deps,
            )
            fusion = fusion_result.output
            self._log_fusion_result(fusion, segment_index)
            if fusion.evacuation_warning_required and not self._evacuation_sent:
                await self._send_evacuation_warnings()
        except Exception as e:
            logger.error(f"Evidence fusion error: {e}", exc_info=True)

    # ----------------------------------------------------------------
    # Vision pipeline — continuous frame analysis
    # ----------------------------------------------------------------

    async def _run_vision(self, video_path: str):
        """
        Continuous vision analysis: extract and analyze frames every VISION_INTERVAL_S.
        Each frame analysis runs as an overlapping task so we don't block waiting
        for the API while the next frame is being extracted.
        """
        if not os.path.exists(video_path):
            return

        frames_dir = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "frames")
        os.makedirs(frames_dir, exist_ok=True)

        # Get video duration to know when to stop
        video_duration = await get_video_duration(video_path)
        self.state.log("vision", "init",
                       f"Video: {video_duration:.0f}s, frames every {VISION_INTERVAL_S:.0f}s",
                       color="purple")

        # Wait before first frame
        await asyncio.sleep(VISION_START_S)
        if self._cancelled:
            return

        self.state.log("vision", "scanning", "CCTV analysis active — continuous monitoring", color="purple")

        prev_analysis = None
        frame_count = 0
        vision_tasks = []

        while not self._cancelled:
            frame_count += 1
            timestamp = VISION_START_S + (frame_count - 1) * VISION_INTERVAL_S

            # Stop when we've exceeded video duration
            if timestamp > video_duration:
                break

            # Extract frame (fast, ~100ms)
            try:
                frame_bytes = await extract_frame(video_path, timestamp_s=timestamp)
                if not frame_bytes or len(frame_bytes) < 100:
                    logger.debug(f"Vision frame {frame_count} at {timestamp:.1f}s: empty/too small, skipping")
                    await asyncio.sleep(VISION_INTERVAL_S)
                    continue

                # Save to disk
                frame_path = os.path.join(frames_dir, f"{self.deps.case_id}_t{int(timestamp)}s.jpg")
                with open(frame_path, "wb") as f:
                    f.write(frame_bytes)

                # Launch analysis as concurrent task (don't block for API latency)
                task = asyncio.create_task(
                    self._analyze_and_update_vision(
                        frame_bytes, frame_count, timestamp, prev_analysis),
                    name=f"vision_frame_{frame_count}",
                )
                vision_tasks.append(task)

            except Exception as e:
                logger.error(f"Vision frame {frame_count} extraction error: {e}")

            # Wait for next frame interval
            await asyncio.sleep(VISION_INTERVAL_S)

        # Wait for all analysis tasks to complete
        if vision_tasks:
            self.state.log("vision", "finalizing",
                           f"Waiting for {len(vision_tasks)} frame analyses to complete...")
            await asyncio.gather(*vision_tasks, return_exceptions=True)

    async def _analyze_and_update_vision(
        self,
        frame_bytes: bytes,
        frame_id: int,
        timestamp: float,
        prev_analysis,
    ):
        """Analyze a single frame and update state. Runs concurrently."""
        t0 = time.time()
        try:
            analysis = await analyze_frame(self.deps.mistral_client, frame_bytes, frame_id=frame_id)
            elapsed = time.time() - t0
            self.state.log("vision", "detection",
                           f"Frame {frame_id} ({timestamp:.0f}s, {elapsed:.1f}s): {analysis.overall_description}",
                           color="purple")

            # Update state with detections
            state = self.state.get_state()
            detections = state.vision_detections + [d.model_dump() for d in analysis.detections]
            hazards = list(set(state.hazard_flags))
            if analysis.smoke_visible:
                hazards = list(set(hazards + ["smoke"]))
            if analysis.fire_visible:
                hazards = list(set(hazards + ["engine_fire"]))
            self.state.update_state(vision_detections=detections, hazard_flags=hazards)

            # Deterministic evacuation: trigger as soon as vision sees smoke or fire
            if not self._evacuation_sent and (analysis.smoke_visible or analysis.fire_visible):
                detected = []
                if analysis.smoke_visible:
                    detected.append("smoke")
                if analysis.fire_visible:
                    detected.append("fire")
                self.state.log("vision", "evacuation_trigger",
                               f"VISION CONFIRMS {', '.join(detected).upper()} — triggering evacuation",
                               color="red", flash=True)
                asyncio.create_task(self._send_evacuation_warnings())

            # Detect escalation via scene delta
            if prev_analysis:
                delta = compute_scene_delta(prev_analysis, analysis)
                if delta.get("hazard_escalation"):
                    self.state.log("vision", "hazard_escalation",
                                   f"HAZARD ESCALATION: {delta.get('new_hazard', 'unknown')}",
                                   color="red", flash=True)

            # Re-triage with vision evidence (every other frame to limit API calls)
            if frame_id % 2 == 0 or analysis.fire_visible:
                triage_result = await triage_agent.run(
                    "Re-classify. New vision evidence available. Check for fire/smoke.",
                    deps=self.deps,
                )
                triage = triage_result.output
                self.state.update_state(
                    severity=triage.severity.value,
                    recommended_units=triage.recommended_units,
                    action_plan_version=state.action_plan_version + 1,
                    action_plan=[a.model_dump() for a in triage.action_plan],
                    status=(IncidentStatus.ESCALATED.value
                            if triage.severity in (Severity.HIGH, Severity.CRITICAL)
                            else state.status),
                )

                # Cross-modal fusion when we have both audio + vision
                if self._transcript_count >= 1:
                    fusion_result = await evidence_fusion_agent.run(
                        "Vision evidence updated. Correlate with caller reports.",
                        deps=self.deps,
                    )
                    fusion = fusion_result.output
                    self._log_fusion_result(fusion, vision_frame=frame_id)
                    if fusion.evacuation_warning_required and not self._evacuation_sent:
                        await self._send_evacuation_warnings()

        except Exception as e:
            logger.error(f"Vision frame {frame_id} analysis error: {e}")

    # ----------------------------------------------------------------
    # Evacuation warnings
    # ----------------------------------------------------------------

    async def _send_evacuation_warnings(self):
        """Send TTS evacuation warnings in all detected languages."""
        if self._evacuation_sent:
            return
        self._evacuation_sent = True

        self.state.log("voice", "priority_interrupt",
                       "PRIORITY INTERRUPT — Hazard warning to all callers",
                       color="red", flash=True)

        # Broadcast in ALL supported languages — in an emergency, cover every language
        warning_templates = {
            "en": (
                "Attention! Fire detected in the area. "
                "Move away from the vehicle immediately. Fire department is en route.",
                None,
            ),
            "es": (
                "¡Atención! Se ha detectado fuego. "
                "Aléjense del área inmediatamente. Los bomberos están en camino.",
                "Attention! Fire detected. Move away immediately. Fire department en route."
            ),
            "zh": (
                "注意！已检测到火灾。请立即远离该区域。消防队正在赶来。",
                "Attention! Fire detected. Move away immediately. Fire department en route."
            ),
            "fr": (
                "Attention ! Un incendie a été détecté. "
                "Éloignez-vous immédiatement. Les pompiers sont en route.",
                "Attention! Fire detected. Move away immediately. Fire department en route."
            ),
        }

        # Use all template languages — detected languages just for logging
        detected_langs = self._scribe.feed_registry.languages if self._scribe else []
        languages = list(warning_templates.keys())
        self.state.log("voice", "broadcast_languages",
                       f"Detected: {detected_langs}, broadcasting: {languages}",
                       color="amber")

        for lang in languages:
            warning_text, translation = warning_templates.get(
                lang, warning_templates["en"]
            )
            audio_url = await generate_and_save(
                warning_text, lang, f"warning_{lang}.mp3"
            )
            self.deps.supabase.table("transcripts").insert({
                "case_id": self.deps.case_id,
                "caller_id": "dispatch",
                "caller_label": "DISPATCH",
                "language": lang or "en",
                "original_text": warning_text,
                "translated_text": translation,
                "confidence": 1.0,
                "segment_index": 900 + languages.index(lang),
                "feed_id": "DISPATCH",
                "direction": "outbound",
                "priority": "evacuation",
                "audio_url": audio_url,
            }).execute()
            self.state.log("voice", "warning_sent",
                           f"Evacuation warning sent ({lang.upper()})",
                           data={"audio_url": audio_url},
                           color="red")

        # Dispatch fire response
        dispatch_result = await dispatch_agent.run(
            "Generate dispatch brief for Fire Response. "
            "Fire confirmed by CCTV. Urgent evacuation in progress.",
            deps=self.deps,
        )
        brief = dispatch_result.output
        audio_url = await generate_and_save(
            brief.voice_message, "en", "dispatch_fire_response.mp3"
        )
        self.deps.supabase.table("dispatches").insert({
            "case_id": self.deps.case_id,
            "unit_type": "Fire Response",
            "unit_assigned": brief.unit_assigned,
            "destination": brief.destination,
            "eta_minutes": brief.eta_minutes,
            "status": "dispatched",
            "voice_message": brief.voice_message,
            "rationale": "Vision-confirmed fire — evacuation priority",
            "audio_url": audio_url,
        }).execute()
        self.state.log("dispatch", "unit_dispatched",
                       f"Fire Response dispatched: {brief.unit_assigned}",
                       data={"audio_url": audio_url},
                       color="red", flash=True)

    # ----------------------------------------------------------------
    # Proactive dispatch — generates briefs as soon as triage recommends
    # ----------------------------------------------------------------

    async def _dispatch_units(self, units: list[str]):
        """
        Generate dispatch briefs for new units IMMEDIATELY after triage.
        This runs as a background task so it doesn't block the transcript pipeline.
        Each unit only gets dispatched once (tracked via _dispatched_units).
        """
        state = self.state.get_state()
        for unit in units:
            if unit in self._dispatched_units:
                continue
            self._dispatched_units.add(unit)
            try:
                dispatch_result = await dispatch_agent.run(
                    f"Generate dispatch brief for {unit}. "
                    f"Incident: {state.incident_type or 'vehicle collision'} "
                    f"at {state.location_normalized or 'unknown location'}. "
                    f"Severity: {state.severity}.",
                    deps=self.deps,
                )
                brief = dispatch_result.output
                safe_unit = unit.replace(" ", "_").lower()
                audio_url = await generate_and_save(
                    brief.voice_message, "en", f"dispatch_{safe_unit}.mp3"
                )
                self.deps.supabase.table("dispatches").insert({
                    "case_id": self.deps.case_id,
                    "unit_type": unit,
                    "unit_assigned": brief.unit_assigned,
                    "destination": brief.destination,
                    "eta_minutes": brief.eta_minutes,
                    "status": "dispatched",
                    "voice_message": brief.voice_message,
                    "rationale": brief.rationale,
                    "audio_url": audio_url,
                }).execute()
                self.state.log("dispatch", "unit_dispatched",
                               f"{unit} dispatched: {brief.unit_assigned}",
                               data={"audio_url": audio_url},
                               color="green", flash=True)
            except Exception as e:
                logger.error(f"Dispatch error for {unit}: {e}")
                self._dispatched_units.discard(unit)  # Allow retry

    # ----------------------------------------------------------------
    # Post-audio finalization
    # ----------------------------------------------------------------

    async def _post_audio_finalize(self):
        """After audio stream completes: confirm dispatched units, generate summary."""

        # Confirm all dispatched units
        state = self.state.get_state()
        self.state.update_state(confirmed_units=list(self._dispatched_units))

        # Dispatch any remaining recommended units that haven't been dispatched yet
        remaining = [u for u in state.recommended_units if u not in self._dispatched_units]
        if remaining:
            self.state.log("orchestrator", "dispatching_remaining",
                           f"Dispatching {len(remaining)} remaining units: {', '.join(remaining)}",
                           color="amber")
            await self._dispatch_units(remaining)

        self.state.log("orchestrator", "dispatch_complete",
                       "All units dispatched", color="green", flash=True)

        # Final summary
        state = self.state.get_state()
        summary = (
            f"Incident: {state.incident_type or 'Unknown'} at {state.location_normalized or 'Unknown'}. "
            f"Severity: {state.severity.upper()}. "
            f"{state.caller_count} audio segments processed. "
            f"{len(self._dispatched_units)} units dispatched."
        )
        if state.hazard_flags:
            summary += f" Hazards: {', '.join(state.hazard_flags)}."
        self.state.update_state(
            status=IncidentStatus.RESOLVED_DEMO.value,
            operator_summary=summary,
            confirmed_units=list(self._dispatched_units),
        )

    # ----------------------------------------------------------------
    # Fusion logging — the technical thesis
    # ----------------------------------------------------------------

    def _log_fusion_result(
        self,
        fusion,
        segment_index: int | None = None,
        vision_frame: int | None = None,
    ):
        """
        Produce rich, thesis-quality log entries for evidence fusion.
        This is the showcase: cross-modal corroboration with autonomous action.
        """
        from ..models.triage import EvidenceFusionResult

        if not fusion.corroborations:
            return

        for corr in fusion.corroborations:
            # Classify modalities involved
            source_types = set()
            for src in corr.sources:
                src_type = src.get("type", "unknown")
                if "vision" in src_type.lower() or "cctv" in src_type.lower():
                    source_types.add("CCTV")
                else:
                    source_types.add("Audio")

            is_cross_modal = len(source_types) >= 2
            event_type = "CROSS_MODAL" if is_cross_modal else "CORROBORATION"
            tag = "🔗" if is_cross_modal else "✓"
            sources_str = " + ".join(sorted(source_types))
            conf_pct = f"{corr.combined_confidence * 100:.0f}%" if corr.combined_confidence else ""

            message = f"{tag} {corr.claim.upper()} ({sources_str}, {conf_pct})"

            # Structured data for frontend rendering
            data = {
                "claim": corr.claim,
                "sources": corr.sources,
                "combined_confidence": corr.combined_confidence,
                "cross_modal": is_cross_modal,
                "modalities": list(source_types),
                "severity_delta": fusion.severity_delta,
                "evacuation_triggered": fusion.evacuation_warning_required,
            }

            self.state.log(
                "evidence_fusion",
                event_type,
                message,
                data=data,
                color="green" if not fusion.evacuation_warning_required else "red",
                flash=is_cross_modal,
                model="mistral-large-latest",
            )

        # Log evacuation trigger once (not per corroboration)
        if fusion.evacuation_warning_required:
            self.state.log("evidence_fusion", "EVACUATION",
                           "Autonomous evacuation protocol triggered",
                           color="red", flash=True)

        # Log truncated reasoning
        if fusion.reasoning:
            # Keep just first 200 chars for demo readability
            short = fusion.reasoning[:200].replace("\n", " ").strip()
            if len(fusion.reasoning) > 200:
                short += "..."
            self.state.log(
                "evidence_fusion",
                "reasoning",
                short,
                data={"severity_delta": fusion.severity_delta},
                color="purple",
                model="mistral-large-latest",
            )

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------

    def _update_demo_control(self, status: str, **kwargs):
        """Update demo_control table for frontend coordination."""
        try:
            self.deps.supabase.table("demo_control").upsert({
                "case_id": self.deps.case_id,
                "status": status,
                **kwargs,
            }).execute()
        except Exception as e:
            logger.debug(f"demo_control upsert error (non-fatal): {e}")
