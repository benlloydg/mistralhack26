"""
ReportBuilder — assembles all 8 sections of the after-action report from Supabase data.

Reads from 4 existing tables (incident_state, agent_logs, transcripts, dispatches),
transforms data into the pre-structured ReportData JSON, and generates an executive
summary via Mistral (cached in-memory).
"""
from __future__ import annotations

import glob
import logging
import os
from datetime import datetime, timezone

from mistralai import Mistral
from supabase import Client as SupabaseClient

from ..models.report import (
    AgentStats,
    AgentUtilization,
    AudioSummary,
    ConvergenceTrack,
    CrossModalSummary,
    EvidenceSources,
    KeyFrame,
    ModelUsage,
    ReportData,
    ReportHeader,
    ResponseAction,
    SpeakerSummary,
    TimelineEntry,
    TrackEvent,
    VisionDetectionEntry,
    VisionSummary,
)

logger = logging.getLogger(__name__)

# Agent → color mapping for timeline
AGENT_COLORS = {
    "orchestrator": "blue",
    "voice": "green",
    "intake": "blue",
    "triage": "amber",
    "evidence_fusion": "red",
    "dispatch": "purple",
    "vision": "purple",
}

# Language → track color for convergence
LANGUAGE_COLORS = {
    "es": "#F59E0B",
    "zh": "#10B981",
    "fr": "#8B5CF6",
    "en": "#3B82F6",
}

# Known models used in the system
KNOWN_MODELS = [
    ModelUsage(model="Mistral Large", roles=["Triage", "Intake", "Fusion", "Dispatch"]),
    ModelUsage(model="Pixtral Large", roles=["Scene analysis", "Hazard detection"]),
    ModelUsage(model="ElevenLabs Scribe v2", roles=["Real-time multilingual transcription"]),
    ModelUsage(model="ElevenLabs TTS", roles=["Multilingual voice response"]),
]


class ReportBuilder:
    """Assembles a complete ReportData from Supabase tables."""

    # Class-level cache: case_id → executive summary text
    _summary_cache: dict[str, str] = {}
    # Class-level cache: case_id → full ReportData
    _report_cache: dict[str, ReportData] = {}

    def __init__(self, supabase: SupabaseClient, mistral_client: Mistral):
        self.sb = supabase
        self.mistral = mistral_client

    async def build(self, case_id: str) -> ReportData:
        """Build the complete report for a case. Caches the result."""
        # Fetch all data in batch
        try:
            state_result = self.sb.table("incident_state") \
                .select("*").eq("case_id", case_id).single().execute()
        except Exception:
            return None  # Case not found

        state = state_result.data
        logs = self.sb.table("agent_logs") \
            .select("*").eq("case_id", case_id).order("created_at").execute().data
        transcripts = self.sb.table("transcripts") \
            .select("*").eq("case_id", case_id).order("created_at").execute().data
        dispatches = self.sb.table("dispatches") \
            .select("*").eq("case_id", case_id).order("created_at").execute().data

        # Check if demo is still in progress
        warning = None
        if state.get("status") != "resolved_demo":
            warning = "Demo is still in progress. Report may be incomplete."

        # Build all 8 sections
        header = self._build_header(case_id, state, transcripts, logs)
        timeline = self._build_timeline(logs, state)
        evidence_sources = self._build_evidence_sources(transcripts, state, logs)
        convergence_tracks = self._build_convergence_tracks(logs, transcripts, state)
        response_actions = self._build_response_actions(dispatches, logs, state)
        agent_stats = self._build_agent_stats(logs, state)
        key_frames = self._build_key_frames(case_id, state)
        executive_summary = await self._generate_executive_summary(
            case_id, state, transcripts, dispatches
        )

        report = ReportData(
            case_id=case_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            warning=warning,
            header=header,
            timeline=timeline,
            evidence_sources=evidence_sources,
            convergence_tracks=convergence_tracks,
            response_actions=response_actions,
            agent_stats=agent_stats,
            key_frames=key_frames,
            executive_summary=executive_summary,
        )

        # Cache the full report
        ReportBuilder._report_cache[case_id] = report
        return report

    @classmethod
    def get_cached(cls, case_id: str) -> ReportData | None:
        """Return cached report if available."""
        return cls._report_cache.get(case_id)

    # ----------------------------------------------------------------
    # Section builders
    # ----------------------------------------------------------------

    def _build_header(
        self, case_id: str, state: dict, transcripts: list, logs: list
    ) -> ReportHeader:
        # Count unique languages from transcripts (exclude dispatch)
        inbound = [t for t in transcripts if t.get("direction") != "outbound"]
        languages = sorted(set(t.get("language", "en") for t in inbound)) if inbound else []
        # Count unique feed_ids as speakers
        feed_ids = set(t.get("feed_id") for t in inbound if t.get("feed_id"))

        # Compute duration from first/last log timestamps
        duration = 0.0
        if logs:
            try:
                first = datetime.fromisoformat(logs[0]["created_at"].replace("Z", "+00:00"))
                last = datetime.fromisoformat(logs[-1]["created_at"].replace("Z", "+00:00"))
                duration = (last - first).total_seconds()
            except Exception:
                pass

        # Count vision frames from detections
        vision_frames = len(state.get("vision_detections", []))

        # Build outcome text
        outcome = state.get("operator_summary", "")
        if not outcome:
            outcome = f"Case {state.get('status', 'unknown').upper()}"

        return ReportHeader(
            case_id=case_id,
            incident_type=state.get("incident_type"),
            location=state.get("location_normalized") or state.get("location_raw"),
            severity=state.get("severity", "unknown"),
            status=state.get("status", "intake"),
            duration_seconds=duration,
            speaker_count=len(feed_ids),
            languages=languages,
            audio_segments=len(inbound),
            vision_frames=vision_frames,
            outcome=outcome,
        )

    def _build_timeline(self, logs: list, state: dict) -> list[TimelineEntry]:
        if not logs:
            return []

        # Reference time = first log
        try:
            ref_time = datetime.fromisoformat(logs[0]["created_at"].replace("Z", "+00:00"))
        except Exception:
            ref_time = None

        entries = []
        for log in logs:
            agent = log.get("agent", "unknown")
            event_type = log.get("event_type", "")
            message = log.get("message", "")

            # Compute elapsed time
            t_str = "00:00"
            ts_str = log.get("created_at")
            if ref_time and ts_str:
                try:
                    log_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    elapsed_s = int((log_time - ref_time).total_seconds())
                    t_str = f"{elapsed_s // 60:02d}:{elapsed_s % 60:02d}"
                except Exception:
                    pass

            # Severity indicator mapping
            severity_indicator = "regular"
            if agent == "evidence_fusion" and "CROSS_MODAL" in event_type:
                severity_indicator = "critical"
            elif agent == "orchestrator" and event_type == "approved":
                severity_indicator = "operator"

            # Color from log or agent default
            color = log.get("display_color", AGENT_COLORS.get(agent, "blue"))
            flash = log.get("display_flash", False)

            entries.append(TimelineEntry(
                t=t_str,
                timestamp=ts_str,
                agent=agent,
                model=log.get("model"),
                event_type=event_type,
                message=message,
                severity_indicator=severity_indicator,
                color=color,
                flash=flash,
            ))

        return entries

    def _build_evidence_sources(
        self, transcripts: list, state: dict, logs: list
    ) -> EvidenceSources:
        # --- Audio ---
        inbound = [t for t in transcripts if t.get("direction") != "outbound"]
        languages = sorted(set(t.get("language", "en") for t in inbound)) if inbound else []
        feed_ids = set(t.get("feed_id") for t in inbound if t.get("feed_id"))

        # Group by feed_id for speaker summaries
        speakers = []
        feed_groups: dict[str, list] = {}
        for t in inbound:
            fid = t.get("feed_id", "UNKNOWN")
            feed_groups.setdefault(fid, []).append(t)

        for fid, segments in feed_groups.items():
            lang = segments[0].get("language", "en")
            # Extract key intelligence from translated text
            key_intel = ""
            for seg in segments:
                translated = seg.get("translated_text") or seg.get("original_text", "")
                if translated:
                    key_intel = translated[:100]
                    break

            speakers.append(SpeakerSummary(
                feed_id=fid,
                language=lang,
                label=segments[0].get("caller_label", f"Scene Audio ({fid})"),
                key_intelligence=key_intel,
                segment_count=len(segments),
            ))

        audio = AudioSummary(
            speaker_count=len(feed_ids),
            languages=languages,
            transcript_count=len(inbound),
            speakers=speakers,
        )

        # --- Vision ---
        detections_raw = state.get("vision_detections", [])
        vision_entries = []
        for d in detections_raw:
            vision_entries.append(VisionDetectionEntry(
                timestamp_s=d.get("timestamp_s", d.get("frame_timestamp", 0.0)),
                type=d.get("type", d.get("label", "unknown")),
                confidence=d.get("confidence", 0.0),
                description=d.get("description", ""),
            ))

        vision = VisionSummary(
            frames_analyzed=len(detections_raw),
            detections=vision_entries,
        )

        # --- Cross-modal ---
        cross_modal = []
        for log in logs:
            if log.get("event_type") == "CROSS_MODAL_CORROBORATION":
                data = log.get("data", {})
                cross_modal.append(CrossModalSummary(
                    claim=data.get("claim", "unknown"),
                    modalities=data.get("modalities", []),
                    details=log.get("message", ""),
                ))

        return EvidenceSources(
            audio=audio,
            vision=vision,
            cross_modal=cross_modal,
        )

    def _build_convergence_tracks(
        self, logs: list, transcripts: list, state: dict
    ) -> list[ConvergenceTrack]:
        if not logs:
            return []

        # Reference time
        try:
            ref_time = datetime.fromisoformat(logs[0]["created_at"].replace("Z", "+00:00"))
        except Exception:
            return []

        tracks: dict[str, ConvergenceTrack] = {}

        # Audio tracks — one per language
        inbound = [t for t in transcripts if t.get("direction") != "outbound"]
        for t in inbound:
            lang = (t.get("language") or "en").upper()
            if lang not in tracks:
                color = LANGUAGE_COLORS.get(lang.lower(), "#6B7280")
                tracks[lang] = ConvergenceTrack(
                    source=lang, type="audio", color=color, events=[]
                )
            # Compute timestamp
            t_seconds = 0.0
            ts = t.get("created_at")
            if ts:
                try:
                    log_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    t_seconds = (log_time - ref_time).total_seconds()
                except Exception:
                    pass
            # Extract a label from the transcript
            text = t.get("translated_text") or t.get("original_text", "")
            label = text[:20].strip() if text else "transcript"

            tracks[lang].events.append(TrackEvent(
                t_seconds=round(t_seconds, 1),
                label=label,
                type="detection",
            ))

        # Vision track
        vision_events = []
        for log in logs:
            if log.get("agent") == "vision":
                ts = log.get("created_at")
                t_seconds = 0.0
                if ts:
                    try:
                        log_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        t_seconds = (log_time - ref_time).total_seconds()
                    except Exception:
                        pass
                event_type_str = log.get("event_type", "")
                label = "detection"
                track_type = "detection"
                if "hazard" in event_type_str.lower() or "escalation" in event_type_str.lower():
                    label = log.get("message", "HAZARD")[:20]
                    track_type = "escalation"
                elif "detection" in event_type_str.lower():
                    label = log.get("message", "detection")[:20]

                vision_events.append(TrackEvent(
                    t_seconds=round(t_seconds, 1),
                    label=label,
                    type=track_type,
                ))

        if vision_events:
            tracks["CAM"] = ConvergenceTrack(
                source="CAM", type="vision", color="#06B6D4", events=vision_events
            )

        # Fused track — from triage state changes and key events
        fused_events = []
        for log in logs:
            agent = log.get("agent", "")
            event_type = log.get("event_type", "")
            ts = log.get("created_at")
            t_seconds = 0.0
            if ts:
                try:
                    log_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    t_seconds = (log_time - ref_time).total_seconds()
                except Exception:
                    pass

            if agent == "orchestrator" and event_type == "init":
                fused_events.append(TrackEvent(
                    t_seconds=round(t_seconds, 1), label="watch", type="state_change"
                ))
            elif agent == "triage" and event_type == "severity_changed":
                msg = log.get("message", "")
                if "CRITICAL" in msg.upper():
                    fused_events.append(TrackEvent(
                        t_seconds=round(t_seconds, 1), label="CRITICAL", type="escalation"
                    ))
                elif "HIGH" in msg.upper() or "MEDIUM" in msg.upper():
                    fused_events.append(TrackEvent(
                        t_seconds=round(t_seconds, 1), label="active", type="state_change"
                    ))
            elif agent == "voice" and event_type == "priority_interrupt":
                fused_events.append(TrackEvent(
                    t_seconds=round(t_seconds, 1), label="evacuation", type="action"
                ))
            elif agent == "orchestrator" and event_type == "complete":
                fused_events.append(TrackEvent(
                    t_seconds=round(t_seconds, 1), label="SECURED", type="state_change"
                ))

        if fused_events:
            tracks["FUSED"] = ConvergenceTrack(
                source="FUSED", type="fused", color="#FBBF24", events=fused_events
            )

        return list(tracks.values())

    def _build_response_actions(
        self, dispatches: list, logs: list, state: dict
    ) -> list[ResponseAction]:
        if not logs:
            ref_time = None
        else:
            try:
                ref_time = datetime.fromisoformat(logs[0]["created_at"].replace("Z", "+00:00"))
            except Exception:
                ref_time = None

        actions = []
        for d in dispatches:
            # Compute authorized_at elapsed time
            authorized_at = None
            ts = d.get("created_at")
            if ref_time and ts:
                try:
                    d_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    elapsed_s = int((d_time - ref_time).total_seconds())
                    authorized_at = f"{elapsed_s // 60:02d}:{elapsed_s % 60:02d}"
                except Exception:
                    pass

            status = d.get("status", "recommended")
            # Determine authorization method
            auth_method = "operator"
            rationale = d.get("rationale", "")
            if "autonomous" in rationale.lower() or "evacuation" in rationale.lower() or "vision" in rationale.lower():
                auth_method = "autonomous"

            # Determine language for evacuation broadcasts
            language = None
            voice_msg = d.get("voice_message", "")
            if d.get("unit_type") == "Fire Response" or "evacuation" in rationale.lower():
                language = None  # fire response is usually en

            unit_type = d.get("unit_type", "")
            unit_assigned = d.get("unit_assigned")
            action_label = f"{unit_type}"
            if unit_assigned:
                action_label = f"{unit_type} ({unit_assigned})"

            actions.append(ResponseAction(
                action=action_label,
                unit_type=unit_type,
                unit_assigned=unit_assigned,
                status=status,
                authorized_at=authorized_at,
                authorization_method=auth_method,
                language=language,
            ))

        # Add evacuation broadcast actions from transcripts
        # (dispatch outbound transcripts = evacuation warnings)
        # These are already in dispatches table, so skip

        return actions

    def _build_agent_stats(self, logs: list, state: dict) -> AgentStats:
        if not logs:
            return AgentStats(models_used=KNOWN_MODELS)

        # Group by agent
        agent_groups: dict[str, list] = {}
        for log in logs:
            agent = log.get("agent", "unknown")
            agent_groups.setdefault(agent, []).append(log)

        # Compute duration
        duration = 0.0
        try:
            first = datetime.fromisoformat(logs[0]["created_at"].replace("Z", "+00:00"))
            last = datetime.fromisoformat(logs[-1]["created_at"].replace("Z", "+00:00"))
            duration = (last - first).total_seconds()
        except Exception:
            pass

        agents = []
        total_invocations = 0
        for agent_name, agent_logs in agent_groups.items():
            count = len(agent_logs)
            total_invocations += count

            # Estimate avg latency from timestamp gaps
            avg_latency = 0.0
            if count >= 2:
                try:
                    times = []
                    for al in agent_logs:
                        t = datetime.fromisoformat(al["created_at"].replace("Z", "+00:00"))
                        times.append(t)
                    deltas = [(times[i+1] - times[i]).total_seconds() for i in range(len(times)-1)]
                    avg_latency = sum(deltas) / len(deltas) if deltas else 0.0
                except Exception:
                    pass

            # Determine model from logs
            model = "unknown"
            for al in agent_logs:
                if al.get("model"):
                    model = al["model"]
                    break
            if model == "unknown":
                # Infer from agent name
                model_map = {
                    "intake": "mistral-large-latest",
                    "triage": "mistral-large-latest",
                    "evidence_fusion": "mistral-large-latest",
                    "dispatch": "mistral-large-latest",
                    "vision": "pixtral-large-latest",
                    "voice": "scribe-v2",
                    "orchestrator": "system",
                }
                model = model_map.get(agent_name, "unknown")

            # Format agent name nicely
            display_name = agent_name.replace("_", " ").title().replace(" ", "")
            if not display_name.endswith("Agent") and agent_name not in ("orchestrator", "voice"):
                display_name += "Agent"

            agents.append(AgentUtilization(
                agent=display_name,
                model=model,
                invocations=count,
                avg_latency_seconds=round(avg_latency, 2),
            ))

        return AgentStats(
            agents=agents,
            total_invocations=total_invocations,
            total_duration_seconds=round(duration, 1),
            models_used=KNOWN_MODELS,
        )

    def _build_key_frames(self, case_id: str, state: dict) -> list[KeyFrame]:
        # Find saved frames on disk
        frames_dir = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "frames")
        pattern = os.path.join(frames_dir, f"{case_id}_t*s.jpg")
        frame_files = sorted(glob.glob(pattern))

        if not frame_files:
            return []

        detections_raw = state.get("vision_detections", [])

        key_frames = []
        for fp in frame_files:
            filename = os.path.basename(fp)
            # Parse timestamp from filename: {case_id}_t{N}s.jpg
            try:
                t_part = filename.split("_t")[-1].replace("s.jpg", "")
                timestamp_s = float(t_part)
            except (ValueError, IndexError):
                continue

            elapsed_s = int(timestamp_s)
            elapsed_str = f"{elapsed_s // 60:02d}:{elapsed_s % 60:02d}"

            # Match detections to this timestamp
            frame_detections = []
            for d in detections_raw:
                d_ts = d.get("timestamp_s", d.get("frame_timestamp", -1))
                # Match within 5 second window
                if abs(d_ts - timestamp_s) < 5:
                    frame_detections.append({
                        "type": d.get("type", d.get("label", "unknown")),
                        "confidence": d.get("confidence", 0.0),
                    })

            # Determine if hero frame (fire detection)
            is_hero = any(
                "fire" in d.get("type", "").lower()
                for d in frame_detections
            )

            # Build description
            if frame_detections:
                det_labels = [f"{d['type']} ({d['confidence']:.2f})" for d in frame_detections]
                description = f"Detected: {', '.join(det_labels)}"
                if is_hero:
                    description += " — highest confidence detection"
            else:
                description = f"Scene at T+{elapsed_s}s"

            key_frames.append(KeyFrame(
                image_url=f"/frames/{filename}",
                timestamp_s=timestamp_s,
                elapsed=elapsed_str,
                detections=frame_detections,
                description=description,
                is_hero=is_hero,
            ))

        return key_frames

    async def _generate_executive_summary(
        self,
        case_id: str,
        state: dict,
        transcripts: list,
        dispatches: list,
    ) -> str:
        # Return cached if available
        if case_id in ReportBuilder._summary_cache:
            return ReportBuilder._summary_cache[case_id]

        # Build context for Mistral
        inbound = [t for t in transcripts if t.get("direction") != "outbound"]
        languages = sorted(set(t.get("language", "en") for t in inbound))
        hazards = state.get("hazard_flags", [])
        detections = state.get("vision_detections", [])

        context = f"""Incident Report Context:
- Case ID: {case_id}
- Type: {state.get('incident_type', 'Unknown')}
- Location: {state.get('location_normalized', 'Unknown')}
- Severity: {state.get('severity', 'unknown')}
- Status: {state.get('status', 'unknown')}
- Audio segments processed: {len(inbound)}
- Languages detected: {', '.join(languages)}
- Vision detections: {len(detections)}
- Hazard flags: {', '.join(hazards) if hazards else 'None'}
- Dispatched units: {len(dispatches)}
- Confirmed units: {', '.join(state.get('confirmed_units', []))}
- People count estimate: {state.get('people_count_estimate', 0)}
- Injury flags: {', '.join(state.get('injury_flags', []))}
- Operator summary: {state.get('operator_summary', 'N/A')}
"""

        prompt = f"""Write a 3-4 sentence executive summary for this emergency incident after-action report.
Be factual and specific. Reference the exact number of audio segments, languages, vision frames,
and the outcome. Emphasize any cross-modal evidence fusion (where multiple independent sensor
modalities confirmed the same hazard). Note any autonomous actions taken by the system.

{context}

Write the summary as a single paragraph, no bullet points."""

        try:
            response = await self.mistral.chat.complete_async(
                model="mistral-large-latest",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3,
            )
            summary = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Mistral summary generation failed: {e}")
            # Fallback to operator summary
            summary = state.get("operator_summary", "Executive summary unavailable.")

        # Cache it
        ReportBuilder._summary_cache[case_id] = summary
        return summary
