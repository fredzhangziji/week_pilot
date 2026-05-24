"""Shared CSS for the Streamlit UI."""

from __future__ import annotations

import streamlit as st


def inject_styles() -> None:
    """Inject restrained workbench styling."""

    st.markdown(
        """
<style>
:root {
  --wp-bg: #f7f8fb;
  --wp-surface: #ffffff;
  --wp-surface-muted: #f1f4f8;
  --wp-border: #d9dee8;
  --wp-text: #172033;
  --wp-muted: #667085;
  --wp-primary: #2563eb;
  --wp-success-bg: #e8f7ef;
  --wp-success: #157347;
  --wp-warning-bg: #fff4d6;
  --wp-warning: #9a6700;
  --wp-error-bg: #ffe7e6;
  --wp-error: #b42318;
  --wp-neutral-bg: #eef2f7;
  --wp-neutral: #475467;
}

.stApp {
  background: var(--wp-bg);
  color: var(--wp-text);
}

.block-container {
  max-width: 1280px;
  padding-top: 1.4rem;
  padding-bottom: 3rem;
}

h1, h2, h3 {
  letter-spacing: 0;
}

.wp-brand {
  border-bottom: 1px solid var(--wp-border);
  margin: 0 0 1rem;
  padding: 0.25rem 0 1rem;
}

.wp-brand-title {
  color: var(--wp-text);
  font-size: 1.2rem;
  font-weight: 700;
  margin: 0;
}

.wp-brand-caption {
  color: var(--wp-muted);
  font-size: 0.84rem;
  margin: 0.1rem 0 0;
}

.wp-page-head {
  margin-bottom: 1.2rem;
}

.wp-page-kicker {
  color: var(--wp-muted);
  font-size: 0.84rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  margin: 0 0 0.25rem;
  text-transform: uppercase;
}

.wp-page-title {
  color: var(--wp-text);
  font-size: 1.85rem;
  line-height: 1.2;
  margin: 0;
}

.wp-page-desc {
  color: var(--wp-muted);
  font-size: 0.96rem;
  margin: 0.35rem 0 0;
}

.wp-week-head {
  align-items: flex-start;
  background: var(--wp-surface);
  border: 1px solid var(--wp-border);
  border-radius: 8px;
  display: flex;
  gap: 1rem;
  justify-content: space-between;
  margin-bottom: 1rem;
  padding: 1.1rem 1.2rem;
}

.wp-week-title {
  font-size: 1.55rem;
  font-weight: 700;
  margin: 0;
}

.wp-week-range {
  color: var(--wp-muted);
  margin: 0.25rem 0 0;
}

.wp-badge-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  justify-content: flex-end;
}

.wp-badge {
  border-radius: 999px;
  display: inline-flex;
  font-size: 0.78rem;
  font-weight: 700;
  line-height: 1;
  padding: 0.42rem 0.62rem;
  white-space: nowrap;
}

.wp-badge.success {
  background: var(--wp-success-bg);
  color: var(--wp-success);
}

.wp-badge.warning {
  background: var(--wp-warning-bg);
  color: var(--wp-warning);
}

.wp-badge.error {
  background: var(--wp-error-bg);
  color: var(--wp-error);
}

.wp-badge.neutral {
  background: var(--wp-neutral-bg);
  color: var(--wp-neutral);
}

.wp-card-title {
  color: var(--wp-text);
  font-size: 1rem;
  font-weight: 700;
  margin: 0 0 0.35rem;
}

.wp-card-desc {
  color: var(--wp-muted);
  font-size: 0.86rem;
  margin: 0 0 0.7rem;
}

.wp-meta-list {
  display: grid;
  gap: 0.45rem;
}

.wp-meta-row {
  align-items: baseline;
  display: flex;
  gap: 0.8rem;
  justify-content: space-between;
}

.wp-meta-row span {
  color: var(--wp-muted);
  font-size: 0.86rem;
}

.wp-meta-row strong {
  color: var(--wp-text);
  font-size: 0.9rem;
  overflow-wrap: anywhere;
  text-align: right;
}

.wp-empty {
  color: var(--wp-muted);
  font-size: 0.9rem;
  margin: 0;
}

.wp-safe-note {
  background: var(--wp-surface-muted);
  border: 1px solid var(--wp-border);
  border-radius: 8px;
  color: var(--wp-muted);
  font-size: 0.88rem;
  line-height: 1.55;
  padding: 0.8rem 0.9rem;
}

@media (max-width: 900px) {
  .wp-week-head {
    display: block;
  }

  .wp-badge-row {
    justify-content: flex-start;
    margin-top: 0.8rem;
  }
}
</style>
""",
        unsafe_allow_html=True,
    )
