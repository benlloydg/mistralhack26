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
from ..services.media import extract_frame, extract_audio_pcm
from ..services.scribe_realtime import ScribeRealtimeService
from ..models.incident import Severity, IncidentStatus

logger = logging.getLogger(__name__)

# Video asset paths
SCENE_VIDEO = "assets/scene.mp4"
SCENE_PCM = "assets/scene_audio.pcm"

# Vision timestamps (seconds into video)
VISION_FRAME_1_S = 25.0
VISION_FRAME_2_S = 38.0


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
        self._cancelled = False
        self._transcript_count = 0
        self._pipeline_tasks: list[asyncio.Task] = []
        self._evacuation_sent = False
        self._scribe: ScribeRealtimeService | None = None

    def approve(self):
        """Called by the /demo/approve endpoint."""
        self._approved.set()

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

        # Update demo_control → "playing"
        self._update_demo_control("playing")

        # Extract PCM audio from video (cached if already exists)
        video_path = SCENE_VIDEO
        pcm_path = SCENE_PCM
        if os.path.exists(video_path):
            self.state.log("orchestrator", "init", "Extracting audio from scene video...")
            pcm_path = await extract_audio_pcm(video_path, pcm_path)
            self.state.log("orchestrator", "init", "Audio extraction complete")
        else:
            self.state.log("orchestrator", "init",
                           f"Video not found: {video_path}. Using fallback if available.",
                           color="amber")
            # Try crash_video.mp4 as fallback
            fallback = "assets/crash_video.mp4"
            if os.path.exists(fallback):
                video_path = fallback
                pcm_path = "assets/crash_audio.pcm"
                pcm_path = await extract_audio_pcm(video_path, pcm_path)

        if not os.path.exists(pcm_path):
            self.state.log("orchestrator", "error", "No audio available. Cannot proceed.", color="red")
            return

        self.state.log("orchestrator", "init", "Video monitor armed", color="blue")

        # --- Connect Scribe v2 Realtime ---
        self._scribe = ScribeRealtimeService(
            on_partial=self._on_partial_transcript,
            on_committed=self._on_committed_transcript,
        )
        await self._scribe.connect()
        self.state.log("orchestrator", "init", "Scribe v2 Realtime connected", color="green")

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
        language = data["language_code"]
        feed_id = data["feed_id"]
        segment_index = data["segment_index"]

        self.state.log("voice", "transcript_committed",
                       f"[{feed_id}] Committed ({language}): {text[:80]}...",
                       color="green")
        self.state.update_state(caller_count=self._transcript_count)

        # Launch pipeline as concurrent task — don't block audio streaming
        task = asyncio.create_task(
            self._process_transcript(text, language, feed_id, segment_index),
            name=f"pipeline_{segment_index}",
        )
        self._pipeline_tasks.append(task)

    async def _process_transcript(
        self,
        text: str,
        language: str,
        feed_id: str,
        segment_index: int,
    ):
        """
        Full agent pipeline for a single committed transcript.
        Runs as fast as possible for minimal latency:
        1. Translate to English (if needed)
        2. Extract intake facts
        3. Write transcript + facts to Supabase
        4. Run triage (updates severity, recommended units)
        5. Evidence fusion (if 2+ transcripts)
        6. Check evacuation conditions
        """
        pipeline_start = time.time()
        try:
            # 1. Translate to English
            translated = await translate_to_english(text, language, self.deps.mistral_client)
            self.state.log("voice", "translated",
                           f"[{feed_id}] EN: {translated[:80]}...",
                           color="blue")

            # 2. Extract intake facts
            facts_result = await intake_agent.run(
                f"Transcript from emergency caller ({language}): {translated}",
                deps=self.deps,
            )
            facts = facts_result.output
            self.state.log("intake", "facts_extracted",
                           f"Location: {facts.location_raw}, Type: {facts.incident_type_candidate}",
                           color="blue")

            # 3. Write transcript to Supabase (with facts)
            self.deps.supabase.table("transcripts").insert({
                "case_id": self.deps.case_id,
                "caller_id": f"scene_{feed_id.lower()}",
                "caller_label": f"Scene Audio ({feed_id})",
                "language": language,
                "original_text": text,
                "translated_text": translated if language != "en" else None,
                "confidence": 0.9,
                "segment_index": segment_index,
                "feed_id": feed_id,
                "direction": "inbound",
                "facts_extracted": facts.model_dump(),
            }).execute()

            # 4. Update incident state with facts
            update_kwargs = {}
            if facts.location_raw and segment_index <= 2:
                update_kwargs["location_raw"] = facts.location_raw
                update_kwargs["location_normalized"] = facts.location_raw
            if facts.incident_type_candidate:
                update_kwargs["incident_type"] = facts.incident_type_candidate
            if update_kwargs:
                self.state.update_state(**update_kwargs)

            # 5. Run triage
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

            # 6. Evidence fusion if 2+ transcripts
            if self._transcript_count >= 2:
                fusion_result = await evidence_fusion_agent.run(
                    "New transcript committed. Fuse all evidence — check for corroborations.",
                    deps=self.deps,
                )
                fusion = fusion_result.output
                self._log_fusion_result(fusion, segment_index)
                if fusion.evacuation_warning_required and not self._evacuation_sent:
                    await self._send_evacuation_warnings()

            elapsed = time.time() - pipeline_start
            self.state.log("orchestrator", "pipeline_complete",
                           f"Pipeline for segment {segment_index} complete ({elapsed:.1f}s)",
                           color="blue")

        except Exception as e:
            logger.error(f"Pipeline error for segment {segment_index}: {e}", exc_info=True)
            self.state.log("orchestrator", "pipeline_error",
                           f"Pipeline error: {e}", color="red")

    # ----------------------------------------------------------------
    # Vision pipeline — runs independently from audio
    # ----------------------------------------------------------------

    async def _run_vision(self, video_path: str):
        """
        Run vision analysis on video frames at predetermined timestamps.
        Runs in parallel with audio streaming.
        """
        if not os.path.exists(video_path):
            return

        # Wait a bit so we have some transcript context first
        await asyncio.sleep(VISION_FRAME_1_S)
        if self._cancelled:
            return

        self.state.log("vision", "scanning", "CCTV analysis active", color="purple")

        # Frame 1
        try:
            frame_bytes_1 = await extract_frame(video_path, timestamp_s=VISION_FRAME_1_S)
            analysis_1 = await analyze_frame(self.deps.mistral_client, frame_bytes_1, frame_id=1)
            self.state.log("vision", "detection",
                           f"Frame 1 analysis: {analysis_1.overall_description}",
                           color="purple")

            # Update state with vision detections
            state = self.state.get_state()
            detections = state.vision_detections + [d.model_dump() for d in analysis_1.detections]
            hazards = list(set(state.hazard_flags))
            if analysis_1.smoke_visible:
                hazards = list(set(hazards + ["smoke"]))
            self.state.update_state(vision_detections=detections, hazard_flags=hazards)
        except Exception as e:
            logger.error(f"Vision frame 1 error: {e}")
            analysis_1 = None

        # Wait for Frame 2 timestamp
        await asyncio.sleep(VISION_FRAME_2_S - VISION_FRAME_1_S)
        if self._cancelled:
            return

        # Frame 2
        try:
            frame_bytes_2 = await extract_frame(video_path, timestamp_s=VISION_FRAME_2_S)
            analysis_2 = await analyze_frame(self.deps.mistral_client, frame_bytes_2, frame_id=2)
            delta = compute_scene_delta(analysis_1, analysis_2)

            if delta.get("hazard_escalation"):
                self.state.log("vision", "hazard_escalation",
                               f"HAZARD ESCALATION: {delta.get('new_hazard', 'unknown')}",
                               color="red", flash=True)

            state = self.state.get_state()
            detections = state.vision_detections + [d.model_dump() for d in analysis_2.detections]
            hazards = list(set(state.hazard_flags))
            if analysis_2.fire_visible:
                hazards = list(set(hazards + ["engine_fire"]))
            if analysis_2.smoke_visible:
                hazards = list(set(hazards + ["smoke"]))
            self.state.update_state(vision_detections=detections, hazard_flags=hazards)

            # Re-triage with vision evidence
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

            # Evidence fusion with vision — cross-modal corroboration
            if self._transcript_count >= 1:
                fusion_result = await evidence_fusion_agent.run(
                    "Vision evidence updated. Fire/smoke detected by CCTV. "
                    "Correlate with caller reports.",
                    deps=self.deps,
                )
                fusion = fusion_result.output
                self._log_fusion_result(fusion, vision_frame=2)
                if fusion.evacuation_warning_required and not self._evacuation_sent:
                    await self._send_evacuation_warnings()

        except Exception as e:
            logger.error(f"Vision frame 2 error: {e}")

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

        languages = self._scribe.feed_registry.languages if self._scribe else []
        if not languages:
            languages = ["en"]

        warning_templates = {
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
            "en": (
                "Attention! Fire detected in the area. "
                "Move away from the vehicle immediately. Fire department is en route.",
                None,
            ),
        }

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
                "language": lang,
                "original_text": warning_text,
                "translated_text": translation,
                "confidence": 1.0,
                "segment_index": 900 + languages.index(lang),
                "feed_id": f"DISPATCH",
                "direction": "outbound",
                "priority": "evacuation",
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
    # Post-audio finalization
    # ----------------------------------------------------------------

    async def _post_audio_finalize(self):
        """After audio stream completes: approval, dispatch, summary."""

        # Enable approve button
        self._update_demo_control("awaiting_approval", approve_enabled=True)
        self.state.log("orchestrator", "awaiting_approval",
                       "Awaiting operator approval for dispatch...",
                       color="amber", flash=True)

        # Wait for approval (or timeout)
        try:
            await asyncio.wait_for(self._approved.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            self.state.log("orchestrator", "auto_approved",
                           "Auto-approved (timeout)", color="amber")

        self._update_demo_control("approved", approve_clicked=True)

        # Confirm recommended units
        state = self.state.get_state()
        self.state.update_state(confirmed_units=state.recommended_units)
        self.state.log("orchestrator", "approved",
                       "Operator confirmed dispatch", color="green", flash=True)

        # Generate dispatch briefs for confirmed units
        for unit in state.recommended_units:
            try:
                dispatch_result = await dispatch_agent.run(
                    f"Generate dispatch brief for {unit}. "
                    f"Incident: {state.incident_type} at {state.location_normalized}.",
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
                    "status": "confirmed",
                    "voice_message": brief.voice_message,
                    "rationale": brief.rationale,
                    "audio_url": audio_url,
                }).execute()
                self.state.log("dispatch", "unit_dispatched",
                               f"{unit} dispatched: {brief.unit_assigned}",
                               data={"audio_url": audio_url},
                               color="green")
            except Exception as e:
                logger.error(f"Dispatch error for {unit}: {e}")

        # Final summary
        state = self.state.get_state()
        summary = (
            f"Incident: {state.incident_type or 'Unknown'} at {state.location_normalized or 'Unknown'}. "
            f"Severity: {state.severity.upper()}. "
            f"{state.caller_count} audio segments processed. "
            f"{len(state.confirmed_units)} units confirmed, "
            f"{len(state.recommended_units)} total recommended."
        )
        if state.hazard_flags:
            summary += f" Hazards: {', '.join(state.hazard_flags)}."
        self.state.update_state(
            status=IncidentStatus.RESOLVED_DEMO.value,
            operator_summary=summary,
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
            source_lines = []
            for src in corr.sources:
                src_type = src.get("type", "unknown")
                conf = src.get("confidence", 0.0)
                if "vision" in src_type.lower() or "cctv" in src_type.lower():
                    source_types.add("vision")
                    # Include frame timestamp if available
                    frame_t = f"T+{VISION_FRAME_2_S:.0f}s" if vision_frame else ""
                    source_lines.append(
                        f"Vision: {corr.claim.upper()} ({conf:.2f})"
                        + (f" at frame {frame_t}" if frame_t else "")
                    )
                else:
                    source_types.add("audio")
                    lang = src.get("language", src_type)
                    source_lines.append(
                        f"Audio: {lang.upper()} speaker reported {corr.claim.lower()} ({conf:.2f})"
                    )

            is_cross_modal = len(source_types) >= 2
            n_modalities = len(source_types)
            event_type = "CROSS_MODAL_CORROBORATION" if is_cross_modal else "CORROBORATION"

            # Build the rich message
            lines = [
                f"{corr.claim.upper()} confirmed by {n_modalities} independent "
                f"{'modalities' if is_cross_modal else 'sources'}:",
            ]
            for sl in source_lines:
                lines.append(f"  → {sl}")

            # Note autonomous action if evacuation triggered
            if fusion.evacuation_warning_required:
                lines.append("Autonomous evacuation protocol triggered.")

            message = "\n".join(lines)

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
                flash=True,
                model="mistral-large-latest",
            )

        # Log the fusion reasoning
        if fusion.reasoning:
            self.state.log(
                "evidence_fusion",
                "reasoning",
                fusion.reasoning,
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
