"""
Email templates for Phase 4 Email Delivery
"""
import re

WEEKLY_PULSE_TEMPLATE = """
Hi {recipient_name},

## INDMoney Weekly Review Pulse -- {week_date}

{weekly_note_content}

---

Best regards,
INDMoney Insights Team
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>INDMoney Weekly Review Pulse</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .content {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .section {{
            margin-bottom: 25px;
        }}
        .section h2 {{
            color: #2c3e50;
            font-size: 18px;
            margin-bottom: 15px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 5px;
        }}
        .theme-item {{
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #9b59b6;
        }}
        .quote {{
            background: #fff3cd;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
            font-style: italic;
        }}
        .quote .rating {{
            color: #f39c12;
            font-weight: bold;
        }}
        .action {{
            background: #d4edda;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #28a745;
        }}
        .priority {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }}
        .priority-high {{
            background: #dc3545;
            color: white;
        }}
        .priority-medium {{
            background: #ffc107;
            color: #212529;
        }}
        .priority-low {{
            background: #6c757d;
            color: white;
        }}
        .footer {{
            text-align: center;
            color: #6c757d;
            font-size: 14px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>INDMoney Weekly Review Pulse</h1>
        <p>{week_date}</p>
    </div>
    
    <div class="content">
        {weekly_note_html}
    </div>
    
        <div class="attached-snippet">
            <h3 style="color:#2c3e50; font-size:14px; margin-bottom:8px;">📎 Weekly Note (attached)</h3>
            <p style="background:#f1f3f5; padding:12px; border-radius:6px; font-size:13px; color:#495057;">{appended_filename}</p>
            <p style="font-size:12px; color:#6c757d; margin-top:8px;">Snippet: {appended_snippet}</p>
        </div>
        <div class="footer">
        <p>Best regards,<br>INDMoney Insights Team</p>
        <p><small>This automated report was generated on {generated_date}</small></p>
    </div>
</body>
</html>
"""

PLAIN_TEXT_TEMPLATE = """
Hi {recipient_name},

INDMONEY WEEKLY REVIEW PULSE -- {week_date}
==================================================

{weekly_note_text}

--------------------------------------------------
📎 Appended: Weekly Note ({appended_filename})
Snippet: {appended_snippet}
--------------------------------------------------
Best regards,
INDMoney Insights Team

This automated report was generated on {generated_date}
"""

# Email formatting utilities
def strip_markdown_headers(content: str) -> str:
    """Remove lines starting with # (markdown headers) to avoid duplicate headers in email."""
    lines = []
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped and stripped[0] == '#':
            continue
        lines.append(line)
    return '\n'.join(lines).strip()


def format_markdown_to_html(markdown_content: str) -> str:
    """Convert markdown content to HTML for email. Header lines (#) are stripped to avoid duplicates."""
    content = strip_markdown_headers(markdown_content)
    # Split by double newline into blocks (themes, quotes, actions)
    blocks = [b.strip() for b in content.split('\n\n') if b.strip()]
    section_titles = ['Top Themes', 'Real User Quotes', 'Action Ideas']
    html_parts = []
    for i, block in enumerate(blocks[:3]):
        title = section_titles[i] if i < len(section_titles) else ''
        html_parts.append(_format_block(block, title))
    return '\n'.join(html_parts)


def _format_block(block: str, section_title: str) -> str:
    """Format a content block to HTML. Theme items use theme-item (purple), quotes use quote (yellow), actions use action (green)."""
    items = []
    for line in block.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('-') or line.startswith('*'):
            items.append(f'<div class="theme-item">{line.lstrip("-*").strip()}</div>')
        elif line.startswith('Action') and 'Priority:' in line:
            # Replace (Priority: High) with styled span only - no duplicate High/Medium/Low
            def _priority_repl(m):
                p = m.group(1)
                return f'(<span class="priority priority-{p.lower()}">{p}</span>)'
            line = re.sub(r'\(Priority:\s*(\w+)\)', _priority_repl, line)
            items.append(f'<div class="action">{line}</div>')
        elif line.startswith('Action'):
            items.append(f'<div class="action">{line}</div>')
        elif '"' in line:
            quote_text = line.split('"')[1] if line.count('"') >= 2 else line
            items.append(f'<div class="quote">{quote_text}</div>')
        else:
            # Top Themes: use theme-item for consistent pointer style (purple)
            items.append(f'<div class="theme-item">{line}</div>')
    body = '\n'.join(items)
    return f'<div class="section"><h2>{section_title}</h2>{body}</div>' if section_title else f'<div class="section">{body}</div>'
