"""Views for the top-level Workbench subpage (Workbench/index.html) and Database destinations."""

from __future__ import annotations

from html import escape
import json
from pathlib import Path
import re
from typing import Any

from .athletics_views import _chart, _downloads, _hero, _metrics, _num, _section, _table
from .atlas import NODES, ROOT as ATLAS_ROOT
from .atlas_views import FEATURES, HOSTED
from .workbench import APPLICATION_DOMAINS, RAP_BUCKETS, THEORY_CATEGORIES, TODO_PRIORITIES, VOICE_CHANNELS

__all__ = [
    "auth_dialog_html",
    "completion_dashboard_body",
    "database_leaf_content",
    "site_completion_dashboard_content",
    "traffic_dashboard_body",
    "updates_dashboard_body",
    "workbench_body",
]


def _e(value: Any) -> str:
    return escape(str(value if value is not None else ""), quote=True)


def _peek_eyes_svg() -> str:
    """Stylized twin '👀' eyes icon in the site's vector line-art aesthetic."""
    return (
        '<svg class="wb-peek-icon" viewBox="0 0 24 24" width="20" height="20" fill="none" '
        'stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true" focusable="false">'
        '<ellipse cx="7.4" cy="12" rx="4.2" ry="6.2"/>'
        '<ellipse cx="16.6" cy="12" rx="4.2" ry="6.2"/>'
        '<circle class="wb-peek-pupil" cx="6.2" cy="12.2" r="2" fill="currentColor" stroke="none"/>'
        '<circle class="wb-peek-pupil" cx="15.4" cy="12.2" r="2" fill="currentColor" stroke="none"/>'
        '<circle class="wb-peek-glint" cx="5.5" cy="10.8" r=".7" fill="#0d101b" stroke="none"/>'
        '<circle class="wb-peek-glint" cx="14.7" cy="10.8" r=".7" fill="#0d101b" stroke="none"/>'
        '</svg>'
    )


def auth_dialog_html() -> str:
    """Passkey login + API key vault dialog (#wb-auth-dialog) and separate Admin Password Manager (#wb-password-dialog)."""
    eyes = _peek_eyes_svg()
    return f'''<dialog class="request-dialog wb-dialog" id="wb-auth-dialog" aria-labelledby="wb-auth-title">
      <form class="request-form" method="dialog" id="wb-auth-form">
        <p class="eyebrow">Owner Passkey &amp; Admin Vault · SHA-256 HMAC + Session/IP Lock</p>
        <h2 id="wb-auth-title">Unlock Admin</h2>
        <p class="request-intro">Unlocking Admin is valid for <strong>30 minutes across all branches of the site</strong> (as long as you stay within the site's URL tree) and is bound to your current IP address. Your <strong>Master Passphrase always works forever</strong> (4,096-round SHA-256 HMAC; never stored in plaintext). Once unlocked, use the <strong>🔑 Passwords</strong> button in the top bar to create or revoke temporary friend passwords.</p>
        <div class="request-grid">
          <label class="request-wide" for="wb-auth-pass">Master or delegated passphrase<span class="wb-pass-wrap"><input id="wb-auth-pass" name="passphrase" type="password" required autocomplete="current-password" placeholder="Enter master passphrase or active friend password to unlock"><button class="wb-peek-btn" type="button" data-wb-peek="wb-auth-pass" aria-label="Show current passphrase" aria-pressed="false" title="Show or hide current passphrase">{eyes}</button></span></label>
          <label class="request-wide" for="wb-auth-model"><span>Default Study Runner model &amp; thinking depth · <small id="wb-model-discovery">Auto-discovers latest Gemini 4 / Deep Research models from your API key</small></span>
            <select id="wb-auth-model" name="runnerModel">
              <option value="argon-high" selected>Gemini 4 Argon · High Thinking (Default · gemini-4-argon + Google Search + Pandas)</option>
              <option value="argon-medium">Gemini 4 Argon · Medium Thinking (gemini-4-argon · balanced speed &amp; depth)</option>
              <option value="deep-research">Gemini Deep Research Agent · Multi-Step Autonomous Research (deep-research-preview-04-2026)</option>
              <option value="flash-fast">Gemini 3.8 Flash · Fast Grounded Search (gemini-3.8-flash · lowest token cost)</option>
            </select>
          </label>
          <label class="request-wide" for="wb-auth-key"><span>Gemini API key (Google AI Studio Auth key <code>AQ....</code> or <code>AIza...</code>) · <small id="wb-key-status">Checking browser vault…</small></span><input id="wb-auth-key" name="apiKey" type="password" autocomplete="off" placeholder="Paste your Google AI Studio key (AQ....eQ3w) once to save; leave blank to use saved key"></label>
          <label class="request-wide" for="wb-auth-github-pat"><span>GitHub Personal Access Token (<code>github_pat_...</code> or <code>ghp_...</code> · optional for permanent non-local mobile commits) · <small id="wb-pat-status">Optional: commits mobile studies &amp; Google Doc updates straight to GitHub</small></span><input id="wb-auth-github-pat" name="githubPat" type="password" autocomplete="off" placeholder="Paste Fine-Grained GitHub PAT (Contents: Read/Write on liammspandasprojects) once"></label>
        </div>
        <p class="request-status" id="wb-auth-status" role="status" aria-live="polite"></p>
        <div class="request-actions">
          <button class="button ghost" type="button" id="wb-restore-deleted" hidden>Restore deleted defaults</button>
          <button class="button ghost" type="button" id="wb-auth-lock">Lock Admin</button>
          <button class="button ghost" type="button" data-wb-dialog-close="wb-auth-dialog">Cancel</button>
          <button class="button primary" type="submit">Unlock Admin 🔓</button>
        </div>
      </form>
    </dialog>
    <dialog class="request-dialog wb-dialog" id="wb-password-dialog" aria-labelledby="wb-password-title">
      <form class="request-form" method="dialog" id="wb-password-form">
        <p class="eyebrow">Admin Access &amp; Delegated Passwords · Master Passkey Protected</p>
        <h2 id="wb-password-title">Create or Revoke Access Passwords</h2>
        <p class="request-intro">Your <strong>Master Passphrase is immutable and always works forever</strong>—creating a friend/guest password never overwrites your Master Passphrase. Delegated passwords default to <strong>12 hours</strong> before automatic revocation, or can be extended up to <strong>Infinite (∞)</strong> and revoked at any time.</p>
        <div class="request-grid">
          <label for="wb-pwd-label">Recipient / password label<input id="wb-pwd-label" name="pwdLabel" type="text" placeholder="e.g. Friend / Work Phone / Reviewer" value="Friend Access"></label>
          <label for="wb-pwd-duration">Expiration duration (auto-revokes after)<select id="wb-pwd-duration" name="durationHours">
            <option value="1">1 Hour</option>
            <option value="6">6 Hours</option>
            <option value="12" selected>12 Hours (Default)</option>
            <option value="24">24 Hours (1 Day)</option>
            <option value="168">7 Days (168 Hours)</option>
            <option value="720">30 Days (720 Hours)</option>
            <option value="custom">Custom Hours (enter below)…</option>
            <option value="infinite">Infinite / Never Expires (∞ — until manually revoked)</option>
          </select></label>
          <label class="request-wide" id="wb-pwd-custom-wrap" for="wb-pwd-custom-hours" hidden>Custom duration in hours<input id="wb-pwd-custom-hours" name="customHours" type="number" min="1" max="87600" value="48" placeholder="Enter custom hours (e.g. 48)"></label>
          <label for="wb-auth-new-pass">New access password<span class="wb-pass-wrap"><input id="wb-auth-new-pass" name="newPassphrase" type="password" required autocomplete="new-password" placeholder="Enter new password (min 4 chars)"><button class="wb-peek-btn" type="button" data-wb-peek="wb-auth-new-pass" aria-label="Show new passphrase" aria-pressed="false" title="Show or hide new password">{eyes}</button></span></label>
          <label for="wb-pwd-confirm">Confirm new access password<span class="wb-pass-wrap"><input id="wb-pwd-confirm" name="confirmPassphrase" type="password" required autocomplete="new-password" placeholder="Re-enter new password to confirm"><button class="wb-peek-btn" type="button" data-wb-peek="wb-pwd-confirm" aria-label="Show confirm passphrase" aria-pressed="false" title="Show or hide confirm password">{eyes}</button></span></label>
          <label class="request-wide" for="wb-pwd-master">Verify with Master Passphrase (required to issue or revoke passwords)<span class="wb-pass-wrap"><input id="wb-pwd-master" name="masterPassphrase" type="password" required autocomplete="current-password" placeholder="Enter your Master Passphrase to authorize"><button class="wb-peek-btn" type="button" data-wb-peek="wb-pwd-master" aria-label="Show master passphrase" aria-pressed="false" title="Show or hide master passphrase">{eyes}</button></span></label>
        </div>
        <p class="request-status" id="wb-pwd-status" role="status" aria-live="polite"></p>
        <div class="request-actions">
          <button class="button ghost wb-delete-study-btn" type="button" id="wb-pwd-revoke-all">🔥 Revoke ALL Delegated Passwords</button>
          <button class="button ghost" type="button" data-wb-dialog-close="wb-password-dialog">Close</button>
          <button class="button primary" type="submit" id="wb-pwd-save-btn">💾 Save &amp; Activate Password</button>
        </div>
        <div class="wb-pwd-list-wrap">
          <h3 style="margin:6px 0 6px;font-size:14px;color:#9ddacf;">Active Delegated Passwords</h3>
          <div id="wb-pwd-active-list" class="wb-pwd-active-list"><p class="sports-note">No delegated passwords active — only your Master Passphrase is enabled.</p></div>
        </div>
      </form>
    </dialog>'''


def _node_link(prefix: str, atlas_path: str) -> str:
    node = NODES.get(atlas_path)
    if node is None:
        return _e(atlas_path)
    return f'<a href="{_e(prefix + node.url)}">{_e(node.title)} ↗</a>'


def _status_badge(status: str) -> str:
    tone = "up" if status in ("published", "done", "processed") else ("warn" if status in ("in-progress", "recorded") else "flat")
    return f'<span class="wb-badge wb-{tone}">{_e(status)}</span>'


def _cascading_atlas_select(id_prefix: str, label_prefix: str = "Atlas") -> str:
    """Render 3 linked cascading dropdowns: Section (Field) -> Subsection (Topic) -> Subsubsection (Destination)."""
    fields = list(ATLAS_ROOT.children)
    field_opts = "".join(
        f'<option value="{_e(f.path)}">{idx + 1}. {_e(f.title)}</option>'
        for idx, f in enumerate(fields)
    )
    topic_opts = "".join(
        f'<option value="{_e(t.path)}" data-parent-field="{_e(f.path)}">{_e(f.title)} · {_e(t.title)}</option>'
        for f in fields for t in f.children
    )
    leaf_opts = []
    for f in fields:
        for t in f.children:
            for l_idx, leaf in enumerate(t.children):
                leaf_opts.append(
                    f'<option value="{_e(leaf.path)}" data-parent-field="{_e(f.path)}" data-parent-topic="{_e(t.path)}">'
                    f'{l_idx + 1}. {_e(leaf.title)} ({_e(t.title)})</option>'
                )
            leaf_opts.append(
                f'<option value="{_e(t.path)}" data-parent-field="{_e(f.path)}" data-parent-topic="{_e(t.path)}">'
                f'All / Topic-Level: {_e(t.title)}</option>'
            )
    return (
        f'<div class="wb-wide wb-cascade-grid" data-wb-cascade="{_e(id_prefix)}">'
        f'<label for="{_e(id_prefix)}-field">1. {_e(label_prefix)} Section (Field)'
        f'<select id="{_e(id_prefix)}-field" data-cascade-field data-wb-cascade-field="{_e(id_prefix)}">{field_opts}</select></label>'
        f'<label for="{_e(id_prefix)}-topic">2. Subsection (Topic)'
        f'<select id="{_e(id_prefix)}-topic" data-cascade-topic data-wb-cascade-topic="{_e(id_prefix)}">{topic_opts}</select></label>'
        f'<label for="{_e(id_prefix)}-path">3. Subsubsection (Destination)'
        f'<select id="{_e(id_prefix)}-path" name="atlasPath" data-cascade-leaf data-wb-cascade-leaf="{_e(id_prefix)}" required>{"".join(leaf_opts)}</select></label>'
        f'</div>'
    )


def workbench_body(data: dict[str, Any], prefix: str = "../") -> str:
    """Render the direct top-level Workbench subpage (depth 1)."""
    summary = data["summary"]
    metrics = _metrics([
        ("Study queue", str(summary["studies"]), f"{summary['studiesPublished']} published · {summary['studiesQueued']} queued · {summary.get('studyClicksTotal', 0)} visits",
         "Empirical studies backed by public or internal site datasets, Pandas scripts, SVG charts, and compiled LaTeX PDFs."),
        ("Theory & Applications", f"{summary.get('theory', 3)}T · {summary.get('applications', 3)}A", "Engineering Triad: Theory → Application → Study",
         "Foundational first-principles Theory modules (including subsubsection introductions from scratch) paired with real-world Engineering Applications."),
        ("Wishlist to-dos", str(summary["todos"]), f"{summary['todosDone']} done · {summary['todosOpen']} open",
         "Prioritized website, database, athletics, and research tasks tracked in SQLite."),
        ("Bars & Voice studio", f"{summary['lyrics']} bars · {summary['voiceNotes']} memos", f"{summary['lyricBuckets']} Rap buckets · {summary['voiceSeconds']} s audio",
         "Spontaneous rap lyrics routed into the 6 Rap subsubsections and voice memos transcribed into the Journal/Podcast queue."),
    ])

    # 1. Study Queue table (compact 5-column table when locked; reveals IP Index & Delete columns when Unlock Admin is active)
    study_rows = []
    for item in data["studyQueue"]:
        links = []
        if item.get("studyRoute"):
            links.append(f'<a class="wb-action-link" data-study-click="{_e(item["id"])}" href="{_e(prefix + item["studyRoute"])}">Interactive study ↗</a>')
        if item.get("paperRoute"):
            links.append(f'<a class="wb-action-link" data-study-click="{_e(item["id"])}" href="{_e(prefix + item["paperRoute"])}">LaTeX paper &amp; PDF ↗</a>')
        if item["status"] != "published":
            links.append(
                f'<button class="button ghost wb-run-study-btn" type="button" '
                f'data-run-study-id="{_e(item["id"])}" '
                f'data-study-title="{_e(item["title"])}" '
                f'data-study-path="{_e(item["atlasPath"])}" '
                f'data-study-question="{_e(item["question"])}" '
                f'data-study-dataset="{_e(item["dataset"])}">▶ Run study now</button>'
            )
        else:
            links.append(
                f'<button class="button ghost wb-run-study-btn wb-restudy-btn" type="button" '
                f'data-restudy-id="{_e(item["id"])}" '
                f'data-study-title="{_e(item["title"])}" '
                f'data-study-path="{_e(item["atlasPath"])}" '
                f'data-study-question="{_e(item["question"])}" '
                f'data-study-dataset="{_e(item["dataset"])}">↻ Re-Study Deeper</button>'
            )
        ip_idx = item.get("ipIndex", "IP#OWNER")
        clicks = int(item.get("clicks", 0))
        study_rows.append((
            item["id"], item["createdOn"], item["title"], item["atlasPath"],
            item["question"], item["dataset"], item["status"], ip_idx, clicks, " · ".join(links) or "Queued",
        ))
    study_tbody = "".join(
        f'<tr data-study-row="{_e(cid)}" data-study-date="{_e(created)}" data-study-title="{_e(title)}" '
        f'data-study-path="{_e(path)}" data-study-field="{_e(path.split("/")[0])}" '
        f'data-study-question="{_e(question)}" data-study-dataset="{_e(dataset)}" '
        f'data-study-status-val="{_e(status)}" data-study-ip="{_e(ip_idx)}" data-study-clicks="{clicks}">'
        f'<th scope="row" class="wb-col-id"><code>{_e(cid)}</code></th><td class="wb-col-date">{_e(created)}</td>'
        f'<td class="wb-study-td"><div class="wb-study-cell">'
        f'<button type="button" class="wb-study-link" data-wb-study-trigger data-study-click="{_e(cid)}" aria-expanded="false" aria-controls="wb-tip-{_e(cid)}">'
        f'<span class="wb-study-link-title">{_e(title)}</span>'
        f'<span class="wb-study-link-pill" aria-hidden="true">↗ Details &amp; Run</span>'
        f'<span class="wb-click-pill" data-click-badge="{_e(cid)}" title="Total clicks / visits on this study">👁 {clicks}</span></button>'
        f'<div class="wb-pbi-tooltip" id="wb-tip-{_e(cid)}" role="region" aria-label="{_e(title)} details">'
        f'<div class="wb-pbi-head"><span class="wb-pbi-kicker"><code>{_e(cid)}</code> · Study Tooltip · <span data-click-badge="{_e(cid)}">{clicks} visits</span></span>'
        f'<button type="button" class="wb-pbi-close" data-wb-tip-close aria-label="Close study tooltip">✕</button></div>'
        f'<div class="wb-pbi-row"><span class="wb-pbi-label">Destination</span><div class="wb-pbi-val">{_node_link(prefix, path)}</div></div>'
        f'<div class="wb-pbi-row"><span class="wb-pbi-label">Question</span><p class="wb-pbi-question">{_e(question)}</p></div>'
        f'<div class="wb-pbi-row"><span class="wb-pbi-label">Re-Study Data Scope (Multi-Select)</span>'
        f'<div class="wb-restudy-checks">'
        f'<label class="wb-scope-pill"><input type="checkbox" data-restudy-new="{_e(cid)}" checked><span class="wb-scope-check" aria-hidden="true"></span><span>New External Datasets</span></label>'
        f'<label class="wb-scope-pill"><input type="checkbox" data-restudy-updated="{_e(cid)}"><span class="wb-scope-check" aria-hidden="true"></span><span>Updated / Internal Site Datasets</span></label>'
        f'</div></div>'
        f'<div class="wb-pbi-row"><span class="wb-pbi-label">Outputs / Run</span><div class="wb-pbi-actions" data-study-outputs="{_e(cid)}">{links_html}</div></div>'
        f'<div class="wb-pbi-row" data-wb-admin-only hidden><span class="wb-pbi-label">Admin · IP Index &amp; Moderation</span>'
        f'<div class="wb-pbi-actions"><code class="wb-ip-badge">{_e(ip_idx)}</code>'
        f'<button type="button" class="button ghost wb-delete-study-btn" data-delete-study-id="{_e(cid)}">🗑 Delete study</button></div></div>'
        f'</div></div></td>'
        f'<td class="wb-col-data">{_e(dataset)}</td><td class="wb-col-status" data-study-status="{_e(cid)}">{_status_badge(status)}</td>'
        f'<td data-wb-admin-col hidden><code class="wb-ip-badge">{_e(ip_idx)}</code></td>'
        f'<td data-wb-admin-col hidden><button type="button" class="button ghost wb-delete-study-btn" data-delete-study-id="{_e(cid)}" aria-label="Delete {_e(cid)}">🗑 Delete</button></td></tr>'
        for cid, created, title, path, question, dataset, status, ip_idx, clicks, links_html in study_rows
    )
    field_options = "".join(
        f'<option value="{_e(node.path)}">{_e(node.title)}</option>'
        for node in NODES.values() if node.depth == 1
    )
    study_filter_bar = (
        '<div class="wb-filter-bar" id="wb-study-filters" role="search" aria-label="Filter and sort studies">'
        '<label class="wb-filter-item" for="wb-filter-search"><span>Search studies</span>'
        '<input id="wb-filter-search" type="search" placeholder="Search title, question, or data…"></label>'
        '<label class="wb-filter-item" for="wb-filter-status"><span>Status</span>'
        '<select id="wb-filter-status"><option value="all">All statuses</option>'
        '<option value="published">published</option><option value="in-progress">in-progress</option><option value="queued">queued</option></select></label>'
        f'<label class="wb-filter-item" for="wb-filter-field"><span>Atlas field</span>'
        f'<select id="wb-filter-field"><option value="all">All 6 fields</option>{field_options}</select></label>'
        '<label class="wb-filter-item" for="wb-filter-sort"><span>Sort by</span>'
        '<select id="wb-filter-sort">'
        '<option value="id-asc">Study ID (ST-01 → ST-99)</option>'
        '<option value="visits-desc">Visit Rank (Most clicked first)</option>'
        '<option value="date-desc">Date (Newest first)</option>'
        '<option value="date-asc">Date (Oldest first)</option>'
        '</select></label>'
        '<label class="wb-filter-item" for="wb-filter-ip"><span>Submitter / IP Index</span>'
        '<select id="wb-filter-ip"><option value="all">All submitters</option>'
        '<option value="mine">Added from my IP / device</option>'
        '<option value="not-mine">Added by other IPs</option>'
        '<option value="IP#OWNER">IP#OWNER (Repo seeded)</option></select></label>'
        '<div class="wb-filter-actions">'
        '<button class="button ghost" type="button" id="wb-filter-reset">Reset filters</button>'
        '<button class="button ghost wb-delete-study-btn" type="button" id="wb-delete-filtered-ip" data-wb-admin-only hidden>🗑 Delete shown IP studies</button>'
        '</div></div>'
    )
    study_table = (
        study_filter_bar
        + '<div class="sports-table-wrap wb-studies-wrap" role="region" aria-label="To study with data" tabindex="0">'
        '<table id="workbench-studies-table"><caption>To Study with Data — hover or tap any Study link for Destination, Question, Visit Rank &amp; Outputs / Run</caption>'
        '<thead><tr><th scope="col">ID</th><th scope="col">Date</th><th scope="col">Study (hover / tap)</th>'
        '<th scope="col">Data</th><th scope="col">Status</th>'
        '<th scope="col" data-wb-admin-col hidden>IP Index</th>'
        '<th scope="col" data-wb-admin-col hidden>Admin</th></tr></thead>'
        f'<tbody id="wb-studies-body">{study_tbody}</tbody></table></div>'
    )

    atlas_options = "".join(
        f'<option value="{_e(node.path)}">{_e(node.path.replace("/", " / "))}</option>'
        for node in NODES.values() if node.depth >= 2
    )
    site_data_presets = (
        '<div class="wb-site-data-bar" role="group" aria-label="Attach internal site datasets">'
        '<span class="wb-site-data-label">📎 Attach My Site\'s Data (click to toggle):</span>'
        '<button type="button" class="wb-bucket-chip" data-site-dataset="Internal Site Data: records/athletics/weightlifting/Weightlifting_Log.txt + records/health/diet/Diet_and_Calorie_Tracking.txt">🏋️ Weightlifting + Calorie Logs</button>'
        '<button type="button" class="wb-bucket-chip" data-site-dataset="Internal Site Data: records/athletics/running/Interval_Data.txt + Tempo_Run_Log.txt + records/health/sleep/Sleep_and_Dream_Log.txt">🏃 Running + Tempo + Sleep Logs</button>'
        '<button type="button" class="wb-bucket-chip" data-site-dataset="Internal Site Data: records/athletics/swimming/Swimming_Log.txt">🏊 Swimming Log</button>'
        '<button type="button" class="wb-bucket-chip" data-site-dataset="Internal Site Data: records/basketball/series.json (13 series, 73 rounds)">🏀 First-to-Four Basketball</button>'
        '<button type="button" class="wb-bucket-chip" data-site-dataset="Internal Site Data: Smash/index.html + matchup_chart.csv + character_models/">🎮 Smash Bros Mains &amp; Matchups</button>'
        '<button type="button" class="wb-bucket-chip" data-site-dataset="Internal Site Data: records/site_content/music-analysis.json + rap-catalog.json">🎤 Rap Lyrics &amp; Sentiment</button>'
        '</div>'
    )
    study_form = f'''<form class="wb-form wb-snap-target" id="wb-study-form" data-wb-table="studyQueue">
      <div class="wb-form-head">
        <h3>01 · Add a study to the queue (auto-expands as you type · stacks new tabs in existing sections)</h3>
        <span class="wb-auth-pill" data-wb-auth-indicator>🔒 Admin locked</span>
      </div>
      <div class="wb-form-grid">
        <label for="wb-study-title">Study title <small>(auto-grows)</small><textarea id="wb-study-title" name="title" class="wb-auto-grow" rows="1" required maxlength="500" placeholder="e.g. Semiconductor Supply Chain Bottlenecks"></textarea></label>
        <label for="wb-study-status">Initial status<select id="wb-study-status" name="status"><option value="queued">queued</option><option value="in-progress">in-progress</option><option value="published">published</option></select></label>
        {_cascading_atlas_select("wb-study", "Target")}
        <label class="wb-wide" for="wb-study-question">Core question &amp; hypotheses <small>(expands automatically as you type)</small><textarea id="wb-study-question" name="question" class="wb-auto-grow" rows="3" required maxlength="4000" placeholder="What hypothesis, mechanism, or distribution are we testing? Box grows automatically..."></textarea></label>
        <label class="wb-wide" for="wb-study-dataset">Data source / URL <small>(optional — leave blank to auto-search, or click your own site data chips below)</small><textarea id="wb-study-dataset" name="dataset" class="wb-auto-grow" rows="1" maxlength="1500" placeholder="Leave blank for LLM dataset discovery, click a site dataset below, or enter StatCan / BLS / CSV / URL"></textarea></label>
      </div>
      {site_data_presets}
      <div class="wb-scope-group" role="group" aria-label="Dataset search and Re-Study scope (Multi-Select)">
        <span class="wb-scope-heading">Dataset search &amp; Re-Study scope <small>(Multi-Select — toggle either or both)</small></span>
        <div class="wb-scope-pills">
          <label class="wb-scope-pill" for="wb-scope-new">
            <input type="checkbox" name="scopeNewDatasets" id="wb-scope-new" value="new" checked>
            <span class="wb-scope-check" aria-hidden="true">✓</span>
            <span class="wb-scope-copy">
              <strong>🌐 Look for New External Datasets <em class="wb-scope-tag">Default</em></strong>
              <small>Search StatCan, IEA, BLS, FRED, NREL, USGS &amp; peer-reviewed tables</small>
            </span>
          </label>
          <label class="wb-scope-pill" for="wb-scope-updated">
            <input type="checkbox" name="scopeUpdatedDatasets" id="wb-scope-updated" value="updated">
            <span class="wb-scope-check" aria-hidden="true">✓</span>
            <span class="wb-scope-copy">
              <strong>🗄️ Re-evaluate Updated / Internal Site Datasets <em class="wb-scope-tag">Site Logs</em></strong>
              <small>Cross-check Athletics, Calorie, Sleep, Smash Bros &amp; Basketball logs</small>
            </span>
          </label>
        </div>
      </div>
      <label class="wb-toggle" for="wb-study-run-now">
        <input id="wb-study-run-now" name="runNow" type="checkbox">
        <span class="wb-toggle-track" aria-hidden="true"><span class="wb-toggle-thumb"></span></span>
        <span class="wb-toggle-text"><strong>Run study right now upon adding</strong> <small>Prompts for Unlock Admin if locked, runs High-Thinking Gemini 4 Argon + Google Search + Pandas, and syncs across Mobile &amp; Web.</small></span>
      </label>
      <div class="wb-form-actions"><button class="button primary" type="submit" id="wb-study-submit">Save to Workbench +</button>
      <button class="button ghost" type="button" data-wb-auth-open>🔐 Unlock Admin</button>
      <button class="button ghost" type="button" data-wb-github="studyQueue">Open in GitHub Mobile ↗</button></div>
    </form>'''

    # 1B. Learn / Theory Queue (Foundations & Subsubsection Introductions from Scratch)
    theory_cat_options = "".join(f'<option value="{_e(c)}">{_e(c)}</option>' for c in THEORY_CATEGORIES)
    theory_tbody = "".join(
        f'<tr data-theory-row="{_e(t["id"])}"><th scope="row" class="wb-col-id"><code>{_e(t["id"])}</code></th>'
        f'<td class="wb-col-date">{_e(t["createdOn"])}</td>'
        f'<td><span class="wb-channel">{_e(t["category"])}</span></td>'
        f'<td><strong>{_e(t["title"])}</strong></td>'
        f'<td>{_node_link(prefix, t["atlasPath"])}</td>'
        f'<td>{_e(t["scopePrompt"])}</td>'
        f'<td>{_status_badge(t["status"])}</td>'
        f'<td><button class="button ghost wb-run-study-btn" type="button" '
        f'data-run-study-id="{_e(t["id"])}" '
        f'data-study-title="Theory: {_e(t["title"])}" '
        f'data-study-path="{_e(t["atlasPath"])}" '
        f'data-study-question="{_e(t["scopePrompt"])}" '
        f'data-study-dataset="First-principles textbook &amp; peer-reviewed theoretical derivation ({_e(t["category"])})">'
        f'{"↻ Re-Derive Theory" if t["status"] == "published" else "▶ Derive Theory Now"}</button></td></tr>'
        for t in data.get("theoryQueue", [])
    )
    theory_table = (
        '<div class="sports-table-wrap" role="region" aria-label="Learn and Theory queue" tabindex="0">'
        '<table id="workbench-theory-table"><caption>Learn / Theory Queue — First-Principles Foundations &amp; Subsubsection Introductions</caption>'
        '<thead><tr><th scope="col">ID</th><th scope="col">Date</th><th scope="col">Category</th>'
        '<th scope="col">Theory Topic</th><th scope="col">Destination</th><th scope="col">Derivation / Scope</th>'
        '<th scope="col">Status</th><th scope="col">Run</th></tr></thead>'
        f'<tbody id="wb-theory-body">{theory_tbody}</tbody></table></div>'
    )
    theory_form = f'''<form class="wb-form wb-snap-target" id="wb-theory-form" data-wb-table="theoryQueue">
      <div class="wb-form-head">
        <h3>02 · Learn / Theory: Introduce a subsubsection from scratch or derive first principles</h3>
        <span class="wb-auth-pill">Engineering Triad · Step 1: Theory</span>
      </div>
      <div class="wb-form-grid">
        <label for="wb-theory-category">Theory category <small>(default: General Introduction from Scratch)</small><select id="wb-theory-category" name="category">{theory_cat_options}</select></label>
        <label for="wb-theory-title">Theory module title <small>(auto-grows)</small><textarea id="wb-theory-title" name="title" class="wb-auto-grow" rows="1" required maxlength="500" placeholder="e.g. Introduction to Non-Equilibrium Thermodynamics &amp; Entropy Production"></textarea></label>
        {_cascading_atlas_select("wb-theory", "Theory")}
        <label class="wb-wide" for="wb-theory-scope">Foundational concepts &amp; equations to derive <small>(auto-expands)</small><textarea id="wb-theory-scope" name="scopePrompt" class="wb-auto-grow" rows="3" required maxlength="4000" placeholder="What laws, axioms, or mathematical derivations should this module build from scratch for the webpage and Mental Map?"></textarea></label>
      </div>
      <div class="wb-form-actions"><button class="button primary" type="submit">Save to Theory Queue +</button>
      <button class="button ghost" type="button" data-wb-github="theoryQueue">Open in GitHub Mobile ↗</button></div>
    </form>'''

    # 1C. Applications Queue (Connecting Theory to Real-World Engineering & Societal Benefit)
    app_domain_options = "".join(f'<option value="{_e(d)}">{_e(d)}</option>' for d in APPLICATION_DOMAINS)
    app_tbody = "".join(
        f'<tr data-app-row="{_e(a["id"])}"><th scope="row" class="wb-col-id"><code>{_e(a["id"])}</code></th>'
        f'<td class="wb-col-date">{_e(a["createdOn"])}</td>'
        f'<td><span class="wb-channel">{_e(a["domain"])}</span></td>'
        f'<td><strong>{_e(a["title"])}</strong></td>'
        f'<td>{_node_link(prefix, a["atlasPath"])}</td>'
        f'<td>{_e(a["systemDesign"])}</td>'
        f'<td>{_e(a["societalBenefit"])}</td>'
        f'<td>{_status_badge(a["status"])}</td>'
        f'<td><button class="button ghost wb-run-study-btn" type="button" '
        f'data-run-study-id="{_e(a["id"])}" '
        f'data-study-title="Application: {_e(a["title"])}" '
        f'data-study-path="{_e(a["atlasPath"])}" '
        f'data-study-question="Engineering Design: {_e(a["systemDesign"])} | Societal Benefit: {_e(a["societalBenefit"])}" '
        f'data-study-dataset="Engineering system benchmarks &amp; real-world deployment data ({_e(a["domain"])})">'
        f'{"↻ Re-Model Application" if a["status"] == "published" else "▶ Build Application Now"}</button></td></tr>'
        for a in data.get("applicationsQueue", [])
    )
    app_table = (
        '<div class="sports-table-wrap" role="region" aria-label="Engineering Applications queue" tabindex="0">'
        '<table id="workbench-apps-table"><caption>Applications Queue — How Fundamentals Apply to Real-World Systems &amp; Societal Benefit</caption>'
        '<thead><tr><th scope="col">ID</th><th scope="col">Date</th><th scope="col">Domain</th>'
        '<th scope="col">Application</th><th scope="col">Destination</th><th scope="col">System Design</th>'
        '<th scope="col">Societal Benefit</th><th scope="col">Status</th><th scope="col">Run</th></tr></thead>'
        f'<tbody id="wb-apps-body">{app_tbody}</tbody></table></div>'
    )
    app_form = f'''<form class="wb-form wb-snap-target" id="wb-app-form" data-wb-table="applicationsQueue">
      <div class="wb-form-head">
        <h3>03 · Applications: Connect theoretical fundamentals to real-world engineering &amp; societal benefit</h3>
        <span class="wb-auth-pill">Engineering Triad · Step 2: Application</span>
      </div>
      <div class="wb-form-grid">
        <label for="wb-app-domain">Engineering domain<select id="wb-app-domain" name="domain">{app_domain_options}</select></label>
        <label for="wb-app-title">Application title <small>(auto-grows)</small><textarea id="wb-app-title" name="title" class="wb-auto-grow" rows="1" required maxlength="500" placeholder="e.g. Solid-State Sensor Array for Urban Air Quality"></textarea></label>
        {_cascading_atlas_select("wb-app", "Application")}
        <label class="wb-wide" for="wb-app-design">System mechanism &amp; implementation <small>(auto-expands)</small><textarea id="wb-app-design" name="systemDesign" class="wb-auto-grow" rows="2" required maxlength="3000" placeholder="How do the physical/mathematical fundamentals get engineered into a working device, algorithm, or policy?"></textarea></label>
        <label class="wb-wide" for="wb-app-benefit">Positive benefit to society <small>(auto-expands)</small><textarea id="wb-app-benefit" name="societalBenefit" class="wb-auto-grow" rows="2" required maxlength="2000" placeholder="What concrete human, economic, environmental, or safety problem does this solve at scale?"></textarea></label>
      </div>
      <div class="wb-form-actions"><button class="button primary" type="submit">Save to Applications Queue +</button>
      <button class="button ghost" type="button" data-wb-github="applicationsQueue">Open in GitHub Mobile ↗</button></div>
    </form>'''

    # 2. Wishlist To-Do table
    todo_tbody = "".join(
        f'<tr><th scope="row"><code>{_e(t["id"])}</code></th><td>{_e(t["createdOn"])}</td>'
        f'<td><strong>{_e(t["title"])}</strong></td><td>{_e(t["category"])}</td>'
        f'<td><span class="wb-prio wb-prio-{_e(t["priority"])}">{_e(t["priority"])}</span></td>'
        f'<td>{_node_link(prefix, t["atlasPath"])}</td><td>{_status_badge(t["status"])}</td>'
        f'<td>{_e(t["notes"])}</td></tr>'
        for t in data["wishlistTodos"]
    )
    todo_table = (
        '<div class="sports-table-wrap" role="region" aria-label="Wishlist to-dos" tabindex="0">'
        '<table id="workbench-todos-table"><caption>To-Do &amp; Website Wishlist</caption>'
        '<thead><tr><th scope="col">ID</th><th scope="col">Date</th><th scope="col">Item</th>'
        '<th scope="col">Category</th><th scope="col">Priority</th><th scope="col">Destination</th>'
        '<th scope="col">Status</th><th scope="col">Notes</th></tr></thead>'
        f'<tbody id="wb-todos-body">{todo_tbody}</tbody></table></div>'
    )
    prio_options = "".join(f'<option value="{p}">{p}</option>' for p in TODO_PRIORITIES)
    todo_form = f'''<form class="wb-form wb-snap-target" id="wb-todo-form" data-wb-table="wishlistTodos">
      <h3>04 · Add a to-do or wishlist change</h3>
      <div class="wb-form-grid">
        <label class="wb-wide" for="wb-todo-title">Wishlist item <small>(auto-grows)</small><textarea id="wb-todo-title" name="title" class="wb-auto-grow" rows="1" required maxlength="600" placeholder="e.g. Add heart-rate zone overlay to Tempo Runs"></textarea></label>
        <label for="wb-todo-category">Category<select id="wb-todo-category" name="category"><option value="Website">Website</option><option value="Database">Database</option><option value="Studies">Studies</option><option value="Athletics">Athletics</option><option value="Automation">Automation</option></select></label>
        <label for="wb-todo-priority">Priority<select id="wb-todo-priority" name="priority">{prio_options}</select></label>
        {_cascading_atlas_select("wb-todo", "To-Do")}
        <label class="wb-wide" for="wb-todo-notes">Implementation notes <small>(auto-grows)</small><textarea id="wb-todo-notes" name="notes" class="wb-auto-grow" rows="2" maxlength="2000" placeholder="Optional schema or UI note"></textarea></label>
      </div>
      <div class="wb-form-actions"><button class="button primary" type="submit">Save to-do +</button>
      <button class="button ghost" type="button" data-wb-github="wishlistTodos">Open in GitHub Mobile ↗</button></div>
    </form>'''

    # 3. Spontaneous Rap Lyric Table
    bucket_names = dict(RAP_BUCKETS)
    bucket_options = "".join(f'<option value="{_e(slug)}">{_e(title)}</option>' for slug, title in RAP_BUCKETS)
    bucket_chips = '<div class="wb-bucket-bar" role="group" aria-label="Filter by Rap bucket">'
    bucket_chips += '<button class="wb-bucket-chip is-active" type="button" data-wb-bucket="all">All buckets</button>'
    for slug, title in RAP_BUCKETS:
        bucket_chips += f'<button class="wb-bucket-chip" type="button" data-wb-bucket="{_e(slug)}">{_e(title)}</button>'
    bucket_chips += "</div>"

    lyric_tbody = "".join(
        f'<tr data-bucket="{_e(r["bucket"])}"><th scope="row" class="wb-col-id"><code>{_e(r["id"])}</code></th>'
        f'<td class="wb-col-date">{_e(r["createdOn"])}</td>'
        f'<td><a href="{_e(prefix)}Language-and-Programming/Rap/{_e(r["bucket"])}/index.html">{_e(bucket_names.get(r["bucket"], r["bucket"]))} ↗</a></td>'
        f'<td><strong>{_e(r["title"])}</strong></td>'
        f'<td><pre class="wb-bars">{_e(r["bars"])}</pre></td>'
        f'<td>{_e(r["themeCue"])}</td><td>{_status_badge(r["status"])}</td></tr>'
        for r in data["rapLyrics"]
    )
    lyric_table = (
        '<div class="sports-table-wrap" role="region" aria-label="Spontaneous rap lyrics" tabindex="0">'
        '<table id="workbench-lyrics-table"><caption>Spontaneous Rap Lyric Table — routed by topic bucket</caption>'
        '<thead><tr><th scope="col">ID</th><th scope="col">Date</th><th scope="col">Topic bucket</th>'
        '<th scope="col">Title / hook</th><th scope="col">Bars</th><th scope="col">Theme / cue</th>'
        '<th scope="col">Status</th></tr></thead>'
        f'<tbody id="wb-lyrics-body">{lyric_tbody}</tbody></table></div>'
    )
    lyric_form = f'''<form class="wb-form wb-snap-target" id="wb-lyric-form" data-wb-table="rapLyrics">
      <h3>05 · Drop spontaneous bars into a topic bucket</h3>
      <div class="wb-form-grid">
        <label for="wb-lyric-bucket">Topic bucket<select id="wb-lyric-bucket" name="bucket" required>{bucket_options}</select></label>
        <label for="wb-lyric-title">Working title / hook<textarea id="wb-lyric-title" name="title" class="wb-auto-grow" rows="1" required maxlength="300" placeholder="e.g. Midnight Set / Chalk &amp; Chrome"></textarea></label>
        <label class="wb-wide" for="wb-lyric-bars">Bars <small>(auto-expands as you write)</small><textarea id="wb-lyric-bars" name="bars" class="wb-auto-grow" rows="4" required placeholder="Write or paste bars as they hit..."></textarea></label>
        <label class="wb-wide" for="wb-lyric-cue">Theme / beat cue<textarea id="wb-lyric-cue" name="themeCue" class="wb-auto-grow" rows="1" placeholder="e.g. 92 BPM boom-bap, pride vs. discipline"></textarea></label>
      </div>
      <div class="wb-form-actions"><button class="button primary" type="submit">Save bars to bucket +</button>
      <button class="button ghost" type="button" data-wb-github="rapLyrics">Send via GitHub Mobile ↗</button></div>
    </form>'''

    # 4. Voice Note Recorder -> Journal / Podcast (Transcripts & Journal entries Admin-protected!)
    channel_options = "".join(f'<option value="{_e(ch)}">{_e(ch)}</option>' for ch in VOICE_CHANNELS)
    voice_tbody = "".join(
        f'<tr><th scope="row" class="wb-col-id"><code>{_e(v["id"])}</code></th><td class="wb-col-date">{_e(v["createdOn"])}</td>'
        f'<td><span class="wb-channel">{_e(v["channel"])}</span></td>'
        f'<td><strong>{_e(v["title"])}</strong><small class="wb-sub">{_e(v["audioFormat"])}</small></td>'
        f'<td>{int(v["durationSeconds"])} s</td>'
        f'<td><div data-wb-admin-only hidden><p class="wb-transcript">{_e(v["transcript"])}</p><small class="wb-summary">Summary: {_e(v["summary"])}</small></div>'
        f'<span class="wb-badge wb-flat" data-wb-admin-locked-msg>🔒 Admin-protected journal log</span></td>'
        f'<td>{_node_link(prefix, v["atlasPath"])}</td><td>{_status_badge(v["status"])}</td></tr>'
        for v in data["voiceNotes"]
    )
    voice_gate = (
        '<div class="admin-gate-banner" data-wb-admin-locked-msg>'
        '<div><strong>🔒 Journal &amp; Voice Note Transcripts are Admin-Protected</strong>'
        '<p>Entry titles and durations are visible; full personal journal transcripts and summaries require Admin unlock (30-minute session across the site).</p></div>'
        '<button class="button primary" type="button" data-wb-auth-open>🔐 Unlock Admin (30m)</button></div>'
    )
    voice_table = (
        voice_gate
        + '<div class="sports-table-wrap" role="region" aria-label="Voice notes journal and podcast queue" tabindex="0">'
        '<table id="workbench-voice-table"><caption>Voice Notes → Journal &amp; Podcast Pipeline</caption>'
        '<thead><tr><th scope="col">ID</th><th scope="col">Date</th><th scope="col">Section</th>'
        '<th scope="col">Title &amp; format</th><th scope="col">Duration</th>'
        '<th scope="col">Transcript &amp; summary (Admin)</th><th scope="col">Destination</th><th scope="col">State</th></tr></thead>'
        f'<tbody id="wb-voice-body">{voice_tbody}</tbody></table></div>'
    )
    voice_form = f'''<form class="wb-form wb-snap-target" id="wb-voice-form" data-wb-table="voiceNotes">
      <h3>06 · Record or upload a voice note</h3>
      <p class="sports-note">Record straight from your phone or laptop microphone (Web Audio + live speech-to-text dictation when supported), or upload an <code>.m4a</code>, <code>.mp3</code> or <code>.wav</code> memo. Recordings stay local until you export or commit them.</p>
      <div class="wb-recorder" role="group" aria-label="Voice recorder controls">
        <button class="button primary" type="button" id="wb-rec-start">● Record voice note</button>
        <button class="button ghost" type="button" id="wb-rec-stop" disabled>■ Stop</button>
        <label class="button ghost wb-upload-btn" for="wb-rec-file">Upload audio file<input id="wb-rec-file" type="file" accept="audio/*" hidden></label>
        <span class="wb-rec-timer" id="wb-rec-timer" role="status" aria-live="polite">0:00 · ready</span>
        <audio id="wb-rec-audio" controls hidden></audio>
        <a class="button ghost" id="wb-rec-download" download="voice-note.webm" hidden>Download audio ↓</a>
      </div>
      <div class="wb-form-grid">
        <label for="wb-voice-channel">Journal / Audio channel<select id="wb-voice-channel" name="channel">{channel_options}</select></label>
        <label for="wb-voice-entry-title">Episode / entry title<textarea id="wb-voice-entry-title" name="title" class="wb-auto-grow" rows="1" required maxlength="300" placeholder="e.g. Post-Lift Thoughts on Macro &amp; AI"></textarea></label>
        <label for="wb-voice-duration">Duration (s)<input id="wb-voice-duration" name="durationSeconds" type="number" min="0" value="0" required></label>
        {_cascading_atlas_select("wb-voice", "Linked")}
        <label class="wb-wide" for="wb-voice-transcript">Transcript / journal text <small>(auto-expands · Admin-protected once saved)</small><textarea id="wb-voice-transcript" name="transcript" class="wb-auto-grow" rows="4" required placeholder="Live dictation fills this automatically, or paste/type your note..."></textarea></label>
        <label class="wb-wide" for="wb-voice-summary">One-line takeaway <small>(auto-expands)</small><textarea id="wb-voice-summary" name="summary" class="wb-auto-grow" rows="1" required placeholder="Short summary shown in the podcast/journal feed"></textarea></label>
      </div>
      <div class="wb-form-actions"><button class="button primary" type="submit">Save voice note +</button>
      <button class="button ghost" type="button" data-wb-github="voiceNotes">Send via GitHub Mobile ↗</button></div>
    </form>'''

    dialogs = auth_dialog_html() + '''
    <dialog class="request-dialog wb-dialog wb-run-dialog" id="wb-run-dialog" aria-labelledby="wb-run-title">
      <div class="request-form">
        <p class="eyebrow" id="wb-run-eyebrow">Live Study Runner · Findings &amp; LaTeX Article</p>
        <h2 id="wb-run-title">Running study…</h2>
        <p class="request-status" id="wb-run-status" role="status" aria-live="polite"></p>
        <div class="wb-run-key-bar" id="wb-run-key-bar" hidden>
          <label class="wb-run-key-label" for="wb-run-inline-key">
            <span>🔑 <strong>Connect your Google AI Studio Auth Key (<code>AQ....eQ3w</code>) to run with live Gemini 4 Argon tokens:</strong> Copy your key from <a href="https://aistudio.google.com/api-keys" target="_blank" rel="noopener">Google AI Studio ↗</a> and paste it below:</span>
            <span class="wb-run-key-row">
              <input id="wb-run-inline-key" type="password" autocomplete="off" placeholder="Paste your AQ....eQ3w key here (saved encrypted in browser)">
              <button class="button primary" type="button" id="wb-run-save-key">⚡ Save Key &amp; Run Gemini Argon</button>
            </span>
          </label>
        </div>
        <div class="wb-restudy-bar">
          <span><strong>Re-Study Data Scope (Multi-Select):</strong></span>
          <label class="wb-scope-pill"><input type="checkbox" id="wb-modal-scope-new" checked><span class="wb-scope-check" aria-hidden="true"></span><span>Look for New External Datasets (Default)</span></label>
          <label class="wb-scope-pill"><input type="checkbox" id="wb-modal-scope-updated"><span class="wb-scope-check" aria-hidden="true"></span><span>Re-evaluate Updated / Internal Site Datasets</span></label>
        </div>
        <div class="wb-run-dest-links" id="wb-run-dest-links" hidden></div>
        <div class="wb-run-visuals" id="wb-run-visuals" hidden></div>
        <div class="wb-run-summary" id="wb-run-summary"></div>
        <label class="request-wide" for="wb-run-tex"><span>Generated standalone LaTeX source (<code>.tex</code>)</span><textarea id="wb-run-tex" rows="12" readonly></textarea></label>
        <div class="request-actions">
          <button class="button ghost" type="button" id="wb-run-rerun">↻ Re-Study Deeper with Gemini Argon</button>
          <button class="button ghost" type="button" id="wb-run-download-py">Download Pandas .py ↓</button>
          <button class="button ghost" type="button" id="wb-run-download-csv">Download Data .csv ↓</button>
          <button class="button ghost" type="button" id="wb-run-download-tex">Download .tex ↓</button>
          <button class="button ghost" type="button" id="wb-run-copy-tex">Copy LaTeX</button>
          <button class="button primary" type="button" data-wb-dialog-close="wb-run-dialog">Done</button>
        </div>
      </div>
    </dialog>'''

    return f'''<main id="main-content" class="collection-page sports-page athletics-page workbench-page">
      <header class="sports-hero">
        <div class="sports-hero-copy">
          <p class="sports-kicker">Direct subpage · Engineering Triad Workbench <span>Theory · Application · Study</span></p>
          <h1>Theory first.<br>Apply &amp; <em>study.</em></h1>
          <p class="sports-deck">Built around the engineering triad: understand foundational <strong>Theory</strong> from first principles, engineer real-world <strong>Applications</strong>, and test empirical <strong>Studies</strong> with Pandas &amp; data — plus site to-dos, spontaneous rap bars, and voice memos.</p>
          <div class="toolbar">
            <a class="button primary" href="#wb-study-form" data-wb-jump="wb-study-form">01 · Add Study</a>
            <a class="button ghost" href="#wb-theory-form" data-wb-jump="wb-theory-form">02 · Learn / Theory</a>
            <a class="button ghost" href="#wb-app-form" data-wb-jump="wb-app-form">03 · Applications</a>
            <a class="button ghost" href="#wb-todo-form" data-wb-jump="wb-todo-form">04 · Add To-Do</a>
            <a class="button ghost" href="#wb-lyric-form" data-wb-jump="wb-lyric-form">05 · Drop Bars</a>
            <a class="button ghost" href="#wb-voice-form" data-wb-jump="wb-voice-form">06 · Record Voice</a>
          </div>
        </div>
        <aside class="wb-status-card" aria-label="Database status">
          <p class="eyebrow"><span class="status-dot"></span> Relational store active · <span data-wb-auth-indicator>🔒 Admin locked</span></p>
          <h2>7 tables · SQLite + Admin Gate</h2>
          <p>Backed by <code>records/workbench/workbench.db</code>. Click any 01–06 button to snap straight to its Add form, or press <strong>Unlock Admin</strong> to run Gemini 4 Argon, view submitter IP Indexes, and moderate rows.</p>
          <div class="wb-export-bar">
            <button class="button primary" type="button" data-wb-auth-open>🔐 Unlock Admin</button>
            <button class="button ghost" type="button" id="wb-export-json">Export local additions · JSON ↓</button>
            <button class="button ghost" type="button" id="wb-export-sql">Copy SQL INSERTs</button>
            <span class="wb-status-msg" id="wb-status-msg" role="status" aria-live="polite"></span>
          </div>
        </aside>
      </header>
      {metrics}
      {_section("01", "To study with data (Engineering Triad · Step 3)", "Add a study above, sort by Date or Visit Rank, and hover/tap any Study link to inspect or Re-Study.", "wb-studies-title",
                '<p>Each Study title below is an interactive PowerBI-style tooltip link: hover over it on desktop (or tap it on mobile) to view its target Atlas destination, full research question, visit count, Re-Study dataset scope (New Datasets and/or Updated Site Datasets), or <strong>▶ Run study now</strong> trigger. Adding a second study to an existing subsubsection automatically stacks a new Study Tab below the first one.</p>'
                + study_form + study_table)}
      {_section("02", "Learn / Theory queue (Engineering Triad · Step 1)", "Go deep into the foundational theory of any topic — or introduce an outlined subsubsection from scratch.", "wb-theory-section-title",
                '<p>Select <strong>General / Subsubsection Introduction</strong> when a destination in the Atlas or Mental Map is empty and needs a complete, first-principles introduction from scratch, or pick a focused derivation category to add deeper theoretical foundations below existing notes.</p>'
                + theory_form + theory_table)}
      {_section("03", "Applications queue (Engineering Triad · Step 2)", "See how theoretical fundamentals apply to real-world engineering systems and positive societal benefit.", "wb-apps-section-title",
                '<p>Bridge first principles and empirical data: document how physical, mathematical, or economic mechanisms are engineered into working devices, algorithms, or policies and quantify their benefit to society.</p>'
                + app_form + app_table)}
      {_section("04", "To-do & wish list", "Capture a website or research task first, then review the queue below.", "wb-todos-title",
                todo_form + todo_table)}
      {_section("05", "Spontaneous rap lyric table", "Drop bars straight into a topic bucket, then filter the archive below.", "wb-lyrics-title",
                lyric_form + bucket_chips + lyric_table)}
      {_section("06", "Voice note studio", "Record or upload a voice memo at the top, then browse the transcribed journal & podcast feed below.", "wb-voice-title",
                voice_form + voice_table)}
      <section class="sports-section sports-method" id="wb-pipeline" aria-labelledby="wb-pipeline-title">
        <p class="sports-kicker">07 / Zero-copy-paste mobile log sync &amp; SQLite architecture</p>
        <h2 id="wb-pipeline-title">Log daily on your phone in Google Docs — never copy-paste into Notepad again.</h2>
        <div class="wb-pipeline-grid">
          <article class="wb-pipe-card">
            <h3>1. Direct Google Docs Cloud Pull (Zero Copy-Paste)</h3>
            <p>Keep logging daily on your phone in the Google Docs app inside your <code>Logs</code> folder. Link each Google Doc URL once on any Athletics/Health page (no Admin needed) or via CLI:</p>
            <pre class="athletics-entry">python -B -m site_content.log_sync --set-doc weightlifting "https://docs.google.com/document/d/..."
python -B -m site_content.log_sync</pre>
            <p><code>log_sync</code> downloads the live plain text straight from Google Docs (or extracts <code>.docx</code> via <code>docx_to_txt</code>), repairs any paste/typo slips for 0 tokens, and updates both <code>records/</code> and <code>LiamMs_PandasProjects/</code>.</p>
          </article>
          <article class="wb-pipe-card">
            <h3>2. How SQLite Works on Static GitHub Pages (Limits &amp; Hybrid Sync)</h3>
            <p><code>records/workbench/workbench.db</code> is a true relational SQLite 3 database (up to 281 TB theoretical capacity, ACID transactions, zero-config single file). Because GitHub Pages serves static files without a persistent write-disk server, live visitor clicks and mobile form entries stage immediately in browser <code>localStorage</code> and merge with the canonical SQLite database on each build or export.</p>
            <pre class="athletics-entry">python -B -m site_content.workbench add-lyric --bucket Vagabond --title "Hook" --bars "..."</pre>
          </article>
        </div>
        <details class="wb-schema-details"><summary>Show the relational SQLite schema (<code>records/workbench/workbench.db</code>)</summary>
          <pre class="athletics-entry">{_e(data["schemaSql"])}</pre>
        </details>
        {_downloads(1, [
            ("workbench.json", "Workbench DB · JSON"),
            ("workbench-studies.csv", "Study queue · CSV"),
            ("workbench-todos.csv", "Wishlist to-dos · CSV"),
            ("workbench-lyrics.csv", "Rap lyrics · CSV"),
            ("workbench-voice.csv", "Voice notes · CSV"),
        ])}
      </section>
      {dialogs}
    </main>'''


def _traffic_ip_svg(traffic: list[dict[str, Any]]) -> str:
    """Horizontal bar chart of site visits and study clicks by anonymized IP Index (safe margins, zero text cutoff)."""
    height = 74 + len(traffic) * 36
    max_v = max(100, *(int(r["visits"]) for r in traffic))
    left, width = 235.0, 415.0
    parts = []
    for tick in (0, 25, 50, 75, 100):
        tx = left + (tick / max_v) * width
        parts.append(
            f'<line class="chart-grid" x1="{tx:.1f}" x2="{tx:.1f}" y1="28" y2="{height - 24}"/>'
            f'<text x="{tx:.1f}" y="18" text-anchor="middle">{tick}</text>'
        )
    for idx, row in enumerate(traffic):
        y = 36 + idx * 36
        v = int(row["visits"])
        c = int(row["studyClicks"])
        wv = (v / max_v) * width
        wc = (c / max_v) * width
        parts.append(
            f'<text x="{left - 10:.1f}" y="{y + 15:.1f}" text-anchor="end">{_e(row["ipIndex"])}</text>'
            f'<rect class="athletics-bar series-0" x="{left:.1f}" y="{y:.1f}" width="{wv:.1f}" height="20">'
            f'<title>{_e(row["ipIndex"])} ({_e(row["maskedIp"])}): {v} visits, {c} study clicks</title></rect>'
            f'<rect class="athletics-bar series-1" x="{left:.1f}" y="{y + 13:.1f}" width="{wc:.1f}" height="7">'
            f'<title>{_e(row["ipIndex"])}: {c} study interactions</title></rect>'
            f'<text class="athletics-label" x="{left + wv + 8:.1f}" y="{y + 15:.1f}">{v} visits · {c} clicks ({_e(row["role"])})</text>'
        )
    return _chart(
        "db-ip-traffic-chart",
        "Site traffic distribution by privacy-safe IP Index (visits vs. study interactions)",
        "Each bar plots total page visits (violet) and study interactions (cyan strip) per SHA-256 hashed IP Index stored in site_traffic (records/workbench/workbench.db).",
        "".join(parts),
        height=height,
    )


def _study_clicks_svg(studies: list[dict[str, Any]]) -> str:
    """Horizontal leaderboard of studies ranked by click / visit count (safe margins, zero text cutoff)."""
    ordered = sorted(studies, key=lambda s: int(s.get("clicks", 0)), reverse=True)
    height = 74 + len(ordered) * 36
    max_c = max(45, *(int(s.get("clicks", 0)) for s in ordered))
    left, width = 255.0, 410.0
    parts = []
    for tick in range(0, max_c + 1, 10):
        tx = left + (tick / max_c) * width
        parts.append(
            f'<line class="chart-grid" x1="{tx:.1f}" x2="{tx:.1f}" y1="28" y2="{height - 24}"/>'
            f'<text x="{tx:.1f}" y="18" text-anchor="middle">{tick} clicks</text>'
        )
    for idx, s in enumerate(ordered):
        y = 36 + idx * 36
        c = int(s.get("clicks", 0))
        w = (c / max_c) * width
        short_title = s["title"][:24] + ("…" if len(s["title"]) > 24 else "")
        cls = "series-1" if s["status"] == "published" else "series-2"
        parts.append(
            f'<text x="{left - 10:.1f}" y="{y + 15:.1f}" text-anchor="end">{_e(s["id"])} · {_e(short_title)}</text>'
            f'<rect class="athletics-bar {cls}" x="{left:.1f}" y="{y:.1f}" width="{w:.1f}" height="20">'
            f'<title>{_e(s["id"])} {_e(s["title"])}: {c} clicks ({_e(s["status"])})</title></rect>'
            f'<text class="athletics-label" x="{left + w + 8:.1f}" y="{y + 15:.1f}">Rank #{idx + 1} · {c} clicks ({_e(s["status"])})</text>'
        )
    return _chart(
        "db-study-clicks-chart",
        "Workbench study visit rank: clicks per study (sorted highest to lowest)",
        "Ranked click counts across all 7 studies in study_queue. Published studies (ST-01, ST-02, ST-06, ST-05) lead total engagement.",
        "".join(parts),
        height=height,
    )


def database_leaf_content(slug: str, data: dict[str, Any], root: str) -> tuple[str, str]:
    """Content injected into Database-Exploration and Relational-Database-Development atlas leaves."""
    summary = data["summary"]
    wb_href = _e(root + "Workbench/index.html")
    if slug == "Relational-Database-Development":
        lede = (
            f"Seven relational SQLite tables (study_queue, theory_queue, applications_queue, wishlist_todos, rap_lyrics, voice_notes, site_traffic) "
            f"backing the live Workbench at Workbench/index.html: {summary['studies']} studies, "
            f"{summary.get('theory', 3)} theory modules, and {summary.get('applications', 3)} applications."
        )
    else:
        lede = (
            "Exploring how a static GitHub Pages notebook pairs with a local SQLite relational store, "
            "live cross-device cloud sync, and mobile capture forms."
        )
    cards = (
        f'<section class="catalog" aria-labelledby="db-leaf-title">'
        f'<div class="catalog-head"><h2 id="db-leaf-title">Live Engineering Triad Database Workbench</h2>'
        f'<p class="catalog-rule"><strong>Direct access:</strong> Open the <a href="{wb_href}">Notebook Workbench (Workbench/index.html) ↗</a> '
        f'to add Theory, Application, or Study entries, wishlist tasks, spontaneous rap bars, or voice notes from desktop or phone.</p></div>'
        f'<pre class="catalog-code"><code>{_e(data["schemaSql"])}</code></pre></section>'
    )
    return lede, cards


def traffic_dashboard_body(data: dict[str, Any], prefix: str = "../") -> str:
    """Render the standalone Admin-only IP & Traffic Reflection page (Traffic/index.html)."""
    summary = data["summary"]
    traffic = data.get("siteTraffic", [])
    studies = data.get("studyQueue", [])
    wb_href = _e(prefix + "Workbench/index.html")

    # Plain KPI cards without tooltips for standalone reflection dashboards
    kpis = _metrics([
        ("Unique IP Indexes", str(summary.get("uniqueIpIndexes", 5)), "SHA-256 anonymized visitor IDs"),
        ("Logged site visits", str(summary.get("totalVisits", 181)), "Synced in site_traffic + browser telemetry"),
        ("Total study clicks", str(summary.get("studyClicksTotal", 169)), f"Across {summary['studies']} queued & published studies"),
        ("SQLite tables", "7 tables", "ACID relational store (workbench.db)"),
    ])
    traffic_rows = [
        [r["ipIndex"], r["maskedIp"], r["role"], str(r["visits"]), str(r["studyClicks"]), r["topSection"], r["lastSeen"]]
        for r in traffic
    ]
    study_rank_rows = [
        [f"#{idx + 1}", s["id"], s["title"], s["atlasPath"], str(s.get("clicks", 0)), s["status"]]
        for idx, s in enumerate(sorted(studies, key=lambda x: int(x.get("clicks", 0)), reverse=True))
    ]
    actions = (
        f'<a class="button primary" href="{wb_href}">Open Workbench ↗</a>'
        f'<a class="button ghost" href="{_e(prefix)}Completion/index.html">Map &amp; Site % Reflection ↗</a>'
        '<button class="button ghost" type="button" data-wb-auth-open>🔓 Admin Vault (30m)</button>'
    )
    art = (
        '<div class="athletics-split-card" aria-hidden="true">'
        f'<span class="split-Back"><strong>{summary.get("uniqueIpIndexes", 5)}</strong>IP Indexes</span>'
        f'<span class="split-Chest"><strong>{summary.get("totalVisits", 181)}</strong>total visits</span>'
        f'<span class="split-Shoulders"><strong>{summary.get("studyClicksTotal", 169)}</strong>study clicks</span></div>'
    )
    gate = (
        '<section class="sports-section" data-wb-admin-locked-msg>'
        '<div class="admin-gate-banner">'
        '<div><strong>🔒 Owner Reflection Dashboard · Admin Login Required</strong>'
        '<p>This standalone IP &amp; Traffic reflection page is private to the site owner. Unlock Admin from the main page or click below (valid for 30 minutes across all branches of the site).</p></div>'
        '<button class="button primary" type="button" data-wb-auth-open>🔐 Unlock Admin (30 min)</button>'
        '</div></section>'
    )
    return f'''<main id="main-content" class="collection-page sports-page athletics-page workbench-page">
      {_hero("Owner Reflection · Admin Only", "IP & Traffic Telemetry", "Who is exploring,<br>and <em>what</em> they read.",
             "Private owner telemetry tracking anonymized visitor IP Indexes, section engagement, and study visit ranks across desktop and mobile.", actions, art)}
      {gate}
      <div data-wb-admin-only hidden>
        <p class="sports-scope">Admin Session Active (30-minute window across site branches) · Backed by <code>site_traffic</code> &amp; <code>study_queue</code> in <code>records/workbench/workbench.db</code>.</p>
        {kpis}
        {_section("01", "Visitor IP Index distribution", "Page visits and study interactions by privacy-safe SHA-256 IP Index.", "traffic-ip-title",
                  '<p class="sports-legend"><span class="series-0">■ Total Page Visits</span><span class="series-1">■ Study Clicks &amp; Runs</span></p>'
                  + _traffic_ip_svg(traffic)
                  + _table("Visitor distribution by anonymized IP Index (site_traffic table in records/workbench/workbench.db).",
                           ["IP Index", "Masked Network / Region", "Role", "Visits", "Study Clicks", "Most Visited Section", "Last Active"],
                           traffic_rows, "db-traffic-table"))}
        {_section("02", "Study visit rank leaderboard", "Which studies draw the most clicks and deep reads.", "traffic-study-title",
                  '<p class="sports-legend"><span class="series-1">■ Published Flagship Study</span><span class="series-2">■ Queued / In-Progress Study</span></p>'
                  + _study_clicks_svg(studies)
                  + _table("Study click leaderboard (powers the Visit Rank sort in Workbench).",
                           ["Rank", "ID", "Study Title", "Destination", "Clicks", "Status"],
                           study_rank_rows, "db-study-rank-table"))}
        {_section("03", "SQLite architecture & static hosting limits", "How workbench.db and live browser telemetry work together.", "traffic-sqlite-title",
                  '<p>SQLite 3 stores all 7 tables in a single binary file (<code>records/workbench/workbench.db</code>, supporting up to 281 TB and full ACID SQL joins). '
                  'Because GitHub Pages is a read-only static CDN without a server-side filesystem lock, live browser visits and mobile study runs sync across devices via the live JSON cloud relay and merge into <code>workbench.db</code> on build.</p>'
                  f'<pre class="athletics-entry">{_e(data["schemaSql"])}</pre>')}
      </div>
      {auth_dialog_html()}
    </main>'''


def site_completion_dashboard_content(root: Path, prefix: str = "../") -> tuple[str, str]:
    """Compute and render the Mental Map & 6 × 6 × 6 Site Completion Reflection content."""
    tex_path = root / "mental_map.tex"
    raw_tex = tex_path.read_text(encoding="utf-8") if tex_path.is_file() else ""
    body_tex = raw_tex.split(r"\begin{document}", 1)[1].rsplit(r"\end{document}", 1)[0] if r"\begin{document}" in raw_tex else raw_tex

    # IMPORTANT: Split by "% atlas: <path>" BEFORE stripping % comments so all 258 markers are preserved!
    raw_parts = re.split(r"(?m)^% atlas: (\S+)\s*$", body_tex)
    sec_bodies: dict[str, str] = {}
    for i in range(1, len(raw_parts) - 1, 2):
        sec_bodies[raw_parts[i].strip()] = re.sub(r"(?<!\\)%[^\n]*", "", raw_parts[i + 1])

    active_tex = re.sub(r"(?<!\\)%[^\n]*", "", body_tex)
    prose_words = re.findall(r"[A-Za-z]{2,}", re.sub(r"\\[A-Za-z@]+", " ", active_tex))
    total_words = len(prose_words)
    display_eqs = len(re.findall(r"\\begin\{(?:equation|align)\}|\\\[", active_tex))
    inline_eqs = len(re.findall(r"(?<!\\)\$[^$\n]+?(?<!\\)\$", active_tex))
    total_formulae = display_eqs + inline_eqs
    total_figures = len(re.findall(r"\\includegraphics", active_tex))
    total_headings = len(re.findall(r"\\(?:sub){0,3}section\*?\{", active_tex))

    field_stats: list[dict[str, Any]] = []
    topic_rows: list[list[str]] = []
    total_leaves = 0
    total_mm_filled = 0
    total_tab_live = 0
    total_active_any = 0

    for field_node in ATLAS_ROOT.children:
        leaves = [leaf for topic in field_node.children for leaf in topic.children]
        n_leaves = len(leaves)
        mm_filled = 0
        tab_live = 0
        active_any = 0
        f_words = 0
        f_eqs = 0
        topic_items: list[dict[str, Any]] = []
        for topic_node in field_node.children:
            t_mm = 0
            t_tab = 0
            t_act = 0
            t_words = len(re.findall(r"[A-Za-z]{2,}", re.sub(r"\\[A-Za-z@]+", " ", sec_bodies.get(topic_node.path, ""))))
            t_eqs = 0
            leaf_items: list[dict[str, Any]] = []
            for leaf in topic_node.children:
                sec_txt = sec_bodies.get(leaf.path, "")
                has_mm_notes = bool(sec_txt.strip()) and ("Open for notes: this destination is outlined" not in sec_txt)
                has_live_tab = (leaf.path in HOSTED) or (leaf.path in FEATURES)
                l_words = len(re.findall(r"[A-Za-z]{2,}", re.sub(r"\\[A-Za-z@]+", " ", sec_txt)))
                l_eqs = len(re.findall(r"\\begin\{(?:equation|align)\}|\\\[|(?<!\\)\$[^$\n]+?(?<!\\)\$", sec_txt))
                t_words += l_words
                t_eqs += l_eqs
                if has_mm_notes:
                    mm_filled += 1
                    t_mm += 1
                if has_live_tab:
                    tab_live += 1
                    t_tab += 1
                if has_mm_notes or has_live_tab:
                    active_any += 1
                    t_act += 1
                leaf_items.append({
                    "title": leaf.title,
                    "path": leaf.path,
                    "mm": 1 if has_mm_notes else 0,
                    "tab": 1 if has_live_tab else 0,
                    "active": 1 if (has_mm_notes or has_live_tab) else 0,
                    "activePct": 100.0 if (has_mm_notes or has_live_tab) else 0.0,
                    "words": l_words,
                    "eqs": l_eqs,
                })
            f_words += t_words
            f_eqs += t_eqs
            topic_items.append({
                "title": topic_node.title,
                "fieldTitle": field_node.title,
                "path": topic_node.path,
                "leaves": 6,
                "mmFilled": t_mm,
                "mmPct": round(t_mm / 6 * 100, 1),
                "tabLive": t_tab,
                "tabPct": round(t_tab / 6 * 100, 1),
                "activeAny": t_act,
                "activePct": round(t_act / 6 * 100, 1),
                "words": t_words,
                "eqs": t_eqs,
                "children": leaf_items,
            })
            topic_rows.append([
                f"{field_node.title} · {topic_node.title}",
                f"{t_mm} / 6",
                f"{t_tab} / 6",
                f"{t_act} / 6 ({round(t_act / 6 * 100)}%)",
                f"{t_words:,} words",
                f"{t_eqs} eqs",
            ])
        total_leaves += n_leaves
        total_mm_filled += mm_filled
        total_tab_live += tab_live
        total_active_any += active_any
        field_stats.append({
            "title": field_node.title,
            "path": field_node.path,
            "leaves": n_leaves,
            "mmFilled": mm_filled,
            "mmPct": round(mm_filled / n_leaves * 100, 1),
            "tabLive": tab_live,
            "tabPct": round(tab_live / n_leaves * 100, 1),
            "activeAny": active_any,
            "activePct": round(active_any / n_leaves * 100, 1),
            "words": f_words,
            "eqs": f_eqs,
            "topics": topic_items,
        })

    overall_pct = round(total_active_any / max(1, total_leaves) * 100, 1)
    mm_pct = round(total_mm_filled / max(1, total_leaves) * 100, 1)
    tab_pct = round(total_tab_live / max(1, total_leaves) * 100, 1)

    # Non-clipping SVG Chart of 6 Fields Completion % (left = 235, width = 415 -> max bar x = 650, 250px right margin for labels!)
    height = 82 + len(field_stats) * 40
    left, width = 235.0, 415.0
    svg_parts = []
    for tick in (0, 25, 50, 75, 100):
        tx = left + (tick / 100.0) * width
        svg_parts.append(
            f'<line class="chart-grid" x1="{tx:.1f}" x2="{tx:.1f}" y1="30" y2="{height - 26}"/>'
            f'<text x="{tx:.1f}" y="20" text-anchor="middle">{tick}%</text>'
        )
    for idx, st in enumerate(field_stats):
        y = 38 + idx * 40
        w_act = (st["activePct"] / 100.0) * width
        w_mm = (st["mmPct"] / 100.0) * width
        svg_parts.append(
            f'<text x="{left - 12:.1f}" y="{y + 15:.1f}" text-anchor="end">{_e(st["title"])}</text>'
            f'<rect class="athletics-bar series-1" x="{left:.1f}" y="{y:.1f}" width="{w_act:.1f}" height="21">'
            f'<title>{_e(st["title"])}: {st["activeAny"]}/{st["leaves"]} destinations active ({st["activePct"]}%)</title></rect>'
            f'<rect class="athletics-bar series-0" x="{left:.1f}" y="{y + 14:.1f}" width="{w_mm:.1f}" height="7">'
            f'<title>{_e(st["title"])} Mental Map notes filled: {st["mmFilled"]}/{st["leaves"]} ({st["mmPct"]}%)</title></rect>'
            f'<text class="athletics-label" x="{left + w_act + 8:.1f}" y="{y + 15:.1f}">{st["activePct"]:.1f}% ({st["activeAny"]}/36 · {st["mmFilled"]} MM · {st["tabLive"]} tabs)</text>'
        )
    comp_chart = (
        f'<div class="bi-completion-host" data-bi-completion="{_e(json.dumps(field_stats, separators=(",", ":")))}">'
        + _chart(
            "site-completion-fields-chart",
            "6 × 6 × 6 Atlas & Mental Map completion across all 6 fields (% of 36 subsubsections active)",
            "Cyan bars show combined active coverage (subsubsections with either authored Mental Map notes or a live interactive dashboard/tab); violet strip shows Mental Map prose/equation coverage.",
            "".join(svg_parts),
            height=height,
        )
        + "</div>"
    )

    # Plain KPI cards without tooltips for standalone reflection dashboards
    kpis = _metrics([
        ("Mental Map words & math", f"{_num(total_words)} words", f"{_num(total_formulae)} formulae ({display_eqs} display + {inline_eqs} inline) · {total_figures} figures"),
        ("Active subsubsections", f"{total_active_any} / {total_leaves} ({overall_pct}%)", f"{total_mm_filled} with Mental Map notes ({mm_pct}%) · {total_tab_live} with live tabs ({tab_pct}%)"),
        ("Engineering Triad modules", "5 Studies · 3 Theory · 3 Apps", "8 compiled Tectonic PDFs + 16 interactive dashboards"),
        ("Total built site pages", "285 pages", "259 Atlas nodes + 24 redirects + Workbench + Updates + 2 Reflections"),
    ])

    field_rows = [
        [
            st["title"],
            f'{st["leaves"]}',
            f'{st["mmFilled"]} / {st["leaves"]} ({st["mmPct"]:.1f}%)',
            f'{st["tabLive"]} / {st["leaves"]} ({st["tabPct"]:.1f}%)',
            f'{st["activeAny"]} / {st["leaves"]} ({st["activePct"]:.1f}%)',
            f'{st["leaves"] - st["activeAny"]} outlined',
        ]
        for st in field_stats
    ]

    inventory_rows = [
        ["Mental Map LaTeX Notebook (mental_map.tex)", f"{_num(total_words)} words · {_num(total_formulae)} equations", f"{total_headings} headings · {total_figures} figures", "Mental-Map/index.html"],
        ["Flagship Empirical Studies (Pandas + SVG + PDF)", "4 live studies + 3 queued (ST-01 to ST-07)", "Macro AI Iceberg, Alberta 2026, Gas Collusion, Sodium Batteries", "Workbench/index.html"],
        ["Athletics & Health Telemetry Dashboards", "5 live SVG dashboards + 3 LaTeX overviews", "Running, Tempo, Swimming, Weightlifting, Sleep/Dreams, Diet/Calories", "Gaming-and-Performance-Log/index.html"],
        ["Smash Bros & First-to-Four Sports Analytics", "86 fighter models + 13 basketball series (73 rounds)", "Rank Atlas, Score Atlas, Opponent Profiles, Series Scrubber, Rules PDF", "Smash/index.html"],
        ["Language, Rap Catalog & LeetCode Explorers", "6 Rap bucket catalogs + 6 LeetCode topic catalogs", "Vocabulary MATTR-50, Feelings Wheel, AST Symbol Index", "Language-and-Programming/index.html"],
        ["Relational SQLite Workbench (workbench.db)", "7 tables (Theory, Application, Study, Todo, Rap, Voice, Traffic)", "Unlock Admin gate, IP Index moderation, Google Docs 0-token sync", "Workbench/index.html"],
    ]

    lede = (
        f"Live completion telemetry across the 6 × 6 × 6 outline (216 subsubsections): "
        f"{_num(total_words)} Mental Map words, {_num(total_formulae)} mathematical formulae, "
        f"and {total_active_any} of {total_leaves} destinations ({overall_pct}%) populated with notes or interactive tabs."
    )
    html = (
        f'{kpis}'
        f'{_section("01", "Field completion overview", "How much of each 36-destination field is populated in the Mental Map and on the website.", "comp-fields-title", "<p class=\"sports-legend\"><span class=\"series-1\">■ Combined Active Subsubsections (Mental Map or Live Tab)</span><span class=\"series-0\">■ Authored Mental Map Notes &amp; Equations</span></p>" + comp_chart + _table("Completion breakdown across the 6 primary fields (36 leaf subsubsections per field = 216 total).", ["Field (6 × 6 = 36 leaves)", "Subsubsections", "Mental Map Notes Filled", "Live Interactive Tabs / Readers", "Combined Active Coverage", "Remaining Outlined"], field_rows, "site-completion-table"))}'
        f'{_section("02", "All 36 subsections (6 × 6 topics)", "Granular word count, formula count, and leaf completion across every topic branch.", "comp-topics-title", _table("Granular completion across all 36 subsections (6 leaves per subsection).", ["Field · Subsection", "Mental Map Leaves", "Live Tab Leaves", "Combined Active", "Words in Branch", "Formulae in Branch"], topic_rows, "site-topics-completion-table"))}'
        f'{_section("03", "Site modules, studies & tools inventory", "Every major system, simulator, PDF, and explorer live in the notebook.", "comp-inventory-title", _table("Inventory of studies, tools, simulators, PDFs, and interactive explorers across the site.", ["System / Module", "Scale & Equations", "Included Dashboards & Tools", "Primary Route"], inventory_rows, "site-inventory-table"))}'
    )
    return lede, html


def completion_dashboard_body(root: Path, prefix: str = "../") -> str:
    """Render the standalone Admin-only Map & Site % Reflection page (Completion/index.html)."""
    lede, inner_html = site_completion_dashboard_content(root, prefix)
    actions = (
        f'<a class="button primary" href="{_e(prefix)}Workbench/index.html">Open Workbench ↗</a>'
        f'<a class="button ghost" href="{_e(prefix)}Mental-Map/index.html">Open Mental Map ↗</a>'
        f'<a class="button ghost" href="{_e(prefix)}Traffic/index.html">IP &amp; Traffic Reflection ↗</a>'
    )
    art = (
        '<div class="athletics-split-card" aria-hidden="true">'
        '<span class="split-Back"><strong>84/216</strong>active leaves (38.9%)</span>'
        '<span class="split-Chest"><strong>1,044</strong>LaTeX formulae</span>'
        '<span class="split-Shoulders"><strong>45.2k</strong>notebook words</span></div>'
    )
    gate = (
        '<section class="sports-section" data-wb-admin-locked-msg>'
        '<div class="admin-gate-banner">'
        '<div><strong>🔒 Owner Reflection Dashboard · Admin Login Required</strong>'
        '<p>This standalone Mental Map &amp; 6 × 6 × 6 Site Completion reflection page is private to the site owner. Unlock Admin from the main page or click below (valid for 30 minutes across all branches of the site).</p></div>'
        '<button class="button primary" type="button" data-wb-auth-open>🔐 Unlock Admin (30 min)</button>'
        '</div></section>'
    )
    return f'''<main id="main-content" class="collection-page sports-page athletics-page workbench-page">
      {_hero("Owner Reflection · Admin Only", "Map & Site % Telemetry", "How much is built,<br>and what comes <em>next.</em>",
             lede, actions, art)}
      {gate}
      <div data-wb-admin-only hidden>
        <p class="sports-scope">Admin Session Active (30-minute window across site branches) · Computed directly from <code>mental_map.tex</code> and the 259-node site tree.</p>
        {inner_html}
      </div>
      {auth_dialog_html()}
    </main>'''


def updates_dashboard_body(root: Path, athletics: dict[str, Any], health: dict[str, Any], prefix: str = "../") -> str:
    """Render the standalone Google Docs & Site Integration Update Hub (Updates/index.html)."""
    gdoc_map_path = root / "records/workbench/gdoc_sources.json"
    saved_map: dict[str, str] = {}
    if gdoc_map_path.is_file():
        try:
            saved_map = json.loads(gdoc_map_path.read_text(encoding="utf-8"))
        except Exception:
            saved_map = {}

    def _gdoc_url(k: str, fallback_id: str) -> str:
        raw_id = saved_map.get(k, fallback_id)
        if not raw_id:
            return ""
        return raw_id if raw_id.startswith("http") else f"https://docs.google.com/document/d/{raw_id}/edit"

    weight_url = _gdoc_url("weightlifting", "1mboHEkA2jzHEbJY0mcuXbP-N_cWfyaN-LiN2z8xueq0")
    running_url = _gdoc_url("running", "1RDyIJPISvIbaM4f-EoBlpVi99kGVZ81fRUKOmzYTJXA")
    tempo_url = _gdoc_url("tempo", "1kaKlOi_fPPrxHyCwf-G3nP93TkC-aPLT5Y-7b776Pmo")
    swim_url = _gdoc_url("swimming", "1wRNnr8kl4ccqGtSn9_G5Y79UFcv3aEn02r_GJ90uY8s")
    sleep_url = _gdoc_url("sleep", "1UMa-zXddL1PCfasksWie27N00IBfWEBUiDq9UDLTJ4w")
    diet_url = _gdoc_url("diet", "1q0g1iAhzHCSrEL0nxUQfW3FjZw5qJ8uj70WPVH2i5Ug")
    mm_url = _gdoc_url("mental_map", "15YE6fyNMoGA9JZlQnkiBG4rGtn4h4cP5gauPV2Wf_rw")

    docs_spec = [
        (
            "weightlifting",
            "01 · Weightlifting Log",
            "records/athletics/weightlifting/Weightlifting_Log.txt",
            f"{prefix}Gaming-and-Performance-Log/Athletics/Weightlifting/index.html",
            athletics["weightlifting"]["summary"]["lastDate"],
            f"{athletics['weightlifting']['summary']['sessions']} sessions · {athletics['weightlifting']['summary']['sets']} working sets · {_num(athletics['weightlifting']['summary']['volume'])} lb volume",
            weight_url,
            "\n".join(athletics["weightlifting"]["source"]["latestEntry"][:8]),
        ),
        (
            "running",
            "02 · Running Interval Log (I1 Loop)",
            "records/athletics/running/Interval_Data.txt",
            f"{prefix}Gaming-and-Performance-Log/Athletics/Running/index.html",
            athletics["running"]["summary"]["lastDate"],
            f"{athletics['running']['summary']['sessions']} interval sessions · {athletics['running']['summary']['intervals']} loops",
            running_url,
            "\n".join(athletics["running"]["source"]["latestEntry"][:6]),
        ),
        (
            "tempo",
            "03 · Running Tempo Log",
            "records/athletics/running/Tempo_Run_Log.txt",
            f"{prefix}Gaming-and-Performance-Log/Athletics/Running/index.html#running-tempo",
            athletics["tempo"]["summary"]["lastDate"],
            f"{athletics['tempo']['summary']['runs']} tempo runs · {athletics['tempo']['summary']['kilometres']} km total",
            tempo_url,
            "\n".join(athletics["tempo"]["source"]["latestEntry"][:5]),
        ),
        (
            "swimming",
            "04 · Swimming Log",
            "records/athletics/swimming/Swimming_Log.txt",
            f"{prefix}Gaming-and-Performance-Log/Athletics/Swimming/index.html",
            athletics["swimming"]["summary"]["lastDate"],
            f"{athletics['swimming']['summary']['sessions']} swim sessions · {_num(athletics['swimming']['summary']['meters'])} m total",
            swim_url,
            "\n".join(athletics["swimming"]["source"]["latestEntry"][:4]),
        ),
        (
            "sleep",
            "05 · Sleep & Dream Log (Dreams Admin-Protected)",
            "records/health/sleep/Sleep_and_Dream_Log.txt",
            f"{prefix}Gaming-and-Performance-Log/Health/Sleep/index.html",
            health["sleep"]["summary"]["lastDate"],
            f"{health['sleep']['summary']['nights']} nights · {health['sleep']['summary']['averageHours']} h avg · {health['sleep']['summary']['dreams']} dreams",
            sleep_url,
            "🔒 Dream text Admin-protected (unlock Admin to preview raw dream entry)",
        ),
        (
            "diet",
            "06 · Diet & Calorie Tracking Log",
            "records/health/diet/Diet_and_Calorie_Tracking.txt",
            f"{prefix}Gaming-and-Performance-Log/Health/Diet/index.html",
            health["diet"]["summary"]["lastDate"],
            f"{health['diet']['summary']['days']} days tracked · {health['diet']['summary']['averageDeficit']:+d} kcal/day avg deficit",
            diet_url,
            "\n".join(health["diet"]["source"]["latestEntry"][:6]),
        ),
        (
            "mental_map",
            "07 · Mental Map & Journal Drafts Google Doc",
            "mental_map.tex / Workbench Study Queue",
            f"{prefix}Mental-Map/index.html",
            "2026-10-27",
            "Sync study notes, LaTeX subsections, or reading notes from any Google Doc into Workbench & Mental Map",
            mm_url,
            "% atlas: Business-and-Economics/Macroeconomics/Fiscal-Policy (ST-09 synced)",
        ),
    ]

    cards_html = []
    for key, title, repo_path, dash_href, last_date, stats_note, default_url, latest_preview in docs_spec:
        cards_html.append(
            f'<article class="gdoc-sync-box wb-pipe-card" data-gdoc-sync="{_e(key)}" data-gdoc-last-date="{_e(last_date)}" data-gdoc-default-url="{_e(default_url)}">'
            f'<div class="gdoc-sync-head">'
            f'<div><span class="eyebrow">{_e(repo_path)}</span><h3 style="margin:2px 0 4px;">{_e(title)}</h3>'
            f'<small class="gdoc-sync-sub">Built through <strong>{_e(last_date)}</strong> · {_e(stats_note)}</small></div>'
            f'<div class="wb-form-actions">'
            f'<button class="button primary gdoc-refresh-btn" type="button" data-gdoc-refresh-btn="{_e(key)}">↻ Check &amp; Update Now (0 Tokens)</button>'
            f'<a class="button ghost" href="{_e(dash_href)}">Open Dashboard ↗</a>'
            f'</div></div>'
            f'<div class="gdoc-sync-controls">'
            f'<label for="gdoc-url-{_e(key)}">Google Doc share URL or ID for <code>{_e(key)}</code> (Ensure Doc sharing is set to <strong>"Anyone with the link: Viewer"</strong> for browser sync):</label>'
            f'<div class="gdoc-sync-row">'
            f'<input id="gdoc-url-{_e(key)}" type="url" value="{_e(default_url)}" placeholder="Paste https://docs.google.com/document/d/... link from your Drive Logs folder">'
            f'<button class="button ghost" type="button" data-gdoc-save-btn="{_e(key)}">Save Link</button>'
            f'</div>'
            f'<p class="gdoc-sync-status" id="gdoc-status-{_e(key)}" role="status" aria-live="polite">'
            f'Ready · Built through {_e(last_date)}. Click "Check &amp; Update Now" or "Update ALL Docs" above.'
            f'</p>'
            f'<details class="wb-schema-details"><summary>Preview latest synced entry ({_e(last_date)})</summary>'
            f'<pre class="athletics-entry" id="gdoc-preview-{_e(key)}">{_e(latest_preview)}</pre></details>'
            f'</div></article>'
        )

    kpis = _metrics([
        ("Connected log streams", "7 Google Docs", "All 6 Athletics/Health logs + Journal/Mental Map linked"),
        ("Athletics live sync", f"Lift {athletics['weightlifting']['summary']['lastDate'][5:]} · Swim {athletics['swimming']['summary']['lastDate'][5:]}", f"{athletics['weightlifting']['summary']['sessions']} lifts · {athletics['swimming']['summary']['sessions']} swims · {athletics['tempo']['summary']['runs']} tempo runs"),
        ("Health live sync", f"Diet {health['diet']['summary']['lastDate'][5:]} · Sleep {health['sleep']['summary']['lastDate'][5:]}", f"{health['diet']['summary']['days']} diet days · {health['sleep']['summary']['nights']} sleep nights"),
        ("Token cost & commit", "0 API tokens", "Deterministic regex + GitHub API / CLI sync"),
    ])

    actions = (
        '<button class="button primary" type="button" id="gdoc-sync-all-btn">⚡ Update &amp; Sync ALL Connected Docs Now (0 Tokens)</button>'
        '<button class="button ghost" type="button" id="gdoc-commit-all-btn">☁ Commit Synced Logs to GitHub Repo</button>'
        f'<a class="button ghost" href="{_e(prefix)}Workbench/index.html">Open Workbench ↗</a>'
    )
    art = (
        '<div class="athletics-split-card" aria-hidden="true">'
        '<span class="split-Back"><strong>7 Docs</strong>all linked</span>'
        '<span class="split-Chest"><strong>Oct 28</strong>logs synced</span>'
        '<span class="split-Shoulders"><strong>0 tok</strong>deterministic</span></div>'
    )
    return f'''<main id="main-content" class="collection-page sports-page athletics-page workbench-page">
      {_hero("Google Drive & Site Integration Hub", "Zero-Token Log & Document Updater", "Update every doc,<br>in <em>one</em> click.",
             "Centralized update center for all Google Docs integrated into your portfolio — Weightlifting, Running, Tempo, Swimming, Sleep & Dreams, Diet & Calories, and Mental Map drafts.",
             actions, art)}
      <p class="sports-scope" id="gdoc-sync-all-status" role="status" aria-live="polite">All 7 Google Docs linked &amp; synced · Weightlifting (<strong>{_e(athletics["weightlifting"]["summary"]["lastDate"])}</strong>, {athletics["weightlifting"]["summary"]["sessions"]} sessions) · Swimming (<strong>{_e(athletics["swimming"]["summary"]["lastDate"])}</strong>, {athletics["swimming"]["summary"]["sessions"]} sessions) · Tempo (<strong>{_e(athletics["tempo"]["summary"]["lastDate"])}</strong>, {athletics["tempo"]["summary"]["runs"]} runs) · Sleep (<strong>{_e(health["sleep"]["summary"]["lastDate"])}</strong>, {health["sleep"]["summary"]["nights"]} nights) · Diet (<strong>{_e(health["diet"]["summary"]["lastDate"])}</strong>, {health["diet"]["summary"]["days"]} days).</p>
      {kpis}
      {_section("01", "All integrated Google Docs", "Link or update any document individually, or click 'Update & Sync ALL Connected Docs Now' above.", "updates-docs-title",
                '<div class="wb-pipeline-grid" style="grid-template-columns:1fr;gap:18px;">' + "".join(cards_html) + '</div>')}
      {_section("02", "CLI & automated GitHub Actions sync", "How zero-token deterministic repair + cloud compilation work end-to-end.", "updates-cli-title",
                '<p>When you log workouts or notes on your phone in Google Docs, the deterministic parser repairs common mobile typing slips at <strong>0 token cost</strong> — including missing colons/semicolons after exercise names (<code>Incline Dumbbell Press 10x40lbs</code>), dash or comma separators (<code>Barbell Press - 25x45lbs</code>, <code>Seated Cable Rows, 15x58lbs</code>), singular <code>lb</code> units, month headers (<code>September 2026</code>), and year typos (<code>10/25/2025</code> after <code>10/24/2026</code>).</p>'
                '<pre class="athletics-entry">python -B -m site_content.log_sync &amp;&amp; python -B -m site_content.build --also-local</pre>')}
      {auth_dialog_html()}
    </main>'''
