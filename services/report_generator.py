from reportlab.platypus import *
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import os

REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)


def json_to_pdf(report_json, filename="meeting_report.pdf"):

    file_path = os.path.join(REPORT_DIR, filename)

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    elements = []

    # ─────────────────────────────
    # TITLE
    # ─────────────────────────────
    elements.append(Paragraph(report_json.get("title", ""), styles['Title']))
    elements.append(Spacer(1, 12))

    # ─────────────────────────────
    # META DETAILS
    # ─────────────────────────────
    meta = report_json.get("meta", {})

    elements.append(Paragraph("<b>Meeting Details</b>", styles['Heading2']))
    elements.append(Paragraph(f"File: {meta.get('audio_filename', '')}", styles['Normal']))
    duration_sec = meta.get("duration_seconds", 0)

# Convert to minutes
    duration_min = round(duration_sec / 60, 2) if duration_sec else 0

    elements.append(Paragraph(
        f"Duration: {duration_min} minutes ({duration_sec} sec)",
        styles['Normal']
    ))
    elements.append(Paragraph(f"Language: {meta.get('language', '')}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # ─────────────────────────────
    # SUMMARY
    # ─────────────────────────────
    elements.append(Paragraph("<b>Summary</b>", styles['Heading2']))
    elements.append(Paragraph(report_json.get("summary", ""), styles['Normal']))
    elements.append(Spacer(1, 12))

    # ─────────────────────────────
    # PARTICIPANTS (CLEAN FIX)
    # ─────────────────────────────
    participants = report_json.get("participants", [])

    # 🔥 Remove garbage names
    participants = [
        p for p in participants
        if p.get("name") and p.get("name").lower() not in ["without", "unknown"]
    ]

    if participants:
        elements.append(Paragraph("<b>Participants</b>", styles['Heading2']))

        table_data = [["Name", "Role"]]
        for p in participants:
            table_data.append([p.get("name"), p.get("role")])

        table = Table(table_data, hAlign='LEFT')
        table.setStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 6),
        ])
        elements.append(table)
        elements.append(Spacer(1, 12))

    # ─────────────────────────────
    # DISCUSSION
    # ─────────────────────────────
    discussions = report_json.get("discussion_sections", [])

    if discussions:
        elements.append(Paragraph("<b>Discussion</b>", styles['Heading2']))

        for d in discussions:

            elements.append(
                Paragraph(
                    f"<b>{d.get('title')}</b> ({d.get('type')})",
                    styles['Heading3']
                )
            )

            elements.append(Paragraph(f"<b>Speaker:</b> {d.get('speaker')}", styles['Normal']))

            elements.append(Paragraph(d.get("description", ""), styles['Normal']))

            # 🔥 Progress + Risk
            progress = d.get("progress_percent", 0)
            risk = d.get("risk_level", "low")

            # 🎨 Color based on risk
            if risk == "high":
                risk_color = "red"
            elif risk == "medium":
                risk_color = "orange"
            else:
                risk_color = "green"

            elements.append(
                Paragraph(
                    f"Progress: {progress}% | <font color='{risk_color}'>Risk: {risk}</font>",
                    styles['Normal']
                )
            )

            # Bullet points
            for point in d.get("points", []):
                elements.append(Paragraph(f"• {point}", styles['Normal']))

            elements.append(Spacer(1, 10))

    # ─────────────────────────────
    # DECISIONS
    # ─────────────────────────────
    decisions = report_json.get("key_decisions", [])

    if decisions:
        elements.append(Paragraph("<b>Key Decisions</b>", styles['Heading2']))
        for d in decisions:
            elements.append(Paragraph(f"• {d}", styles['Normal']))
        elements.append(Spacer(1, 12))

    # ─────────────────────────────
    # ACTION ITEMS
    # ─────────────────────────────
    actions = report_json.get("action_items", [])

    if actions:
        elements.append(Paragraph("<b>Action Items</b>", styles['Heading2']))

        table_data = [["Owner", "Task", "Priority"]]

        for a in actions:
            table_data.append([
                a.get("owner"),
                a.get("task"),
                a.get("priority")
            ])

        table = Table(table_data, hAlign='LEFT')
        table.setStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.green),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 6),
        ])

        elements.append(table)
        elements.append(Spacer(1, 12))

    # ─────────────────────────────
    # RISKS
    # ─────────────────────────────
    risks = report_json.get("risks", [])

    if risks:
        elements.append(Paragraph("<b>Risks</b>", styles['Heading2']))

        for r in risks:
            elements.append(
                Paragraph(
                    f"• {r.get('risk')} (Impact: {r.get('impact')}) - {r.get('solution')}",
                    styles['Normal']
                )
            )

        elements.append(Spacer(1, 12))

    # ─────────────────────────────
    # SPEAKERS (🔥 FIXED MAIN ISSUE)
    # ─────────────────────────────
    speakers = report_json.get("speakers", [])

    if speakers:
        elements.append(Paragraph("<b>Speakers Timeline</b>", styles['Heading2']))

        for s in speakers:
            elements.append(
                Paragraph(
                    f"<b>{s.get('speaker')}</b> "
                    f"({s.get('start_time')}s - {s.get('end_time')}s)",
                    styles['Normal']
                )
            )

            elements.append(
                Paragraph(
                    s.get("text", "")[:300] + "...",
                    styles['Normal']
                )
            )

            elements.append(Spacer(1, 10))

    # BUILD PDF
    doc.build(elements)

    return file_path